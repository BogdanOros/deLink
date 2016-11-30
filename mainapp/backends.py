from models import CustomUser
from django.contrib.auth.backends import ModelBackend


class CustomUserAuth(object):

	# @staticmethod
	def authenticate(self, username=None, password=None):
		try:
			user = CustomUser.objects.get(email=username)
			print (username, password)
			if user.check_password(password):
				return user
		except CustomUser.DoesNotExist:
			return None

	def get_user(self, user_id):
		try:
			user = CustomUser.objects.get(pk=user_id)
			if user.is_active:
				return user
			return None
		except CustomUser.DoesNotExist:
			return None
