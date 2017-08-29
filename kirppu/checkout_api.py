from __future__ import unicode_literals, print_function, absolute_import
import functools
import inspect
import logging
import random

from django.contrib.auth import get_user_model

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, F
from django.http.response import (
    HttpResponse,
    JsonResponse,
    StreamingHttpResponse,
)
from django.shortcuts import (
    get_object_or_404,
    render,
)
from django.utils.six import string_types, text_type, iteritems, PY3
from django.utils.translation import ugettext as _
from django.utils.timezone import now

from .api.common import (
    get_item_or_404 as _get_item_or_404,
    item_state_conflict as _item_state_conflict,
    get_receipt,
)
from .provision import Provision
from .models import (
    Item,
    Receipt,
    Clerk,
    Counter,
    ReceiptItem,
    ReceiptExtraRow,
    Vendor,
    UserAdapter,
    ItemStateLog,
    Box,
)
from .fields import ItemPriceField
from .forms import ItemRemoveForm

from . import ajax_util
from .ajax_util import (
    AjaxError,
    AjaxFunc,
    get_counter,
    get_clerk,
    require_user_features,
    RET_ACCEPTED,
    RET_BAD_REQUEST,
    RET_CONFLICT,
    RET_AUTH_FAILED,
    RET_LOCKED,
)

logger = logging.getLogger(__name__)


def raise_if_item_not_available(item):
    """Raise appropriate AjaxError if item is not in buyable state."""
    if item.state == Item.STAGED:
        # Staged somewhere other?
        raise AjaxError(RET_LOCKED, 'Item is already staged to be sold.')
    elif item.state == Item.ADVERTISED:
        return 'Item has not been brought to event.'
    elif item.state in (Item.SOLD, Item.COMPENSATED):
        raise AjaxError(RET_CONFLICT, 'Item has already been sold.')
    elif item.state == Item.RETURNED:
        raise AjaxError(RET_CONFLICT, 'Item has already been returned to owner.')
    return None


# Registry for ajax functions. Maps function names to AjaxFuncs.
AJAX_FUNCTIONS = {}


def _register_ajax_func(func):
    AJAX_FUNCTIONS[func.name] = func


def ajax_func(url, method='POST', counter=True, clerk=True, overseer=False, atomic=False, staff_override=False):
    """
    Decorate a function with some common logic.
    The names of the function being decorated are required to be present in the JSON object
    that is passed to the function, and they are automatically decoded and passed to those
    arguments.

    :param url: URL RegEx this function is served in.
    :type url: str
    :param method: HTTP Method required. Default is POST.
    :type method: str
    :param counter: Is registered Counter required? Default: True.
    :type counter: bool
    :param clerk: Is logged in Clerk required? Default: True.
    :type clerk: bool
    :param overseer: Is overseer permission required for Clerk? Default: False.
    :type overseer: bool
    :param atomic: Should this function run in atomic transaction? Default: False.
    :type atomic: bool
    :return: Decorated function.
    """

    def decorator(func):
        # Get argspec before any decoration.
        if PY3:
            spec = inspect.getfullargspec(func)
        else:
            # noinspection PyDeprecation
            spec = inspect.getargspec(func)

        func = require_user_features(counter, clerk, overseer, staff_override=staff_override)(func)

        fn = ajax_util.ajax_func(
            method,
            spec.args[1:],
            spec.defaults
        )(func)
        if atomic:
            fn = transaction.atomic(fn)

        # Copy name etc from original function to wrapping function.
        # The wrapper must be the one referred from urlconf.
        fn = functools.wraps(func)(fn)
        _register_ajax_func(AjaxFunc(fn, url, method, staff_override))

        return fn
    return decorator


# Must be after ajax_func to ensure circular import works. Must be imported, for part to be included at all in the API.
# noinspection PyUnresolvedReferences
from .api import (
    boxes_api,
    receipt as receipt_api,
)


