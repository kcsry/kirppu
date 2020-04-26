# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.utils.translation import activate

from kirppu.views.accounting import accounting_receipt


class Command(BaseCommand):
    help = 'Dump accounting CSV to standard output'

    def add_arguments(self, parser):
        parser.add_argument('--lang', type=str, help="Change language, for example: en")
        parser.add_argument('event', type=str, help="Event slug to dump data for")

    def handle(self, *args, **options):
        if "lang" in options:
            activate(options["lang"])

        from kirppu.models import Event
        event = Event.objects.get(slug=options["event"])
        accounting_receipt(self.stdout, event)
