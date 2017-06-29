# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import kirppu.models
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Clerk',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('access_key', models.CharField(null=True, validators=[django.core.validators.RegexValidator(b'^[0-9a-f]{14}$', message=b'Must be 14 hex chars.')], max_length=128, blank=True, help_text='Access code assigned to the clerk. 14 hexlets.', unique=True, verbose_name='Access key value')),
                ('user', models.OneToOneField(null=True, to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Counter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(help_text='Identifier of the counter', unique=True, max_length=32, blank=True)),
                ('name', models.CharField(help_text='Name of the counter', max_length=64, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(help_text='Barcode content of the product', unique=True, max_length=16, db_index=True, blank=True)),
                ('name', models.CharField(max_length=256, blank=True)),
                ('price', models.DecimalField(max_digits=8, decimal_places=2, validators=[kirppu.models.validate_positive])),
                ('state', models.CharField(default=b'AD', max_length=8, choices=[(b'AD', 'Advertised'), (b'BR', 'Brought to event'), (b'ST', 'Staged for selling'), (b'SO', 'Sold'), (b'MI', 'Missing'), (b'RE', 'Returned to vendor'), (b'CO', 'Compensated to vendor')])),
                ('type', models.CharField(default=b'short', max_length=8, choices=[(b'tiny', 'Tiny price tag'), (b'short', 'Short price tag'), (b'long', 'Long price tag')])),
                ('printed', models.BooleanField(default=False)),
                ('hidden', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Receipt',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(default=b'PEND', max_length=16, choices=[(b'PEND', 'Not finished'), (b'FINI', 'Finished'), (b'ABRT', 'Aborted')])),
                ('total', models.DecimalField(default=0, max_digits=8, decimal_places=2)),
                ('start_time', models.DateTimeField(auto_now_add=True)),
                ('sell_time', models.DateTimeField(null=True, blank=True)),
                ('clerk', models.ForeignKey(to='kirppu.Clerk', on_delete=models.CASCADE)),
                ('counter', models.ForeignKey(to='kirppu.Counter', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReceiptItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action', models.CharField(default=b'ADD', max_length=16, choices=[(b'ADD', 'Added to receipt'), (b'RL', 'Removed later'), (b'DEL', 'Removed from receipt')])),
                ('add_time', models.DateTimeField(auto_now_add=True)),
                ('item', models.ForeignKey(to='kirppu.Item', on_delete=models.CASCADE)),
                ('receipt', models.ForeignKey(to='kirppu.Receipt', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='receipt',
            name='items',
            field=models.ManyToManyField(to='kirppu.Item', through='kirppu.ReceiptItem'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='item',
            name='vendor',
            field=models.ForeignKey(to='kirppu.Vendor', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
