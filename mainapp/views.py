from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from .models import CustomUser, Friendship


def homepage(request):
	return render(request, 'mainapp/homepage.html')


def registration(request):
	if request.method == 'POST':
		return HttpResponseRedirect('/')
	return render(request, 'mainapp/registration.html')


def authorization(request):

	if request.method == 'POST':
		email = request.POST['email']
		password = request.POST['password']
		user = auth.authenticate(email=email, password=password)

		if user:
			auth.login(request, user)
			return HttpResponseRedirect('/loggedIn')
		else:
			return HttpResponseRedirect('/invlid')

	return render(request, 'mainapp/authorization.html')