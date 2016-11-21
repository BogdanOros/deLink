from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from .models import User, Friendship
import hashlib
from .hash_manager import HashManager

hash_manager = HashManager()


def check_auth(request):
	auth = None
	try:
		auth = request.session['user_id']
	except KeyError:
		pass
	return auth


def homepage(request):
	user_id = check_auth(request)
	if user_id:
		logged_user = User.objects.get(pk=user_id)
		return render(request, 'mainapp/homepage.html', {'logged_user': logged_user})
	return render(request, 'mainapp/homepage.html')


def registration(request):

	if request.method == 'POST':
		email, password, name, surname = request.POST['mail'], request.POST['password'], \
				request.POST['name'], request.POST['surname']

		new_user = User(email=email, password=hash_manager.hash_value(password), name=name, surname=surname)
		new_user.save()
		return HttpResponseRedirect('/')
	return render(request, 'mainapp/registration.html')


def authorization(request):

	if request.method == 'POST':
		email, password = request.POST['mail'], request.POST['password']
		# logged_user = None

		try:
			logged_user = User.objects.get(email=email)
		except ObjectDoesNotExist:
			return render(request, 'mainapp/authorization.html', {'error': 'Email doesn\'t exist'})

		if logged_user and logged_user.password == hash_manager.hash_value(password):
			request.session['user_id'] = logged_user.id
			return HttpResponseRedirect('/')

	return render(request, 'mainapp/authorization.html')