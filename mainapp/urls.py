from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^$', views.homepage, name='homepage'),
    url(r'^registration$', views.registration, name='registration'),
    url(r'^authorization$', views.authorization, name='authorization'),
    url(r'^upload_file$', views.upload_file, name='upload_file'),
    url(r'^folders$', views.folders),
    url(r'^folders/(?P<path>[A-Za-z0-9/]*)$', views.folder),
    url(r'^logout$', views.logout)
]
