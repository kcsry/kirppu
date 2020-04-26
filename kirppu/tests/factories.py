# -*- coding: utf-8 -*-
from datetime import timedelta
from decimal import Decimal
import re

from django.utils.timezone import now
from kirppuauth.models import User
from kirppu.models import (
    Box,
    Clerk,
    Counter,
    Event,
    EventPermission,
    Item,
    ItemType,
    Person,
    Receipt,
    ReceiptItem,
    Vendor,
)

import factory.django

Factory = factory.django.DjangoModelFactory

__author__ = 'codez'


class UserFactory(Factory):
    class Meta:
        model = User

    username = factory.LazyAttribute(lambda a: "{}{}".format(a.last_name, a.first_name).lower())
    phone = factory.Faker("phone_number")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        obj = model_class(*args, **kwargs)
        if not obj.password:
            obj.set_password(cls.DEFAULT_PASSWORD)
        obj.save(force_insert=True, using=manager.db)
        return obj


# Outside of the class to avoid meta-class magic from sending this to _create.
UserFactory.DEFAULT_PASSWORD = "AjU2k3Pzpdpz5yf5sjZn9p56"


class EventFactory(Factory):
    class Meta:
        model = Event

    slug = factory.LazyFunction(lambda: re.sub(r"\W", "", factory.Faker("sentence", nb_words=5).generate({}).lower())[:50])
    name = factory.LazyAttribute(lambda a: a.slug)
    start_date = (now() + timedelta(days=2)).date()
    end_date = (now() + timedelta(days=3)).date()

    registration_end = now() + timedelta(days=1)
    checkout_active = True


class EventPermissionFactory(Factory):
    class Meta:
        model = EventPermission


class VendorFactory(Factory):
    class Meta:
        model = Vendor

    user = factory.SubFactory(UserFactory)
    terms_accepted = factory.LazyFunction(now)
    event = factory.SubFactory(EventFactory)


class CounterFactory(Factory):
    class Meta:
        model = Counter
    event = factory.SubFactory(EventFactory)
    identifier = factory.Sequence(lambda n: "counter_{}".format(n))
    name = factory.LazyAttribute(lambda a: a.identifier.capitalize())


class ClerkFactory(Factory):
    class Meta:
        model = Clerk

    event = factory.SubFactory(EventFactory)
    user = factory.SubFactory(UserFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        obj = manager.create(*args, **kwargs)
        obj.generate_access_key()
        obj.save(update_fields=("access_key",))
        return obj


class ItemTypeFactory(Factory):
    class Meta:
        model = ItemType
    event = factory.SubFactory(EventFactory)
    key = factory.Sequence(lambda n: "type_{}".format(n))
    order = factory.Sequence(lambda n: n)
    title = factory.Faker("sentence", nb_words=2)


class ItemFactory(Factory):
    class Meta:
        model = Item
    vendor = factory.SubFactory(VendorFactory)
    price = Decimal("1.25")
    code = factory.LazyFunction(lambda: Item.gen_barcode())
    name = factory.Faker("sentence", nb_words=2)
    itemtype = factory.SubFactory(ItemTypeFactory)


class PersonFactory(Factory):
    class Meta:
        model = Person
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    phone = factory.Faker("phone_number")


class ReceiptFactory(Factory):
    class Meta:
        model = Receipt

    counter = factory.SubFactory(CounterFactory)
    clerk = factory.SubFactory(ClerkFactory)


class ReceiptItemFactory(Factory):
    class Meta:
        model = ReceiptItem

    item = factory.SubFactory(ItemFactory)
    receipt = factory.SubFactory(ReceiptFactory)


class BoxFactory(Factory):
    class Meta:
        model = Box

    description = factory.Faker("sentence", nb_words=3)
    box_number = factory.Sequence(lambda n: n + 1)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)

        if kwargs.get("adopt", False):
            kwargs.pop("adopt")
            items = kwargs.pop("items")

            kwargs.setdefault("representative_item", items[0])
            obj = manager.create(*args, **kwargs)

            for i in items:
                i.box = obj
                i.save(update_fields=("box",))

            return obj

        vendor = kwargs.pop("vendor")
        item_count = kwargs.pop("item_count")

        representative_item = ItemFactory(vendor=vendor)

        kwargs["representative_item"] = representative_item
        obj = manager.create(*args, **kwargs)

        representative_item.box = obj
        representative_item.save(update_fields=("box",))

        ItemFactory.create_batch(
            item_count - 1,
            vendor=vendor,
            box=obj,
            price=representative_item.price,
            itemtype=representative_item.itemtype
        )

        return obj
