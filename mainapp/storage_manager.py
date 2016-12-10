# from mongoengine import connect
from mongo_models import Folder
# from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId


class StorageManager(object):

	def __init__(self):
		self.db = MongoClient().delink_storage

	def save_folder(self, folder_obj):
		self.db.folders.insert(folder_obj)

	def get_folders(self):
		folder_list = []
		for folder in self.db.folder.find():
			folder["id"] = folder["_id"]
			folder["_id"] = None
			folder_list.append(folder)
		return folder_list

	def search_folder_by_id(self, folder_id):
		return self.db.folder.find_one({'_id': ObjectId(folder_id)})

# storage = StorageManager()
