# -*- coding: utf-8 -*-
from django.http import Http404
from django.utils.translation import ugettext as _

from ..ajax_util import AjaxError, RET_CONFLICT
from ..models import Item

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


def item_state_conflict(item):
    raise AjaxError(
        RET_CONFLICT,
        _(u"Unexpected item state: {state_name} ({state})").format(
            state=item.state,
            state_name=item.get_state_display()
        ),
    )
