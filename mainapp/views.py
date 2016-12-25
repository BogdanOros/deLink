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
from .services import get_friend_status, get_title_from_path, \
	get_type_of_file, generate_reset_code, check_permissions
from .cache_manager import CacheManager
from bson.objectid import ObjectId
import pickle
from bson import json_util
from django.db.models import Q
from django.core.mail import send_mail

import base64
import json
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
		user_id = CustomUser.objects.get(username=username).pk
		folder_id = data['folder_id']

		if user_id == request.user.id:
			folder = storage_manager.search_folder_by_id(folder_id)
			serializer = FolderSerializer(folder)
			cache_manager.cache_last_visited_folder(request.user.id, serializer.data)
			return Response(serializer.data, status=status.HTTP_200_OK)
		else:
			friendship = Friendship.objects.filter(first_user=request.user.id, second_user=user_id)
			if not friendship:
				return Response('You have no access to this folder', status=status.HTTP_423_LOCKED)
			folder = check_permissions(storage_manager.search_folder_by_id(folder_id))
			serializer = FolderSerializer(folder)
			return Response(serializer.data, status=status.HTTP_200_OK)
	elif request.method == 'GET':
		# title = get_title_from_path(path)

		user_id = CustomUser.objects.get(username=username).pk
		if user_id == request.user.id:
			folder = cache_manager.get_last_visited_folder(request.user.id)
			if not folder:
				folder = storage_manager.search_folder_by_title(settings.DEFAULT_FOLDER_NAME, request.user.id)
			else:
				return Response(folder, status=status.HTTP_200_OK)
		else:
			friendship = Friendship.objects.filter(first_user=request.user.id, second_user=user_id)
			if not friendship:
				return Response('You have no access to this folder', status=status.HTTP_423_LOCKED)

			folder = check_permissions(storage_manager.search_folder_by_title(settings.DEFAULT_FOLDER_NAME, user_id))

		serializer = FolderSerializer(folder)
		return Response(serializer.data, status=status.HTTP_200_OK)


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
		obj_to_cache['folders'], obj_to_cache['files'] = [], []
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
		if not user:
			return Response('No such user', status=status.HTTP_400_BAD_REQUEST)
		serializer = UserSerializer(user)
		if user.id != request.user.id:
			data = serializer.data
			data["status"] = get_friend_status(request.user, user)
			return Response(data, status=status.HTTP_200_OK)
		requests = FriendRequest.objects.filter(to_user=request.user.pk)
		data = serializer.data
		if requests:
			friend_request = dict()
			buff = []
			for r in requests:
				friend_request['id'] = r.pk
				friend_request['username'] = r.from_user.username
				friend_request['date'] = r.created_date
				buff.append(json.loads(json.dumps(friend_request, default=json_util.default)))
			data['requests'] = buff
		friendships = Friendship.objects.filter(first_user=request.user.id)

		if friendships:
			friends = []
			for friendship in friendships:
				friends.append(friendship.second_user)
			serialized_friends = UserSerializer(friends, many=True)
			data['friends'] = serialized_friends.data
		return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny, ))
def registration(request):
	"""
	Register a new user in the system
	"""

	if request.method == 'POST':
		data = JSONParser().parse(request)
		username = data['username']
		email = data['email']
		user = CustomUser.objects.filter(username=username)
		if user:
			return Response('User with such username already exists!', status=status.HTTP_400_BAD_REQUEST)
		user = CustomUser.objects.filter(email=email)
		if user:
			return Response('User with such email already exists!', status=status.HTTP_400_BAD_REQUEST)
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
			token = Token.objects.get(user=user)
			token.delete()
			new_token = Token.objects.create(user=user)
			serializer = UserSerializer(user)
			data = serializer.data
			data['token'] = new_token.key
			return Response(data)
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


@api_view(['POST'])
@permission_classes((AllowAny, ))
def search_user(request):

	if request.method == 'POST':
		data = JSONParser().parse(request)
		query = data['query']
		searched_users = CustomUser.objects.filter(Q(username__icontains=query) & ~Q(pk=request.user.id))
		data = []
		for user in searched_users:
			serializer = UserSerializer(user)
			buff = serializer.data
			buff["is_friend"] = get_friend_status(request.user, user)
			data.append(buff)
		if data:
			return Response(data, status=status.HTTP_200_OK)
		return Response("No users with such username", status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((AllowAny, ))
def forgot_password(request):

	if request.method == 'POST':
		data = JSONParser().parse(request)
		to_mail = data['email']
		code = generate_reset_code().upper()
		message = """
				  <html>
				  <head></head>
				  <body>
			          <h2> Hello cutie </h2>
			          <h3> I\'ve heard that you forgot your password :(.
			               So I\'m here today to send you something that might help you :).<br>
			               Here\'s the code <b>""" + code + """</b>.
	                       Put it in the form and create new password.</h3>
	                  <h2>Don\'t forget it next time! :)</h2>
	              </body>
				  </html>
                  """
		storage_manager.save_reset_code(code, to_mail)
		send_mail('Reset code', '', settings.FROM_MAIL, [to_mail], fail_silently=False, html_message=message)
		return Response('Reset code is sent.', status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny, ))
