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

class LLMComponentConfigModel(BaseModel):
    name: str
    model: str
    is_active: bool

class WebCrawl(BaseModel):
    tools: List[SimpleComponentConfigModel]
    parallel_executor: int

class GenreModel(BaseModel):
    assign_genre: List[SimpleComponentConfigModel]
    genre_list: List[str]

class AppConfigModel(BaseModel):
    _llm: List[LLMConfigModel] = PrivateAttr()
    _web_crawl: WebCrawl = PrivateAttr()
    _summarizer: List[LLMComponentConfigModel] = PrivateAttr()
    _genre: GenreModel = PrivateAttr()

    @classmethod
    def from_json_file(cls, file_path: str) -> "AppConfigModel":
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        instance = cls()
        instance._llm = [LLMConfigModel(**llm) for llm in data.get("llm", [])]
        instance._web_crawl = WebCrawl(**data.get("web_crawl", {}))
        instance._summarizer = [LLMComponentConfigModel(**item) for item in data.get("summarizer", [])]
        instance._genre = GenreModel(**data.get("genre", {}))
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
        return self._get_active_or_first(self._web_crawl.tools)
    
    @property
    def web_crawl_parallel(self) -> Optional[int]:
        return self._web_crawl.parallel_executor

    @property
    def active_summarizer(self) -> Optional[LLMComponentConfigModel]:
        return self._get_active_or_first(self._summarizer)
    
    @property
    def genre_list(self) -> List[str]:
        return self._genre.genre_list

    @property
    def active_assign_genre(self) -> Optional[SimpleComponentConfigModel]:
        return self._get_active_or_first(self._genre.assign_genre)