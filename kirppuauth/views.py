# -*- coding: utf-8 -*-
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model, login, logout
from django.http import Http404
from django.http.response import HttpResponseForbidden
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

__author__ = 'codez'


@csrf_protect
@never_cache
def local_admin_login(request):
    if not (settings.KIRPPU_SU_AS_USER and request.user.is_authenticated and request.user.is_superuser):
        raise Http404()

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "")
        if username != "":
            UserModel = get_user_model()
            try:
                user = UserModel.objects.get(username=username)
            except UserModel.DoesNotExist:
                error = _("User {} not found.").format(username)
            else:
                if user.is_superuser:
                    return HttpResponseForbidden()
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                logout(request)
                login(request, user)
                return redirect(reverse('kirppu:front_page'))
        else:
            error = _("Username is required.")

    return render(request, "kirppuauth/login.html", {
        "submit": reverse('kirppuauth:local_admin_login'),
        "plain_error": error,
    })