def checkout_js(request):
    """
    Render the JavaScript file that defines the AJAX API functions.
    """
    context = {
        'funcs': iteritems(AJAX_FUNCTIONS),
        'api_name': 'Api',
    }
    return render(
        request,
        "kirppu/app_ajax_api.js",
        context,
        content_type="application/javascript"
    )


@transaction.atomic
def item_mode_change(request, code, from_, to, message_if_not_first=None):
    item = _get_item_or_404(code)
    if not isinstance(from_, tuple):
        from_ = (from_,)
    if item.state in from_:
        if item.hidden:
            # If an item is brought to the event, even though the user deleted it, it should begin showing again in
            # users list. The same probably applies to any interaction with the item.
            item.hidden = False

        ItemStateLog.objects.log_state(item=item, new_state=to, request=request)
        old_state = item.state
        item.state = to
        item.save()
        ret = item.as_dict()
        if message_if_not_first is not None and len(from_) > 1 and old_state != from_[0]:
            ret.update(_message=message_if_not_first)
        return ret

    else:
        # Item not in expected state.
        _item_state_conflict(item)


@ajax_func('^clerk/login$', clerk=False, counter=False)
def clerk_login(request, code, counter):
    try:
        counter_obj = Counter.objects.get(identifier=counter)
    except Counter.DoesNotExist:
        raise AjaxError(RET_AUTH_FAILED, _(u"Counter has gone missing."))

    try:
        clerk = Clerk.by_code(code)
    except ValueError as ve:
        raise AjaxError(RET_AUTH_FAILED, repr(ve))

    if clerk is None:
        raise AjaxError(RET_AUTH_FAILED, _(u"No such clerk."))

    clerk_data = clerk.as_dict()
    clerk_data['overseer_enabled'] = clerk.user.has_perm('kirppu.oversee')
    clerk_data['stats_enabled'] = clerk.user.is_staff or clerk.user.has_perm('kirppu.oversee')

    active_receipts = Receipt.objects.filter(clerk=clerk, status=Receipt.PENDING, type=Receipt.TYPE_PURCHASE)
    if active_receipts:
        if len(active_receipts) > 1:
            clerk_data["receipts"] = [receipt.as_dict() for receipt in active_receipts]
            clerk_data["receipt"] = "MULTIPLE"
        else:
            receipt = active_receipts[0]
            if "receipt" in request.session:
                logging.warning("Previous receipt reference found in session at login.")
            request.session["receipt"] = receipt.pk
            clerk_data["receipt"] = receipt.as_dict()

    elif "receipt" in request.session:
        logging.warning("Stale receipt reference found in session at login.")
        del request.session["receipt"]

    request.session["clerk"] = clerk.pk
    request.session["clerk_token"] = clerk.access_key
    request.session["counter"] = counter_obj.pk
    return clerk_data


@ajax_func('^clerk/logout$', clerk=False, counter=False)
def clerk_logout(request):
    """
    Logout currently logged in clerk.
    """
    clerk_logout_fn(request)
    return HttpResponse()


def clerk_logout_fn(request):
    """
    The actual logout procedure that can be used from elsewhere too.

    :param request: Active request, for session access.
    """
    for key in ["clerk", "clerk_token", "counter", "receipt"]:
        request.session.pop(key, None)


@ajax_func('^counter/validate$', clerk=False, counter=False)
def counter_validate(request, code):
    """
    Validates the counter identifier and returns its exact form, if it is
    valid.
    """
    try:
        counter = Counter.objects.get(identifier__iexact=code)
    except Counter.DoesNotExist:
        raise AjaxError(RET_AUTH_FAILED)

    return {"counter": counter.identifier,
            "name": counter.name}


