# from mongoengine import connect
from mongo_models import Folder
from datetime import date
from pymongo import MongoClient
from bson.objectid import ObjectId
import gridfs


class StorageManager(object):

	def __init__(self):
		self.db = MongoClient().delink_storage
		self.fs = gridfs.GridFS(self.db)

	def user_activity(self, username, url):
		self.db.search_statistics.insert_one({'user': username, 'date': str(date.today()), 'url': url})

	def cache_activity(self, username, url):
		self.db.search_statistics.insert_one({'user': username, 'date': str(date.today()), 'url': url})

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
		# folder['prev'] = ObjectId(parent_id)
		return folder

	def save_file(self, file_):
		return self.fs.put(file_)

	def add_to_folder(self, folder_id, file_):
		if self.is_home_folder(folder_id):
			self.db.mainfolder.update_one({'_id': ObjectId(folder_id)},
			                              {'$addToSet': {'files': file_}})
		else:
			self.db.folder.update_one({'_id': ObjectId(folder_id)},
			                              {'$addToSet': {'files': file_}})
		self.db.files.insert_one(file_)

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

	def search(self, request, user_id):
		request = ".*" + request + ".*"
		files = []
		for file_ in self.db.files.find({'filename': {'$regex': request}}):
			if file_['user_id'] == user_id:
				files.append(file_)
		mainfolders = []
		for folder in self.db.mainfolder.find({'title': {'$regex': request}}):
			if folder['user_id'] == user_id:
				del folder['subfolders']
				del folder['files']
				mainfolders.append(folder)
		folders = []
		for folder in self.db.folder.find({'title': {'$regex': request}}):
			if folder['user_id'] == user_id:
				del folder['subfolders']
				del folder['files']
				folders.append(folder)
		return files, mainfolders + folders

	def get_file(self, file_id):
		return self.fs.get(ObjectId(file_id))

	def delete_file(self, file_id, parent_id):
		file_ = self.db.files.find_one({'_id': ObjectId(file_id)})
		self.fs.delete(file_id)
		if self.is_home_folder(parent_id):

			self.db.mainfolder.update_one({'_id': ObjectId(parent_id)},
			                              {'$pull': {'files': file_}})
		else:
			self.db.folder.update_one({'_id': ObjectId(parent_id)},
			                          {'$pull': {'files': file_}})
		self.db.files.delete_one(file_)

	def update_file(self, file_id, parent_id, new_filename):
		self.db.files.update_one({'_id': ObjectId(file_id)},
		                          {'$set': {'filename': new_filename}})
		if self.is_home_folder(parent_id):
			self.db.mainfolder.update({'_id': ObjectId(parent_id), 'files._id': ObjectId(file_id)},
			                          {'$set': {'files.$.filename': new_filename}})
		else:
			self.db.folder.update({'_id': ObjectId(parent_id), 'files._id': ObjectId(file_id)},
			                      {'$set': {'files.$.filename': new_filename}})

	def save_reset_code(self, code, email):
		self.db.codes.insert_one({'code': code, 'date': str(date.today()), 'email': email})

	def get_reset_code(self, code):
		reset_code_obj = self.db.codes.find_one({'code': code})
		if reset_code_obj:
			self.db.codes.delete_one(reset_code_obj)
			return reset_code_obj
		return False

	def delete_reset_code(self, email):
		reset_code_obj = self.db.codes.find_one({'email': email})
		if reset_code_obj:
			self.db.codes.delete_one(reset_code_obj)

	def give_folder_read_perm(self, folder_id, user_id):
		self.db.folder.update_one({'_id': ObjectId(folder_id)},
		                          {'$addToSet': {'read_permission': user_id}})

	def give_file_read_perm(self, file_id, user_id):
		self.db.files.update_one({'_id': ObjectId(file_id)},
		                          {'$addToSet': {'read_permission': user_id}})

	def give_folder_edit_perm(self, folder_id, user_id):
		self.db.folder.update_one({'_id': ObjectId(folder_id)},
		                          {'$addToSet': {'edit_permission': user_id}})

	def give_file_edit_perm(self, file_id, user_id):
		self.db.files.update_one({'_id': ObjectId(file_id)},
		                         {'$addToSet': {'edit_permission': user_id}})

	def deny_folder_read_perm(self, folder_id, user_id):
		self.db.folder.update_one({'_id': ObjectId(folder_id)},
		                          {'$pull': {'read_permission': user_id}})

	def deny_file_read_perm(self, file_id, user_id):
		self.db.files.update_one({'_id': ObjectId(file_id)},
		                         {'$pull': {'read_permission': user_id}})

	def deny_folder_edit_perm(self, folder_id, user_id):
		self.db.folder.update_one({'_id': ObjectId(folder_id)},
		                          {'$pull': {'edit_permission': user_id}})

	def deny_file_edit_perm(self, file_id, user_id):
		self.db.files.update_one({'_id': ObjectId(file_id)},
		                         {'$pull': {'edit_permission': user_id}})