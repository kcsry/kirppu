from urllib import parse

from django import template
from django.conf import settings

register = template.Library()

__author__ = 'codez'


def _join_next(original, redirect):
    url = parse.urlsplit(original)
    if not url.netloc and redirect:
        url = list(url)
        query = parse.parse_qs(url[3])  # 3=query
        query["next"] = redirect
        url[3] = parse.urlencode(query)
        return parse.urlunsplit(url)
    return original


@register.simple_tag(name="kirppu_login_url")
def login_url(redirect=None):
    return _join_next(settings.LOGIN_URL, redirect)


@register.simple_tag(name="kirppu_logout_url")
def logout_url(redirect=None):
    return _join_next(settings.LOGOUT_URL, redirect)
