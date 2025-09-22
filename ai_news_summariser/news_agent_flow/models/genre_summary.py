from typing import List, Dict
from pydantic import BaseModel, HttpUrl
import json
from pathlib import Path
from .news_summary import SummarisedNewsArticle


class GenreSumarisedModel(BaseModel):
    categories: Dict[str, List[SummarisedNewsArticle]]

    @staticmethod
    def from_json_file(file_path: str) -> 'GenreSumarisedModel':
        """Reads a JSON file and returns a validated TechDigest object."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        return GenreSumarisedModel(categories=raw_data["categories"])

class FinalGenreSummaryModel(BaseModel):
    genre: str
    summary: str

    @staticmethod
    def from_json_file(file_path: str) -> List['FinalGenreSummaryModel']:
        """Reads a JSON file and returns a list of FinalGenreSummary objects."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        return [
        FinalGenreSummaryModel(genre=genre, summary=summary_data.get("final_summary", ""))
        for genre, summary_data in raw_data.items() 
        ]