from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from config import *

db_mongo_client = MongoClient('mongodb://localhost:27017/')
db_mongo_main = db_mongo_client[config_app['db_mongo']['main']['name']]

class model_main_users:
    @staticmethod
    def get(action = None, user_id = None, email = None):
        if action == 'user_id':
            data = db_mongo_main.users.find_one({'_id': user_id})
            return data
        elif action == 'email':
            data = db_mongo_main.users.find_one({'email': email})
            return data
        
        return None

    @staticmethod
    def insert(action = None, user_id = None, name = None, surname = None, email = None, password = None):
        try: 
            if action == 'client':
                document = {
                    '_id': user_id,
                    'name': name,
                    'surname': surname,
                    'email': email,
                    'password': password,
                    'regdate': datetime.utcnow(),
                    'apps': None,
                    'user_role': {'$ref': 'user_roles', '$id': 'normal'}
                } 

                db_mongo_main.users.insert_one(document, bypass_document_validation = True)
                
                return True
            
            return False
        except Exception as e:
            return False

class model_main_user_sessions: 
    @staticmethod
    def get(action = None, session_id = None):
        if action == 'session_id':
            data = db_mongo_main.user_sessions.find_one({'_id': session_id})
            return data
        
        return None  

    @staticmethod
    def insert(action = None, session_id = None, useragent = None, user_id = None):
        try: 
            if action == 'client':
                document = {
                    '_id': session_id,
                    'online': True,
                    'twofacauth': True,
                    'useragent': useragent,
                    'regdate': datetime.utcnow(),
                    'user': {'$ref': 'users', '$id': user_id}
                }

                db_mongo_main.user_sessions.insert_one(document, bypass_document_validation = True)
                
                return True
            
            return False
        except Exception as e:
            return False

    @staticmethod
    def delete(action = None, session_id = None):
        try: 
            if action == 'session':
                document = {
                    '_id': session_id
                } 

                db_mongo_main.user_sessions.delete_many(document)
                
                return True
            
            return False
        except Exception as e:
            return False
        
class model_restaurant_users:
    @staticmethod
    def get(action = None, start = None, length = None, search = None, order_column = '_id', order_direction = 'asc'):
        if action == 'all_table':
            pipeline = [
                {'$lookup': {'from': 'user_roles', 'localField': 'user_role.$id', 'foreignField': '_id', 'as': 'user_role'}},                
                {'$unwind': {'path': '$user_role', 'preserveNullAndEmptyArrays': True}},
                {'$lookup': {'from': 'user_persons', 'localField': 'user_person.$id', 'foreignField': '_id', 'as': 'user_person'}},                
                {'$unwind': {'path': '$user_person', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        '$or': [
                            {'email': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'user_person.name': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'user_person.surname': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'user_role.name': {'$regex': config_searchRegex(search), '$options': 'i'}}
                        ]
                    }
                },
                {'$sort': {order_column: 1 if order_direction == 'asc' else -1}},
                {'$skip': start},
                {'$limit': length}
            ]

            data = list(db_mongo_main.users.aggregate(pipeline))
            return data
        elif action == 'all_table_count':
            pipeline = [
                {'$lookup': {'from': 'user_roles', 'localField': 'user_role.$id', 'foreignField': '_id', 'as': 'user_role'}},                
                {'$unwind': {'path': '$user_role', 'preserveNullAndEmptyArrays': True}},
                {'$lookup': {'from': 'user_persons', 'localField': 'user_person.$id', 'foreignField': '_id', 'as': 'user_person'}},                
                {'$unwind': {'path': '$user_person', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        '$or': [
                            {'email': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'user_person.name': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'user_person.surname': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'user_role.name': {'$regex': config_searchRegex(search), '$options': 'i'}}
                        ]
                    }
                },
                {'$sort': {order_column: 1 if order_direction == 'asc' else -1}},
                {'$count': 'total'}
            ]

            data = list(db_mongo_main.users.aggregate(pipeline))          
            count = data[0]['total'] if data else 0 
            return count        

        return None