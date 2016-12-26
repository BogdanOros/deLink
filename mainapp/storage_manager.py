# from mongoengine import connect
from mongo_models import Folder
from datetime import date, datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
import gridfs
import os
import shutil
import subprocess
import moment


class StorageManager(object):

	def __init__(self):
		self.db = MongoClient(host='localhost:27100').delink_storage
		self.fs = gridfs.GridFS(self.db)
		# self.db_restore('2016-12-25')
		self.handle_dump_creation()

	def user_activity(self, username, url):
		self.db.search_statistics.insert_one({'user': username, 'date': datetime.utcnow(), 'url': url})

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
		# folder = self.db.folder.find_one({'_id': ObjectId(folder_id)})
		self.db.folder.update_one({'_id': ObjectId(folder_id)},
		                          {'$addToSet': {'read_permission': user_id}})
		folder = self.db.folder.find_one({'_id': ObjectId(folder_id)})
		if self.is_home_folder(folder['parent_id']):
			self.db.mainfolder.update({'_id': ObjectId(folder['parent_id']), 'subfolders._id': ObjectId(folder_id)},
			                          {'$addToSet': {'subfolders.$.read_permission': user_id}})

	def deny_folder_read_perm(self, folder_id, user_id):
		folder = self.db.folder.find_one({'_id': ObjectId(folder_id)})
		if self.is_home_folder(folder['parent_id']):
			self.db.mainfolder.update({'_id': ObjectId(folder['parent_id']), 'subfolders._id': ObjectId(folder_id)},
			                          {'$pull': {'subfolders.$.read_permission': user_id}})
		self.db.folder.update_one({'_id': ObjectId(folder_id)},
		                          {'$pull': {'read_permission': user_id}})

	def handle_dump_creation(self):
		date_ = self.db.dumps.find_one({'date': str(date.today())})
		if not date_:
			self.db_dump()

	def db_dump(self):
		self.db.dumps.insert_one({'date': str(date.today())})
		cmd = "mongodump --host localhost --port 27100 --db delink_storage --out dump/" + str(date.today())
		print (subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True))

	def db_restore(self, date):
		# self.r.flushdb()
		cmd = "mongorestore --host localhost --port 27100 --db delink_storage --drop dump/" + date + "/delink_storage"
		print (subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True))

	def get_statistics(self):
		today = str(date.today())
		year = int(today[:4])
		month = int(today[5:7])
		day = int(today[8:])
		day_ago = moment.date(year, month, day).subtract(day=1).datetime
		day_activity = self.db.search_statistics.find({'date': {'$gt': day_ago}})
		week_ago = moment.date(year, month, day).subtract(weeks=1).datetime
		week_activity = self.db.search_statistics.find({'date': {'$gt': week_ago}})
		month_age = moment.date(year, month, day).subtract(month=1).datetime
		month_activity = self.db.search_statistics.find({'date': {'$gt': month_age}})
		return day_activity.count(), week_activity.count(), month_activity.count()
