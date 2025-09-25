from pydantic import BaseModel, PrivateAttr
from typing import List, Optional
import json
from pathlib import Path

class ModelConfigModel(BaseModel):
    langchain: str
    crew_ai: str
    default: str

class LLMConfigModel(BaseModel):
    name: str
    model: ModelConfigModel
    temprature: float
    is_active: bool

class SimpleComponentConfigModel(BaseModel):
    name: str
    is_active: bool

class AppConfigModel(BaseModel):
    _llm: List[LLMConfigModel] = PrivateAttr()
    _web_crawl: List[SimpleComponentConfigModel] = PrivateAttr()
    _summarizer: List[SimpleComponentConfigModel] = PrivateAttr()
    _assign_genre: List[SimpleComponentConfigModel] = PrivateAttr()

    @classmethod
    def from_json_file(cls, file_path: str) -> "AppConfigModel":
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        instance = cls()
        instance._llm = [LLMConfigModel(**llm) for llm in data.get("llm", [])]
        instance._web_crawl = [SimpleComponentConfigModel(**item) for item in data.get("web_crawl", [])]
        instance._summarizer = [SimpleComponentConfigModel(**item) for item in data.get("summarizer", [])]
        instance._assign_genre = [SimpleComponentConfigModel(**item) for item in data.get("assign_genre", [])]
        return instance

    def _get_active_or_first(self, items: List[BaseModel]) -> Optional[BaseModel]:
        active_items = [item for item in items if item.is_active]
        if len(active_items) == 1:
            return active_items[0]
        return items[0] if items else None
    
    def get_llm_by_name(self, name: str) -> Optional[LLMConfigModel]:
        return next((llm for llm in self._llm if llm.name == name), None)

    @property
    def active_llm(self) -> Optional[LLMConfigModel]:
        return self._get_active_or_first(self._llm)

    @property
    def active_web_crawl(self) -> Optional[SimpleComponentConfigModel]:
        return self._get_active_or_first(self._web_crawl)

    @property
    def active_summarizer(self) -> Optional[SimpleComponentConfigModel]:
        return self._get_active_or_first(self._summarizer)

    @property
    def active_assign_genre(self) -> Optional[SimpleComponentConfigModel]:
        return self._get_active_or_first(self._assign_genre)