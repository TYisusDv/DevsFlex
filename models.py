from pymongo import MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError
from config import *

db_mongo_client = MongoClient('mongodb://localhost:27017/')
db_mongo_main = db_mongo_client[config_app['db_mongo']['main']['name']]
db_mongo_restaurant = db_mongo_client[config_app['db_mongo']['restaurant']['name']]

def model_next_count(name):
    result = db_mongo_main.counters.find_one_and_update(
        {'_id': name},
        {'$inc': {'seq': 1}},
        upsert = True,
        return_document = ReturnDocument.AFTER
    )
    return result['seq']      

def model_restaurant_next_count(name):
    result = db_mongo_restaurant.counters.find_one_and_update(
        {'_id': name},
        {'$inc': {'seq': 1}},
        upsert = True,
        return_document = ReturnDocument.AFTER
    )
    return result['seq'] 

class model_main_users:
    @staticmethod
    def get(action = None, start = None, length = None, search = None, order_column = '_id', order_direction = 'asc', user_id = None, email = None, status = False):
        if action == 'user_id':
            data = db_mongo_main.users.find_one({'_id': user_id})
            return data
        elif action == 'email':
            data = db_mongo_main.users.find_one({'email': email})
            return data
        elif action == 'one':
            pipeline = [
                {'$lookup': {'from': 'user_roles', 'localField': 'user_role.$id', 'foreignField': '_id', 'as': 'user_role'}},                
                {'$unwind': {'path': '$user_role', 'preserveNullAndEmptyArrays': True}},
                {'$lookup': {'from': 'user_persons', 'localField': 'user_person.$id', 'foreignField': '_id', 'as': 'user_person'}},                
                {'$unwind': {'path': '$user_person', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        '_id': user_id
                    }
                },
                {'$limit': 1}
            ]

            data = list(db_mongo_main.users.aggregate(pipeline))
            if not data:
                return None
            return data[0]
        elif action == 'all_table':
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
                            {'user_role.name': {'$regex': config_searchRegex(search), '$options': 'i'}},
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
                            {'user_person.phone': {'$regex': config_searchRegex(search), '$options': 'i'}},
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
        elif action == 'count_status':
            pipeline = [
                {
                    '$match': {
                        'status': status,
                    }
                },
                {'$count': 'total'}
            ]

            data = list(db_mongo_main.users.aggregate(pipeline))          
            count = data[0]['total'] if data else 0 
            return count        

        return None
    
    @staticmethod
    def insert(action = None, user_id = None, name = None, surname = None, email = None, password = 'x'):
        try: 
            if action == 'one_register':
                v_model_person = model_main_user_persons.insert(action = 'one_register', name = name, surname = surname)
                if v_model_person[0]:
                    document = {
                        '_id': user_id,                    
                        'email': email,
                        'password': password,
                        'access': [],
                        'regdate': datetime.utcnow(),
                        'status': True,
                        'user_person': {'$ref': 'user_persons', '$id': v_model_person[1]},
                        'user_role': {'$ref': 'user_roles', '$id': 'normal'}
                    } 

                    db_mongo_main.users.insert_one(document, bypass_document_validation = True)
                    
                    return True
            return False
        except Exception as e:
            return False
    
    @staticmethod
    def update(action = None, user_id = None, email = None, password = 'x', status = False):
        try:
            if action == 'one':
                document = {'_id': user_id} 

                update = {
                    '$set': {
                        'email': email,
                        'password': password,
                        'status': status,
                    }
                }

                db_mongo_main.users.update_one(document, update)
                return True
            
            return False
        except Exception as e:
            return False

class model_main_user_persons:
    @staticmethod
    def get(action = None, user_person_id = None, email = None):
                
        return None

    @staticmethod
    def insert(action = None, name = None, surname = None):
        try: 
            if action == 'one_register':
                new_id = model_next_count('user_person_id')
                document = {
                    '_id': new_id,
                    'name': name,
                    'surname': surname,
                    'phone': None
                } 

                db_mongo_main.user_persons.insert_one(document, bypass_document_validation = True)
                
                return True, new_id
            
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

