from django import template
from django.conf import settings

register = template.Library()

__author__ = 'codez'


@register.simple_tag(name="kirppu_login_url")
def login_url():
    return settings.LOGIN_URL


@register.simple_tag(name="kirppu_logout_url")
def logout_url():
    return settings.LOGOUT_URL
