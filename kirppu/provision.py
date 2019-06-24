# -*- coding: utf-8 -*-
import builtins
from decimal import Decimal
from typing import Optional

import django.db.models
from django.db.models import Sum, Q

from .models import ReceiptExtraRow, Receipt, Item, ReceiptItem

__author__ = 'codez'


class Provision(object):
    def __init__(self, vendor_id, provision_function, receipt=None):
        self._vendor_id = vendor_id

        self._vendor_items = vendor_items = Item.objects.filter(vendor__id=vendor_id)

        # Amount of total provision based on sold (=sold/compensated) items.
        if receipt is None:
            total_compensation_items = vendor_items.filter(state__in=(Item.SOLD, Item.COMPENSATED))
        else:
            # Include already compensated items and items being compensated.
            # Items that are recently sold should not change the compensation WITHIN a receipt.
            query = Q(state=Item.COMPENSATED) | Q(receiptitem__receipt=receipt)
            total_compensation_items = vendor_items.filter(query).distinct()

        self._total_compensation_items = total_compensation_items
        self._receipt = receipt

        self._sub_total = None
        self._provision_result = None
        self._provision_fix_result = None

        self._provision_function = provision_function

        if not total_compensation_items:
            self._provision = None
        else:
            self._provision = self.run_function(
                self._provision_function,
                total_compensation_items
            )

            if self._provision is not None:
                if receipt is None:
                    self._sum_for_compensation = \
                        vendor_items.filter(state=Item.SOLD).aggregate(sum=Sum("price"))["sum"]
                else:
                    self._sum_for_compensation = \
                        ReceiptItem.objects.filter(receipt=receipt, action=ReceiptItem.ADD) \
                                           .aggregate(sum=Sum("item__price"))["sum"]
                if self._sum_for_compensation is None:
                    self._sum_for_compensation = Decimal(0)

    @property
    def has_provision(self):
        return self._provision is not None

    MODELS_FNS = (
        'F', 'Q',
        'Avg', 'Count', 'Max', 'Min', 'Sum',
    )

    @classmethod
    def run_function(cls, provision_function, sold_and_compensated) -> Optional[Decimal]:
        if provision_function is None or provision_function == "":
            return None

        builtins_copy = {k: getattr(builtins, k) for k in dir(builtins) if k not in (
            "eval", "exec", "open", "__import__"
        )}
        env = {
            "__builtins__": builtins_copy,
            "Decimal": Decimal,
            "sold_and_compensated": sold_and_compensated,
        }
        env.update({k: getattr(django.db.models, k) for k in cls.MODELS_FNS})

        _r = None

        def result(r):
            nonlocal _r
            _r = r

        env["result"] = result
        exec(provision_function, env, env)
        assert _r is None or isinstance(_r, Decimal), "Value given to result() must be None or a Decimal instance"
        return _r

    def _calculate_provision_information(self):
        """

        :return: Provision value for current items and provision fix for total.
        :rtype: (ReceiptExtraRow, ReceiptExtraRow)
        """
        extras = ReceiptExtraRow.objects.filter(
            type=ReceiptExtraRow.TYPE_PROVISION,
            receipt__type=Receipt.TYPE_COMPENSATION,
            receipt__receiptitem__item__vendor_id=self._vendor_id,
        ).distinct()
        extras = extras.aggregate(extras_value=Sum("value"))
        previous_provisions = extras["extras_value"] or Decimal(0)

        provision_now = -min(self._provision + previous_provisions, self._sum_for_compensation)
        previous_items = self._vendor_items.filter(state=Item.COMPENSATED)
        if self._receipt:
            # Due no state for staged for compensation, exclude current receipt from fix calculations.
            previous_items = previous_items.exclude(receipt=self._receipt)
        old_target_provision = self.run_function(self._provision_function, previous_items)
        provision_fixup_value = -(old_target_provision + previous_provisions)

        assert provision_now <= provision_fixup_value, str(provision_now) + " " + str(provision_fixup_value)
        self._provision_result = (provision_now - provision_fixup_value).quantize(Decimal(".01"))
        self._provision_fix_result = provision_fixup_value.quantize(Decimal(".01"))

    @property
    def sub_total(self):
        if self._sub_total is None:
            self._sub_total = self._vendor_items.aggregate(sum=Sum("price"))["sum"]
        return self._sub_total

    @property
    def provision(self):
        if self._provision_result is None and self.has_provision:
            self._calculate_provision_information()
        return self._provision_result

    @property
    def provision_fix(self):
        if self._provision_fix_result is None and self.has_provision:
            self._calculate_provision_information()
        return self._provision_fix_result
