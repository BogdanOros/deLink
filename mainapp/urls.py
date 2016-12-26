from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    # url(r'^folders$', views.folders),
    # url(r'^folders/(?P<path>[A-Za-z0-9/]*)$', views.get_folder),

    url(r'^registration$', views.registration),
    url(r'^authorization$', views.authorization),
    url(r'^logout$', views.logout),
    url(r'^search_user$', views.search_user),
    url(r'^forgot_password$', views.forgot_password),
    url(r'^reset_password$', views.reset_password),
    url(r'^change_password$', views.change_password),

    url(r'^(?P<username>[A-Za-z0-9]{2,})/(?P<path>[A-Za-z0-9/]*)$', views.get_folder),
    url(r'^create_folder$', views.create_new_folder),
    url(r'^delete_folder$', views.delete_folder),
    url(r'^update_folder$', views.update_folder),

    url(r'^search$', views.search_content),
    url(r'^statistics$', views.show_statistics),

    url(r'^upload_file$', views.upload_file),
    url(r'^download_file$', views.get_file),
    url(r'^delete_file$', views.delete_file),
    url(r'^update_file$', views.update_file),

    url(r'^u/(?P<username>[A-Za-z0-9]+)$', views.profile),

    url(r'^send_request$', views.send_friend_request),
    url(r'^accept_request$', views.accept_friend_request),
    url(r'^decline_request$', views.decline_friend_request),
    url(r'^delete_friend$', views.delete_from_friends),

    url(r'^give_read_permission$', views.give_read_permission),
    url(r'^deny_read_permission$', views.deny_read_permission),

    url(r'^restore_db$', views.restore_db),

]

