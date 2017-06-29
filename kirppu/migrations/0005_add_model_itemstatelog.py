# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0004_modify_counter'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemStateLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('old_state', models.CharField(max_length=2, choices=[(b'AD', 'Advertised'), (b'BR', 'Brought to event'), (b'ST', 'Staged for selling'), (b'SO', 'Sold'), (b'MI', 'Missing'), (b'RE', 'Returned to vendor'), (b'CO', 'Compensated to vendor')])),
                ('new_state', models.CharField(max_length=2, choices=[(b'AD', 'Advertised'), (b'BR', 'Brought to event'), (b'ST', 'Staged for selling'), (b'SO', 'Sold'), (b'MI', 'Missing'), (b'RE', 'Returned to vendor'), (b'CO', 'Compensated to vendor')])),
                ('item', models.ForeignKey(to='kirppu.Item', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
