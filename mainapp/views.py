from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist

from django.contrib import auth
from backends import CustomUserAuth
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import CustomUser, Friendship
from .mongo_models import Folder
from .serializers import FolderSerializer, UserSerializer
from .storage_manager import StorageManager

storage_manager = StorageManager()


@api_view(['GET', 'POST'])
@csrf_exempt
def folders(request):

	if request.method == 'GET':
		serialized_list = FolderSerializer(storage_manager.get_folders(), many=True)
		print (serialized_list.data)
		# return Response(serialized_list.data)
		return render(request, 'mainapp/folders.html', {'folders': storage_manager.get_folders()})


@login_required
@api_view(['GET', 'POST'])
@csrf_exempt
def folder(request, path):
	if request.method == 'POST':
		folder_id = request.POST['folder_id']
		folder = storage_manager.search_folder_by_id(folder_id)
		serializer = FolderSerializer(folder)

		return Response(serializer.data)
	# elif request.method == 'GET':
	# 	return render(request, 'mainapp/folders.html', {'folders': storage_manager.get_folders()})


@login_required
@api_view(['POST'])
@csrf_exempt
def create_new_folder(request, parent_folder=None):
	if request.method == 'POST':
		folder_title = request.POST['title']
		print (request.user.id)


@api_view(['GET'])
def homepage(request):
	return render(request, 'mainapp/homepage.html')


@api_view(['GET', 'POST'])
@csrf_exempt
def registration(request):
	if request.method == 'POST':
		return Response({'ok':'dunno'})
	elif request.method == 'GET':
		return render(request, 'mainapp/registration.html')


@api_view(['GET', 'POST'])
@csrf_exempt
def authorization(request):
	"""
	Authenticate and login user in the system
	"""
	if request.method == 'POST':
		email = request.POST['email']
		password = request.POST['password']
		user = CustomUserAuth.authenticate(username=email, password=password)
		if user:
			auth.login(request, user)
			return Response({'ok': 'true'})
		else:
			return Response({'ok': 'false'})
	elif request.method == 'GET':
		return render(request, 'mainapp/authorization.html')


@api_view(['GET', 'POST'])
@csrf_exempt
def logout(request):
	"""
	Logout user from system
	"""
	# if request.method == 'POST':
	print ('lol')
	auth.logout(request)
	# return Response({'ok': 'true'})
	return render(request, 'mainapp/authorization.html')


def upload_file(request):

	if request.method == 'POST':
		filename = request.FILES['file'].name
		file_doc = File(title=filename, user_id=1)
		uploaded_file = request.FILES['file'].read()
		file_doc.file.put(uploaded_file)
		folder = Folder.objects.first()
		print (folder)
		if folder.files:
			folder.files.append(file_doc)
		else:
			folder.files = [file_doc]
		folder.save()
	return HttpResponseRedirect('/')


