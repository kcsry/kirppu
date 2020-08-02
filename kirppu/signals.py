# -*- coding: utf-8 -*-

from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver


@receiver(pre_save)
def save_handler(sender, instance, using, **kwargs):
    # noinspection PyProtectedMember
    if instance._meta.app_label in ("kirppu", "kirppuauth") and using != "default":
        raise ValueError("Saving objects in non-default database should not happen")


@receiver(pre_delete)
def delete_handler(sender, instance, using, **kwargs):
    # noinspection PyProtectedMember
    if instance._meta.app_label in ("kirppu", "kirppuauth") and using != "default":
        raise ValueError("Deleting objects from non-default database should not happen")