class model_restaurant_order_types:
    @staticmethod
    def get(action = None, start = None, length = None, search = None, order_column = '_id', order_direction = 'asc', order_type_id = None, status = False):
        if action == 'one':            
            data = db_mongo_restaurant.order_types.find_one({'_id': order_type_id})
            return data
        elif action == 'all_table':
            pipeline = [
                {
                    '$match': {
                        '$or': [
                            {'_id': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'name': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'status': {'$regex': config_searchRegex(search), '$options': 'i'}}
                        ]
                    }
                },
                {'$sort': {order_column: 1 if order_direction == 'asc' else -1}},
                {'$skip': start},
                {'$limit': length}
            ]

            data = list(db_mongo_restaurant.order_types.aggregate(pipeline))
            return data
        elif action == 'all_table_count':
            pipeline = [
                {
                    '$match': {
                        '$or': [
                            {'_id': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'name': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'status': {'$regex': config_searchRegex(search), '$options': 'i'}}
                        ]
                    }
                },
                {'$sort': {order_column: 1 if order_direction == 'asc' else -1}},
                {'$count': 'total'}
            ]

            data = list(db_mongo_restaurant.order_types.aggregate(pipeline))          
            count = data[0]['total'] if data else 0 
            return count        
        elif action == 'count_status':
            pipeline = [
                {
                    '$match': {
                        'status': status,
                    }
                },
                {'$count': 'total'}
            ]

            data = list(db_mongo_restaurant.order_types.aggregate(pipeline))          
            count = data[0]['total'] if data else 0 
            return count  
        return None

    @staticmethod
    def insert(action = None, name = None):
        try:
            if action == 'one':
                document = {
                    '_id': model_restaurant_next_count('order_type_id'),
                    'name': name,
                    'status': False
                }

                db_mongo_restaurant.order_types.insert_one(document)
                return True
            
            return False
        except Exception as e:
            return False
        
    @staticmethod
    def update(action = None, order_type_id = None, name = None, status = False):
        try:
            if action == 'one':
                document = {'_id': order_type_id} 

                update = {
                    '$set': {
                        'name': name,
                        'status': status,
                    }
                }

                db_mongo_restaurant.order_types.update_one(document, update)
                return True
            
            return False
        except Exception as e:
            return False

class model_restaurant_product_categories:
    @staticmethod
    def get(action = None, start = None, length = None, search = None, order_column = '_id', order_direction = 'asc', product_category_id = None, status = False):
        if action == 'one':            
            data = db_mongo_restaurant.product_categories.find_one({'_id': product_category_id})
            return data
        elif action == 'all_table':
            pipeline = [
                {
                    '$match': {
                        '$or': [
                            {'_id': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'name': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'status': {'$regex': config_searchRegex(search), '$options': 'i'}}
                        ]
                    }
                },
                {'$sort': {order_column: 1 if order_direction == 'asc' else -1}},
                {'$skip': start},
                {'$limit': length}
            ]

            data = list(db_mongo_restaurant.product_categories.aggregate(pipeline))
            return data
        elif action == 'all_table_count':
            pipeline = [
                {
                    '$match': {
                        '$or': [
                            {'_id': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'name': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'status': {'$regex': config_searchRegex(search), '$options': 'i'}}
                        ]
                    }
                },
                {'$sort': {order_column: 1 if order_direction == 'asc' else -1}},
                {'$count': 'total'}
            ]

            data = list(db_mongo_restaurant.product_categories.aggregate(pipeline))          
            count = data[0]['total'] if data else 0 
            return count        
        elif action == 'count_status':
            pipeline = [
                {
                    '$match': {
                        'status': status,
                    }
                },
                {'$count': 'total'}
            ]

            data = list(db_mongo_restaurant.product_categories.aggregate(pipeline))          
            count = data[0]['total'] if data else 0 
            return count        

        return None

    @staticmethod
    def insert(action = None, name = None):
        try:
            if action == 'one':
                document = {
                    '_id': model_restaurant_next_count('product_category_id'),
                    'name': name,
                    'status': False
                }

                db_mongo_restaurant.product_categories.insert_one(document)
                return True
            
            return False
        except Exception as e:
            return False
        
    @staticmethod
    def update(action = None, product_category_id = None, name = None, status = False):
        try:
            if action == 'one':
                document = {'_id': product_category_id} 

                update = {
                    '$set': {
                        'name': name,
                        'status': status,
                    }
                }

                db_mongo_restaurant.product_categories.update_one(document, update)
                return True
            
            return False
        except Exception as e:
            return False