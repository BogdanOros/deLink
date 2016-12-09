from __future__ import unicode_literals
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, AbstractUser
from django.db import models
from datetime import datetime
from django.utils.timezone import now


class Friendship(models.Model):
	first_user = models.ForeignKey('CustomUser', models.DO_NOTHING, blank=True, null=True,
	                               related_name='first_contact')
	second_user = models.ForeignKey('CustomUser', models.DO_NOTHING, blank=True, null=True,
	                                related_name='second_contact')

	class Meta:
		# managed = False
		db_table = 'Friendship'


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
	name = models.CharField(max_length=100, blank=True, null=True)
	surname = models.CharField(max_length=100, blank=True, null=True)
	facebook_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
	date_joined = models.DateTimeField(default=now())

	# is_staff = models.BooleanField(default=False)
	is_active = models.BooleanField(default=True)
	is_superuser = models.BooleanField(default=False)
	USERNAME_FIELD = 'email'

	REQUIRED_FIELDS = ['name', 'surname']

	objects = CustomUserManager()

	def get_full_name(self):
		return self.surname + ' ' + self.name

	def get_short_name(self):
		return self.name

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