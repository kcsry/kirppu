# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse, HttpResponseBadRequest, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.http import is_safe_url
from django.views.decorators.http import require_http_methods

from .forms import PersonCreationForm
from .models import Event, Vendor
from .util import get_form

__author__ = 'codez'


def get_multi_vendor_values(request, event):
    """
    Get values for multi-vendor template operations.

    :param request: Request to read values from.
    :return: Dict for template.
    :rtype: dict
    """
    user = request.user
    can_create_vendor = False
    can_switch_vendor = False

    if event.multiple_vendors_per_user and user.is_authenticated:
        if user.is_staff and "user" in request.GET:
            raise NotImplementedError  # FIXME: Decide how this should work.
        multi_vendor = Vendor.objects.filter(user=user, person__isnull=False)
        self_vendor = Vendor.objects.filter(user=user, person__isnull=True).first()
        can_create_vendor = user.has_perm("kirppu.can_create_sub_vendor")
        can_switch_vendor = can_create_vendor or user.has_perm("kirppu.can_switch_sub_vendor")
    else:
        multi_vendor = []
        self_vendor = None

    if user.is_authenticated:
        vendor = Vendor.get_vendor(request, event)
    else:
        vendor = None

    return {
        'self_vendor': self_vendor,
        'self_name': str(self_vendor) if self_vendor is not None else str(user),
        'multi_vendor': multi_vendor,
        'current_vendor': vendor,
        'can_create_vendor': can_create_vendor,
        'can_switch_vendor': can_switch_vendor,
    }


@login_required
@require_http_methods(["POST"])
def change_vendor(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    if not event.multiple_vendors_per_user:
        raise Http404()

    user = request.user
    if not (user.has_perm("kirppu.can_create_sub_vendor") or user.has_perm("kirppu.can_switch_sub_vendor")):
        raise PermissionDenied

    new_vendor_id = int(request.POST["vendor"])
    new_vendor = get_object_or_404(Vendor, event=event, id=new_vendor_id, user=user)
    if new_vendor.person:
        request.session["vendor_id"] = new_vendor.id
    else:
        del request.session["vendor_id"]

    ref = request.META["HTTP_REFERER"]
    if not (ref and is_safe_url(ref, allowed_hosts={request.get_host()})):
        ref = reverse("kirppu:page")

    return HttpResponseRedirect(ref)


@login_required
@require_http_methods(["POST"])
@permission_required("kirppu.can_create_sub_vendor", raise_exception=True)
def create_vendor(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    if not event.multiple_vendors_per_user:
        raise Http404()

    form = get_form(PersonCreationForm, request)
    if form.is_valid():
        with transaction.atomic():
            instance = form.save()
            new_vendor = Vendor(
                event=event,
                user=request.user,
                person=instance,
            )
            new_vendor.save(force_insert=True)
        return JsonResponse({
            "result": "ok",
            "id": new_vendor.id,
        })

    return HttpResponseBadRequest(
        form.errors.as_json(),
        content_type="application/json",
    )
