# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0009_add_permissions_for_item'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemstatelog',
            name='clerk',
            field=models.ForeignKey(to='kirppu.Clerk', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='itemstatelog',
            name='counter',
            field=models.ForeignKey(to='kirppu.Counter', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
