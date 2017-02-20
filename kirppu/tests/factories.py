# -*- coding: utf-8 -*-
from decimal import Decimal

from django.utils.timezone import now
from kirppuauth.models import User
from kirppu.models import Receipt, Item, Vendor, Clerk, Counter, ReceiptItem

import factory
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


class VendorFactory(Factory):
    class Meta:
        model = Vendor

    user = factory.SubFactory(UserFactory)
    terms_accepted = factory.LazyFunction(now)


class CounterFactory(Factory):
    class Meta:
        model = Counter
    identifier = factory.Sequence(lambda n: "counter_{}".format(n))
    name = factory.LazyAttribute(lambda a: a.identifier.capitalize())


class ClerkFactory(Factory):
    class Meta:
        model = Clerk

    user = factory.SubFactory(UserFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        obj = manager.create(*args, **kwargs)
        obj.generate_access_key()
        obj.save(update_fields=("access_key",))
        return obj


class ItemFactory(Factory):
    class Meta:
        model = Item
    vendor = factory.SubFactory(VendorFactory)
    price = Decimal("1.25")
    code = factory.LazyFunction(lambda: Item.gen_barcode())
    name = factory.Faker("sentence", nb_words=2)


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