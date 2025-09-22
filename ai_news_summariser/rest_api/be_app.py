import uvicorn
from fastapi import FastAPI, HTTPException
import json
from starlette.responses import StreamingResponse
import asyncio


import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from news_agent_flow import create_news_agent_flow
from news_agent_flow.models import OutputGenreSummarisedResponseModel

app = FastAPI(title="News Summariser")

graph = create_news_agent_flow()


def news_agent_stream():
    events = graph.stream({"query": "latest news on AI, Technology, Entertainment, Politics, World and Sports"},
                             stream_mode="updates")
    
    event_node_map = {
        "search_the_web" : "results_search",
        "crawl_the_news" : "result_crawl",
        "summarise_the_news" : "news_summary",
        "assign_genre" : "genre_summary",
        "final_genre_summary" : "final_summary"

    }
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

                    if key == "final_genre_summary":
                        return

@app.get("/news_summariser")
async def news_summariser():
    try:
        return StreamingResponse(news_agent_stream(), media_type="text/event-stream")

        # result = (await graph.ainvoke({"query": "latest news on AI advancements in the last week"}))["final_summary"]

        # return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def event_stream():
    for i in range(10):
        yield f"data: {i}\n\n"
        await asyncio.sleep(1)  # simulate delay

@app.get("/stream")
async def stream():
    return StreamingResponse(event_stream(), media_type="text/event-stream")
