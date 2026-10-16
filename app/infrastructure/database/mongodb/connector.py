from pymongo import MongoClient
from pymongo.database import Database


def create_mongo_database(uri: str, database_name: str) -> Database:
    return MongoClient(uri, tz_aware=True)[database_name]
