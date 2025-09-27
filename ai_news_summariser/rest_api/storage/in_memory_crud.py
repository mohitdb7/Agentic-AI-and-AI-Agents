from rest_api.models import NewsSummaryResult
from .storage_facade import StorageInterface

class InMemoryStorage(StorageInterface):
    def __init__(self):
        self.db = {}

    async def setup(self, config):
        pass

    async def get_all_documents(self, query: str):
        return len([v for k, v in self.db.items() if query.lower() in k.lower()])

    async def cleanup(self, query: str):
        to_delete = [k for k in self.db if query.lower() in k.lower()]
        for k in to_delete:
            del self.db[k]
        print(f"Deleted {len(to_delete)} documents.")
        return len(to_delete)

    async def get_document(self, query: str):
        if query in self.db:
            return self.db[query]
        print(f"No document found for genre: {query}")
        return None

    async def insert_document(self, news_summary: NewsSummaryResult):
        self.db[news_summary.genre] = news_summary
        print("Inserted document in-memory")
        return "Inserted Successfully"
