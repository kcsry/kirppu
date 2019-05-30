# -*- coding: utf-8 -*-
from django.shortcuts import render

__author__ = 'codez'

from .models import Event


def front_page(request):
    events = Event.objects.filter(
        start_date__isnull=False,
        end_date__isnull=False,
    ).order_by("-start_date")
    return render(
        request,
        "kirppu/frontpage.html",
        {
            "events": events,
        },
    )
