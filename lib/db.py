import os
import pymongo

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client["griffith-punters"]

users_collection = db["users"]
markets_collection = db["markets"]