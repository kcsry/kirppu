# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0003_add_abandoned'),
    ]

    operations = [
        migrations.AlterField(
            model_name='counter',
            name='identifier',
            field=models.CharField(help_text='Registration identifier of the counter', unique=True, max_length=32, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='counter',
            name='name',
            field=models.CharField(help_text='Common name of the counter', max_length=64, blank=True),
            preserve_default=True,
        ),
    ]
