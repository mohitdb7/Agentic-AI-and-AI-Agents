from pydantic import BaseModel, HttpUrl
from typing import List
from pathlib import Path
import json

class TavilyCrawlItemModel(BaseModel):
    url: str
    raw_content: str


class TavilyCrawlListModel(BaseModel):
    base_url: str
    results: List[TavilyCrawlItemModel]
    response_time: float
    request_id: str

    @staticmethod
    def from_json_file(file_path: str) -> List["TavilyCrawlListModel"]:
        """
        Load and parse a list of ResponseItem objects from a JSON file.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"No such file: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return [TavilyCrawlListModel(**item) for item in data]