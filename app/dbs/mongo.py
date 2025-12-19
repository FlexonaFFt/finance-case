"""
Mongo connector placeholder.
Initialize an async client here when moving ingestion storage out of memory.
"""
import os
from dataclasses import dataclass


@dataclass
class MongoSettings:
    user: str = os.getenv("MONGO_INITDB_ROOT_USERNAME", "mongo")
    password: str = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "mongo")
    host: str = os.getenv("MONGO_HOST", "mongo")
    port: int = int(os.getenv("MONGO_PORT", "27017"))
    db: str = os.getenv("MONGO_DB", "finance_raw")

    @property
    def uri(self) -> str:
        return f"mongodb://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


settings = MongoSettings()

# Example stub (uncomment when motor/pymongo is added):
# from motor.motor_asyncio import AsyncIOMotorClient
# client = AsyncIOMotorClient(settings.uri, retryWrites=True)
# db = client[settings.db]
