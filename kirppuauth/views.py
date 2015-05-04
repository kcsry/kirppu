# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model, login, logout
from django.http import Http404
from django.http.response import HttpResponseForbidden
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

__author__ = 'codez'


@csrf_protect
@never_cache
def local_admin_login(request):
    if not (settings.KIRPPU_SU_AS_USER and request.user.is_authenticated() and request.user.is_superuser):
        raise Http404()

    if request.method == "POST":
        username = request.POST.get("username", "")
        if username != "":
            user = get_user_model().objects.get(username=username)
            if user.is_superuser:
                return HttpResponseForbidden()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            logout(request)
            login(request, user)
            return redirect(reverse('kirppu:vendor_view'))

    return render(request, "kirppuauth/login.html", {
        "submit": reverse('kirppuauth:local_admin_login'),
    })
