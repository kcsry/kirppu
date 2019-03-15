# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.utils.translation import activate

from kirppu.accounting import accounting_receipt


class Command(BaseCommand):
    help = 'Dump accounting CSV to standard output'

    def add_arguments(self, parser):
        parser.add_argument('--lang', type=str, help="Change language, for example: en")

    def handle(self, *args, **options):
        if "lang" in options:
            activate(options["lang"])
        accounting_receipt(self.stdout)