@ajax_func('^item/find$', method='GET')
def item_find(request, code):
    item = _get_item_or_404(code)
    value = item.as_dict()
    if "available" in request.GET:
        if item.state == Item.STAGED:
            suspended = item.receipt_set.filter(status=Receipt.SUSPENDED, type=Receipt.TYPE_PURCHASE).distinct()
            if len(suspended) == 1:
                suspended = suspended[0]
                value.update(receipt=suspended.as_dict())
                return JsonResponse(
                    value,
                    status=RET_LOCKED,
                    content_type='application/json',
                )

        message = raise_if_item_not_available(item)
        if message is not None:
            value.update(_message=message)
    return value


@ajax_func('^item/search$', method='GET', overseer=True)
def item_search(request, query, code, vendor, min_price, max_price, item_type, item_state):

    clauses = []

    types = item_type.split()
    if types:
        clauses.append(Q(itemtype__in=types))

    code = code.strip()
    if code:
        clauses.append(Q(code__contains=code))

    if vendor:
        clauses.append(Q(vendor=vendor))

    states = item_state.split()
    if states:
        clauses.append(Q(state__in=states))

    for part in query.split():
        p = Q(name__icontains=part)
        if Item.is_item_barcode(part):
            p |= Q(code=part)
        clauses.append(p)

    try:
        clauses.append(Q(price__gte=float(min_price)))
    except ValueError:
        pass

    try:
        clauses.append(Q(price__lte=float(max_price)))
    except ValueError:
        pass

    results = []

    for item in Item.objects.filter(*clauses).all():
        item_dict = item.as_dict()
        item_dict['vendor'] = item.vendor.as_dict()
        results.append(item_dict)

    return results


@ajax_func('^item/edit$', method='POST', overseer=True, atomic=True)
def item_edit(request, code, price, state):
    try:
        price = ItemPriceField().clean(price)
    except ValidationError as v:
        raise AjaxError(RET_BAD_REQUEST, ' '.join(v.messages))

    if state not in {st for (st, _) in Item.STATE}:
        raise AjaxError(RET_BAD_REQUEST, 'Unknown state: {0}'.format(state))

    item = _get_item_or_404(code)

    if price != item.price:
        price_editable_states = {
            Item.ADVERTISED,
            Item.BROUGHT,
        }
        if (item.state not in price_editable_states and
                state not in price_editable_states):
            raise AjaxError(
                RET_BAD_REQUEST,
                'Cannot change price in state "{0}"'.format(item.get_state_display())
            )

    if item.state != state:
        unsold_states = {
            Item.ADVERTISED,
            Item.BROUGHT,
            Item.MISSING,
            Item.RETURNED,
        }
        # Removing already sold item from receipt.
        if item.state not in unsold_states and item.state != Item.STAGED and state in unsold_states:
            # Need to remove item from receipt.
            receipt_ids = ReceiptItem.objects.filter(
                action=ReceiptItem.ADD,
                item=item,
            ).values_list('receipt_id', flat=True)

            for receipt_id in receipt_ids:
                remove_form = ItemRemoveForm({
                    'receipt': receipt_id,
                    'item': item.code,
                })
                assert remove_form.is_valid()
                remove_form.save(request)
        else:
            raise AjaxError(
                RET_BAD_REQUEST,
                u'Cannot change state from "{0}" to "{1}".'.format(
                    item.get_state_display(), text_type(dict(Item.STATE)[state])
                )
            )

    item.state = state
    item.price = price
    item.save()

    item_dict = item.as_dict()
    item_dict['vendor'] = item.vendor.as_dict()
    return item_dict


@ajax_func('^item/list$', method='GET')
def item_list(request, vendor, state=None, include_box_items=False):
    items = Item.objects.filter(vendor__id=vendor)
    if state is not None:
        items = items.filter(state=state)
    if not include_box_items:
        items = items.filter(box__isnull=True)
    return [i.as_dict() for i in items]


