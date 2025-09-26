import uvicorn
from fastapi import FastAPI, HTTPException
import json
from starlette.responses import StreamingResponse
import asyncio

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List

from rest_api import MongoDBCRUD
from rest_api.models import NewsSummaryResult
from rest_api.configs import ConfigModel
from datetime import datetime, timezone

import time
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from news_agent_flow import create_news_agent_flow
from news_agent_flow.models import OutputGenreSummarisedResponseModel


be_config = ConfigModel.from_json_file("rest_api/configs/be_config.json")

in_progress_queries = {}  # key: query, value: asyncio.Lock
partial_results = {}      # key: query, value: list of NewsSummaryResult

#Initialise the FastAPI
app = FastAPI(title="News Summariser")

try:
    mongodb_config = be_config.storage.mongo
    print(f"Starting mongo at {mongodb_config.url}:{mongodb_config.port}")
    # MongoDB setup
    MONGO_DETAILS = f"{mongodb_config.url}:{mongodb_config.port}"
    client = AsyncIOMotorClient(MONGO_DETAILS)
    db = client.news_summary_db
    collection = db.news_summary
except Exception as e:
    print(f"Exception in starting the mongo db {e}")

#Graph instance
graph = create_news_agent_flow()


@app.on_event("startup")
async def startup_event():
    mongodb_config = be_config.storage.mongo
    try:
        # Create TTL index on createdAt (expire after 3600 seconds)
        await collection.create_index("createdAt", expireAfterSeconds=mongodb_config.row_expiry)
        # Create index on genre string
        await collection.create_index([("genre", 1)], unique=True)
    except Exception as e:
        print(f"Exception in starting the mongo db {e}")

class StreamRequest(BaseModel):
    items: List[str]

async def news_agent_stream(query: str):
    query_key = ",".join(sorted(query.split(","))).strip(",")
    event_node_map = be_config.stream_events
    result_key_flow = be_config.stream_sequence

    # Ensure a single running instance per query using a lock
    if query_key not in in_progress_queries:
        in_progress_queries[query_key] = asyncio.Lock()

    lock = in_progress_queries[query_key]

    # If another process is already running, return partial results (if any)
    if lock.locked():
        print(f"Query '{query_key}' is already in progress. Returning partial results.")
        if query_key in partial_results:
            for item in partial_results[query_key]:
                output = {
                    "node_name": item.genre.replace(f"{query_key}_", ""),
                    "node_result": item.result
                }
                yield f"data:{json.dumps(output)}\n\n"
        return

    # Check if already fully stored in MongoDB
    is_all_values_present = await MongoDBCRUD.get_all_documents(f"{query_key}", collection)
    if is_all_values_present and is_all_values_present == len(result_key_flow):
        for keys_flow in result_key_flow:
            result = await MongoDBCRUD.get_document(f"{query_key}_{keys_flow}", collection)
            if result:
                output = {
                    "node_name": keys_flow,
                    "node_result": result.result
                }
                yield f"data:{json.dumps(output)}\n\n"
                time.sleep(5)
        return

    # Otherwise, acquire the lock and start processing
    async with lock:
        partial_results[query_key] = []
        try:
            # Clean up any partial records in DB (from earlier crash)
            await MongoDBCRUD.cleanup(f"{query_key}", collection)

            events = graph.stream({"query": f"latest news on {query_key}"}, stream_mode="updates")

            for event in events:
                for key, value in event.items():
                    if key == "__end__":
                        return  # Skip final state

                    if value.get("has_error"):
                        error = {
                            "error": str(value["error_message"])
                        }
                        yield f"data:{json.dumps(error)}\n\n"
                        # cleanup partial memory
                        partial_results.pop(query_key, None)
                        return

                    if key in event_node_map:
                        result_value = None
                        if isinstance(value[event_node_map[key]], list):
                            result_value = [
                                item if isinstance(item, dict) else item.model_dump()
                                for item in value[event_node_map[key]]
                            ]
                        else:
                            result_value = value[event_node_map[key]].model_dump()

                        output = {
                            "node_name": key,
                            "node_result": result_value if key != "crawl_the_news" else ""
                        }

                        yield f"data:{json.dumps(output)}\n\n"

                        if key != "crawl_the_news":
                            document = {
                                "genre": f"{query_key}_{key}",
                                "result": result_value,
                                "createdAt": datetime.now(timezone.utc)
                            }
                            obj = NewsSummaryResult(**document)
                            partial_results[query_key].append(obj)

                    # Final node: now write to DB
                    if key == "final_genre_summary":
                        for obj in partial_results[query_key]:
                            await MongoDBCRUD.insert_document(obj, collection)
                        # Clean up memory
                        partial_results.pop(query_key, None)
                        return

        except Exception as e:
            print(f"[ERROR] Streaming error for query '{query_key}': {e}")
            partial_results.pop(query_key, None)  # Clean in-memory
            await MongoDBCRUD.cleanup(f"{query_key}", collection)  # Clean in DB
            error = {"error": str(e)}
            yield f"data:{json.dumps(error)}\n\n"
        finally:
            # Always release lock and cleanup
            if query_key in in_progress_queries:
                del in_progress_queries[query_key]


@app.get("/news_summariser")
async def news_summariser(query: str):
    try:
        return StreamingResponse(news_agent_stream(query=query), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def event_stream():
    for i in range(10):
        yield f"data: {i}\n\n"
        await asyncio.sleep(1)  # simulate delay

@app.get("/stream")
async def stream():
    return StreamingResponse(event_stream(), media_type="text/event-stream")
