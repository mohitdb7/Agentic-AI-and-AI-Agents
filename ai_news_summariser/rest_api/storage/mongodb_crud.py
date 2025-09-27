from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import PyMongoError
from pydantic import ValidationError
from rest_api.models import NewsSummaryResult
from .storage_facade import StorageInterface

class MongoDBStorage(StorageInterface):
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def setup(self, config):
        try:
            # Create TTL index on createdAt (expire after 3600 seconds)
            await self.collection.create_index("createdAt", expireAfterSeconds=config.row_expiry)
            # Create index on genre string
            await self.collection.create_index([("genre", 1)], unique=True)
        except Exception as e:
            print(f"Exception in starting the mongo db {e}")

    async def get_all_documents_count(self, query: str) -> int:
        try:
            cursor = self.collection.find({"genre": {"$regex": query, "$options": "i"}})
            documents = await cursor.to_list(length=None)
            return len(documents)
        except Exception as e:
            print(f"Exception in get_all_documents {str(e)}")

    async def cleanup(self, query: str):
        try:
            result = await self.collection.delete_many({"genre": {"$regex": query, "$options": "i"}})
            print(f"Deleted {result.deleted_count} documents.")
            return result.deleted_count
        except Exception as e:
            print(f"Exception while delete attempt {query}, {str(e)}")
            return 0

    async def get_document(self, query: str):
        try:
            document = await self.collection.find_one({"genre": query})
            if document:
                document.pop("_id", None)
                return NewsSummaryResult(**document)
            else:
                print(f"No document found for genre: {query}")
        except ValidationError as ve:
            print(f"Validation Error: {ve}")
        except PyMongoError as e:
            print(f"MongoDB Retrieval Error: {e}")
        except Exception as e:
            print(f"Unexpected error during retrieval: {e}")
        return None

    async def insert_document(self, news_summary: NewsSummaryResult):
        try:
            document = news_summary.dict()
            key_filter = {"genre": document["genre"]}
            result = await self.collection.update_one(
                key_filter,
                {"$set": document},
                upsert=True
            )
            print(f"Inserted document with result: {result}")
            return "Inserted Successfully"
        except ValidationError as ve:
            print(f"Validation Error: {ve}")
        except PyMongoError as e:
            print(f"MongoDB Insert Error: {e}")
        except Exception as e:
            print(f"Unexpected error during insert: {e}")
        return None
