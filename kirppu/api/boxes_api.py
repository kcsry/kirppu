# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _

from .common import (
    get_item_or_404 as _get_item_or_404,
    get_box_or_404 as _get_box_or_404,
    item_state_conflict as _item_state_conflict,
    get_receipt,
)
from ..ajax_util import AjaxError, RET_BAD_REQUEST, RET_CONFLICT
from ..checkout_api import ajax_func
from ..forms import remove_item_from_receipt
from ..models import Item, ItemStateLog, ReceiptItem

__author__ = 'codez'


def _parse_item_count(inp, minimum=1):
    """
    Parse input string as integer.

    :type inp: int|str
    :type minimum: int
    :raises AjaxError: If value is not a valid integer or the value is less than minimum allowed.
    :rtype: int
    """
    try:
        value = int(inp)
        if value < minimum:
            raise AjaxError(RET_BAD_REQUEST, "Value {} less than minimum {}".format(value, minimum))
        return value
    except ValueError as e:
        raise AjaxError(RET_BAD_REQUEST, "Value is not a valid number.")


@ajax_func('^box/find$', method='GET')
def box_find(request, event, box_number, box_item_count="1"):
    box_item_count = _parse_item_count(box_item_count)

    box = _get_box_or_404(box_number, event=event)
    available_count = box.item_set.filter(state=Item.BROUGHT).count()
    if available_count < box_item_count:
        raise AjaxError(RET_CONFLICT, _("Not enough available box items, only {} exist").format(available_count))

    ret = box.as_dict()
    ret.update(available=available_count)
    return ret


@ajax_func('^box/checkin$', atomic=True)
def box_checkin(request, event, code, box_info):
    item = _get_item_or_404(code, event=event)
    if not item.vendor.terms_accepted:
        raise AjaxError(500, _(u"Vendor has not accepted terms!"))

    if item.state != Item.ADVERTISED:
        _item_state_conflict(item)

    box = item.box

    box_number = int(box_info)
    if box_number != box.box_number:
        raise AjaxError(500, _("Unexpected box number conflict"))

    items = box.get_items().select_for_update()
    wrong_count = items.exclude(state=Item.ADVERTISED).count()
    if wrong_count > 0:
        raise AjaxError(RET_CONFLICT,
                        _("Some box items ({}/{}) are in unexpected state.").format(wrong_count, items.count()))

    ItemStateLog.objects.log_states(item_set=items, new_state=Item.BROUGHT, request=request)
    items.update(state=Item.BROUGHT)

    return {
        "box": box.as_dict(),
        "changed": items.count(),
        "code": item.code,
    }


@ajax_func("^box/item/reserve$", atomic=True)
def box_item_reserve(request, event, box_number, box_item_count="1"):
    box_item_count = _parse_item_count(box_item_count)
    box = _get_box_or_404(box_number, event=event)

    receipt_id = request.session.get("receipt")
    if receipt_id is None:
        raise AjaxError(RET_BAD_REQUEST, "No active receipt found")
    receipt = get_receipt(receipt_id, for_update=True)

    # Must force id-list to ensure stability.
    # Otherwise the "list" is considered as a subquery which may not be stable.
    candidates = list(box.item_set.select_for_update()
                      .filter(state=Item.BROUGHT)[:box_item_count].values_list("pk", flat=True))
    if len(candidates) == box_item_count:
        items = Item.objects.filter(pk__in=candidates)
        rows = [
            ReceiptItem(
                item=item,
                receipt=receipt,
            )
            for item in items
        ]

        ItemStateLog.objects.log_states(items, Item.STAGED, request=request)
        items.update(state=Item.STAGED)

        ReceiptItem.objects.bulk_create(rows)
        receipt.calculate_total()
        receipt.save(update_fields=("total",))

        ret = box.as_dict()
        ret.update(
            total=receipt.total_cents,
            changed=box_item_count,
            item_codes=list(items.values_list("code", flat=True)),
            item_name=box.representative_item.name,
        )
        return ret
    else:
        raise AjaxError(RET_CONFLICT,
                        _("Only {} items of {} available for reservation.").format(len(candidates), box_item_count))


@ajax_func('^box/item/release$', atomic=True)
def box_item_release(request, event, box_number, box_item_count="1"):
    box_item_count = _parse_item_count(box_item_count)
    box = _get_box_or_404(box_number, event=event)

    receipt_id = request.session.get("receipt")
    if receipt_id is None:
        raise AjaxError(RET_BAD_REQUEST, "No active receipt found")
    receipt = get_receipt(receipt_id, for_update=True)

    box_items = receipt.items.select_for_update().filter(receiptitem__action=ReceiptItem.ADD, box=box)[:box_item_count]
    if box_items.count() != box_item_count:
        raise AjaxError(RET_CONFLICT,
                        _("Only {} items of {} available for removal.").format(box_items.count(), box_item_count))

    ret = box.as_dict()
    item_codes = list()
    for box_item in box_items:
        removal_entry = remove_item_from_receipt(request, box_item, receipt, update_receipt=False)
        item_codes.append(removal_entry.item.code)
    receipt.calculate_total()
    receipt.save(update_fields=("total",))

    ret.update(
        total=receipt.total_cents,
        changed=box_item_count,
        item_codes=item_codes,
        item_name=box.representative_item.name
    )
    return ret
