from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from config import *

db_mongo_client = MongoClient('mongodb://localhost:27017/')
db_mongo = db_mongo_client[config_app['db_mongo']['name']]

class model_users:
    @staticmethod
    def get(action = None, user_id = None, email = None):
        if action == "user_id":
            data = db_mongo.users.find_one({"_id": user_id})
            return data
        elif action == "email":
            data = db_mongo.users.find_one({"email": email})
            return data
        
        return None

    @staticmethod
    def insert(user_id, name, surname, email, password):
        document = {
            "_id": user_id,
            "name": name,
            "surname": surname,
            "email": email,
            "password": password,
            "regdate": datetime.utcnow(),
            "user_rol": {"$ref": "user_roles", "$id": "normal"}
        } 

        try: 
            data = db_mongo.users.insert_one(document, bypass_document_validation=True)            
        except Exception as e:
            return False
        
        return True

class model_user_sessions: 
    @staticmethod
    def get(action = None, session_id = None):
        if action == "session_id":
            data = db_mongo.user_sessions.find_one({"_id": session_id})
            return data
        
        return None  

    @staticmethod
    def insert(session_id, useragent, user_id):
        document = {
            "_id": session_id,
            "online": True,
            "twofacauth": True,
            "useragent": useragent,
            "regdate": datetime.utcnow(),
            "user": {"$ref": "users", "$id": user_id}
        } 

        try: 
            data = db_mongo.user_sessions.insert_one(document, bypass_document_validation=True)            
        except Exception as e:
            return False
        
        return True

    @staticmethod
    def delete(session_id):
        document = {
            "_id": session_id
        } 

        try: 
            data = db_mongo.user_sessions.delete_many(document)            
        except Exception as e:
            return False
        
        return True