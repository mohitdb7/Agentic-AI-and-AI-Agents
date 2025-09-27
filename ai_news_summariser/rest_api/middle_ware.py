import uuid
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

class RequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        # Store it in request.state
        request.state.request_id = request_id

        # Add it to the response header for traceability
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response