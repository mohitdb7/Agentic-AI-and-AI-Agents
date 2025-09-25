from pydantic import BaseModel, RootModel
from typing import Dict, List

class SummarisedNewsArticleModel(BaseModel):
    url: str
    title: str | None = None
    summary: str


class NewsGenredSummaryModel(RootModel[Dict[str, List[SummarisedNewsArticleModel]]]):
    pass