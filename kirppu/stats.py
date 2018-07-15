# -*- coding: utf-8 -*-
from collections import OrderedDict
from django.conf import settings
from django.db import models
from django.db.models import F

from .models import Item, ItemType

__author__ = 'codez'

__all__ = (
    "ItemCountData",
    "ItemEurosData",
    "iterate_logs",
)


# region Terse statistics generators.


class ItemCollectionData(object):
    """
    Collection of data for statistics, item states per item type or vendor.
    The sole argument to constructor decides which data set is represented on rows.
    A row can be retrieved with `data_set` function, which gives an instance of
    `ItemCollectionRow` used to iterate over the row.

    The query that is run will yield two-dimensional result (actually with all states, but no empty group_by's):

        [
        {'staged': 1, 'sum': 5, 'advertised': 3, 'sold': 1, 'itemtype': 'manga-english'},
        {'staged': 0, 'sum': 2, 'advertised': 0, 'sold': 2, 'itemtype': 'other'},
        ...
        ]
    """

    PROPERTIES = OrderedDict((
        ('advertized', Item.ADVERTISED),
        ('brought', Item.BROUGHT),
        ('staged', Item.STAGED),
        ('sold', Item.SOLD),
        ('missing', Item.MISSING),
        ('returned', Item.RETURNED),
        ('compensated', Item.COMPENSATED),
        ('sum', None),
    ))

    ABANDONED_PROPERTIES = OrderedDict((
        ("brought_abandoned", Item.BROUGHT),
        ("staged_abandoned", Item.STAGED),
        ("sold_abandoned", Item.SOLD),
    ))

    _DEFAULT_VALUES = {
        p: 0
        for p in PROPERTIES.keys()
    }

    GROUP_ITEM_TYPE = "itemtype"
    GROUP_VENDOR = "vendor"

    def __init__(self, group_by):
        self._group_by = group_by
        self._raw_data = self._populate(Item.objects.values(group_by))

        if group_by == self.GROUP_ITEM_TYPE:
            self._init_for_item_type()
        elif group_by == self.GROUP_VENDOR:
            self._init_for_vendor()
        else:
            raise ValueError("Unknown group_by value")

    def _init_for_item_type(self):
        # Make the list data associative by item type.
        # The item type in raw_data is pk of ItemType.
        data = {
            row["itemtype"]: row
            for row in self._raw_data
        }

        # Add sum row. (Sum-column already exists.)
        # For optimization, this is done before filling gaps to avoid unnecessary calculations.
        sums = self._DEFAULT_VALUES.copy()
        for item_type, item_data in data.items():
            for property_key in self.PROPERTIES.keys():
                cell_value = item_data[property_key]
                if cell_value is None:
                    cell_value = 0
                    item_data[property_key] = cell_value
                sums[property_key] += cell_value

        # Fill possible gaps and order correctly.
        self._data = OrderedDict(
            (key, data.get(key, self._DEFAULT_VALUES))
            for key in ItemType.objects.order_by("order").values_list("id", flat=True)
        )

        # Append calculated sum row.
        self._data["sum"] = sums

    def _init_for_vendor(self):
        # Order vendor data by their id.
        self._raw_data = self._raw_data.order_by("vendor_id")

        data = OrderedDict(
            (row["vendor"], row)
            for row in self._raw_data
        )
        self._data = data

    def data_set(self, key, name):
        """
        Return a data set / row from the collection.

        :param key: Data set key, such as item type or vendor id.
        :param name: Name for the data set.
        :return: Row containing the data.
        :rtype: ItemCollectionRow
        """
        raise NotImplementedError()

    def keys(self):
        return self._data.keys()

    def _populate(self, query):
        raise NotImplementedError()

    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__, self._group_by, self._data)


class ItemCollectionRow(object):
    """
    Base class for row data in `ItemCollectionData` mainly used for template to iterate over the row.
    """
    def __init__(self, data, name):
        self.name = name
        self._data = data

    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__, self.name, self._data)

    @property
    def property_values(self):
        for property_name in ItemCollectionData.PROPERTIES:
            yield self.fmt(self._data[property_name])

    @property
    def property_names(self):
        for property_name in ItemCollectionData.PROPERTIES:
            yield property_name

    @property
    def abandoned(self):
        for property_name in ItemCollectionData.ABANDONED_PROPERTIES:
            yield self.fmt(self._data[property_name])

    def fmt(self, value):
        raise NotImplementedError()


class ItemCountData(ItemCollectionData):
    def _populate(self, query):
        # Count items per state. query must be already made group_by with query.values.
        states = {
            key: models.Count(models.Case(models.When(state=p, then=1), output_field=models.IntegerField()))
            for key, p in self.PROPERTIES.items()
            if p is not None
        }
        abandoned = {
            key: models.Count(models.Case(models.When(
                models.Q(state=p) & models.Q(abandoned=True), then=1), output_field=models.IntegerField()))
            for key, p in self.ABANDONED_PROPERTIES.items()
        }
        states.update(abandoned)
        # Return a result list that contains counts for all states, sum and the value for group_by per list item.
        return query.annotate(
            sum=models.Count("id"),
            **states
        )

    def data_set(self, key, name):
        return ItemCountRow(self._data[key], name)


class ItemCountRow(ItemCollectionRow):
    def fmt(self, value):
        return value


class ItemEurosData(ItemCollectionData):
    def __init__(self, *args, **kwargs):
        super(ItemEurosData, self).__init__(*args, **kwargs)
        self.use_cents = False

    def _populate(self, query):
        # Count item prices per state. query must be already made group_by with query.values.
        p_field = Item._meta.get_field("price")
        decimals, digits = p_field.decimal_places, p_field.max_digits
        states = {
            key: models.Sum(models.Case(models.When(state=p, then=models.F("price")),
                                        output_field=models.DecimalField(decimal_places=decimals, max_digits=digits)))
            for key, p in self.PROPERTIES.items()
            if p is not None
        }
        abandoned = {
            key: models.Sum(models.Case(models.When(
                models.Q(state=p) & models.Q(abandoned=True),
                then=models.F("price")), output_field=models.DecimalField(decimal_places=decimals, max_digits=digits)))
            for key, p in self.ABANDONED_PROPERTIES.items()
        }
        states.update(abandoned)
        # Return a result list that contains prices for all states, sum and the value for group_by per list item.
        return query.annotate(
            sum=models.Sum("price"),
            **states
        )

    def data_set(self, key, name):
        return ItemEurosRow(self.use_cents, self._data[key], name)


class ItemEurosRow(ItemCollectionRow):
    def __init__(self, use_cents, *args, **kwargs):
        super(ItemEurosRow, self).__init__(*args, **kwargs)
        self._use_cents = use_cents
        self._currency = settings.KIRPPU_CURRENCY["html"]

    def fmt(self, value):
        if self._use_cents:
            return int((value or 0) * 100)
        value = "{}{}{}".format(self._currency[0], value or 0, self._currency[1])
        return value


# endregion


########################


# region Statistics graphs generators.


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


# endregion
