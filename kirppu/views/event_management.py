# -*- coding: utf-8 -*-
import json
import typing

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import View

from ..models import Clerk, Event, EventPermission, UserAdapter


def _requirements(request, **kwargs):
    event_slug = kwargs["event_slug"]
    event = get_object_or_404(Event, slug=event_slug)

    permissions = EventPermission.get(event, request.user)
    if not permissions.can_manage_event and not request.user.is_superuser:
        return HttpResponseForbidden()
    return event


@login_required
def index(request, event_slug: str):
    _requirements(request, event_slug=event_slug)
    return HttpResponseRedirect(reverse("kirppu:people_manage", kwargs={
        "event_slug": event_slug,
    }))


class PersonInfo:
    user: AbstractUser
    id: int
    name: str

    is_clerk: bool = False
    has_clerk_code: bool = False
    clerk_code: typing.Optional[str] = None

    manage_event: bool = False

    see_clerk_codes: bool = False
    see_statistics: bool = False
    see_accounting: bool = False
    register_items_outside_registration: bool = False
    perform_overseer_actions: bool = False
    switch_sub_vendor: bool = False
    create_sub_vendor: bool = False

    def __init__(self, user: AbstractUser):
        self.user = user
        self.id = user.id
        self.name = "%s (%s)" % (UserAdapter.full_name(user), user.username)

    def as_dict(self):
        return {key: getattr(self, key) for key in (
            "id",
            "name",
            "is_clerk",
            "has_clerk_code",
            "clerk_code",
            "manage_event",
            "see_clerk_codes",
            "see_statistics",
            "see_accounting",
            "register_items_outside_registration",
            "perform_overseer_actions",
            "switch_sub_vendor",
            "create_sub_vendor",
        )}