@ajax_func('^item/compensable', method='GET', atomic=True)
def compensable_items(request, vendor):
    vendor = int(vendor)
    vendor_items = Item.objects.filter(vendor__id=vendor)

    items_for_compensation = vendor_items.filter(state=Item.SOLD)
    if not items_for_compensation:
        return {"items": []}

    r = dict(items=[i.as_dict() for i in items_for_compensation])

    provision = Provision(vendor_id=vendor)
    if provision.has_provision:
        # DON'T SAVE THESE OBJECTS!
        provision_obj = ReceiptExtraRow(
            type=ReceiptExtraRow.TYPE_PROVISION,
            value=provision.provision,
        )
        r["extras"] = [provision_obj.as_dict()]

        if not provision.provision_fix.is_zero():
            print(provision.provision_fix, provision.provision_fix.is_zero())

            provision_fixup_obj = ReceiptExtraRow(
                type=ReceiptExtraRow.TYPE_PROVISION_FIX,
                value=provision.provision_fix,
            )
            r["extras"].append(provision_fixup_obj.as_dict())

    return r


@ajax_func('^box/list$', method='GET')
def box_list(request, vendor):
    out_boxes = []
    boxes = Box.objects.filter(item__vendor__id=vendor, item__hidden=False).distinct()
    for box in boxes:
        data = box.as_dict()
        items = box.get_items()
        data["items_brought_total"] = items.filter(state__in=(Item.BROUGHT, Item.STAGED, Item.SOLD, Item.RETURNED))\
            .count()
        data["items_sold"] = items.filter(state=Item.SOLD).count()
        data["items_returnable"] = items.filter(state__in=(Item.BROUGHT, Item.STAGED)).count()
        out_boxes.append(data)
    return out_boxes


@ajax_func('^item/checkin$', atomic=True)
def item_checkin(request, code):
    item = _get_item_or_404(code)
    if not item.vendor.terms_accepted:
        raise AjaxError(500, _(u"Vendor has not accepted terms!"))

    if item.state != Item.ADVERTISED:
        _item_state_conflict(item)

    if item.box is not None:
        # Client did not expect box, but this is a box.
        # Assign box number and return box information to client.
        # Expecting a retry to box_checkin.
        box = item.box
        box.assign_box_number()

        response = item.as_dict()
        response["box"] = box.as_dict()

        # TODO: Consider returning bad request to clearly separate actual success.
        return JsonResponse(response, status=RET_ACCEPTED, reason="OTHER API")

    return item_mode_change(request, code, Item.ADVERTISED, Item.BROUGHT)


@ajax_func('^item/checkout$', atomic=True)
def item_checkout(request, code):
    item = _get_item_or_404(code)
    box = item.box
    if box:
        items = box.get_items().select_for_update().filter(state=Item.BROUGHT)

        ItemStateLog.objects.log_states(item_set=items, new_state=Item.RETURNED, request=request)
        items.update(state=Item.RETURNED)
        ret = {
            "box": box.as_dict(),
            "changed": items.count(),
            "code": box.representative_item.code,
        }
        return ret
    else:
        return item_mode_change(request, code, (Item.BROUGHT, Item.ADVERTISED), Item.RETURNED,
                                _(u"Item was not brought to event."))


@ajax_func('^item/compensate/start$')
def item_compensate_start(request, vendor):
    if "compensation" in request.session:
        raise AjaxError(RET_CONFLICT, _(u"Already compensating"))

    vendor_id = int(vendor)
    if not Vendor.objects.filter(pk=vendor_id).exists():
        raise AjaxError(RET_BAD_REQUEST)

    clerk = Clerk.objects.get(pk=request.session["clerk"])
    counter = Counter.objects.get(pk=request.session["counter"])

    receipt = Receipt()
    receipt.clerk = clerk
    receipt.counter = counter
    receipt.type = Receipt.TYPE_COMPENSATION
    receipt.save()

    request.session["compensation"] = (receipt.pk, vendor_id)

    return receipt.as_dict()