def reset_password(request):

	if request.method == 'POST':
		data = JSONParser().parse(request)
		reset_obj = storage_manager.get_reset_code(data['code'].upper())
		if reset_obj:
			new_password = data['password']
			user = CustomUser.objects.get(email=reset_obj['email'])
			if user:
				user.set_password(new_password)
				user.save()
				return Response('OK', status=status.HTTP_200_OK)
		return Response('Invalid code', status=status.HTTP_400_BAD_REQUEST)
# --------------------------------------------FRIENDSHIP METHODS----------------------------------------------------


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def send_friend_request(request):
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'POST':
		data = JSONParser().parse(request)
		from_user = request.user.id
		to_user_username = data['to_user']
		to_user = CustomUser.objects.get(username=to_user_username).pk
		friend_request = FriendRequest.objects.filter(Q(from_user=from_user, to_user=to_user) |
		                                              Q(from_user=to_user, to_user=from_user))
		if not friend_request:
			data['to_user'] = to_user
			data['from_user'] = request.user.id
			serializer = FriendRequestSerializer(data=data)
			if serializer.is_valid():
				serializer.save()
				return Response(serializer.data, status=status.HTTP_201_CREATED)
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
		return Response('You have already sent the request!')


@api_view(['POST'])
@permission_classes((AllowAny, ))
def accept_friend_request(request):
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'POST':
		data = JSONParser().parse(request)
		request_id = data['request_id']
		friend_request = FriendRequest.objects.get(pk=request_id)
		if not friend_request:
			return Response('Server error', status=status.HTTP_404_NOT_FOUND)

		from_user, to_user = friend_request.from_user, friend_request.to_user
		friend_request.delete()
		friendship = Friendship(first_user=from_user, second_user=to_user)
		friendship.save()
		friendship = Friendship(first_user=to_user, second_user=from_user)
		friendship.save()
		return Response('Friendship created', status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes((AllowAny,))
def decline_friend_request(request):
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'POST':
		data = JSONParser().parse(request)
		request_id = data['request_id']
		friend_request = FriendRequest.objects.get(pk=request_id)
		if not friend_request:
			return Response('Server error', status=status.HTTP_404_NOT_FOUND)
		friend_request.delete()
		return Response('Request declined', status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
def delete_from_friends(request):
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'POST':
		data = JSONParser().parse(request)
		user_id = data['user_id']
		from_friendship = Friendship.objects.get(from_user=user_id)
		to_friendship = Friendship.objects.get(to_user=user_id)
		if from_friendship and to_friendship:
			from_friendship.delete()
			to_friendship.delete()
			return Response('Deleted', status=status.HTTP_200_OK)
		return Response('Server error', status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def update_profile(request):
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'POST':
		data = JSONParser().parse(request)
		# user_id = data['user_id']
		user = CustomUser.objects.get(pk=request.user.id)
		serializer = UserSerializer(user)
		serializer.update(user, data)
		serializer.save()
		return Response('OK', status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def give_read_permission(request):
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'POST':
		data = JSONParser().parse(request)
		if 'folder_id' in data.keys():
			folder_id = data['folder_id']
			storage_manager.give_folder_read_perm(folder_id, request.user.id)
			return Response('OK', status=status.HTTP_200_OK)
		elif 'file_id' in data.keys():
			file_id = data['file_id']
			storage_manager.give_file_read_perm(file_id, request.user.id)
			return Response('OK', status=status.HTTP_200_OK)
		return Response('Error', status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def give_edit_permission(request):
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'POST':
		data = JSONParser().parse(request)
		if 'folder_id' in data.keys():
			folder_id = data['folder_id']
			storage_manager.give_folder_edit_perm(folder_id, request.user.id)
			return Response('OK', status=status.HTTP_200_OK)
		elif 'file_id' in data.keys():
			file_id = data['file_id']
			storage_manager.give_file_edit_perm(file_id, request.user.id)
			return Response('OK', status=status.HTTP_200_OK)
		return Response('Error', status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def deny_read_permission(request):
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'POST':
		data = JSONParser().parse(request)
		if 'folder_id' in data.keys():
			folder_id = data['folder_id']
			storage_manager.deny_folder_read_perm(folder_id, request.user.id)
			return Response('OK', status=status.HTTP_200_OK)
		elif 'file_id' in data.keys():
			file_id = data['file_id']
			storage_manager.deny_file_read_perm(file_id, request.user.id)
			return Response('OK', status=status.HTTP_200_OK)
		return Response('Error', status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def deny_edit_permission(request):
	storage_manager.user_activity(request.user.username, request.build_absolute_uri())
	if request.method == 'POST':
		data = JSONParser().parse(request)
		if 'folder_id' in data.keys():
			folder_id = data['folder_id']
			storage_manager.deny_folder_edit_perm(folder_id, request.user.id)
			return Response('OK', status=status.HTTP_200_OK)
		elif 'file_id' in data.keys():
			file_id = data['file_id']
			storage_manager.deny_file_edit_perm(file_id, request.user.id)
			return Response('OK', status=status.HTTP_200_OK)
		return Response('Error', status=status.HTTP_400_BAD_REQUEST)
# -----------------------------------------------FILE METHODS-----------------------------------------------------


@api_view(['POST'])
@permission_classes((AllowAny, ))
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