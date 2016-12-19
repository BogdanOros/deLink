from .models import CustomUser as User
from .models import FriendRequest, Friendship
from django.db.models import Q


def get_friend_status(session_user, requested_user):
	is_friend = Friendship.objects.filter(Q(first_user=session_user, second_user=requested_user) &
	                                       Q(first_user=requested_user, second_user=session_user))
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