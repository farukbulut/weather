# MongoDBConnector.py
from pymongo import MongoClient
import config

class MongoDBConnector:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(MongoDBConnector, cls).__new__(cls)
            cls._instance.client = MongoClient(config.DB_URL)
            cls._instance.db = cls._instance.client[config.DB_NAME]
        return cls._instance

    def get_collection(self, collection_name):
        return self.db[collection_name]

    def add_document(self, collection_name, document):
        collection = self.get_collection(collection_name)
        return collection.insert_one(document).inserted_id

    def find_document(self, collection_name, query):
        collection = self.get_collection(collection_name)
        return collection.find(query)

    def update_document(self, collection_name, query, new_values):
        collection = self.get_collection(collection_name)
        updated_result = collection.update_many(query, new_values)
        return updated_result.modified_count

    def update_last_activity(self, collection_name, query, new_values):
        collection = self.get_collection(collection_name)
        updated_result = collection.update_many(query, new_values)
        return updated_result.modified_count
