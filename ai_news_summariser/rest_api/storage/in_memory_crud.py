from datetime import datetime, timedelta, timezone
from rest_api.models import NewsSummaryResult
from .storage_facade import StorageInterface
import asyncio

class InMemoryStorage(StorageInterface):
    def __init__(self, ttl_minutes: int = 10):
        self.db = {}  # key: genre, value: (NewsSummaryResult, expiry_time)
        self.ttl = timedelta(minutes=ttl_minutes)
        self.lock = asyncio.Lock()  # Lock for thread/task safety

    async def setup(self, config):
        pass

    async def _cleanup_expired(self):
        """Removes expired entries from the in-memory store."""
        now = datetime.now(timezone.utc)
        async with self.lock:
            expired_keys = [k for k, (_, exp_time) in self.db.items() if exp_time <= now]
            for k in expired_keys:
                del self.db[k]
            if expired_keys:
                print(f"[Cleanup] Expired {len(expired_keys)} entries.")

    async def get_all_documents_count(self, query: str) -> int:
        await self._cleanup_expired()
        query_lower = query.lower()
        async with self.lock:
            return len([
                v for k, (v, _) in self.db.items()
                if query_lower in k.lower()
            ])

    async def cleanup(self, query: str):
        await self._cleanup_expired()
        query_lower = query.lower()
        async with self.lock:
            to_delete = [k for k in self.db if query_lower in k.lower()]
            for k in to_delete:
                del self.db[k]
            print(f"Deleted {len(to_delete)} documents.")
            return len(to_delete)

    async def get_document(self, query: str):
        await self._cleanup_expired()
        async with self.lock:
            item = self.db.get(query)
            if item:
                value, exp_time = item
                if exp_time > datetime.now(timezone.utc):
                    return value
        print(f"No document found for genre: {query}")
        return None

    async def insert_document(self, news_summary: NewsSummaryResult):
        await self._cleanup_expired()
        expiry_time = datetime.now(timezone.utc) + self.ttl
        async with self.lock:
            self.db[news_summary.genre] = (news_summary, expiry_time)
        print(f"Inserted document in-memory with TTL of {self.ttl}.")
        return "Inserted Successfully"
