# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0010_add_owner_info_for_state_log'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clerk',
            name='access_key',
            field=models.CharField(null=True, validators=[django.core.validators.RegexValidator('^[0-9a-fA-F]{14}$', message='Must be 14 hex chars.')], max_length=128, blank=True, help_text='Access code assigned to the clerk. 14 hexlets.', unique=True, verbose_name='Access key value'),
        ),
        migrations.AlterField(
            model_name='item',
            name='itemtype',
            field=models.CharField(default='other', max_length=24, choices=[('manga-finnish', 'Finnish manga book'), ('manga-english', 'English manga book'), ('manga-other', 'Manga book in another language'), ('book', 'Non-manga book'), ('magazine', 'Magazine'), ('movie-tv', 'Movie or TV-series'), ('game', 'Game'), ('figurine-plushie', 'Figurine or a stuffed toy'), ('clothing', 'Clothing'), ('other', 'Other item')]),
        ),
        migrations.AlterField(
            model_name='uitext',
            name='identifier',
            field=models.CharField(help_text='Identifier of the textitem', unique=True, max_length=16, blank=True),
        ),
        migrations.AlterField(
            model_name='uitext',
            name='text',
            field=models.CharField(help_text='Textitem in UI', max_length=16384),
        ),
    ]
