# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0011_auto_20160127_2212'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='terms_accepted',
            field=models.DateTimeField(null=True),
        ),
    ]
