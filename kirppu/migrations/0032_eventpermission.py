from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('kirppu', '0031_event_age_restricted_items'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventPermission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('can_see_clerk_codes', models.BooleanField(default=False)),
                ('can_see_statistics', models.BooleanField(default=False)),
                ('can_see_accounting', models.BooleanField(default=False)),
                ('can_register_items_outside_registration', models.BooleanField(default=False)),
                ('can_perform_overseer_actions', models.BooleanField(default=False)),
                ('can_switch_sub_vendor', models.BooleanField(default=False)),
                ('can_create_sub_vendor', models.BooleanField(default=False)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='kirppu.Event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('event', 'user')},
            },
        ),
    ]
