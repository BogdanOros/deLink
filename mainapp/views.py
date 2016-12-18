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
	FriendshipSerializer, FriendRequestSerializer
from .storage_manager import StorageManager
from .services import get_friend_status, get_title_from_path
from .cache_manager import CacheManager


# TODO get folder method - permissions

storage_manager = StorageManager()
cache_manager = CacheManager()
# -----------------------------------------------FOLDER METHODS-----------------------------------------------------


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated, ))
def get_folder(request, username, path):
	"""
	Gets user's folder in two ways:
		1: if it is GET request, parses the path and checks if user has such folder
		2: if it is POST request, pulls out folder's id from POST and does select in MongoDB
	"""
	if request.method == 'POST':
		data = JSONParser().parse(request)
		folder = cache_manager.get_data(data['folder_id'])
		if not folder:
			print ('FROM MONGO')
			folder = storage_manager.search_folder_by_id(data['folder_id'])
			cache_manager.cache_data(folder['_id'], folder)

		serializer = FolderSerializer(folder)
		return Response(serializer.data, status=status.HTTP_200_OK)

	elif request.method == 'GET':
		title = get_title_from_path(path)
		if title == 'home':
			user_id = CustomUser.objects.get(username=username).pk
			if user_id == request.user.id:
				folder = storage_manager.search_folder_by_title(title, request.user.id)
			else:
				folder = storage_manager.search_folder_by_title(title, user_id)

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
	if request.method == 'POST':
		data = JSONParser().parse(request)
		folder = Folder(data['title'], request.user.id).as_dict()
		inserted_folder = storage_manager.save_folder(folder, data['parent_id'])
		serializer = FolderSerializer(inserted_folder)
		return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def delete_folder(request):
	"""
	Function that deletes folder by its ID
	"""
	if request.method == 'POST':
		data = JSONParser().parse(request)
		storage_manager.delete_folder(data['folder_id'], data['parent_id'])
		cache_manager.clear_cache(data['parent_id'])
		return Response(1, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def update_folder(request):
	"""
	Function that updates folder by its ID
	"""
	if request.method == 'POST':
		data = JSONParser().parse(request)
		storage_manager.update_folder(data['folder_id'], data['parent_id'], data['new_title'])
		cache_manager.clear_cache(data['parent_id'])
		return Response(1, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
def search_content(request):
	"""
	Searches files and folders in user's file system
	"""
	if request.method == 'POST':
		data = JSONParser().parse(request)



#  -----------------------------------------------USER METHODS-----------------------------------------------------


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def profile(request, username):

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
		print (data)
		user = CustomUserAuth.authenticate(username=data['username'], password=data['password'])
		if user:
			auth.login(request, user)
			serializer = UserSerializer(user)
			print (request.user.id)
			return Response(serializer.data)
		else:
			return Response('Authorization error', status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def logout(request):
	"""
	Logout user from system
	"""
	if request.method == 'GET':
		auth.logout(request)
		return Response('logged out')


# --------------------------------------------FRIENDSHIP METHODS----------------------------------------------------


@api_view(['POST'])
def send_friend_request(request):

	if request.method == 'POST':
		data = JSONParser().parse(request)
		friend_request = FriendRequest.objects.filter(from_user=data['from_user'], to_user=data['to_user'])
		if not friend_request:
			serializer = FriendRequestSerializer(data=data)
			if serializer.is_valid():
				serializer.save()
				return Response(serializer.data, status=status.HTTP_201_CREATED)
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
		return Response('You have already sent the request!')


# -----------------------------------------------FILE METHODS-----------------------------------------------------


@api_view(['POST'])
def upload_file(request):

	if request.method == 'POST':
		data = JSONParser().parse(request)
		filename = data['filename']
		uploaded_file = data['file']
		is_main = data['is_main']
		folder_id = data['folder_id']
		file_to_store = File(filename, storage_manager.save_file(uploaded_file))
		storage_manager.add_to_folder(folder_id, file_to_store, is_main)
		return Response({'ok': 'true'})


