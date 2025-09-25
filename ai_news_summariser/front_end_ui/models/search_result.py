from pydantic import BaseModel
from typing import List, Optional, Dict

class WebResultItemModel(BaseModel):
    url: str
    title: str
    content: str
    score: float

class WebResponseModel(BaseModel):
    results: List[WebResultItemModel] = []
    response_time: Optional[float] = None
