# -*- coding: utf-8 -*-
from django.http import Http404
from django.utils.translation import ugettext as _

from ..ajax_util import AjaxError, RET_BAD_REQUEST, RET_CONFLICT
from ..models import Box, Item, Receipt

__author__ = 'codez'


def get_item_or_404(code, **kwargs):
    """
    :param code: Item barcode to find.
    :type code: str
    :param kwargs: Extra query filters.
    :rtype: Item
    :raises Http404: If an Item matching the query does not exist.
    """
    try:
        item = Item.get_item_by_barcode(code, **kwargs)
    except Item.DoesNotExist:
        item = None

    if item is None:
        raise Http404(_(u"No item found matching '{0}'").format(code))
    return item


def get_box_or_404(box_number, **kwargs):
    """
    :param box_number: Number of the box to find.
    :type box_number: int|str
    :param kwargs: Extra query filters.
    :rtype: Box
    :raises Http404: If a Box matching the query does not exist.
    :raises AjaxError: If `box_number` is not a valid number.
    """
    number = None
    try:
        number = int(box_number)
        box = Box.objects.get(box_number=box_number, **kwargs)
        return box
    except ValueError as e:
        raise AjaxError(RET_BAD_REQUEST, "box_number must be a number")
    except Box.DoesNotExist as e:
        raise Http404(_("Box #{} does not exist.").format(number))


def item_state_conflict(item):
    raise AjaxError(
        RET_CONFLICT,
        _(u"Unexpected item state: {state_name} ({state})").format(
            state=item.state,
            state_name=item.get_state_display()
        ),
    )


def get_receipt(receipt_id):
    try:
        return Receipt.objects.get(pk=receipt_id, type=Receipt.TYPE_PURCHASE)
    except Receipt.DoesNotExist:
        raise AjaxError(500, "Receipt {} does not exist.".format(receipt_id))
