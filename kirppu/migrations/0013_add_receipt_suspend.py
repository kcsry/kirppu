# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0012_add_terms_accepting'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReceiptNote',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('text', models.TextField()),
                ('clerk', models.ForeignKey(to='kirppu.Clerk')),
            ],
        ),
        migrations.AlterField(
            model_name='receipt',
            name='status',
            field=models.CharField(max_length=16, choices=[('PEND', 'Not finished'), ('FINI', 'Finished'), ('SUSP', 'Suspended'), ('ABRT', 'Aborted')], default='PEND'),
        ),
        migrations.AddField(
            model_name='receiptnote',
            name='receipt',
            field=models.ForeignKey(to='kirppu.Receipt'),
        ),
    ]
