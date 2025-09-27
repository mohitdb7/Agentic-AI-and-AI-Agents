import uvicorn
from fastapi import FastAPI, HTTPException
import json
from starlette.responses import StreamingResponse
import asyncio

from pydantic import BaseModel
from typing import List
from rest_api.models import NewsSummaryResult
from rest_api.configs import ConfigModel
from datetime import datetime, timezone

import time
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from news_agent_flow import create_news_agent_with_final_summary_flow
from rest_api.storage import StorageManager


be_config = ConfigModel.from_json_file("rest_api/configs/be_config.json")

in_progress_queries = {}  # key: query, value: asyncio.Lock
partial_results = {}      # key: query, value: list of NewsSummaryResult
# New dictionary to store complete results temporarily
complete_results = {}     # key: query, value: list of NewsSummaryResult

#Initialise the FastAPI
app = FastAPI(title="News Summariser")

# try:
#     mongodb_config = be_config.storage.mongo
#     print(f"Starting mongo at {mongodb_config.url}:{mongodb_config.port}")
#     # MongoDB setup
#     MONGO_DETAILS = f"{mongodb_config.url}:{mongodb_config.port}"
#     client = AsyncIOMotorClient(MONGO_DETAILS)
#     db = client.news_summary_db
#     collection = db.news_summary
# except Exception as e:
#     print(f"Exception in starting the mongo db {e}")

StorageManager.initialize()

#Graph instance
graph_final_summary = create_news_agent_with_final_summary_flow()


@app.on_event("startup")
async def startup_event():
    # mongodb_config = be_config.storage.mongo
    # try:
    #     # Create TTL index on createdAt (expire after 3600 seconds)
    #     await collection.create_index("createdAt", expireAfterSeconds=mongodb_config.row_expiry)
    #     # Create index on genre string
    #     await collection.create_index([("genre", 1)], unique=True)
    # except Exception as e:
    #     print(f"Exception in starting the mongo db {e}")
    StorageManager.startup_setup()

class StreamRequest(BaseModel):
    items: List[str]

async def news_agent_stream(query: str):
    query_key = ",".join(sorted(query.split(","))).strip(",").strip(' ')
    event_node_map = be_config.stream_events
    result_key_flow = be_config.stream_sequence

    if query_key not in in_progress_queries:
        in_progress_queries[query_key] = asyncio.Lock()

    lock = in_progress_queries[query_key]

    # If query is in progress, stream from partial results
    # if lock.locked():
    #     print(f"Query '{query_key}' is already in progress. Returning partial results.")
    #     if query_key in partial_results:
    #         for item in partial_results[query_key]:
    #             output = {
    #                 "node_name": item.genre.replace(f"{query_key}_", ""),
    #                 "node_result": item.result
    #             }
    #             yield f"data:{json.dumps(output)}\n\n"
    #     return

    # Check if results are already stored in database
    is_all_values_present = await StorageManager.get_all_documents(f"{query_key}")
    if is_all_values_present and is_all_values_present == len(result_key_flow):
        for keys_flow in result_key_flow:
            result = await StorageManager.get_document(f"{query_key}_{keys_flow}")
            if result:
                output = {
                    "node_name": keys_flow,
                    "node_result": result.result
                }
                yield f"data:{json.dumps(output)}\n\n"
                time.sleep(5)
        return

    async with lock:
        # Initialize temporary storage for this query
        partial_results[query_key] = []
        complete_results[query_key] = []
        
        streaming_completed = False
        streaming_error = None

        try:
            await StorageManager.cleanup(f"{query_key}")
            events = graph_final_summary.stream({"query": f"latest news on {query_key}"}, stream_mode="updates")

            for event in events:
                for key, value in event.items():
                    print(f"Current Key is {key}")
                    if key == "__end__":
                        print("reached end {streaming_completed or streaming_error}")
                        streaming_completed = True
                        break  # Exit the inner loop

                    if value.get("has_error"):
                        streaming_error = str(value["error_message"])
                        error = {"error": streaming_error}
                        yield f"data:{json.dumps(error)}\n\n"
                        break  # Exit the inner loop

                    if key in event_node_map:
                        result_value = (
                            [item if isinstance(item, dict) else item.model_dump()
                             for item in value[event_node_map[key]]]
                            if isinstance(value[event_node_map[key]], list)
                            else value[event_node_map[key]].model_dump()
                        )

                        output = {
                            "node_name": key,
                            "node_result": result_value if key != "crawl_the_news" else ""
                        }

                        # Stream to user immediately
                        yield f"data:{json.dumps(output)}\n\n"

                        # Store in temporary collections (but don't save to database yet)
                        if key != "crawl_the_news":
                            document = {
                                "genre": f"{query_key}_{key}",
                                "result": result_value,
                                "createdAt": datetime.now(timezone.utc)
                            }
                            obj = NewsSummaryResult(**document)
                            # Add to both partial results (for concurrent requests) and complete results
                            partial_results[query_key].append(obj)
                            complete_results[query_key].append(obj)
                        
                        if key == "final_genre_summary":
                            streaming_completed = True
                        
                    await asyncio.sleep(0.5)
                
                # If we broke out of inner loop due to end or error, break outer loop too
                if streaming_completed or streaming_error:
                    print(f"reached {streaming_completed or streaming_error} - {streaming_error}")
                    break

        except Exception as e:
            print(f"[ERROR] Streaming error for query '{query_key}': {e}")
            streaming_error = str(e)
            error = {"error": streaming_error}
            yield f"data:{json.dumps(error)}\n\n"
            await StorageManager.cleanup(f"{query_key}")
        finally:
            # Only save to storage if streaming completed successfully
            if streaming_completed and (not streaming_error) and (query_key in complete_results):
                try:
                    print(f"[INFO] Streaming completed successfully for '{query_key}'. Saving to storage...")
                    for obj in complete_results[query_key]:
                        await StorageManager.insert_document(obj)
                    print(f"[INFO] Successfully saved {len(complete_results[query_key])} results for '{query_key}'")
                except Exception as e:
                    print(f"[ERROR] Failed to store results for '{query_key}': {e}")
                    # Optionally, you could retry storage here
            else:
                print(f"{streaming_completed} - {streaming_error} - {query_key in complete_results}")
                if streaming_error:
                    print(f"[INFO] Not saving results for '{query_key}' due to streaming error: {streaming_error}")
                else:
                    print(f"[INFO] Not saving results for '{query_key}' - streaming not completed successfully")

            # Clean up temporary storage
            partial_results.pop(query_key, None)
            complete_results.pop(query_key, None)

            # Remove the query from in_progress_queries
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