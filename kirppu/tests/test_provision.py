# -*- coding: utf-8 -*-
import textwrap

from django.test import Client, override_settings
from django.test import TestCase

from kirppu.provision import Provision

from .factories import *
from .api_access import Api
from . import ResultMixin

__author__ = 'codez'


class ApiOK(Api, ResultMixin):
    def _check_response(self, response):
        self.assertSuccess(response)

    # noinspection PyPep8Naming
    @staticmethod
    def assertEqual(expect, actual, msg=""):
        # used by assertSuccess.
        if expect != actual:
            raise AssertionError(msg or ("%s != %s" % (repr(expect), repr(actual))))


class SoldItemFactory(ItemFactory):
    state = Item.SOLD


@override_settings(KIRPPU_ALLOW_PROVISION_FUNCTIONS=True)
class ProvisionTest(TestCase):
    def setUp(self):
        self.vendor = VendorFactory()

    def test_no_items_no_provision(self):
        p = Provision(self.vendor.id, provision_function=lambda _: None)

        self.assertFalse(p.has_provision)
        self.assertIsNone(p.provision_fix)
        self.assertIsNone(p.provision)

    def test_no_items_with_provision(self):
        p = Provision(self.vendor.id, provision_function=lambda _: Decimal("0.10"))

        self.assertFalse(p.has_provision)
        self.assertIsNone(p.provision_fix)
        self.assertIsNone(p.provision)

    """def test_no_items_with_provision_already_compensated(self):
        some_items = ItemFactory.create_batch(10, vendor=self.vendor, state=Item.COMPENSATED)

        p = Provision(self.vendor.id, provision_function=lambda q: Decimal("0.10") * len(q))

        self.assertTrue(p.has_provision)
        self.assertEqual(p.provision_fix, Decimal("-1.00"))
        self.assertIn(p.provision, (None, Decimal("0.00")))
        # FIXME: Failing. This should be either None/0 or -1, but which?"""


@override_settings(KIRPPU_ALLOW_PROVISION_FUNCTIONS=True)
class BeforeProvisionTest(TestCase):
    def setUp(self):
        self.vendor = VendorFactory()
        self.items = SoldItemFactory.create_batch(10, vendor=self.vendor)

    def test_no_provision_before_compensation(self):
        p = Provision(self.vendor.id, provision_function="result(None)")

        self.assertEqual(len(p._vendor_items), len(self.items))
        self.assertFalse(p.has_provision)
        self.assertIsNone(p.provision)
        self.assertIsNone(p.provision_fix)

    def test_simple_provision_before_compensation(self):
        p = Provision(self.vendor.id, provision_function="""result(Decimal("0.10") * len(sold_and_compensated))""")

        self.assertEqual(len(p._vendor_items), len(self.items))
        self.assertTrue(p.has_provision)
        self.assertEqual(p.provision_fix, Decimal("0.00"))
        self.assertEqual(p.provision, Decimal("-1.00"))  # -(10 * 0.10) == -1

    def test_missing_provision(self):
        some_items = ItemFactory.create_batch(10, vendor=self.vendor, state=Item.COMPENSATED)

        p = Provision(self.vendor.id, provision_function="""result(Decimal("0.10") * len(sold_and_compensated))""")

        self.assertTrue(p.has_provision)
        self.assertEqual(p.provision_fix, Decimal("-1.00"))
        self.assertEqual(p.provision, Decimal("-1.00"))


@override_settings(KIRPPU_ALLOW_PROVISION_FUNCTIONS=True)
class FinishingProvisionTest(TestCase):
    def setUp(self):
        self.vendor = VendorFactory()
        self.receipt = ReceiptFactory(type=Receipt.TYPE_COMPENSATION)
        self.items = ReceiptItemFactory.create_batch(
            10, receipt=self.receipt, item__vendor=self.vendor, item__state=Item.COMPENSATED)

    def test_no_provision_finishing_compensation(self):
        p = Provision(self.vendor.id, receipt=self.receipt,
                      provision_function="""result(None)""")

        self.assertEqual(len(p._vendor_items), len(self.items))
        self.assertFalse(p.has_provision)
        self.assertIsNone(p.provision)
        self.assertIsNone(p.provision_fix)

    def test_simple_provision_finishing_compensation(self):
        p = Provision(self.vendor.id, receipt=self.receipt,
                      provision_function="""result(Decimal("0.10") * len(sold_and_compensated))""")

        self.assertEqual(len(p._vendor_items), len(self.items))
        self.assertTrue(p.has_provision)
        self.assertEqual(p.provision_fix, Decimal("0.00"))
        self.assertEqual(p.provision, Decimal("-1.00"))  # -(10 * 0.10) == -1

    def test_concurrent_sell_finishing_compensation(self):
        more_items = SoldItemFactory.create_batch(10, vendor=self.vendor)

        p = Provision(self.vendor.id, receipt=self.receipt,
                      provision_function="""result(Decimal("0.10") * len(sold_and_compensated))""")

        still_more_items = SoldItemFactory.create_batch(10, vendor=self.vendor)

        self.assertTrue(p.has_provision)
        self.assertEqual(p.provision_fix, Decimal("0.00"))
        self.assertEqual(p.provision, Decimal("-1.00"))  # -(10 * 0.10) == -1