@ajax_func('^item/compensate$', atomic=True)
def item_compensate(request, code):
    if "compensation" not in request.session:
        raise AjaxError(RET_CONFLICT, _(u"No compensation started!"))
    receipt_pk, vendor_id = request.session["compensation"]
    receipt = Receipt.objects.get(pk=receipt_pk, type=Receipt.TYPE_COMPENSATION)

    item = _get_item_or_404(code, vendor=vendor_id)
    item_dict = item_mode_change(request, code, Item.SOLD, Item.COMPENSATED)

    ReceiptItem.objects.create(item=item, receipt=receipt)
    receipt.calculate_total()
    receipt.save()

    return item_dict


@ajax_func('^item/compensate/end', atomic=True)
def item_compensate_end(request):
    if "compensation" not in request.session:
        raise AjaxError(RET_CONFLICT, _(u"No compensation started!"))

    receipt_pk, vendor_id = request.session["compensation"]
    receipt = Receipt.objects.get(pk=receipt_pk, type=Receipt.TYPE_COMPENSATION)

    provision = Provision(vendor_id=vendor_id, receipt=receipt)
    if provision.has_provision:
        ReceiptExtraRow.objects.create(
            type=ReceiptExtraRow.TYPE_PROVISION,
            value=provision.provision,
            receipt=receipt,
        )

        if not provision.provision_fix.is_zero():
            ReceiptExtraRow.objects.create(
                type=ReceiptExtraRow.TYPE_PROVISION_FIX,
                value=provision.provision_fix,
                receipt=receipt,
            )

    receipt.status = Receipt.FINISHED
    receipt.end_time = now()
    receipt.calculate_total()
    receipt.save()

    del request.session["compensation"]

    return receipt.as_dict()


@ajax_func('^vendor/get$', method='GET')
def vendor_get(request, id):
    try:
        vendor = Vendor.objects.get(pk=int(id))
    except (ValueError, Vendor.DoesNotExist):
        raise AjaxError(RET_BAD_REQUEST, _(u"Invalid vendor id"))
    else:
        return vendor.as_dict()


@ajax_func('^vendor/find$', method='GET')
def vendor_find(request, q):
    clauses = [Q(vendor__isnull=False)]

    for part in q.split():
        clause = (
              Q(**UserAdapter.phone_query(part))
            | Q(username__icontains=part)
            | Q(first_name__icontains=part)
            | Q(last_name__icontains=part)
            | Q(email__icontains=part)
        )
        try:
            clause = clause | Q(vendor__id=int(part))
        except ValueError:
            pass

        clauses.append(clause)

    return [
        u.vendor.as_dict()
        for u in get_user_model().objects.filter(*clauses).all()
    ]


@ajax_func('^receipt/start$', atomic=True)
def receipt_start(request):
    if "receipt" in request.session:
        raise AjaxError(RET_CONFLICT, "There is already an active receipt on this counter!")

    clerk = get_clerk(request)
    if Receipt.objects.filter(clerk=clerk, status=Receipt.PENDING, type=Receipt.TYPE_PURCHASE).count() > 0:
        raise AjaxError(RET_CONFLICT, "There is already an active receipt!")

    receipt = Receipt()
    receipt.clerk = clerk
    receipt.counter = get_counter(request)
    receipt.type = Receipt.TYPE_PURCHASE

    receipt.save()

    request.session["receipt"] = receipt.pk
    return receipt.as_dict()


@ajax_func('^item/reserve$', atomic=True)
def item_reserve(request, code):
    item = _get_item_or_404(code)
    receipt_id = request.session["receipt"]
    receipt = receipt = get_receipt(receipt_id)

    message = raise_if_item_not_available(item)
    if item.state in (Item.ADVERTISED, Item.BROUGHT, Item.MISSING):
        ItemStateLog.objects.log_state(item, Item.STAGED, request=request)
        item.state = Item.STAGED
        item.save()

        ReceiptItem.objects.create(item=item, receipt=receipt)
        # receipt.items.create(item=item)
        receipt.calculate_total()
        receipt.save()

        ret = item.as_dict()
        ret.update(total=receipt.total_cents)
        if message is not None:
            ret.update(_message=message)
        return ret
    else:
        # Not in expected state.
        raise AjaxError(RET_CONFLICT)


