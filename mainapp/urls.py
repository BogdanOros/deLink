from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^$', views.homepage, name='homepage'),
    url(r'^registration$', views.registration, name='registration'),
    url(r'^authorization', views.authorization, name='authorization'),
]
