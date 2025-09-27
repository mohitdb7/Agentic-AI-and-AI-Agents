from motor.motor_asyncio import AsyncIOMotorClient
from rest_api.models import NewsSummaryResult
from .storage_facade import StorageInterface
from .mongodb_crud import MongoDBStorage
from .in_memory_crud import InMemoryStorage
from rest_api.configs import ConfigModel

be_config = ConfigModel.from_json_file("rest_api/configs/be_config.json")

class StorageManager:
    _instance: StorageInterface = None

    @classmethod
    def initialize(cls):
        if cls._instance is not None:
            return  # Already initialized

        if be_config.active_storage and "mongo" in be_config.active_storage:
            try:
                mongodb_config = be_config.storage.mongo
                print(f"Starting mongo at {mongodb_config.url}:{mongodb_config.port}")
                # MongoDB setup
                MONGO_DETAILS = f"{mongodb_config.url}:{mongodb_config.port}"
                client = AsyncIOMotorClient(MONGO_DETAILS)
                db = client.news_summary_db
                collection = db.news_summary
                cls._instance = MongoDBStorage(collection)
            except Exception as e:
                print(f"Failed to init the mongoDB - {str(e)}")
                cls._instance = InMemoryStorage()
        else:
            cls._instance = InMemoryStorage()

    @classmethod
    async def startup_setup(cls):
        await cls._get_instance().setup(be_config.active_storage)

    @classmethod
    def _get_instance(cls) -> StorageInterface:
        if cls._instance is None:
            raise RuntimeError("StorageManager is not initialized.")
        return cls._instance

    @classmethod
    async def insert_document(cls, news_summary: NewsSummaryResult):
        return await cls._get_instance().insert_document(news_summary)

    @classmethod
    async def get_document(cls, query: str):
        return await cls._get_instance().get_document(query)

    @classmethod
    async def get_all_documents_count(cls, query: str) -> int:
        return await cls._get_instance().get_all_documents_count(query)

    @classmethod
    async def cleanup(cls, query: str):
        return await cls._get_instance().cleanup(query)