@ajax_func('^item/release$', atomic=True)
def item_release(request, code):
    item = _get_item_or_404(code)
    receipt_id = request.session["receipt"]
    remove_form = ItemRemoveForm({
        'receipt': receipt_id,
        'item': code,
    })
    if not remove_form.is_valid():
        raise AjaxError(RET_CONFLICT, ", ".join(remove_form.errors))

    remove_form.save(request)
    return remove_form.removal_entry.as_dict()


def _get_active_receipt(request, id, allowed_states=(Receipt.PENDING,)):
    arg_id = int(id)
    in_session = "receipt" in request.session
    if in_session:
        receipt_id = request.session["receipt"]
        if receipt_id != arg_id:
            msg = "Receipt id conflict: {} != {}".format(receipt_id, arg_id)
            logger.error(msg)
            raise AjaxError(RET_CONFLICT, msg)
    else:
        receipt_id = arg_id
        logger.warning("Active receipt is being read without it being in session: %i", receipt_id)

    receipt = receipt = get_receipt(receipt_id)
    if receipt.status not in allowed_states:
        if not in_session and receipt.status == Receipt.FINISHED:
            raise AjaxError(RET_CONFLICT, "Receipt {} was already ended at {}".format(receipt_id, receipt.end_time))
        raise AjaxError(RET_CONFLICT, "Receipt {} is in unexpected state: {}".format(
            receipt_id, receipt.get_status_display()))
    return receipt, receipt_id


@ajax_func('^receipt/finish$', atomic=True)
def receipt_finish(request, id):
    receipt, receipt_id = _get_active_receipt(request, id)

    receipt.end_time = now()
    receipt.status = Receipt.FINISHED
    receipt.save()

    receipt_items = Item.objects.filter(receipt=receipt, receiptitem__action=ReceiptItem.ADD)
    for item in receipt_items:
        ItemStateLog.objects.log_state(item=item, new_state=Item.SOLD, request=request)
    receipt_items.update(state=Item.SOLD)

    del request.session["receipt"]
    return receipt.as_dict()


@ajax_func('^receipt/abort$', atomic=True)
def receipt_abort(request, id):
    receipt, receipt_id = _get_active_receipt(request, id, (Receipt.PENDING, Receipt.SUSPENDED))

    # For all ADDed items, add REMOVE-entries and return the real Item's back to available.
    added_items = ReceiptItem.objects.filter(receipt_id=receipt_id, action=ReceiptItem.ADD)
    for receipt_item in added_items.only("item"):
        item = receipt_item.item

        ReceiptItem(item=item, receipt=receipt, action=ReceiptItem.REMOVE).save()

        if item.state != Item.BROUGHT:
            ItemStateLog.objects.log_state(item=item, new_state=Item.BROUGHT, request=request)
            item.state = Item.BROUGHT
            item.save()

    # Update ADDed items to be REMOVED_LATER. This must be done after the real Items have
    # been updated, and the REMOVE-entries added, as this will change the result set of
    # the original added_items -query (to always return zero entries).
    added_items.update(action=ReceiptItem.REMOVED_LATER)

    # End the receipt. (Must be done after previous updates, so calculate_total calculates
    # correct sum.)
    receipt.end_time = now()
    receipt.status = Receipt.ABORTED
    receipt.calculate_total()
    receipt.save()

    del request.session["receipt"]
    return receipt.as_dict()


def _get_receipt_data_with_items(**kwargs):
    kwargs.setdefault("type", Receipt.TYPE_PURCHASE)
    receipt = get_object_or_404(Receipt, **kwargs)

    data = receipt.as_dict()
    data["items"] = receipt.row_list()
    return data


