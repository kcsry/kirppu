# -*- coding: utf-8 -*-

from django.apps import AppConfig
from django.db.models.signals import pre_delete, pre_save

__all__ = [
    "KirppuApp",
]


class KirppuApp(AppConfig):
    name = "kirppu"

    def ready(self):
        from .signals import delete_handler, save_handler
        pre_delete.connect(delete_handler)
        pre_save.connect(save_handler)
        super().ready()