class PeopleManagement(View):
    template_name = "kirppu/people_management.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        event = _requirements(request, **kwargs)
        return super().dispatch(request, event, *args, **kwargs)

    def get(self, request, event, *args, **kwargs):
        permissions = EventPermission.objects.select_related("user").filter(event=event)
        clerks = Clerk.objects.select_related("user").filter(event=event)

        infos: typing.Dict[int, PersonInfo] = {}

        for p in permissions:
            info = infos.get(p.user_id)
            if info is None:
                info = PersonInfo(p.user)
                infos[p.user_id] = info

            self._make_permission_info(info, p)

        available_clerks: typing.List[str] = []
        for c in clerks:
            if c.user_id is None:
                # Unbound Clerk.
                available_clerks.append(c.access_code)
                continue
            info = infos.get(c.user_id)
            if info is None:
                info = PersonInfo(c.user)
                infos[c.user_id] = info

            self._make_clerk_info(info, c)

        info_data: typing.List[typing.Dict[str, typing.Any]] = [
            info.as_dict()
            for info in sorted(infos.values(), key=lambda item: item.user.username)
        ]

        return render(request, self.template_name, {
            "event_slug": event.slug,
            "available_clerks": available_clerks,
            "info_data": info_data,
        })

    @staticmethod
    def _make_permission_info(info: PersonInfo, p: EventPermission):
        info.manage_event = p.can_manage_event
        info.see_clerk_codes = p.can_see_clerk_codes
        info.see_statistics = p.can_see_statistics
        info.see_accounting = p.can_see_accounting
        info.register_items_outside_registration = p.can_register_items_outside_registration
        info.perform_overseer_actions = p.can_perform_overseer_actions
        info.switch_sub_vendor = p.can_switch_sub_vendor
        info.create_sub_vendor = p.can_create_sub_vendor

    @staticmethod
    def _make_clerk_info(info: PersonInfo, c: Clerk):
        info.is_clerk = True
        info.has_clerk_code = c.is_enabled
        info.clerk_code = c.access_code

    def post(self, request, event, *args, **kwargs):
        data = json.loads(request.body.decode(request.encoding or "utf-8"))

        user_id = data["id"]
        user = get_user_model().objects.get(id=user_id)
        expect = data["expect"]
        values = data["values"]

        need_clerk = any(
            values[item]
            for item in (
                "is_clerk",
                # has_clerk_code depends on is_clerk and cannot exist alone.
            )
        )
        need_permissions = any(
            values[item]
            for item in (
                "manage_event",
                "see_clerk_codes",
                "see_statistics",
                "see_accounting",
                "register_items_outside_registration",
                "perform_overseer_actions",
                "switch_sub_vendor",
                "create_sub_vendor",
            )
        )

        with transaction.atomic():
            try:
                clerk = Clerk.objects.select_for_update().get(event=event, user_id=user_id)
            except Clerk.DoesNotExist:
                if need_clerk:
                    clerk = Clerk(event=event, user_id=user_id)
                else:
                    clerk = None

            try:
                perm = EventPermission.objects.select_for_update().get(event=event, user_id=user_id)
            except EventPermission.DoesNotExist:
                if need_permissions:
                    perm = EventPermission(event=event, user_id=user_id)
                else:
                    perm = None

            clerk_changed = False
            if clerk is not None:
                set_code: str = values["clerk_code"]
                if values["is_clerk"] and set_code != "remove":
                    if set_code.startswith("c_"):
                        stub = Clerk.by_code(set_code.removeprefix("c_"), include_unbound=True, event=event)
                        if stub is None or stub.is_enabled:
                            return HttpResponseBadRequest("Invalid Clerk selection. Please reload the page.")
                        clerk.access_key = stub.access_key
                        stub.delete()
                        clerk_changed = True
                    elif set_code == "generate":
                        clerk.generate_access_key()
                        clerk_changed = True
                    elif set_code == "keep":
                        pass
                    else:
                        return HttpResponseBadRequest("Invalid Clerk value.")
                elif (not values["is_clerk"] or set_code == "remove") and clerk.is_enabled:
                    clerk.access_key = None
                    clerk_changed = True

            perm_changed = False
            if perm is not None:
                perm_changed |= self._do_change_bool(perm, "can_manage_event",
                                                     expect, values, "manage_event")
                perm_changed |= self._do_change_bool(perm, "can_see_clerk_codes",
                                                     expect, values, "see_clerk_codes")
                perm_changed |= self._do_change_bool(perm, "can_see_statistics",
                                                     expect, values, "see_statistics")
                perm_changed |= self._do_change_bool(perm, "can_see_accounting",
                                                     expect, values, "see_accounting")
                perm_changed |= self._do_change_bool(perm, "can_register_items_outside_registration",
                                                     expect, values, "register_items_outside_registration")
                perm_changed |= self._do_change_bool(perm, "can_perform_overseer_actions",
                                                     expect, values, "perform_overseer_actions")
                perm_changed |= self._do_change_bool(perm, "can_switch_sub_vendor",
                                                     expect, values, "switch_sub_vendor")
                perm_changed |= self._do_change_bool(perm, "can_create_sub_vendor",
                                                     expect, values, "create_sub_vendor")

            info = PersonInfo(user)
            if clerk is not None:
                if clerk_changed:
                    clerk.save()
                self._make_clerk_info(info, clerk)

            if perm is not None:
                if perm_changed:
                    perm.save()
                self._make_permission_info(info, perm)

        adict = info.as_dict()
        return HttpResponse(
            json.dumps(adict),
            status=200,
            content_type='application/json',
        )

    @staticmethod
    def _do_change_bool(obj, obj_key: str, expects, values, dict_key: str) -> bool:
        current_val = getattr(obj, obj_key)
        new_val = values[dict_key]
        if expects is not None:
            expect_val = expects[dict_key]
            if current_val != expect_val and current_val != new_val:
                # TODO: Maybe return the info data in response to update UI?
                raise ValueError("Value of {} is not {} as expected, but {}".format(
                    obj_key, expect_val, current_val))

        if current_val != new_val:
            setattr(obj, obj_key, values[dict_key])
            return True
        return False
