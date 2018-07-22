# -*- coding: utf-8 -*-
from collections import OrderedDict
from decimal import Decimal
import textwrap

from django.conf import settings
from django.core import signing
from django.db import transaction, models
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.http.response import HttpResponseForbidden, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from ipware.ip import get_ip
from ratelimit.utils import is_ratelimited

from .models import Item, TemporaryAccessPermit, Vendor, TemporaryAccessPermitLog, Box
from .templatetags.kirppu_tags import format_price
from .util import first, shorten_text

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
        self.boxes = set()
        self.sum = Decimal(0)


def _ratelimit_key(group, request):
    return get_ip(request)


def _login_view(request):
    errors = []
    if request.method == "POST":
        key = request.POST.get("key", "")
        if len(key) == 0:
            errors.append(_("Access key must be given"))
        elif is_ratelimited(
                request,
                fn=_login_view,
                key=_ratelimit_key,
                rate=settings.KIRPPU_MOBILE_LOGIN_RATE_LIMIT,
                increment=True):
            errors.append(_("You are trying too much. Try again later."))
        else:
            with transaction.atomic():
                try:
                    permit = TemporaryAccessPermit.objects.get(short_code=key)
                except TemporaryAccessPermit.DoesNotExist:
                    errors.append(_("Invalid access key"))
                else:
                    can_use = permit.state == TemporaryAccessPermit.STATE_UNUSED\
                              and permit.expiration_time >= timezone.now()

                    TemporaryAccessPermitLog.objects.create(
                        permit=permit,
                        action=TemporaryAccessPermitLog.ACTION_USE if can_use else TemporaryAccessPermitLog.ACTION_TRY,
                        address=shorten_text(get_ip(request) + "; " + request.META.get("REMOTE_HOST", ""),
                                             TemporaryAccessPermitLog._meta.get_field("address").max_length, False),
                        peer=shorten_text(request.META.get("HTTP_USER_AGENT", ""),
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
        try:
            vendor = Vendor.get_vendor(request)
        except Vendor.DoesNotExist:
            if request.GET.get("type") == "txt":
                return HttpResponse(_("Unregistered vendor."), content_type="text/plain; charset=utf-8")
            return render(request, "kirppu/vendor_status.html", {
                "tables": {},
                "CURRENCY": settings.KIRPPU_CURRENCY,
                "vendor": request.user,
            })

    items = Item.objects \
        .filter(vendor=vendor, hidden=False) \
        .select_related("box") \
        .only("id", "hidden", "price", "state", "code", "name", "box__id")

    box_extras = {
        "items_%s" % key: models.Count(models.Case(models.When(item__state__in=table.states, then=1),
                                                   output_field=models.IntegerField()))
        for key, table in TABLES.items()
    }

    box_objects = Box.objects \
        .filter(item__vendor=vendor) \
        .select_related("representative_item") \
        .annotate(item_count=Count("item"), **box_extras)

    boxes = {box.pk: box for box in box_objects}

    currency_length = len(format_price(Decimal(0))) - 1

    tables = OrderedDict((k, TableContents(spec=TABLES[k])) for k in TABLES_ORDER)
    max_price_width = 0
    for item in items:
        table_key = TABLE_FOR_STATE[item.state]
        for candidate in table_key:
            table_spec = TABLES[candidate]
            if table_spec.filter(item) and candidate in tables:
                table = tables[candidate]  # type: TableContents
                row = None

                price_value = None
                price_multiplier = 1

                if item.box is not None:
                    pk = item.box.pk
                    if pk not in table.boxes:
                        table.boxes.add(pk)
                        box = boxes[pk]
                        row = _box(box, candidate)

                        price_multiplier = getattr(box, "items_%s" % candidate)
                        price_value = box.representative_item.price
                else:
                    row = _item(item)
                    price_value = item.price

                if row is not None:
                    max_price_width = max(max_price_width, len(str(row["price"])) + currency_length)
                    table.items.append(row)
                    table.sum += price_value * price_multiplier
                break

    if request.GET.get("type") == "txt":
        sign_data = {}
        total_items = 0
        for key, table in tables.items():
            if key == "registered":
                continue
            items = [_sign_data(i) for i in table.items]
            total_items += len(items)
            sign_data[key] = items
            sign_data[key + "_s"] = str(table.sum)

        if total_items > 0:
            sign_data["vendor"] = vendor.id
            signature = signing.dumps(sign_data, compress=True)
            signature = "\n".join(textwrap.wrap(signature, 78, break_on_hyphens=False))
        else:
            signature = None

        return render(request, "kirppu/vendor_status.txt", {
            "tables": tables,
            "price_width": max_price_width,
            "vendor": vendor.id,
            "signature": signature,
        }, content_type="text/plain; charset=utf-8")
    return render(request, "kirppu/vendor_status.html", {
        "tables": tables,
        "CURRENCY": settings.KIRPPU_CURRENCY,
        "vendor": vendor.id,
    })


def _item(item):
    return {
        "code": item.code,
        "price": item.price_fmt,
        "name": item.name,
    }


def _box(box, table_key):
    """
    :type box: Box
    :type table_key: str
    """
    return {
        "box": True,
        "code": box.representative_item.code,
        "price": box.representative_item.price_fmt,
        "name": box.description,
        "value": getattr(box, "items_%s" % table_key),
        "total": box.item_count,
    }


def _sign_data(item_dict):
    if "box" in item_dict:
        return "{}@{}:{}/{}".format(item_dict["code"], item_dict["price"], item_dict["value"], item_dict["total"])
    return "{}@{}".format(item_dict["code"], item_dict["price"])


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
    # FIXME: Implement a better way to enable the link. db-options...
    from .models import UIText
    try:
        login_text = UIText.objects.get(identifier="mobile_login")
        if "--enable--" not in login_text.text:
            raise UIText.DoesNotExist()
    except UIText.DoesNotExist:
        return HttpResponseForbidden(_("This location is not in use."))

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
