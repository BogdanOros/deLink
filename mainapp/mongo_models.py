

class Folder(object):
	def __init__(self, _id, title, list_of_subfolders, list_of_files, creation_date, user_id):
		self.id = _id
		self.title = title
		self.subfolders = list_of_subfolders
		self.files = list_of_files
		self.creation_date = creation_date
		self.user_id = user_id

	def __str__(self):
		return self.title





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
