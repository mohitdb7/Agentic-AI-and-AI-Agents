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
from datetime import datetime, timezone



import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from news_agent_flow import create_news_agent_flow
from news_agent_flow.models import OutputGenreSummarisedResponseModel

#Initialise the FastAPI
app = FastAPI(title="News Summariser")

# MongoDB setup
MONGO_DETAILS = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_DETAILS)
db = client.news_summary_db
collection = db.news_summary

#Graph instance
graph = create_news_agent_flow()


@app.on_event("startup")
async def startup_event():
    # Create TTL index on createdAt (expire after 3600 seconds)
    await collection.create_index("createdAt", expireAfterSeconds=5*60)
    # Create index on genre string
    await collection.create_index([("genre", 1)], unique=True)

class StreamRequest(BaseModel):
    items: List[str]

def get_or_create_event_loop():
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        # No running loop in this thread, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

async def news_agent_stream(query: str):
    query = ", ".join(sorted(query.split(","))).strip(",")
    events = graph.stream({"query": f"latest news on {query}"},
                             stream_mode="updates")
    
    event_node_map = {
        "search_the_web" : "results_search",
        "crawl_the_news" : "result_crawl",
        "summarise_the_news" : "news_summary",
        "assign_genre" : "genre_summary",
        "final_genre_summary" : "final_summary"

    }

    results_in_store = False
    result_key_flow = ["search_the_web", "summarise_the_news", "assign_genre", "final_genre_summary"]
    for keys_flow in result_key_flow:
        result = await MongoDBCRUD.get_document(f"{query}_{keys_flow}", collection)
        if not result:
            break

        output = {
                    "node_name": keys_flow,
                    "node_result": result.result
                }
        yield f"data:{json.dumps(output)}\n\n"
        results_in_store = True

    if results_in_store:
        return
    
     # Stream the updates
    for event in events:
        for key, value in event.items():
                print("Key is ", key)
                if key == "__end__":
                    continue  # Skips the final END state
                
                result_value = None
                if isinstance(value[event_node_map[key]], list):
                     result_value = [
                                        item if isinstance(item, dict) else item.model_dump()
                                        for item in value[event_node_map[key]]
                                    ]
                else:
                     result_value = value[event_node_map[key]].model_dump()

                if event_node_map.get(key):
                    print("Inside If: ", key)
                    output = {
                        "node_name": key,
                        "node_result": result_value if key != "crawl_the_news" else ""
                    }
                    yield f"data:{json.dumps(output)}\n\n"

                    if key != "crawl_the_news":
                        document = {
                            "genre" : f"{query}_{key}",
                            "result": result_value,
                            "createdAt": datetime.now(timezone.utc)
                        }

                        print(f"Inserting {query}_{key}, Value of {type(result_value)}")
                        obj = NewsSummaryResult(**document)
                        print(f"Insertied {query}_{key}")
                        # loop = get_or_create_event_loop()

                        # future = loop.run_until_complete(MongoDBCRUD.insert_document(obj, db, collection))
                        # print(f"Result Id is {future}")

                        res = await MongoDBCRUD.insert_document(obj, collection)
                        print("After insert", res)

                    if key == "final_genre_summary":
                        return

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
