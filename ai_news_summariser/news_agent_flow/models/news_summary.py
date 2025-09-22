from typing import List
from pydantic import BaseModel, HttpUrl
import json

class SummarisedNewsArticle(BaseModel):
    url: str
    title: str | None = None
    summary: str

    @staticmethod
    def from_file(file_path: str) -> List['SummarisedNewsArticle']:
        """
        Reads a JSON file and returns a list of Article instances.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [SummarisedNewsArticle(**item) for item in data]