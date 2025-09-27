from fastapi import FastAPI, HTTPException
from starlette.responses import StreamingResponse
import asyncio
from pydantic import BaseModel
from typing import List
import os
import sys
from fastapi import Request
from rest_api import RequestMiddleware

# Import your custom logger
from rest_api.utils import (
    cleanup_old_logs,
    log_with_context
)
from rest_api.business_logic import NewsSummarizer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from rest_api.configs import ConfigModel

class StreamRequest(BaseModel):
    items: List[str]


app = FastAPI(title="News Summariser")
app.add_middleware(RequestMiddleware)
be_config = ConfigModel.from_json_file("rest_api/configs/be_config.json")


news_summarizer = NewsSummarizer(be_config)


@app.on_event("startup")
async def startup_event():
    try:
        # Cleanup old logs on startup
        cleanup_old_logs(days=be_config.log_expiry.days, hours=be_config.log_expiry.hours, minutes=be_config.log_expiry.minutes)

        await news_summarizer.startup_setup()
        log_with_context("app_startup", {"event": "Application startup completed successfully"}, source="undecided", request_id="Startup")
    except Exception as e:
        log_with_context("app_startup", {"event": "Application startup failed"}, source="undecided", request_id="Startup", error=str(e))


@app.get("/news_summariser")
async def news_summariser_endpoint(query: str, request: Request):
    try:
        cleanup_old_logs(days=be_config.log_expiry.days, hours=be_config.log_expiry.hours, minutes=be_config.log_expiry.minutes)
        request_id = request.state.request_id

        # Wrap query into dict for log_node decorator signature
        state = {
            "query": query,
            "request_id": request_id
            }
        
        return StreamingResponse(news_summarizer.news_agent_stream(state), 
                                 media_type="text/event-stream", 
                                 headers={"X-Request-ID": request_id})
    except Exception as e:
        log_with_context("api_error", {"event": "Application startup failed"}, source="undecided", request_id=request.state.request_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Stream Testing code
async def _event_stream():
    for i in range(10):
        yield f"data: {i}\n\n"
        await asyncio.sleep(1)


@app.get("/stream")
async def stream(request: Request):
    return StreamingResponse(_event_stream(), media_type="text/event-stream")

@app.get("/")
async def read_root(request: Request):
    return {"request_id": request.state.request_id}
