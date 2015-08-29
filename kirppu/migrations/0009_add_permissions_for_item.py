# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0008_add_model_box'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='item',
            options={'permissions': (('register_override', 'Can register items after registration is closed'),)},
        )
    ]
