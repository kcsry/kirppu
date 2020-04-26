# -*- coding: utf-8 -*-
from datetime import date, timedelta

from django.shortcuts import render

__author__ = 'codez'

__all__ = [
    "front_page",
    "front_for_mobile_view",
]

from ..models import Event


def _events():
    today = date.today()

    # 26 weeks ~= half year
    hidden_event_limit = today - timedelta(weeks=26)
    events = Event.objects.filter(
        end_date__gte=hidden_event_limit,
        visibility=Event.VISIBILITY_VISIBLE,
    ).order_by("-start_date")

    # Keep ongoing / just ended events for awhile in the "future" list.
    old_event_limit = today - timedelta(days=7)
    coming_events = []
    old_events = []
    for event in events:
        if event.end_date >= old_event_limit:
            if event.start_date <= today <= event.end_date:
                event.fp_currently_ongoing = True
            coming_events.append(event)
        else:
            old_events.append(event)

    return coming_events, old_events


def front_page(request):
    coming_events, old_events = _events()
    return render(
        request,
        "kirppu/frontpage.html",
        {
            "events": coming_events,
            "old_events": old_events,
        },
    )


def front_for_mobile_view(request):
    events, _ = _events()
    return render(
        request,
        "kirppu/frontpage_for_mobile_view.html",
        {
            "events": events,
        },
    )
