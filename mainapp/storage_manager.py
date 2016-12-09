# from mongoengine import connect
from mongo_models import Folder
# from datetime import datetime
from pymongo import MongoClient


class StorageManager(object):

	def __init__(self):
		self.db = MongoClient().delink_storage

	def save_folder(self, folder_obj):
		self.db.folders.insert(folder_obj)

	def get_folders(self):
		return [folder for folder in self.db.folder.find()]

# storage = StorageManager()
