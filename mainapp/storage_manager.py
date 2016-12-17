# from mongoengine import connect
from mongo_models import Folder
# from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
import gridfs


class StorageManager(object):

	def __init__(self):
		self.db = MongoClient().delink_storage
		self.fs = gridfs.GridFS(self.db)

	def save_folder(self, folder, parent_id):
		result = self.db.folder.insert_one(folder)
		inserted_folder = self.db.folder.find_one({'_id': result.inserted_id})
		if self.db.mainfolder.find_one({'_id': ObjectId(parent_id)}):
			self.db.mainfolder.update_one({'_id': ObjectId(parent_id)},
			                              {'$addToSet': {'subfolders': inserted_folder}})
		else:
			self.db.folder.update_one({'_id': ObjectId(parent_id)},
			                          {'$addToSet': {'subfolders': inserted_folder}})


	def save_main_folder(self, main_folder):
		self.db.mainfolder.insert_one(main_folder)

	def get_folders(self):
		folder_list = []
		for folder in self.db.folder.find():
			folder["id"] = folder["_id"]
			folder["_id"] = None
			folder_list.append(folder)
		return folder_list

	def search_folder_by_id(self, folder_id):
		return self.db.folder.find_one({'_id': ObjectId(folder_id)})

	def search_folder_by_title(self, title, user_id):
		return self.db.folder.find_one({'title': title, 'user_id': user_id})

	def get_main_folder(self, user_id):
		return self.db.mainfolder.find_one({'user_id': user_id})

	def save_file(self, bin_file):
		return self.fs.put(bin_file)

	def add_to_folder(self, folder_id, file_,is_main=False):
		if is_main:
			self.db.mainfolder.update_one({'_id': ObjectId(folder_id)},
			                              {'$addToSet': {'files': file_}})
		else:
			self.db.folder.update_one({'_id': ObjectId(folder_id)},
			                              {'$addToSet': {'files': file_}})

# storage = StorageManager()
