# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-13 12:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


# noinspection PyPep8Naming
def migrate_forwards(apps, schema_editor):
    Box = apps.get_model("kirppu", "Box")
    Item = apps.get_model("kirppu", "Item")
    db_alias = schema_editor.connection.alias

    for box in Box.objects.select_for_update().all():
        representative_item = Item.objects.filter(box=box.id).all()[:1][0]
        box.representative_item = representative_item
        box.save(
            force_update=True,
            update_fields=["representative_item"],
        )


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0016_allow_blank_in_uitext_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='box',
            name='representative_item',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='kirppu.Item'),
            preserve_default=False,
        ),
        migrations.RunPython(
            migrate_forwards,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='box',
            name='representative_item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='kirppu.Item'),
        ),
        migrations.AddField(
            model_name='box',
            name='box_number',
            field=models.IntegerField(blank=True, null=True, unique=True),
        ),
    ]