@ajax_func('^receipt$', method='GET')
def receipt_get(request):
    """
    Find receipt by receipt id or one item in the receipt.
    """
    if "id" in request.GET:
        receipt_id = int(request.GET.get("id"))
        query = {"pk": receipt_id}
        if request.GET.get("type") == "compensation":
            query["type"] = Receipt.TYPE_COMPENSATION
    elif "item" in request.GET:
        item_code = request.GET.get("item")
        query = {
            "receiptitem__item__code": item_code,
            "receiptitem__action": ReceiptItem.ADD,
            "status": Receipt.FINISHED,
        }
    else:
        raise AjaxError(RET_BAD_REQUEST)
    return _get_receipt_data_with_items(**query)


@ajax_func('^receipt/activate$')
def receipt_activate(request):
    """
    Activate previously started pending receipt.
    """
    clerk = request.session["clerk"]
    receipt_id = int(request.POST.get("id"))
    data = _get_receipt_data_with_items(pk=receipt_id, clerk__id=clerk, status=Receipt.PENDING,
                                        type=Receipt.TYPE_PURCHASE)
    request.session["receipt"] = receipt_id
    return data


@ajax_func('^receipt/pending', overseer=True)
def receipt_pending(request):
    receipts = Receipt.objects.filter(status__in=(Receipt.PENDING, Receipt.SUSPENDED), type=Receipt.TYPE_PURCHASE)
    return list(map(lambda i: i.as_dict(), receipts))


@ajax_func('^receipt/compensated', method='GET')
def receipt_compensated(request, vendor):
    receipts = Receipt.objects.filter(
        type=Receipt.TYPE_COMPENSATION,
        receiptitem__item__vendor_id=int(vendor),
    ).distinct().order_by("start_time")

    return [receipt.as_dict() for receipt in receipts]


@ajax_func('^barcode$', counter=False, clerk=False, staff_override=True)
def get_barcodes(request, codes=None):
    """
    Get barcode images for a code, or list of codes.

    :param codes: Either list of codes, or a string, encoded in Json string.
    :type codes: str
    :return: List of barcode images encoded in data-url.
    :rtype: list[str]
    """
    from .templatetags.kirppu_tags import barcode_dataurl
    from json import loads

    codes = loads(codes)
    if isinstance(codes, string_types):
        codes = [codes]

    # XXX: This does ignore the width assertion. Beware with style sheets...
    outs = [
        barcode_dataurl(code, "png", None)
        for code in codes
    ]
    return outs


@ajax_func('^item/abandon$')
def items_abandon(request, vendor):
    """
    Set all of the vendor's 'brought to event' and 'missing' items to abandoned
    The view is expected to refresh itself
    """
    Item.objects.filter(
        vendor__id=vendor,
        state__in=(Item.BROUGHT, Item.MISSING),
    ).update(abandoned=True)
    return


@ajax_func('^item/mark_lost$', overseer=True, atomic=True)
def item_mark_lost(request, code):
    item = get_object_or_404(Item, code=code)
    if item.state == Item.SOLD:
        raise AjaxError(RET_CONFLICT, u"Item is sold!")
    if item.state == Item.STAGED:
        raise AjaxError(RET_CONFLICT, u"Item is staged to be sold!")
    if item.abandoned:
        raise AjaxError(RET_CONFLICT, u"Item is abandoned.")

    item.lost_property = True
    item.save()
    return item.as_dict()


