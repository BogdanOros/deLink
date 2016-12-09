from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from .mongo_models import Folder
from .models import CustomUser as User
from collections import defaultdict
import json


class UserSerializer(serializers.Serializer):
	id = serializers.IntegerField(read_only=True)
	email = serializers.CharField(required=True, allow_blank=False, max_length=80)
	name = serializers.CharField(required=True, allow_blank=False, max_length=100)
	surname = serializers.CharField(required=True, allow_blank=False, max_length=100)
	facebook_id = serializers.CharField(required=False, allow_blank=True, max_length=100)
	date_joined = serializers.DateTimeField()

	def create(self, validated_data):
		return User.objects.create_user(**validated_data)

	def update(self, instance, validated_data):
		instance.email = validated_data.get('email', instance.email)
		instance.name = validated_data.get('name', instance.name)
		instance.surname = validated_data.get('surname', instance.surname)
		instance.facebook_id = validated_data.get('facebook_id', instance.facebook_id)
		instance.save()
		return instance


class FolderSerializer(object):
	def __init__(self, data, many=False):
		self.data = self.serialize(data, many)

	@staticmethod
	def serialize_folder_object(data):
		data['id'] = str(data['_id'])
		del data['_id']

		if 'subfolders' in data.keys():
			for folder in data['subfolders']:
				folder['id'] = str(folder['_id'])
				folder['subfolders'], folder['files'] = None, None

		if 'files' in data.keys():
			for file_ in data['files']:
				file_['id'] = str(file_['_id'])
		# return pickle.dumps(d)
		return data

	def serialize(self, data, many):
		if many:
			list_of_folders = []
			for obj in data:
				list_of_folders.append(self.serialize_folder_object(obj))

			return json.dumps(list_of_folders)
		return json.dumps(self.serialize_folder_object(data[0]))
		# return JSONRenderer.render(data)
