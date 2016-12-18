from __future__ import unicode_literals
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, AbstractUser
from django.db import models
from datetime import datetime
from django.utils.timezone import now
from django.db.models.signals import post_save
from django.dispatch import receiver
from deLink import settings
from rest_framework.authtoken.models import Token


# This code is triggered whenever a new user has been created and saved to the database
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
	if created:
		Token.objects.create(user=instance)


class Friendship(models.Model):
	first_user = models.ForeignKey('CustomUser', models.DO_NOTHING, blank=True, null=True,
	                               related_name='first_contact')
	second_user = models.ForeignKey('CustomUser', models.DO_NOTHING, blank=True, null=True,
	                                related_name='second_contact')
	created_date = models.DateTimeField(default=now())

	class Meta:
		# managed = False
		db_table = 'Friendship'


class FriendRequest(models.Model):
	from_user = models.ForeignKey('CustomUser', models.DO_NOTHING, blank=True, null=True,
	                               related_name='from_user')
	to_user = models.ForeignKey('CustomUser', models.DO_NOTHING, blank=True, null=True,
	                                related_name='to_user')
	created_date = models.DateTimeField(default=now())

	class Meta:
		db_table = 'FriendRequest'


class CustomUserManager(BaseUserManager):
	def _create_user(self, email, password, is_superuser, **extra_fields):
		"""
		Creates and saves a User with the given email and password.
		"""

		if not email:
			raise ValueError('The given email must be set')

		email = self.normalize_email(email)
		user = self.model(email=email, is_active=True,
		                  is_superuser=is_superuser, last_login=now(),
		                  date_joined=now(), **extra_fields)

		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_user(self, email, password=None, **extra_fields):
		return self._create_user(email, password, False, **extra_fields)

	def create_superuser(self, email, password=None, **extra_fields):
		return self._create_user(email, password, True, **extra_fields)


class CustomUser(AbstractUser, PermissionsMixin):

	email = models.CharField(max_length=80, unique=True)
	facebook_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
	date_joined = models.DateTimeField(default=now())

	is_active = models.BooleanField(default=True)
	is_superuser = models.BooleanField(default=False)
	USERNAME_FIELD = 'email'

	REQUIRED_FIELDS = ['first_name', 'last_name']

	objects = CustomUserManager()

	def get_full_name(self):
		return self.last_name + ' ' + self.first_name

	def get_short_name(self):
		return self.first_name

	class Meta:
		verbose_name = 'user'
		verbose_name_plural = 'users'

	def get__absolute_url(self):
		return '/users/%s/' % urlquote(self.email)

	def has_perm(self, perm, obj=None):
		return True

	def has_module_perms(self, app_label):
		return True

	@property
	def is_staff(self):
		return self.is_superuser