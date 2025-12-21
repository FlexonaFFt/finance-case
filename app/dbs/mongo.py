"""
Mongo connector for logging transfer events.
"""
import os
from dataclasses import dataclass

from pymongo import MongoClient


@dataclass
class MongoSettings:
    uri: str = os.getenv("MONGO_URI", "mongodb://mongo:27017")
    db_name: str = os.getenv("MONGO_DB", "finance_logs")


settings = MongoSettings()
client = MongoClient(settings.uri)
db = client[settings.db_name]
transfers_collection = db.get_collection("transfer_events")