# noinspection PyPep8Naming,PyAttributeOutsideInit
class _ApiMixin(object):
    def _setUp_Event(self):
        self.event = EventFactory()

    def setUp(self):
        self.client = Client()

        self._setUp_Event()

        self.vendor = VendorFactory(event=self.event)
        self.items = SoldItemFactory.create_batch(10, vendor=self.vendor)

        self.counter = CounterFactory(event=self.event)
        self.clerk = ClerkFactory(event=self.event)

        self.apiOK = ApiOK(client=self.client, event=self.event.slug)

        self.apiOK.clerk_login(code=self.clerk.get_code(), counter=self.counter.identifier)

    def tearDown(self):
        self.apiOK.clerk_logout()

    def _compensate(self, items):
        receipt = self.apiOK.item_compensate_start(vendor=self.vendor.id)

        for item in items:
            self.apiOK.item_compensate(code=item.code)

        response = self.apiOK.item_compensate_end()
        receipt = response.json()
        return receipt, response

    def _get_extra(self, extras, extra_type):
        e = [item for item in extras if item["type"] == extra_type]
        self.assertTrue(len(e) <= 1)
        if not e:
            return None
        return e[0]

    def _get_receipt(self, receipt_id):
        # The arguments are actually consumed by the view.
        # noinspection PyArgumentList
        receipt = self.apiOK.receipt_get(id=receipt_id, type="compensation")
        extras = [item for item in receipt.json()["items"] if item["action"] == "EXTRA"]
        return extras


@override_settings(KIRPPU_ALLOW_PROVISION_FUNCTIONS=True)
class ApiNoProvisionTest(_ApiMixin, TestCase):

    # region No Provision
    def test_no_provision_no_items(self):
        receipt, response = self._compensate([])
        self.assertEqual(receipt["total"], 0)

    def test_no_provision_single_go(self):
        receipt, response = self._compensate(self.items)
        self.assertEqual(receipt["total"], 1250)  # 10*1.25 as cents

    def test_no_provision_two_phases(self):
        part_1 = self.items[:6]
        part_2 = self.items[6:]

        receipt_1, response_1 = self._compensate(part_1)
        self.assertEqual(receipt_1["total"], 750)  # 6*1.25 as cents

        receipt_2, response_2 = self._compensate(part_2)
        self.assertEqual(receipt_2["total"], 500)  # 4*1.25 as cents
        # 750 + 500 == 1250
    # endregion


@override_settings(KIRPPU_ALLOW_PROVISION_FUNCTIONS=True)
class ApiLinearProvisionTest(_ApiMixin, TestCase):
    def _setUp_Event(self):
        self.event = EventFactory(
            provision_function="""result(Decimal("0.10") * len(sold_and_compensated))"""
        )

    # region Linear Provision
    def test_linear_provision_no_items(self):
        receipt, response = self._compensate([])
        self.assertEqual(receipt["total"], 0)

    def test_linear_provision_single_go(self):
        guess = self.apiOK.compensable_items(vendor=self.vendor.id)
        provision = self._get_extra(guess.json()["extras"], "PRO")
        self.assertEqual(provision["value"], -100)

        receipt, response = self._compensate(self.items)
        self.assertEqual(receipt["total"], 1150)  # 10*(1.25-0.10) as cents

    def test_linear_provision_two_phases(self):
        part_1 = self.items[:6]
        part_2 = self.items[6:]

        receipt_1, response_1 = self._compensate(part_1)
        self.assertEqual(receipt_1["total"], 690)  # 6*(1.25-0.10) as cents

        receipt_2, response_2 = self._compensate(part_2)
        self.assertEqual(receipt_2["total"], 460)  # 4*(1.25-0.10) as cents
        # 690 + 460 == 1150
    # endregion


@override_settings(KIRPPU_ALLOW_PROVISION_FUNCTIONS=True)
class ApiStepProvisionTest(_ApiMixin, TestCase):
    def _setUp_Event(self):
        self.event = EventFactory(
            provision_function="""result(Decimal("0.50") * (len(sold_and_compensated) // 4))"""
        )

    # region Step Provision
    def test_step_provision_single_go(self):
        guess = self.apiOK.compensable_items(vendor=self.vendor.id)
        provision = self._get_extra(guess.json()["extras"], "PRO")
        self.assertEqual(provision["value"], -100)

        receipt, response = self._compensate(self.items)
        self.assertEqual(receipt["total"], 1150)  # 10*1.25-(10//4)*0.50 as cents

    def test_step_provision_two_phases(self):
        part_1 = self.items[:6]
        part_2 = self.items[6:]

        receipt_1, response_1 = self._compensate(part_1)
        self.assertEqual(receipt_1["total"], 700)  # 6*1.25-0.50 as cents

        receipt_2, response_2 = self._compensate(part_2)
        self.assertEqual(receipt_2["total"], 450)  # 4*1.25-0.50 as cents
        # 700 + 450 == 1150

        # Ensure there is no fixup entry in the item set.
        extras = [item["type"] for item in self._get_receipt(receipt_2["id"])]
        self.assertEqual(len(extras), 1)
        self.assertIn("PRO", extras)
        self.assertNotIn("PRO_FIX", extras)
    # endregion


