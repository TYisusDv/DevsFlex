from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from config import *

db_mongo_client = MongoClient('mongodb://localhost:27017/')
db_mongo = db_mongo_client[config_app['db_mongo']['name']]