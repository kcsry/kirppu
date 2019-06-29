import django.core.validators
from django.db import migrations, models
import kirppu.models


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0029_apply_default_event'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='mobile_view_visible',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='event',
            name='multiple_vendors_per_user',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='event',
            name='provision_function',
            field=models.TextField(blank=True, help_text='Python function body that gets sold_and_compensated queryset as argument and must call result() with None or Decimal argument.', null=True, validators=[kirppu.models._validate_provision_function]),
        ),
        migrations.AddField(
            model_name='event',
            name='use_boxes',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='event',
            name='max_brought_items',
            field=models.IntegerField(blank=True, help_text='Amount of unsold Items a Vendor can have in the Event. If blank, no limit is imposed.', null=True, validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AddField(
            model_name='event',
            name='visibility',
            field=models.SmallIntegerField(choices=[(0, 'Visible'), (1, 'Not listed in front page')], default=0),
        ),
    ]
