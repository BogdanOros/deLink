# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-21 13:40
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Contacts',
            new_name='Friendship',
        ),
        migrations.RenameModel(
            old_name='Users',
            new_name='User',
        ),
        migrations.AlterModelTable(
            name='friendship',
            table='Friendship',
        ),
        migrations.AlterModelTable(
            name='user',
            table='User',
        ),
    ]
