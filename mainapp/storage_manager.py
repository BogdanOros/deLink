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

	def is_home_folder(self, folder_id):
		return self.db.mainfolder.find_one({'_id': ObjectId(folder_id)})

	def save_folder(self, folder, parent_id):
		result = self.db.folder.insert_one(folder)
		inserted_folder = self.db.folder.find_one({'_id': result.inserted_id})
		if self.is_home_folder(parent_id):
			self.db.mainfolder.update_one({'_id': ObjectId(parent_id)},
			                              {'$addToSet': {'subfolders': inserted_folder}})
		else:
			self.db.folder.update_one({'_id': ObjectId(parent_id)},
			                          {'$addToSet': {'subfolders': inserted_folder}})
		return inserted_folder

	def save_main_folder(self, main_folder):
		self.db.mainfolder.insert_one(main_folder)

	def get_main_folder(self, user_id):
		return self.db.mainfolder.find_one({'user_id': user_id})

	def get_folders(self):
		folder_list = []
		for folder in self.db.folder.find():
			folder["id"] = folder["_id"]
			folder["_id"] = None
			folder_list.append(folder)
		return folder_list

	def search_folder_by_id(self, folder_id):
		folder = self.db.folder.find_one({'_id': ObjectId(folder_id)})
		if not folder:
			folder = self.db.mainfolder.find_one({'_id': ObjectId(folder_id)})
		return folder

	def search_folder_by_title(self, title, user_id):
		folder = self.db.folder.find_one({'title': title, 'user_id': user_id})
		if not folder:
			folder = self.db.mainfolder.find_one({'title': title, 'user_id': user_id})
		return folder

	def save_file(self, bin_file):
		return self.fs.put(bin_file)

	def add_to_folder(self, folder_id, file_):
		if self.is_home_folder(folder_id):
			self.db.mainfolder.update_one({'_id': ObjectId(folder_id)},
			                              {'$addToSet': {'files': file_}})
		else:
			self.db.folder.update_one({'_id': ObjectId(folder_id)},
			                              {'$addToSet': {'files': file_}})

	def delete_folder(self, folder_id, parent_id):
		folder = self.db.folder.find_one({'_id': ObjectId(folder_id)})
		if self.is_home_folder(parent_id):

			self.db.mainfolder.update_one({'_id': ObjectId(parent_id)},
			                              {'$pull': {'subfolders': folder}})
		else:
			self.db.folder.update_one({'_id': ObjectId(parent_id)},
			                              {'$pull': {'subfolders': folder}})
		self.db.folder.delete_one(folder)

	def update_folder(self, folder_id, parent_id, new_title):
		self.db.folder.update_one({'_id': ObjectId(folder_id)},
		                          {'$set': {'title': new_title}})
		if self.is_home_folder(parent_id):
			self.db.mainfolder.update({'_id': ObjectId(parent_id), 'subfolders._id': ObjectId(folder_id)},
			                          {'$set': {'subfolders.$.title': new_title}})
		else:
			self.db.folder.update({'_id': ObjectId(parent_id), 'subfolders._id': ObjectId(folder_id)},
			                          {'$set': {'subfolders.$.title': new_title}})