def iterate_logs(entries, hide_advertised=False, hide_sales=False, show_prices=False):
    """ Iterate through ItemStateLog objects returning current sum of each type of object at each timestamp.

    Example of returned CVS: js_time, advertized, brought, unsold, money, compensated

    js_time is milliseconds from unix_epoch.
    advertized is the number of items registered to the event at any time.
    brought is the cumulative sum of all items brought to the event.
    unsold is the number of items physically at the event. Should aproach zero by the end of the event.
    money is the number of sold items not yet redeemed by the seller. Should aproach zero by the end of the event.
    compensated is the number of sold and unsold items redeemed by the seller. Should aproach brought.

    :param entries: iterator to ItemStateLog objects.
    :return: JSON presentation of the objects, one item at a time.

    """
    from datetime import datetime, timedelta
    import pytz

    advertised_status = (Item.ADVERTISED,)
    brought_status = (Item.BROUGHT, Item.STAGED, Item.SOLD, Item.MISSING, Item.RETURNED, Item.COMPENSATED)
    unsold_status = (Item.BROUGHT, Item.STAGED)
    money_status = (Item.SOLD,)
    compensated_status = (Item.COMPENSATED, Item.RETURNED)
    unix_epoch = datetime(1970, 1, 1, tzinfo=pytz.utc)

    def datetime_to_js_time(dt):
        return int((dt - unix_epoch).total_seconds() * 1000)

    def get_log_str(bucket_time, balance):
        entry_time = datetime_to_js_time(bucket_time)
        advertised = sum(balance[status] for status in advertised_status)
        brought = sum(balance[status] for status in brought_status)
        unsold = sum(balance[status] for status in unsold_status)
        money = sum(balance[status] for status in money_status)
        compensated = sum(balance[status] for status in compensated_status)
        return '%d,%s,%s,%s,%s,%s\n' % (
            entry_time,
            advertised if not hide_advertised else '',
            brought if not hide_sales else '',
            unsold if not hide_sales else '',
            money if not hide_sales else '',
            compensated if not hide_sales else '',
        )

    # Collect the data into buckets of size bucket_td to reduce the amount of data that has to be sent
    # and parsed at client side.
    balance = { item_type: 0 for item_type, _item_desc in Item.STATE }
    bucket_time = None
    bucket_td = timedelta(seconds=60)

    # Modify the query to include item price, because we need it.
    only = "old_state", "new_state", "time"
    if show_prices:
        entries = entries.only("item__price", *only).annotate(price=F("item__price"))
    else:
        entries = entries.only(*only)

    for entry in entries.order_by("time"):
        if bucket_time is None:
            bucket_time = entry.time
            # Start the graph before the first entry, such that everything starts at zero.
            yield get_log_str(bucket_time - bucket_td, balance)
        if (entry.time - bucket_time) > bucket_td:
            # Fart out what was in the old bucket and start a new bucket.
            yield get_log_str(bucket_time, balance)
            bucket_time = entry.time

        item_weight = 1
        if show_prices:
            item_weight = entry.price

        if entry.old_state:
            balance[entry.old_state] -= item_weight
        balance[entry.new_state] += item_weight

    # Fart out the last bucket.
    if bucket_time is not None:
        yield get_log_str(bucket_time, balance)


@ajax_func('^stats/get_sales_data$', method='GET', staff_override=True)
def stats_sales_data(request):
    entries = ItemStateLog.objects.exclude(new_state=Item.ADVERTISED)
    log_generator = iterate_logs(entries, hide_advertised=True)
    return StreamingHttpResponse(log_generator, content_type='text/csv')


@ajax_func('^stats/get_registration_data$', method='GET', staff_override=True)
def stats_registration_data(request):
    entries = ItemStateLog.objects.filter(new_state=Item.ADVERTISED)
    log_generator = iterate_logs(entries, hide_sales=True)
    return StreamingHttpResponse(log_generator, content_type='text/csv')


@ajax_func('^stats/get_sales_data_prices$', method='GET', staff_override=True)
def stats_sales_data_prices(request):
    entries = ItemStateLog.objects.exclude(new_state=Item.ADVERTISED)
    log_generator = iterate_logs(entries, hide_advertised=True, show_prices=True)
    return StreamingHttpResponse(log_generator, content_type='text/csv')


@ajax_func('^stats/get_registration_data_prices$', method='GET', staff_override=True)
def stats_registration_data_prices(request):
    entries = ItemStateLog.objects.filter(new_state=Item.ADVERTISED)
    log_generator = iterate_logs(entries, hide_sales=True, show_prices=True)
    return StreamingHttpResponse(log_generator, content_type='text/csv')
