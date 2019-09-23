from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0030_add_event_feature_columns'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='age_restricted_items',
            field=models.BooleanField(default=True),
        ),
    ]
