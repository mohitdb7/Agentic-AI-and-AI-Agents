from abc import ABC, abstractmethod
from rest_api.models import NewsSummaryResult

class StorageInterface(ABC):

    @abstractmethod
    async def get_all_documents(self, query: str):
        pass

    @abstractmethod
    async def cleanup(self, query: str):
        pass

    @abstractmethod
    async def get_document(self, query: str):
        pass

    @abstractmethod
    async def insert_document(self, news_summary: NewsSummaryResult):
        pass

    @abstractmethod
    async def setup(self, config):
        pass
