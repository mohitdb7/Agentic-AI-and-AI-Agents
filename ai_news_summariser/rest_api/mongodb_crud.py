from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

from rest_api.models import NewsSummaryResult
from pydantic import BaseModel, Field, ValidationError


class MongoDBCRUD:
    @staticmethod
    async def get_document(query: str, collection):
        try:
            # Query MongoDB for matching genre
            document = await collection.find_one({"genre": query})
            if document:
                # Convert Mongo document to Pydantic model (exclude Mongo's '_id')
                document.pop("_id", None)
                return NewsSummaryResult(**document)
            else:
                print(f"No document found for genre: {query}")
        except ValidationError as ve:
            print(f"Validation Error on retrieved document: {ve}")
        except PyMongoError as e:
            print(f"MongoDB Retrieval Error: {e}")
        except Exception as e:
            print(f"Unexpected error during retrieval: {e}")
        return None
    
    @staticmethod
    async def insert_document(news_summary: NewsSummaryResult, collection):
        try:
            document = news_summary.dict()
            # Define the key filter to find the document to update (change 'id' to your unique key)
            key_filter = {"genre": document["genre"]}
            result = await collection.update_one(
                                                key_filter,
                                                {"$set": document},
                                                upsert=True)
            print(f"Inserted document with ID: {result}")
            return "Inserted Successfully"
        except ValidationError as ve:
            print(f"Validation Error: {ve}")
        except PyMongoError as e:
            print(f"MongoDB Insert Error: {e}")
        except Exception as e:
            print(f"Unexpected error during insert: {e}")
        return None