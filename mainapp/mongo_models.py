from mongoengine import Document, StringField, \
	EmbeddedDocumentField, EmbeddedDocument, \
	FileField, DateTimeField, ListField


class File(EmbeddedDocument):
	file = FileField()
	file_title = StringField(max_length=200, required=True)
	upload_date = DateTimeField()


class Folder(Document):
	folder_title = StringField(max_length=200, required=True)
	files = ListField(EmbeddedDocumentField(File), null=True)
	# folders = ListField(EmbeddedDocumentField(Folder), null=True)
	creation_date = DateTimeField()