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
                {'$lookup': {'from': 'persons', 'localField': 'person.$id', 'foreignField': '_id', 'as': 'person'}},                
                {'$unwind': {'path': '$person', 'preserveNullAndEmptyArrays': True}},
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
                {'$lookup': {'from': 'persons', 'localField': 'person.$id', 'foreignField': '_id', 'as': 'person'}},                
                {'$unwind': {'path': '$person', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        '$or': [
                            {'email': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'person.name': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'person.surname': {'$regex': config_searchRegex(search), '$options': 'i'}},
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
                {'$lookup': {'from': 'persons', 'localField': 'person.$id', 'foreignField': '_id', 'as': 'person'}},                
                {'$unwind': {'path': '$person', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        '$or': [
                            {'email': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'person.name': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'person.surname': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'person.phone': {'$regex': config_searchRegex(search), '$options': 'i'}},
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
                v_model_person = model_main_persons.insert(action = 'one_register', name = name, surname = surname)
                if v_model_person[0]:
                    document = {
                        '_id': user_id,                    
                        'email': email,
                        'password': password,
                        'access': [],
                        'regdate': datetime.utcnow(),
                        'status': True,
                        'person': {'$ref': 'persons', '$id': v_model_person[1]},
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

class model_main_persons:
    @staticmethod
    def get(action = None, person_id = None, email = None):
                
        return None

    @staticmethod
    def insert(action = None, name = None, surname = None, phone = None):
        try: 
            if action == 'one_register':
                new_id = model_next_count('person_id')
                document = {
                    '_id': new_id,
                    'name': name,
                    'surname': surname,
                    'phone': phone,
                } 

                db_mongo_main.persons.insert_one(document, bypass_document_validation = True)
                
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

class model_restaurant_persons:
    @staticmethod
    def get(action = None, person_id = None, email = None):
                
        return None

    @staticmethod
    def insert(action = None, name = None, surname = None, phone = None):
        try: 
            if action == 'one_register':
                new_id = model_restaurant_next_count('person_id')
                document = {
                    '_id': new_id,
                    'name': name,
                    'surname': surname,
                    'phone': phone,
                } 

                db_mongo_restaurant.persons.insert_one(document, bypass_document_validation = True)
                
                return True, new_id
            
            return False
        except Exception as e:
            return False
    
    @staticmethod
    def update(action = None, person_id = None, name = None, surname = None, phone = None):
        try: 
            if action == 'one':
                document = {'_id': person_id} 

                update = {
                    '$set': {
                        'name': name,
                        'surname': surname,
                        'phone': phone,
                    }
                }

                db_mongo_restaurant.persons.update_one(document, update)
                return True
            
            return False
        except Exception as e:
            return False
        
class model_restaurant_customers:
    @staticmethod
    def get(action = None, start = None, length = None, search = None, order_column = '_id', order_direction = 'asc', customer_id = None, email = None, status = False):
        if action == 'person_id':
            data = db_mongo_restaurant.customers.find_one({'_id': customer_id})
            return data
        elif action == 'email':
            data = db_mongo_restaurant.customers.find_one({'email': email})
            return data
        elif action == 'one':
            pipeline = [
                {'$lookup': {'from': 'user_roles', 'localField': 'user_role.$id', 'foreignField': '_id', 'as': 'user_role'}},                
                {'$unwind': {'path': '$user_role', 'preserveNullAndEmptyArrays': True}},
                {'$lookup': {'from': 'persons', 'localField': 'person.$id', 'foreignField': '_id', 'as': 'person'}},                
                {'$unwind': {'path': '$person', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        '_id': customer_id
                    }
                },
                {'$limit': 1}
            ]

            data = list(db_mongo_restaurant.customers.aggregate(pipeline))
            if not data:
                return None
            return data[0]
        elif action == 'all_table':
            pipeline = [
                {'$lookup': {'from': 'user_roles', 'localField': 'user_role.$id', 'foreignField': '_id', 'as': 'user_role'}},                
                {'$unwind': {'path': '$user_role', 'preserveNullAndEmptyArrays': True}},
                {'$lookup': {'from': 'persons', 'localField': 'person.$id', 'foreignField': '_id', 'as': 'person'}},                
                {'$unwind': {'path': '$person', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        '$or': [
                            {'email': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'person.name': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'person.surname': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'user_role.name': {'$regex': config_searchRegex(search), '$options': 'i'}},
                        ]
                    }
                },
                {'$sort': {order_column: 1 if order_direction == 'asc' else -1}},
                {'$skip': start},
                {'$limit': length}
            ]

            data = list(db_mongo_restaurant.customers.aggregate(pipeline))
            return data
        elif action == 'all_table_count':
            pipeline = [
                {'$lookup': {'from': 'user_roles', 'localField': 'user_role.$id', 'foreignField': '_id', 'as': 'user_role'}},                
                {'$unwind': {'path': '$user_role', 'preserveNullAndEmptyArrays': True}},
                {'$lookup': {'from': 'persons', 'localField': 'person.$id', 'foreignField': '_id', 'as': 'person'}},                
                {'$unwind': {'path': '$person', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        '$or': [
                            {'email': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'person.name': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'person.surname': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'person.phone': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'user_role.name': {'$regex': config_searchRegex(search), '$options': 'i'}}
                        ]
                    }
                },
                {'$sort': {order_column: 1 if order_direction == 'asc' else -1}},
                {'$count': 'total'}
            ]

            data = list(db_mongo_restaurant.customers.aggregate(pipeline))          
            count = data[0]['total'] if data else 0 
            return count        
        elif action == 'all_count':
            pipeline = [
                {'$count': 'total'}
            ]

            data = list(db_mongo_restaurant.customers.aggregate(pipeline))          
            count = data[0]['total'] if data else 0 
            return count        

        return None
    
    @staticmethod
    def insert(action = None, customer_id = None, name = None, surname = None, email = None, phone = None):
        try: 
            if action == 'one_register':
                v_model_person = model_restaurant_persons.insert(action = 'one_register', name = name, surname = surname, phone = phone)
                if v_model_person[0]:
                    document = {
                        '_id': customer_id,                    
                        'email': email,
                        'regdate': datetime.utcnow(),
                        'person': {'$ref': 'persons', '$id': v_model_person[1]},
                        'user_role': {'$ref': 'user_roles', '$id': 'normal'}
                    } 

                    db_mongo_restaurant.customers.insert_one(document, bypass_document_validation = True)
                    
                    return True
            return False
        except Exception as e:
            return False
    
    @staticmethod
    def update(action = None, customer_id = None, person_id = None, email = None, name = None, surname = None, phone = None):
        try:
            if action == 'one':
                model_restaurant_persons.update(action = 'one', person_id = person_id, name = name, surname = surname, phone = phone)
                document = {'_id': customer_id} 

                update = {
                    '$set': {
                        'email': email
                    }
                }

                db_mongo_restaurant.customers.update_one(document, update)
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
        elif action == 'all':            
            data = db_mongo_restaurant.product_categories.find()
            return data
        elif action == 'all_status':            
            data = db_mongo_restaurant.product_categories.find({'status': status})
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

class model_restaurant_table_states:
    @staticmethod
    def get(action = None, table_status_id = None):
        if action == 'one':            
            data = db_mongo_restaurant.table_states.find_one({'_id': table_status_id})
            return data
        elif action == 'all':
            data = list(db_mongo_restaurant.table_states.find())
            return data
       
        return None

class model_restaurant_tables:
    @staticmethod
    def get(action = None, start = None, length = None, search = None, order_column = '_id', order_direction = 'asc', table_id = None):
        if action == 'one':            
            pipeline = [
                {'$lookup': {'from': 'table_states', 'localField': 'table_status.$id', 'foreignField': '_id', 'as': 'table_status'}},                
                {'$unwind': {'path': '$table_status', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        '_id': table_id
                    }
                },
                {'$limit': 1}
            ]

            data = list(db_mongo_restaurant.tables.aggregate(pipeline))
            if not data:
                return None
            
            return data[0]
        elif action == 'all':
            pipeline = [
                {'$lookup': {'from': 'table_states', 'localField': 'table_status.$id', 'foreignField': '_id', 'as': 'table_status'}},                
                {'$unwind': {'path': '$table_status', 'preserveNullAndEmptyArrays': True}},
                {'$sort': {'_id': 1}},
            ]

            data = list(db_mongo_restaurant.tables.aggregate(pipeline))
            return data
        elif action == 'all_table':
            pipeline = [
                {'$lookup': {'from': 'table_states', 'localField': 'table_status.$id', 'foreignField': '_id', 'as': 'table_status'}},                
                {'$unwind': {'path': '$table_status', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        '$or': [
                            {'_id': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'name': {'$regex': config_searchRegex(search), '$options': 'i'}},
                        ]
                    }
                },
                {'$sort': {order_column: 1 if order_direction == 'asc' else -1}},
                {'$skip': start},
                {'$limit': length}
            ]

            data = list(db_mongo_restaurant.tables.aggregate(pipeline))
            return data
        elif action == 'all_table_count':
            pipeline = [
                {'$lookup': {'from': 'table_states', 'localField': 'table_status.$id', 'foreignField': '_id', 'as': 'table_status'}},                
                {'$unwind': {'path': '$table_status', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        '$or': [
                            {'_id': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'name': {'$regex': config_searchRegex(search), '$options': 'i'}},
                        ]
                    }
                },
                {'$sort': {order_column: 1 if order_direction == 'asc' else -1}},
                {'$count': 'total'}
            ]

            data = list(db_mongo_restaurant.tables.aggregate(pipeline))          
            count = data[0]['total'] if data else 0 
            return count        
        elif action == 'all_count':
            pipeline = [
                {'$count': 'total'}
            ]

            data = list(db_mongo_restaurant.tables.aggregate(pipeline))          
            count = data[0]['total'] if data else 0 
            return count
    
        return None

    @staticmethod
    def insert(action = None, name = None, table_status_id = None):
        try:
            if action == 'one':
                document = {
                    '_id': model_restaurant_next_count('table_id'),
                    'name': name,
                    'table_status': {'$ref': 'table_states', '$id': table_status_id},
                }

                db_mongo_restaurant.tables.insert_one(document)
                return True
            
            return False
        except Exception as e:
            return False
        
    @staticmethod
    def update(action = None, table_id = None, name = None, table_status_id = False):
        try:
            if action == 'one':
                document = {'_id': table_id} 

                update = {
                    '$set': {
                        'name': name,
                        'table_status': {'$ref': 'table_states', '$id': table_status_id},
                    }
                }

                db_mongo_restaurant.tables.update_one(document, update)
                return True
            
            return False
        except Exception as e:
            return False

class model_restaurant_products:
    @staticmethod
    def get(action = None, start = None, length = None, search = None, order_column = '_id', order_direction = 'asc', product_id = None, product_category_id = None, status = False):
        if action == 'one':            
            pipeline = [
                {'$lookup': {'from': 'product_categories', 'localField': 'product_category.$id', 'foreignField': '_id', 'as': 'product_category'}},                
                {'$unwind': {'path': '$product_category', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        '_id': product_id
                    }
                },
                {'$limit': 1}
            ]

            data = list(db_mongo_restaurant.products.aggregate(pipeline))
            if not data:
                return None
            
            return data[0]
        elif action == 'all_status':
            pipeline = [
                {'$lookup': {'from': 'product_categories', 'localField': 'product_category.$id', 'foreignField': '_id', 'as': 'product_category'}},                
                {'$unwind': {'path': '$product_category', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        'status': status, 
                    }
                }
            ]

            data = list(db_mongo_restaurant.products.aggregate(pipeline))
            return data
        elif action == 'all_category_status':
            pipeline = [
                {'$lookup': {'from': 'product_categories', 'localField': 'product_category.$id', 'foreignField': '_id', 'as': 'product_category'}},                
                {'$unwind': {'path': '$product_category', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        'status': status, 
                        'product_category._id': product_category_id, 
                    }
                }
            ]

            data = list(db_mongo_restaurant.products.aggregate(pipeline))
            return data
        elif action == 'all_table':
            pipeline = [
                {'$lookup': {'from': 'product_categories', 'localField': 'product_category.$id', 'foreignField': '_id', 'as': 'product_category'}},                
                {'$unwind': {'path': '$product_category', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        '$or': [
                            {'_id': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'name': {'$regex': config_searchRegex(search), '$options': 'i'}},
                        ]
                    }
                },
                {'$sort': {order_column: 1 if order_direction == 'asc' else -1}},
                {'$skip': start},
                {'$limit': length}
            ]

            data = list(db_mongo_restaurant.products.aggregate(pipeline))
            return data
        elif action == 'all_table_count':
            pipeline = [
                {'$lookup': {'from': 'product_categories', 'localField': 'product_category.$id', 'foreignField': '_id', 'as': 'product_category'}},                
                {'$unwind': {'path': '$product_category', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        '$or': [
                            {'_id': {'$regex': config_searchRegex(search), '$options': 'i'}},
                            {'name': {'$regex': config_searchRegex(search), '$options': 'i'}},
                        ]
                    }
                },
                {'$sort': {order_column: 1 if order_direction == 'asc' else -1}},
                {'$count': 'total'}
            ]

            data = list(db_mongo_restaurant.products.aggregate(pipeline))          
            count = data[0]['total'] if data else 0 
            return count        
        elif action == 'all_count':
            pipeline = [
                {'$count': 'total'}
            ]

            data = list(db_mongo_restaurant.products.aggregate(pipeline))          
            count = data[0]['total'] if data else 0 
            return count  
        elif action == 'all_count_status':
            pipeline = [
                {
                    '$match': {
                        'status': status,
                    }
                },
                {'$count': 'total'}
            ]

            data = list(db_mongo_restaurant.products.aggregate(pipeline))          
            count = data[0]['total'] if data else 0 
            return count    
        return None

    @staticmethod
    def insert(action = None, name = None, description = None, price = None, product_category_id = None):
        try:
            if action == 'one':
                document = {
                    '_id': model_restaurant_next_count('product_id'),
                    'name': name,
                    'description': description,
                    'price': price,
                    'status': False,
                    'product_category': {'$ref': 'product_categories', '$id': product_category_id},
                }

                db_mongo_restaurant.products.insert_one(document)
                return True
            
            return False
        except Exception as e:
            return False
        
    @staticmethod
    def update(action = None, product_id = None, name = None, description = None, price = None, status = False, product_category_id = None):
        try:
            if action == 'one':
                document = {'_id': product_id} 

                update = {
                    '$set': {
                        'name': name,
                        'description': description,
                        'price': price,
                        'status': status,
                        'product_category': {'$ref': 'product_categories', '$id': product_category_id},
                    }
                }

                db_mongo_restaurant.products.update_one(document, update)
                return True
            
            return False
        except Exception as e:
            return False

class model_restaurant_orders:
    @staticmethod
    def get(action = None, order_id = None):
        if action == 'one':
            data = db_mongo_restaurant.orders.find_one({'_id': order_id})
            return data         

        return None
 
    @staticmethod
    def insert(action = None, order_id = None, total = 0, user_id = None):
        try:
            if action == 'one_order_id':                
                document = {
                    '_id': order_id,
                    'no': model_restaurant_next_count('order_id'),
                    'total': total,
                    'regdate': datetime.utcnow(),
                    'user': user_id,
                }

                db_mongo_restaurant.orders.insert_one(document)
                return True
            
            return False
        except Exception as e:
            return False
        
class model_restaurant_order_details:
    @staticmethod
    def get(action = None, order_detail_id = None, table_id = None, order_id = None, status = 0):
        if action == 'one':
            data = db_mongo_restaurant.order_details.find_one({'_id': order_detail_id})
            return data  
        elif action == 'all_table':
            pipeline = [
                {'$lookup': {'from': 'products', 'localField': 'product.$id', 'foreignField': '_id', 'as': 'product'}},                
                {'$unwind': {'path': '$product', 'preserveNullAndEmptyArrays': True}},
                {'$lookup': {'from': 'product_categories', 'localField': 'product.product_category.$id', 'foreignField': '_id', 'as': 'product.product_category'}},                
                {'$unwind': {'path': '$product.product_category', 'preserveNullAndEmptyArrays': True}},
                {'$lookup': {'from': 'tables', 'localField': 'table.$id', 'foreignField': '_id', 'as': 'table'}},                
                {'$unwind': {'path': '$table', 'preserveNullAndEmptyArrays': True}},
                {'$lookup': {'from': 'table_states', 'localField': 'table.table_status.$id', 'foreignField': '_id', 'as': 'table.table_status'}},                
                {'$unwind': {'path': '$table.table_status', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        'order': None,
                        'table._id': table_id,
                    }
                }
            ]

            data = list(db_mongo_restaurant.order_details.aggregate(pipeline))
            return data 
        elif action == 'all_order':
            pipeline = [
                {'$lookup': {'from': 'products', 'localField': 'product.$id', 'foreignField': '_id', 'as': 'product'}},                
                {'$unwind': {'path': '$product', 'preserveNullAndEmptyArrays': True}},
                {'$lookup': {'from': 'product_categories', 'localField': 'product.product_category.$id', 'foreignField': '_id', 'as': 'product.product_category'}},                
                {'$unwind': {'path': '$product.product_category', 'preserveNullAndEmptyArrays': True}},
                {'$lookup': {'from': 'tables', 'localField': 'table.$id', 'foreignField': '_id', 'as': 'table'}},                
                {'$unwind': {'path': '$table', 'preserveNullAndEmptyArrays': True}},
                {'$lookup': {'from': 'table_states', 'localField': 'table.table_status.$id', 'foreignField': '_id', 'as': 'table.table_status'}},                
                {'$unwind': {'path': '$table.table_status', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        'order.$id': order_id,
                    }
                },
                {
                    '$project': {
                        'order': 0,
                    }
                }
            ]

            data = list(db_mongo_restaurant.order_details.aggregate(pipeline))
            return data    
        elif action == 'all_status':
            pipeline = [
                {'$lookup': {'from': 'products', 'localField': 'product.$id', 'foreignField': '_id', 'as': 'product'}},                
                {'$unwind': {'path': '$product', 'preserveNullAndEmptyArrays': True}},
                {'$lookup': {'from': 'product_categories', 'localField': 'product.product_category.$id', 'foreignField': '_id', 'as': 'product.product_category'}},                
                {'$unwind': {'path': '$product.product_category', 'preserveNullAndEmptyArrays': True}},
                {'$lookup': {'from': 'tables', 'localField': 'table.$id', 'foreignField': '_id', 'as': 'table'}},                
                {'$unwind': {'path': '$table', 'preserveNullAndEmptyArrays': True}},
                {'$lookup': {'from': 'table_states', 'localField': 'table.table_status.$id', 'foreignField': '_id', 'as': 'table.table_status'}},                
                {'$unwind': {'path': '$table.table_status', 'preserveNullAndEmptyArrays': True}},
                {
                    '$match': {
                        'order': None,
                        'status': status,
                    }
                }
            ]

            data = list(db_mongo_restaurant.order_details.aggregate(pipeline))
            return data 
        
        return None
 
    @staticmethod
    def insert(action = None, price = None, quantity = None, note = None, total = 0, product_id = None, table_id = None, user_id = None, status = 0):
        try:
            if action == 'one':
                document = {
                    '_id': model_restaurant_next_count('order_detail_id'),
                    'price': price,
                    'quantity': quantity,
                    'note': note,
                    'total': total,
                    'status': status,
                    'regdate': datetime.utcnow(),
                    'product': {'$ref': 'products', '$id': product_id},
                    'table': {'$ref': 'tables', '$id': table_id},
                    'user': user_id,
                    'order': None
                }

                db_mongo_restaurant.order_details.insert_one(document)
                return True
            
            return False
        except Exception as e:
            return False
    
    @staticmethod
    def update(action = None, order_detail_id = None, order_id = None, table_id = None, total = 0, user_id = None, status_search = None, status_update = None):
        try:
            if action == 'all_order':
                insert = model_restaurant_orders.insert(action = 'one_order_id', order_id = order_id, total = total, user_id = user_id)
                if insert:
                    document = {
                        'table.$id': table_id,
                        'order': None
                    } 

                    update = {
                        '$set': {
                            'order': {'$ref': 'orders', '$id': order_id},
                        }
                    }

                    db_mongo_restaurant.order_details.update_many(document, update)
                    return True
            elif action == 'all_status':
                document = {
                    'table.$id': table_id,
                    'order': None,
                    'status': status_search
                } 

                update = {
                    '$set': {
                        'status': status_update
                    }
                }

                db_mongo_restaurant.order_details.update_many(document, update)
                return True
            elif action == 'one_status':
                document = {
                    '_id': order_detail_id,
                    'table.$id': table_id,
                    'order': None,
                    'status': status_search
                } 

                update = {
                    '$set': {
                        'status': status_update
                    }
                }

                db_mongo_restaurant.order_details.update_many(document, update)
                return True
            
            return False
        except Exception as e:
            return False
    
    @staticmethod
    def delete(action = None, order_detail_id = None):
        try: 
            if action == 'one':
                document = {
                    '_id': order_detail_id
                } 

                db_mongo_restaurant.order_details.delete_many(document)
                
                return True
            
            return False
        except Exception as e:
            return False
            