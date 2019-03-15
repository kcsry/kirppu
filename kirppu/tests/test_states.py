# -*- coding: utf-8 -*-

from http import HTTPStatus

from django.test import Client, TestCase

from .factories import *
from .api_access import Api
from . import ResultMixin

__author__ = 'codez'


class PublicTest(TestCase, ResultMixin):
    def setUp(self):
        self.client = Client()
        self.vendor = VendorFactory()
        self.type = ItemTypeFactory()

        user = self.vendor.user

        if not self.client.login(username=user.username, password=UserFactory.DEFAULT_PASSWORD):
            raise RuntimeError("Could not log in.")

    def test_register_item(self):
        data = dict(
            name=factory.Faker("sentence", nb_words=3).generate({}),
            price="1.25",
            tag_type="short",
            suffixes="",
            item_type=self.type.key,
            adult=False,
        )
        result = self.assertSuccess(self.client.post("/kirppu/vendor/item/", data=data)).json()
        self.assertEqual(1, len(result))
        r_item = result[0]
        self.assertEquals(self.vendor.id, r_item["vendor_id"])

    def test_register_box(self):
        data = dict(
            description=factory.Faker("sentence", nb_words=3).generate({}),
            price="1.25",
            item_type=self.type.key,
            adult=False,
            count=4,
            bundle_size=1,
        )
        # Returns actually an html-page.. Test within context.
        result = self.assertSuccess(self.client.post("/kirppu/vendor/box/", data=data))
        self.assertEquals(data["description"], result.context["description"])

    def test_register_box_with_single_item(self):
        data = dict(
            description=factory.Faker("sentence", nb_words=3).generate({}),
            price="1.25",
            item_type=self.type.key,
            adult=False,
            count=1,
            bundle_size=1,
        )
        # Returns actually an html-page.. Test within context.
        result = self.assertSuccess(self.client.post("/kirppu/vendor/box/", data=data))
        self.assertEquals(data["description"], result.context["description"])

    def test_register_single_bundle_box(self):
        data = dict(
            description=factory.Faker("sentence", nb_words=3).generate({}),
            price="1.25",
            item_type=self.type.key,
            adult=False,
            count=1,
            bundle_size=2,
        )
        # Returns actually an html-page.. Test within context.
        result = self.assertSuccess(self.client.post("/kirppu/vendor/box/", data=data))
        self.assertEquals(data["description"], result.context["description"])


class StatesTest(TestCase, ResultMixin):
    def setUp(self):

        self.client = Client()

        self.vendor = VendorFactory()
        self.items = ItemFactory.create_batch(10, vendor=self.vendor)

        self.counter = CounterFactory()
        self.clerk = ClerkFactory()

        self.api = Api(client=self.client)
        self.api.clerk_login(code=self.clerk.get_code(), counter=self.counter.identifier)

    def test_fail_reserve_without_receipt(self):
        ret = self.api.item_reserve(code=self.items[0].code)
        self.assertEqual(ret.status_code, HTTPStatus.BAD_REQUEST.value)

    def test_normal_item_receipt(self):
        item_code = self.items[0].code

        receipt = self.assertSuccess(self.api.receipt_start()).json()

        self.assertSuccess(self.api.item_reserve(code=item_code))

        db_item = Item.objects.get(code=item_code)
        self.assertEqual(Item.STAGED, db_item.state)

        finished_receipt = self.assertSuccess(self.api.receipt_finish(id=receipt["id"])).json()

        db_item = Item.objects.get(code=item_code)
        self.assertEqual(Item.SOLD, db_item.state)
        self.assertEqual(finished_receipt["status"], Receipt.FINISHED)

    def test_double_reservation(self):
        # Note: This tests only two subsequent requests.
        # Two simultaneous requests cannot be tested here as basic tests require sequential request/database access.
        item_code = self.items[0].code

        receipt = self.assertSuccess(self.api.receipt_start()).json()
        self.assertSuccess(self.api.item_reserve(code=item_code))

        expected_failure = self.api.item_reserve(code=item_code)
        self.assertEqual(HTTPStatus.LOCKED.value, expected_failure.status_code)

    def test_normal_box_receipt(self):
        box = BoxFactory(adopt=True, items=self.items)
        box_checkin = self.assertResult(self.api.item_checkin(code=box.representative_item.code),
                                        expect=HTTPStatus.ACCEPTED.value).json()
        self.assertSuccess(self.api.box_checkin(code=box.representative_item.code,
                                                box_info=box_checkin["box"]["box_number"]))

        receipt = self.assertSuccess(self.api.receipt_start()).json()
        reserve_count = 3

        self.assertSuccess(self.api.box_item_reserve(box_number=box.box_number, box_item_count=reserve_count))
        self.assertEqual(reserve_count, Item.objects.filter(box=box, state=Item.STAGED).count())

        finished_receipt = self.assertSuccess(self.api.receipt_finish(id=receipt["id"])).json()

        self.assertEqual(finished_receipt["status"], Receipt.FINISHED)

    def test_box_over_reserve(self):
        reserve_count = 3

        box = BoxFactory(vendor=VendorFactory(), item_count=reserve_count - 1)
        box_checkin = self.assertResult(self.api.item_checkin(code=box.representative_item.code),
                                        expect=HTTPStatus.ACCEPTED.value).json()
        self.assertSuccess(self.api.box_checkin(code=box.representative_item.code,
                                                box_info=box_checkin["box"]["box_number"]))

        receipt = self.assertSuccess(self.api.receipt_start()).json()

        self.assertResult(self.api.box_item_reserve(box_number=box.box_number, box_item_count=reserve_count),
                          expect=HTTPStatus.CONFLICT)
