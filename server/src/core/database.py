from functools import lru_cache

from pymongo import MongoClient

from src.core.config import MONGO_DB_NAME, MONGO_URI


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    if not MONGO_URI:
        raise RuntimeError("MONGO_URI is not configured")

    return MongoClient(MONGO_URI)


def get_database():
    return get_mongo_client()[MONGO_DB_NAME]
