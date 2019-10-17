from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
)
from django.forms import forms
from django.contrib import admin

from .models import User

__author__ = 'codez'


class KirppuUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(
            self.error_messages['duplicate_username']
        )


class KirppuUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User


class KirppuUserAdmin(UserAdmin):
    form = KirppuUserChangeForm
    add_form = KirppuUserCreationForm


admin.site.register(User, KirppuUserAdmin)
