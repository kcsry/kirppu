# -*- coding: utf-8 -*-
from collections import OrderedDict

from django.conf import settings
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from ipware.ip import get_ip

from .util import first, shorten_text
from .models import Item, TemporaryAccessPermit, Vendor, TemporaryAccessPermitLog

__author__ = 'codez'
_PERMIT_SESSION_KEY = "temporary_permit_key"


class Table(object):
    def __init__(self, states, title, hidden=False, checkable=False, custom_filter=None):
        self.states = states
        self.title = title
        self.hidden = hidden
        self.checkable = checkable
        self.custom_filter = custom_filter

    def filter(self, item):
        if self.custom_filter:
            return self.custom_filter(self, item)
        else:
            return item.state in self.states


TABLES = {
    "returnable": Table(
        [Item.BROUGHT, Item.STAGED],
        title=_('Returnable Items'),
        checkable=True,
    ),
    "compensable": Table(
        [Item.SOLD],
        title=_('Compensable Items'),
    ),
    "compensated": Table(
        [Item.COMPENSATED],
        title=_('Compensated Items'),
    ),
    "other": Table(
        [Item.MISSING, Item.RETURNED],
        title=_('Other Items'),
    ),
    "registered": Table(
        [Item.ADVERTISED],
        title=_('Not brought to event'),
        hidden=True,
        custom_filter=lambda self, i: i.state in self.states and not i.hidden,
    ),
    "deleted": Table(
        [Item.ADVERTISED],
        title=_('Deleted'),
        hidden=True,
        custom_filter=lambda self, i: i.state in self.states and i.hidden,
    ),
}

TABLES_ORDER = [
    "returnable",
    "compensable",
    "compensated",
    "other",
    "registered",
]

TABLE_FOR_STATE = {}


def __populate_table_for_state():
    for key, table in TABLES.items():
        for state in table.states:
            TABLE_FOR_STATE.setdefault(state, []).append(key)
__populate_table_for_state()


class TableContents(object):
    def __init__(self, spec):
        self.spec = spec
        self.items = []


def _login_view(request):
    errors = []
    if request.method == "POST":
        key = request.POST.get("key", "")
        if len(key) == 0:
            errors.append(_("Access key must be given"))
        else:
            with transaction.atomic():
                try:
                    permit = TemporaryAccessPermit.objects.get(short_code=key)
                except TemporaryAccessPermit.DoesNotExist as e:
                    errors.append(_("Invalid access key"))
                else:
                    can_use = permit.state == TemporaryAccessPermit.STATE_UNUSED\
                              and permit.expiration_time >= timezone.now()

                    TemporaryAccessPermitLog.objects.create(
                        permit=permit,
                        action=TemporaryAccessPermitLog.ACTION_USE if can_use else TemporaryAccessPermitLog.ACTION_TRY,
                        address=shorten_text(get_ip(request) + "; " + request.META["REMOTE_HOST"],
                                             TemporaryAccessPermitLog._meta.get_field("address").max_length, False),
                        peer=shorten_text(request.META["HTTP_USER_AGENT"],
                                          TemporaryAccessPermitLog._meta.get_field("peer").max_length, False)
                    )

                    if can_use:
                        permit.state = TemporaryAccessPermit.STATE_IN_USE
                        permit.save(update_fields=("state",))
                        request.session[_PERMIT_SESSION_KEY] = permit.pk
                        return HttpResponseRedirect(reverse("kirppu:mobile"))
                    else:
                        errors.append(_("Invalid access key"))

    field = TemporaryAccessPermit._meta.get_field("short_code")
    min_length = first(field.validators, lambda v: v.code == "min_length")
    return render(request, "kirppu/vendor_status_login.html", {
        'min_length': min_length.limit_value if min_length else 0,
        'max_length': field.max_length,
        'errors': errors,
    })


def _data_view(request, permit):
    if permit:
        vendor = permit.vendor
    else:
        vendor = Vendor.objects.get(user_id=request.user.pk)

    items = Item.objects.filter(vendor=vendor, box__isnull=True)

    tables = OrderedDict((k, TableContents(spec=TABLES[k])) for k in TABLES_ORDER)
    for item in items:
        table_key = TABLE_FOR_STATE[item.state]
        for candidate in table_key:
            table = TABLES[candidate]
            if table.filter(item) and candidate in tables:
                tables[candidate].items.append(item)
                break

    return render(request, "kirppu/vendor_status.html", {
        "tables": tables,
    })


def _is_permit_valid(request):
    if _PERMIT_SESSION_KEY in request.session:
        try:
            permit = TemporaryAccessPermit.objects.get(pk=request.session[_PERMIT_SESSION_KEY])
            if permit.state in (TemporaryAccessPermit.STATE_EXHAUSTED, TemporaryAccessPermit.STATE_INVALIDATED):
                raise TemporaryAccessPermit.DoesNotExist()

            if permit.state == TemporaryAccessPermit.STATE_UNUSED and permit.expiration_time < timezone.now():
                raise TemporaryAccessPermit.DoesNotExist()

            return permit

        except TemporaryAccessPermit.DoesNotExist:
            del request.session[_PERMIT_SESSION_KEY]
            return None
    else:
        return None


def index(request):
    if request.user.is_authenticated:
        return _data_view(request, None)
    else:
        permit = _is_permit_valid(request)
        if permit:
            return _data_view(request, permit)
        else:
            return _login_view(request)


def logout(request):
    # TODO: Check session and temporary_codes, remove both.
    if _PERMIT_SESSION_KEY in request.session:
        permit = TemporaryAccessPermit.objects.get(pk=request.session[_PERMIT_SESSION_KEY])
        if settings.KIRPPU_EXHAUST_SHORT_CODE_ON_LOGOUT:
            permit.state = TemporaryAccessPermit.STATE_EXHAUSTED
        else:
            permit.state = TemporaryAccessPermit.STATE_UNUSED
        permit.save(update_fields=["state"])

        del request.session[_PERMIT_SESSION_KEY]

    if request.user.is_authenticated:
        return HttpResponseRedirect(settings.LOGOUT_URL)
    else:
        request.session.flush()
        return HttpResponseRedirect(reverse("kirppu:mobile"))
