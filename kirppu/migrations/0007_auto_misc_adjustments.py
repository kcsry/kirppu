# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0006_item_lost_property'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clerk',
            name='access_key',
            field=models.CharField(null=True, validators=[django.core.validators.RegexValidator(b'^[0-9a-fA-F]{14}$', message=b'Must be 14 hex chars.')], max_length=128, blank=True, help_text='Access code assigned to the clerk.', unique=True, verbose_name='Access key value'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='item',
            name='itemtype',
            field=models.CharField(default=b'other', max_length=24, choices=[(b'manga-finnish', 'Manga (Finnish)'), (b'manga-english', 'Manga (English)'), (b'manga-other', 'Manga (other language)'), (b'book', 'Book'), (b'magazine', 'Magazine'), (b'movie-tv', 'Movie/TV-series'), (b'game', 'Game'), (b'figurine-plushie', 'Figurine/Plushie'), (b'clothing', 'Clothing'), (b'other', 'Other')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='uitext',
            name='identifier',
            field=models.CharField(help_text='Identifier of the text item', unique=True, max_length=16, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='uitext',
            name='text',
            field=models.CharField(help_text='Text item in UI', max_length=16384),
            preserve_default=True,
        ),
    ]
