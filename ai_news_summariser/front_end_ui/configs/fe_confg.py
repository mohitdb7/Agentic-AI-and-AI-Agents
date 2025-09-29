from typing import List, Dict
from pydantic import BaseModel
import json
from pathlib import Path


class EndpointConfigModel(BaseModel):
    method: str
    transport_type: str
    url: str
    query_param: List[str]


class FE_ConfigModel(BaseModel):
    base_url: str
    port: int
    endpoints: Dict[str, EndpointConfigModel]
    genres: List[str]

    @staticmethod
    def from_json_file(file_path: str) -> "FE_ConfigModel":
        with open(file_path, 'r') as f:
            data = json.load(f)
        return FE_ConfigModel(**data)
