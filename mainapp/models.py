from __future__ import unicode_literals
from django.contrib.auth.models import AbstractBaseUser
from django.db import models


class Friendship(models.Model):
    first_user = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True,
                                   related_name='first_contact')
    second_user = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True,
                                    related_name='second_contact')

    class Meta:
        # managed = False
        db_table = 'Friendship'


class User(AbstractBaseUser):
    email = models.CharField(max_length=80, unique=True)
    # password = models.CharField(max_length=80)
    name = models.CharField(max_length=100, blank=True, null=True)
    surname = models.CharField(max_length=100, blank=True, null=True)
    facebook_id = models.CharField(max_length=100, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['name', 'surname', 'password']

    class Meta:
        # managed = False
        db_table = 'User'
