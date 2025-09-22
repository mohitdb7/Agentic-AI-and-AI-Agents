from pydantic import BaseModel
from typing import List, Optional
import json
from pathlib import Path


class TavilyResultItem(BaseModel):
    url: str
    title: str
    content: str
    score: float
    raw_content: Optional[str] = None


class TavilyResponse(BaseModel):
    query: str
    follow_up_questions: Optional[str] = None
    answer: Optional[str] = None
    images: List[str] = []
    results: List[TavilyResultItem] = []
    response_time: Optional[float] = None
    request_id: Optional[str] = None

    @staticmethod
    def from_json_file(path: str) -> "TavilyResponse":
        file_path = Path(path)
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return TavilyResponse(**data)