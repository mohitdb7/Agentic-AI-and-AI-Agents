# Pydantic model for input data
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class NewsSummaryResult(BaseModel):
    genre: str = Field(..., description="List of genres separated by comma")
    result: dict | list = Field(..., description="News results")
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))