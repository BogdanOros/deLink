from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    # url(r'^folders$', views.folders),
    # url(r'^folders/(?P<path>[A-Za-z0-9/]*)$', views.get_folder),

    url(r'^registration$', views.registration),
    url(r'^authorization$', views.authorization),
    url(r'^logout$', views.logout, name='logout'),

    url(r'^(?P<username>[A-Za-z0-9]{2,})/(?P<path>[A-Za-z0-9/]*)$', views.get_folder),
    url(r'^create_folder$', views.create_new_folder),
    url(r'^delete_folder$', views.delete_folder),
    url(r'^update_folder$', views.update_folder),

    url(r'^upload_file$', views.upload_file),

    url(r'^u/(?P<username>[A-Za-z0-9]+)$', views.profile),
    url(r'^send_request$', views.send_friend_request),
]

