import bitarray
import base64
import json
# imports from django
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
# import from rest
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.authtoken.models import Token
# imports from custom modules
from deLink import settings
from backends import CustomUserAuth
from .models import CustomUser, Friendship, FriendRequest
from .mongo_models import Folder, File
from .serializers import FolderSerializer, UserSerializer, \
	FriendshipSerializer, FriendRequestSerializer, FileSerializer
from .storage_manager import StorageManager
from .services import get_friend_status, get_title_from_path, get_type_of_file
from .cache_manager import CacheManager
from bson.objectid import ObjectId
import pickle

# TODO get folder method - permissions

storage_manager = StorageManager()
cache_manager = CacheManager()
# -----------------------------------------------FOLDER METHODS-----------------------------------------------------


@api_view(['GET', 'POST'])
@permission_classes((AllowAny, ))
def get_folder(request, username, path):
	"""
	Gets user's folder in two ways:
		1: if it is GET request, parses the path and checks if user has such folder
		2: if it is POST request, pulls out folder's id from POST and does select in MongoDB
	"""
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	cache_manager.cache_statistics()
	if request.method == 'POST':
		data = JSONParser().parse(request)
		folder_id = data['folder_id']
		folder = storage_manager.search_folder_by_id(folder_id)


		serializer = FolderSerializer(folder)

		cache_manager.cache_last_visited_folder(request.user.id, serializer.data)
		return Response(serializer.data, status=status.HTTP_200_OK)

	elif request.method == 'GET':
		title = get_title_from_path(path)
		if title == 'home':
			user_id = CustomUser.objects.get(username=username).pk
			if user_id == request.user.id:
				folder = cache_manager.get_last_visited_folder(user_id)
				if not folder:
					folder = storage_manager.search_folder_by_title(title, request.user.id)
				else:
					return Response(folder, status=status.HTTP_200_OK)
			else:
				# friendship = Friendship.objects.filter(first_user=)
				folder = cache_manager.get_last_visited_folder(user_id)
				if not folder:
					folder = storage_manager.search_folder_by_title(title, user_id)
				else:
					return Response(folder, status=status.HTTP_200_OK)

			serializer = FolderSerializer(folder)
			return Response(serializer.data, status=status.HTTP_200_OK)
		else:
			return Response('Bad request', status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def create_new_folder(request):
	"""
	Function that creates new folder.
	Also checks where folders is creating(main folder or no)
	"""
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'POST':
		data = JSONParser().parse(request)
		new_folder = Folder(data['title'], request.user.id, data['parent_id']).as_dict()
		inserted_folder = storage_manager.save_folder(new_folder, data['parent_id'])

		folder = storage_manager.search_folder_by_id(data['parent_id'])
		serializer = FolderSerializer(folder)
		cache_manager.cache_last_visited_folder(request.user.id, serializer.data)

		serializer = FolderSerializer(inserted_folder)
		return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def delete_folder(request):
	"""
	Function that deletes folder by its ID
	"""
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'POST':
		data = JSONParser().parse(request)
		storage_manager.delete_folder(data['folder_id'], data['parent_id'])
		cache_manager.clear_folders_cache(data['parent_id'])

		folder = storage_manager.search_folder_by_id(data['parent_id'])
		serializer = FolderSerializer(folder)
		cache_manager.cache_last_visited_folder(request.user.id, serializer.data)
		return Response(1, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def update_folder(request):
	"""
	Function that updates folder by its ID
	"""
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'POST':
		data = JSONParser().parse(request)
		storage_manager.update_folder(data['folder_id'], data['parent_id'], data['new_title'])
		cache_manager.clear_folders_cache(data['parent_id'])

		folder = storage_manager.search_folder_by_id(data['parent_id'])
		serializer = FolderSerializer(folder)
		cache_manager.cache_last_visited_folder(request.user.id, serializer.data)
		return Response(1, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
def search_content(request):
	"""
	Searches files and folders in user's file system
	"""
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	# request.user.id = 23
	if request.method == 'POST':
		data = JSONParser().parse(request)
		query = data['query']
		data_from_cache = cache_manager.get_data_by_query(request.user.id, query)
		if data_from_cache:
			response_folder = Folder(None, request.user.id, None, data_from_cache['folders'],
			                         data_from_cache['files']).as_dict()
			serializer = FolderSerializer(response_folder)
			return Response(serializer.data, status=status.HTTP_200_OK)

		files, folders = storage_manager.search(query, request.user.id)
		obj_to_cache = dict()
		obj_to_cache['folders'], obj_to_cache['files'] = None, None
		if folders:
			serializer = FolderSerializer(folders, many=True)
			obj_to_cache['folders'] = serializer.data

		if files:
			serializer = FileSerializer(files)
			obj_to_cache['files'] = serializer.data

		response_folder = Folder(None, request.user.id, None, obj_to_cache['folders'],
		                         obj_to_cache['files']).as_dict()
		serializer = FolderSerializer(response_folder)

		if folders or files:
			cache_manager.cache_search_query(request.user.id, query, obj_to_cache)

		return Response(serializer.data, status=status.HTTP_200_OK)


#  -----------------------------------------------USER METHODS-----------------------------------------------------


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def profile(request, username):
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'GET':

		user = CustomUser.objects.get(username=username)
		serializer = UserSerializer(user)
		if user.id != request.user.id:
			data = serializer.data
			data["status"] = get_friend_status(request.user, user)
			return Response(data, status=status.HTTP_200_OK)
		return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny, ))
def registration(request):
	"""
	Register a new user in the system
	"""

	if request.method == 'POST':
		data = JSONParser().parse(request)
		serializer = UserSerializer(data=data)
		if serializer.is_valid():
			serializer.save()
			email = serializer.data['email']
			main_folder = Folder(settings.DEFAULT_FOLDER_NAME, CustomUser.objects.get(email=email).id).as_dict()
			storage_manager.save_main_folder(main_folder)
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((AllowAny, ))
def authorization(request):
	"""
	Authenticate and login user in the system
	"""
	if request.method == 'POST':
		data = JSONParser().parse(request)
		user = CustomUserAuth.authenticate(username=data['username'], password=data['password'])
		if user:
			auth.login(request, user)
			serializer = UserSerializer(user)
			return Response(serializer.data)
		else:
			return Response('Authorization error', status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes((AllowAny, ))
def logout(request):
	"""
	Logout user from system
	"""
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'GET':
		auth.logout(request)
		return Response('logged out')


# --------------------------------------------FRIENDSHIP METHODS----------------------------------------------------


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def send_friend_request(request):
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'POST':
		data = JSONParser().parse(request)
		friend_request = FriendRequest.objects.filter(Q(from_user=data['from_user'], to_user=data['to_user']) |
		                                              Q(from_user=data['to_user'], to_user=data['from_user']))
		if not friend_request:
			serializer = FriendRequestSerializer(data=data)
			if serializer.is_valid():
				serializer.save()
				return Response(serializer.data, status=status.HTTP_201_CREATED)
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
		return Response('You have already sent the request!')

#
# @api_view(['POST'])
# @permission_classes((AllowAny, ))
# def accept_friend_request(request):
# 	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
# 	if request.method == 'POST':
#


# -----------------------------------------------FILE METHODS-----------------------------------------------------


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def upload_file(request):
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'POST':
		files = request.FILES
		parent_id = request.POST['parent_id']
		file_ = files['uploads[]']

		filename = file_.name
		file_type = get_type_of_file(filename)
		file_to_store = File(filename, storage_manager.save_file(file_.read()),
		                     file_type, request.user.id).as_dict()
		storage_manager.add_to_folder(parent_id, file_to_store)

		folder = storage_manager.search_folder_by_id(parent_id)
		serializer = FolderSerializer(folder)
		cache_manager.cache_last_visited_folder(request.user.id, serializer.data)

		serializer = FileSerializer(file_to_store)
		return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def get_file(request):
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'POST':
		data = JSONParser().parse(request)
		file_ = storage_manager.get_file(data['file_id'])
		if file_:
			content = file_.read()
			binary_content = base64.b64encode(content)
			return Response(binary_content, status=status.HTTP_200_OK)
		return Response('Error loading file', status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((AllowAny, ))
def delete_file(request):
	"""
	Function that deletes folder by its ID
	"""
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'POST':
		data = JSONParser().parse(request)
		storage_manager.delete_file(data['file_id'], data['parent_id'])
		cache_manager.clear_folders_cache(data['parent_id'])

		folder = storage_manager.search_folder_by_id(data['parent_id'])
		serializer = FolderSerializer(folder)
		cache_manager.cache_last_visited_folder(request.user.id, serializer.data)

		return Response(1, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny, ))
def update_file(request):
	"""
	Function that updates folder by its ID
	"""
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'POST':
		data = JSONParser().parse(request)
		storage_manager.update_file(data['file_id'], data['parent_id'], data['new_filename'])
		cache_manager.clear_folders_cache(data['parent_id'])

		folder = storage_manager.search_folder_by_id(data['parent_id'])
		serializer = FolderSerializer(folder)
		cache_manager.cache_last_visited_folder(request.user.id, serializer.data)

		return Response(1, status=status.HTTP_200_OK)