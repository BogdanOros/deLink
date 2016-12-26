from .models import CustomUser as User
from .models import FriendRequest, Friendship
from django.db.models import Q
from deLink import settings
import random


def get_friend_status(session_user, requested_user):
	is_friend = Friendship.objects.filter(first_user=session_user.id, second_user=requested_user.id)
	if is_friend:
		return 1

	is_requested = FriendRequest.objects.filter(Q(from_user=session_user, to_user=requested_user) |
	                                       Q(from_user=requested_user, to_user=session_user))
	if is_requested:
		return 2
	return 0


def get_title_from_path(path):
	if path[-1] == '/':
		path = path[:-1]

	return path.split('/')[-1]


def get_type_of_file(filename):
	return filename.split('.')[-1]


def generate_reset_code():
	code = ""
	for i in range(settings.RESET_CODE_LENGTH):
		next_index = random.randrange(len(settings.ALPHABET))
		code += settings.ALPHABET[next_index]
	return code


def check_permissions(folder, user_id):

	subfolders = folder['subfolders']
	if subfolders:
		subfolders_with_perm = []
		for subfolder in subfolders:
			if user_id in subfolder['read_permission']:
				subfolders_with_perm.append(subfolder)
		folder['subfolders'] = subfolders_with_perm
	# files = folder['files']
	# if files:
	# 	files_with_perm = []
	# 	for file in files:
	# 		if user_id in file['read_permission']:
	# 			if user_id in file['edit_permission']:
	# 				file['editable'] = 1
	# 			files_with_perm.append(file)
	# 	folder['files'] = files_with_perm
	return folder