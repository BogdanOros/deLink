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
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
# imports from custom modules
from deLink import settings
from backends import CustomUserAuth
from .models import CustomUser, Friendship
from .mongo_models import Folder, File
from .serializers import FolderSerializer, UserSerializer
from .storage_manager import StorageManager


storage_manager = StorageManager()


# @login_required
@api_view(['GET'])
@csrf_exempt
def folders(request):

	if request.method == 'GET':
		# serializer = UserSerializer(CustomUser.objects.get(pk=1))
		serializer = FolderSerializer(storage_manager.get_main_folder(1))
		return Response(serializer.data)


@login_required
@api_view(['GET'])
@csrf_exempt
def profile(request):

	if request.method == 'GET':
		serializer = UserSerializer(CustomUser.objects.get(pk=request.user.id))
		return Response(serializer.data)


@login_required
@api_view(['GET', 'POST'])
def get_folder(request, path):
	"""
	Gets user's folder in two ways:
		1: if it is GET request, parses the path and checks if user has such folder
		2: if it is POST request, pulls out folder's id from POST and does select in MongoDB
	"""
	folder = None
	if request.method == 'POST':
		if 'folder_id' in request.POST:
			folder_id = request.POST['folder_id']
			folder = storage_manager.search_folder_by_id(folder_id)

	elif request.method == 'GET':
		if path[-1] == '/':
			path = path[:-1]

		user_id = request.user.id
		title = path.split('/')[-1]
		folder = storage_manager.search_folder_by_title(title, user_id)

	if folder:
		serializer = FolderSerializer(folder)
		return Response(serializer.data, status=status.HTTP_200_OK)
	return Response({'error': 'Folder doesn\'t exists'}, status=status.HTTP_400_BAD_REQUEST)


# @login_required
@api_view(['POST'])
def create_new_folder(request):
	"""
	Function that creates new folder.
	Also checks where folders is creating(main folder or no)
	"""
	if request.method == 'POST':
		data = JSONParser().parse(request)
		print (data)
		folder = Folder(data['title'], 1).as_dict()
		storage_manager.save_folder(folder, data['parent_id'])
		return Response(1, status=status.HTTP_200_OK)


# @login_required
@api_view(['GET'])
def homepage(request):
	"""
	Home page
	"""
	if request.method == 'GET':
		user = request.user
		print (repr(user))
		# return Response({'ok': 'true'})
		return render(request, 'mainapp/homepage.html')


@api_view(['POST'])
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
def authorization(request):
	"""
	Authenticate and login user in the system
	"""
	if request.method == 'POST':
		data = JSONParser().parse(request)
		user = CustomUserAuth.authenticate(username=data['email'], password=data['password'])
		if user:
			auth.login(request, user)
			return Response({'ok': 'true'})
		else:
			return Response({'ok': 'false'})


@api_view(['GET'])
@csrf_exempt
def logout(request):
	"""
	Logout user from system
	"""
	if request.method == 'GET':
		auth.logout(request)
		return Response({'ok': 'logged out'})


# @login_required
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


