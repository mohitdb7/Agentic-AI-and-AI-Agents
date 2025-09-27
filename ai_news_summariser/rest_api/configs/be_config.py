from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional
from pathlib import Path
import json


class MongoConfig(BaseModel):
    url: str
    port: int
    row_expiry: int
    is_active: bool


class LocalStorageConfig(BaseModel):
    is_active: bool


class StorageConfig(BaseModel):
    mongo: MongoConfig
    local: LocalStorageConfig


class ServerConfig(BaseModel):
    path: str
    host: str
    port: int


class ConfigModel(BaseModel):
    storage: StorageConfig
    stream_sequence: List[str]
    stream_events: Dict[str, str]
    server_config: ServerConfig

    @property
    def active_storage(self) -> Optional[Dict[str, BaseModel]]:
        for name, config in self.storage.__dict__.items():
            if getattr(config, "is_active", False):
                return {name: config}
        return None

    @staticmethod
    def from_json_file(file_path: str) -> "ConfigModel":
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return ConfigModel(**data)

