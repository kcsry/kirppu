from collections import defaultdict
from decimal import Decimal
import sys
import re

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.core.management.base import BaseCommand

try:
    from typing import Dict, List
except ImportError:
    class _AbstractType(object):
        def __getitem__(self, item): pass
    Dict = _AbstractType()
    List = _AbstractType()

from kirppu.models import Item, Vendor
from kirppuauth.models import User


# noinspection SpellCheckingInspection,PyPep8Naming
class PostgreDumpParser(object):
    def __init__(self, file_name):
        self._file_name = file_name
        self._data = defaultdict(list)  # type: Dict[str, List[Dict[str, str]]]

    @property
    def data(self):
        return self._data

    def parse(self, handle=None):
        with (handle or open(self._file_name, "r")) as stream:
            current_line_data = None
            for line in stream:
                if line.endswith("\n"):
                    line = line[:-1]
                if current_line_data is not None:
                    if line == "\\.":
                        current_line_data = None
                        continue
                    if self.parse_STDIN(line, *current_line_data):
                        continue

                if line.strip() == "":
                    continue

                if line.startswith("COPY "):
                    current_line_data = self.parse_COPY(line)

    @staticmethod
    def parse_COPY(line):
        m = re.match("COPY (?P<table>[\w_]+) \((?P<columns>(?:\w+, )*\w+)\) FROM stdin;", line)
        if m is None:
            raise ValueError("Not understood copy: " + line)

        table = m.group("table")
        columns = m.group("columns").split(", ")
        return table, columns

    def parse_STDIN(self, line, table, columns):
        parts = line.split("\t")
        assert len(parts) == len(columns), "Sizes differ: {} != {}: {}".format(len(parts), len(columns), line)

        data = {
            column: value
            for column, value in zip(columns, parts)
        }

        self._data[table].append(data)


class TypeConverter(object):
    @staticmethod
    def int(inp):
        return int(inp) if inp != "\\N" else None

    @staticmethod
    def str(inp):
        return str(inp) if inp != "\\N" else None

    @staticmethod
    def bool(inp):
        return (True, False)["tf".index(inp)] if inp != "\\N" else None

    @staticmethod
    def decimal(inp):
        return Decimal(inp) if inp != "\\N" else None

    @staticmethod
    def datetime(inp):
        return parse_datetime(inp) if inp != "\\N" else None

ItemColumnTypes = {
    "hidden": "bool",
    "lost_property": "bool",
    "box_id": "int",
    "vendor_id": "int",
    "code": "str",
    "abandoned": "bool",
    "type": "str",
    "price": "decimal",
    "printed": "bool",
    "adult": "str",
    "itemtype": "str",
    "name": "str",
    "id": "int",
}

UserColumnTypes = {
    "password": "str",
    "last_login": "datetime",
    "is_superuser": "bool",
    "username": "str",
    "first_name": "str",
    "last_name": "str",
    "email": "str",
    "is_staff": "bool",
    "is_active": "bool",
    "date_joined": "datetime",
    "phone": "str",
    "last_checked": "datetime",
    "id": "int",
}

VendorColumnTypes = {
    "terms_accepted": "str",
    "id": "int",
}


# noinspection SpellCheckingInspection
class DbConverter(object):
    def __init__(self, table_name):
        self._table_name = table_name
        self._result = []

    def parse(self, data):
        p = getattr(self, "_parse_" + self._table_name)
        return [
            p(row)
            for row in data
        ]

    @staticmethod
    def _parse_kirppu_item(row):
        attrs = {
            col: getattr(TypeConverter, ItemColumnTypes[col])(row[col])
            for col in [
                "hidden",
                "lost_property",
                "box_id",
                "vendor_id",
                "code",
                "abandoned",
                "type",
                "price",
                "printed",
                "adult",
                "itemtype",
                "name",
            ]
        }
        r = Item(**attrs)
        return r

    @staticmethod
    def _parse_kirppuauth_user(row):
        attrs = {
            col: getattr(TypeConverter, UserColumnTypes[col])(row[col])
            for col in [
                "password",
                "last_login",
                "is_superuser",
                "username",
                "first_name",
                "last_name",
                "email",
                "is_staff",
                "is_active",
                "date_joined",
                "phone",
                "last_checked",
            ]
        }
        r = User(**attrs)
        return r

    @staticmethod
    def _parse_kirppu_vendor(row):
        attrs = {
            col: getattr(TypeConverter, VendorColumnTypes[col])(row[col])
            for col in [
            ]
        }
        r = Vendor(**attrs)
        return r


class Command(BaseCommand):
    help = r"""Import Item data from PostgreSQL dump from stdin or from a file that has been pre-processed.
    Do not use unless you know how this works.
    One part of Item-data pre-work: grep -P '^\d+\t[^\t]+\t[^\t]+\t[^\t]+\t\w\w\t\w+\t\w\t\w\t@@@\t.*$'
    """

    def add_arguments(self, parser):
        parser.add_argument("file", type=str, nargs="?")

    def handle(self, *args, **options):
        f_name = options.get("file")
        if f_name is None:
            parser = PostgreDumpParser("stdin")
            parser.parse(sys.stdin)
        else:
            parser = PostgreDumpParser(f_name)
            parser.parse()

        results = {}
        for table, data in parser.data.items():
            converter = DbConverter(table)
            results[table] = converter.parse(data)

        user = results["kirppuauth_user"]
        assert len(user) == 1
        user = user[0]

        vendor = results["kirppu_vendor"]
        assert len(vendor) == 1
        vendor = vendor[0]

        items = results["kirppu_item"]
        assert len(items) > 0

        with transaction.atomic():
            # Create the user if it doesn't exist. user is predefined for exception to use.
            try:
                user = User.objects.get(username=user.username)
            except ObjectDoesNotExist:
                user.save()

            # Create vendor if it doesn't exist. vendor is predefined for exception to use.
            try:
                vendor = Vendor.objects.get(user=user)
            except ObjectDoesNotExist:
                vendor.user = user
                vendor.save()

            # TODO: Create boxes..

            # Create items for the vendor.
            for item in items:
                item.vendor = vendor
                item.save()

        for table in results.keys():
            # noinspection PyProtectedMember
            print("\n".join("{} {}: {}".format(r._meta.object_name, r.pk, str(r)) for r in results[table]))
