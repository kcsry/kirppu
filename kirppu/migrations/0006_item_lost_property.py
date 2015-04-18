# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0005_add_model_itemstatelog'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='lost_property',
            field=models.BooleanField(default=False, help_text='Forgotten or lost property/item'),
            preserve_default=True,
        ),
    ]
