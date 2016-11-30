from django.contrib import admin
from django import forms
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser
from django.contrib.auth.models import Group
from django.contrib.auth.forms import ReadOnlyPasswordHashField


class UserCreationForm(forms.ModelForm):
	password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
	password2 = forms.CharField(label='Password confirm', widget=forms.PasswordInput)

	class Meta:
		model = CustomUser
		fields = ('email', 'name', 'surname', 'facebook_id')

	def clean_password2(self):
		# Check that the two password entries match
		password1 = self.cleaned_data.get("password1")
		password2 = self.cleaned_data.get("password2")
		if password1 and password2 and password1 != password2:
			raise forms.ValidationError("Passwords don't match")
		return password2

	def save(self, commit=True):
		# Save the provided password in hashed format
		user = super(UserCreationForm, self).save(commit=False)
		user.set_password(self.cleaned_data["password1"])
		if commit:
			user.save()
		return user


class UserChangeForm(forms.ModelForm):
	"""A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
	password = ReadOnlyPasswordHashField()

	class Meta:
		model = CustomUser
		fields = ('email', 'password', 'name', 'surname', 'date_joined',
		          'facebook_id', 'is_active', 'is_superuser')

	def clean_password(self):
		# Regardless of what the user provides, return the initial value.
		# This is done here, rather than on the field, because the
		# field does not have access to the initial value
		return self.initial["password"]


class UserAdmin(BaseUserAdmin):
	# The forms to add and change user instances
	form = UserChangeForm
	add_form = UserCreationForm

	# The fields to be used in displaying the User model.
	# These override the definitions on the base UserAdmin
	# that reference specific fields on auth.User.
	list_display = ('email', 'password', 'name', 'surname', 'date_joined',
	                'facebook_id', 'is_active', 'is_superuser')
	list_filter = ('is_superuser',)
	fieldsets = (
	    (None, {'fields': ('email', 'name',)}),
	    ('Personal info', {'fields': ('facebook_id', 'name', 'surname')}),
	    ('Permissions', {'fields': ('is_superuser',)}),
	)
	# add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
	# overrides get_fieldsets to use this attribute when creating a user.
	add_fieldsets = (
	    (None, {
	        'classes': ('wide',),
	        'fields': ('email', 'name', 'surname', 'password1', 'password2')}
	    ),
	)
	search_fields = ('email',)
	ordering = ('email',)
	filter_horizontal = ()

admin.site.register(CustomUser, UserAdmin)
admin.site.unregister(Group)