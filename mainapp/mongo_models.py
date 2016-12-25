from datetime import datetime


class File(object):
	def __init__(self, filename, id, type_, user_id):
		self.id = id
		self.filename = filename
		self.type = type_
		self.user_id = user_id

	def __str__(self):
		return self.filename

	def as_dict(self):
		d = dict()
		d['_id'] = self.id
		d['filename'] = self.filename
		d['type'] = self.type
		d['user_id'] = self.user_id
		return d


class Folder(object):
	def __init__(self, title, user_id, parent_id=None, subfolders=None, files=None):
		self.title = title
		self.creation_date = datetime.now()
		self.user_id = user_id
		self.subfolders = subfolders if subfolders is not None else []
		self.files = files if files is not None else []
		self.parent_id = parent_id
		self.read_permission = []
		self.edit_permission = []

	def __str__(self):
		return self.title

	def as_dict(self):
		d = dict()
		d['title'] = self.title
		d['creation_date'] = self.creation_date
		d['user_id'] = self.user_id
		d['subfolders'] = self.subfolders
		d['files'] = self.files
		d['parent_id'] = self.parent_id
		d['read_permission'] = self.read_permission
		d['edit_permission'] = self.edit_permission
		return d


# class MainFolder(Folder):
# 	def __init__(self, title, list_of_subfolders, list_of_files, creation_date, user_id):
# 		super(MainFolder, self).__init__(title, list_of_subfolders, list_of_files, creation_date, user_id)
#
#
# f = Folder('suk', None, None, datetime.now(), 1).as_dict()
# print (f)
# main_f = MainFolder('pzdc', None, None, datetime.now(), 1).as_dict()
# print (main_f)

# from mongoengine import Document, StringField, \
# 	EmbeddedDocumentField, EmbeddedDocument, \
# 	FileField, DateTimeField, ListField, IntField
#
#
# class File(EmbeddedDocument):
# 	file = FileField()
# 	title = StringField(max_length=200, required=True)
# 	upload_date = DateTimeField()
# 	user_id = IntField(required=True)
#
#
# class Folder(Document):
# 	title = StringField(max_length=200, required=True)
# 	files = ListField(EmbeddedDocumentField(File), null=True)
# 	subfolders = ListField(null=True)
# 	creation_date = DateTimeField()
# 	user_id = IntField(required=True)
