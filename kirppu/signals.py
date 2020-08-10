# -*- coding: utf-8 -*-

from django.db.models.signals import pre_migrate, post_migrate
from django.dispatch import receiver

ENABLE_CHECK = True


@receiver(pre_migrate)
def pre_migrate_handler(*args, **kwargs):
    global ENABLE_CHECK
    ENABLE_CHECK = False


@receiver(post_migrate)
def post_migrate_handler(*args, **kwargs):
    global ENABLE_CHECK
    ENABLE_CHECK = True


def save_handler(sender, instance, using, **kwargs):
    # noinspection PyProtectedMember
    if ENABLE_CHECK and instance._meta.app_label in ("kirppu", "kirppuauth") and using != "default":
        raise ValueError("Saving objects in non-default database should not happen")


def delete_handler(sender, instance, using, **kwargs):
    # noinspection PyProtectedMember
    if ENABLE_CHECK and instance._meta.app_label in ("kirppu", "kirppuauth") and using != "default":
        raise ValueError("Deleting objects from non-default database should not happen")
