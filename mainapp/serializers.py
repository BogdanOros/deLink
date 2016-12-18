from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from .mongo_models import Folder
from .models import CustomUser as User, Friendship, FriendRequest
from collections import defaultdict
from bson import json_util
import json
# TODO: change FolderSerializer for mainfolder objects


# class UserSerializer(serializers.ModelSerializer):
# 	class Meta:
# 		model = User
# 		fields = ('id', 'email', 'first_name', 'last_name', 'facebook_id', 'username', 'password')


class FolderSerializer(object):
	def __init__(self, data, many=False):
		self.data = self.serialize(data, many)

	@staticmethod
	def serialize_folder_object(data):
		# data['id'] = str(data['_id'])
		# del data['_id']

		if 'subfolders' in data.keys():
			for folder in data['subfolders']:
				# folder['id'] = str(folder['_id'])
				# folder['_id'] = None
				folder['subfolders'], folder['files'] = None, None

		# if 'files' in data.keys():
		# 	for file_ in data['files']:
		# 		file_['id'] = str(file_['_id'])
		# 		file_['_id'] = None
		# return pickle.dumps(d)
		return data

	def serialize(self, data, many):
		if many:
			list_of_folders = []
			for obj in data:
				list_of_folders.append(self.serialize_folder_object(obj))

			return json.loads(json.dumps(list_of_folders, default=json_util.default))
		return json.loads(json.dumps(self.serialize_folder_object(data), default=json_util.default))


class UserSerializer(serializers.Serializer):
	id = serializers.IntegerField(read_only=True)
	password = serializers.CharField(required=True, allow_blank=False, max_length=80)
	email = serializers.CharField(required=True, allow_blank=False, max_length=80)
	first_name = serializers.CharField(required=True, allow_blank=False, max_length=100)
	username = serializers.CharField(required=True, allow_blank=False, max_length=100)
	last_name = serializers.CharField(required=True, allow_blank=False, max_length=100)
	facebook_id = serializers.CharField(required=False, allow_blank=True, max_length=100)

	def create(self, validated_data):
		return User.objects.create_user(**validated_data)

	def update(self, instance, validated_data):
		instance.email = validated_data.get('email', instance.email)
		instance.password = validated_data.get('password', instance.password)
		instance.username = validated_data.get('username', instance.username)
		instance.first_name = validated_data.get('first_name', instance.first_name)
		instance.last_name = validated_data.get('last_name', instance.last_name)
		instance.facebook_id = validated_data.get('facebook_id', instance.facebook_id)
		instance.save()
		return instance


class FriendshipSerializer(serializers.ModelSerializer):
	class Meta:
		model = Friendship
		fields = ('first_user', 'second_user', 'created_date')


class FriendRequestSerializer(serializers.ModelSerializer):
	class Meta:
		model = FriendRequest
		fields = ('from_user', 'to_user', 'created_date')