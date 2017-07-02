# -*- coding: utf-8 -*-
from collections import OrderedDict
from django.conf import settings
from django.db import models

from .models import Item

__author__ = 'codez'

__all__ = (
    "ItemCountData",
    "ItemEurosData",
)


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
            for key, _ in Item.ITEMTYPE
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
        # Return a result list that contains prices for all states, sum and the value for group_by per list item.
        return query.annotate(
            sum=models.Sum("price"),
            **states
        )

    def data_set(self, key, name):
        return ItemEurosRow(self._data[key], name)


class ItemEurosRow(ItemCollectionRow):
    def __init__(self, *args, **kwargs):
        super(ItemEurosRow, self).__init__(*args, **kwargs)
        self._currency = settings.KIRPPU_CURRENCY["html"]

    def fmt(self, value):
        value = "{}{}{}".format(self._currency[0], value or 0, self._currency[1])
        return value
