from mongoengine import connect
from mongo_models import File, Folder
from datetime import datetime


class StorageManager(object):

	def __init__(self):
		connect('delink_storage')

	@staticmethod
	def create_folder(title):
		folder = Folder(folder_title=title, creation_date=datetime.now())
		folder.save()

	@staticmethod
	def show_folders():
		for folder in Folder.objects:
			print (folder.folder_title)

storage = StorageManager()
storage.show_folders()