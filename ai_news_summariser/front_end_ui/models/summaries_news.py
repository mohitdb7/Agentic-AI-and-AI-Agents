from pydantic import BaseModel

class SummarisedNewsArticleModel(BaseModel):
    url: str
    title: str | None = None
    summary: str