@override_settings(KIRPPU_ALLOW_PROVISION_FUNCTIONS=True)
class ApiRoundingProvisionTest(_ApiMixin, TestCase):
    def _setUp_Event(self):
        self.event = EventFactory(
            provision_function=textwrap.dedent("""
            def round(value):
                "Round given decimal value to next 50 cents."
                remainder = value % Decimal('.5')
                if remainder > Decimal('0'):
                    value += Decimal('.5') - remainder
                return value

            result(round(Decimal("0.20") * len(sold_and_compensated)))
            """)
        )

    # region Rounding Provision
    def test_rounding_provision_single_go(self):
        guess = self.apiOK.compensable_items(vendor=self.vendor.id).json()["extras"]
        provision = self._get_extra(guess, "PRO")
        self.assertEqual(provision["value"], -200)
        self.assertIsNone(self._get_extra(guess, "PRO_FIX"))

        receipt, response = self._compensate(self.items)
        self.assertEqual(receipt["total"], 1050)  # 10*1.25-10*0.20 as cents

    def test_rounding_provision_two_phases(self):
        part_1 = self.items[:6]
        part_2 = self.items[6:]

        receipt_1, response_1 = self._compensate(part_1)
        self.assertEqual(receipt_1["total"], 600)  # 6*1.25-1.50 as cents

        receipt_2, response_2 = self._compensate(part_2)
        receipt = self._get_receipt(receipt_2["id"])

        self.assertEqual(receipt_2["total"], 450)  # 4*1.25-2*0.50 as cents
        # 600 + 450 == 1050

        receipt = self._get_receipt(receipt_2["id"])
        extras = [item["type"] for item in receipt]
        self.assertEqual(len(extras), 1)
        self.assertIn("PRO", extras)
        self.assertNotIn("PRO_FIX", extras)

    def test_rounding_provision_two_phases_2(self):
        part_1 = self.items[:5]
        part_2 = self.items[5:]

        receipt_1, response_1 = self._compensate(part_1)
        self.assertEqual(receipt_1["total"], 525)  # 5*1.25-1.00 as cents

        receipt_2, response_2 = self._compensate(part_2)
        receipt = self._get_receipt(receipt_2["id"])

        self.assertEqual(receipt_2["total"], 525)  # 5*1.25-2*0.50 as cents

        receipt = self._get_receipt(receipt_2["id"])
        extras = [item["type"] for item in receipt]
        self.assertEqual(len(extras), 1)
        self.assertIn("PRO", extras)
        self.assertNotIn("PRO_FIX", extras)

    def test_rounding_provision_two_phases_3(self):
        part_1 = self.items[:4]
        part_2 = self.items[4:]

        receipt_1, response_1 = self._compensate(part_1)
        self.assertEqual(receipt_1["total"], 400)  # 4*1.25-1.00 as cents

        receipt_2, response_2 = self._compensate(part_2)
        receipt = self._get_receipt(receipt_2["id"])

        self.assertEqual(receipt_2["total"], 650)  # 6*1.25-2*0.50 as cents
        # 400 + 650 == 1050

        receipt = self._get_receipt(receipt_2["id"])
        extras = [item["type"] for item in receipt]
        self.assertEqual(len(extras), 1)
        self.assertIn("PRO", extras)
        self.assertNotIn("PRO_FIX", extras)

    def test_rounding_provision_with_add(self):
        guess = self.apiOK.compensable_items(vendor=self.vendor.id).json()["extras"]
        provision = self._get_extra(guess, "PRO")
        self.assertEqual(provision["value"], -200)
        self.assertIsNone(self._get_extra(guess, "PRO_FIX"))

        receipt_1, response_1 = self._compensate(self.items)
        self.assertEqual(receipt_1["total"], 1050)

        more = SoldItemFactory.create_batch(4, vendor=self.vendor)
        guess = self.apiOK.compensable_items(vendor=self.vendor.id).json()["extras"]
        provision = self._get_extra(guess, "PRO")
        self.assertEqual(provision["value"], -100)
        self.assertIsNone(self._get_extra(guess, "PRO_FIX"))

        receipt_2, response_2 = self._compensate(more)
        receipt = self._get_receipt(receipt_2["id"])

        self.assertEqual(receipt_2["total"], 400)
# [<-needed for ide-region]
    # endregion
