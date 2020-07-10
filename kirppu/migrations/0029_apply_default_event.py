from datetime import timedelta

from django.conf import settings
from django.db import migrations, models
from django.utils.timezone import now
import django.db.models.deletion


FIELDS = {
    'Clerk': 'event',
    'Counter': 'event',
    'Itemtype': 'event',
    'Uitext': 'event',
    'Vendor': 'event',
}


# noinspection PyPep8Naming
def set_default_event(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    need_default_event = False
    for model_name, _ in FIELDS.items():
        mdl = apps.get_model("kirppu", model_name)
        if mdl.objects.using(db_alias).exists():
            need_default_event = True
            break

    if not need_default_event:
        return

    Event = apps.get_model("kirppu", "Event")
    if not Event.objects.using(db_alias).filter(id=1).exists():
        Event.objects.using(db_alias).create(
            slug="default",
            name="Default event",
            start_date=now(),
            end_date=now() + timedelta(days=2),
        )

    event = Event.objects.using(db_alias).get(id=1)
    for model_name, field_name in FIELDS.items():
        mdl = apps.get_model("kirppu", model_name)
        mdl.objects.using(db_alias).filter(**{field_name + "__isnull": True}).update(**{field_name: event})


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('kirppu', '0028_create_event'),
    ]

    operations = [
        migrations.RunPython(set_default_event),
        migrations.AlterField(
            model_name='clerk',
            name='event',
            field=models.ForeignKey(null=False, on_delete=django.db.models.deletion.CASCADE, to='kirppu.Event'),
        ),
        migrations.AlterField(
            model_name='counter',
            name='event',
            field=models.ForeignKey(null=False, on_delete=django.db.models.deletion.CASCADE, to='kirppu.Event'),
        ),
        migrations.AlterField(
            model_name='itemtype',
            name='event',
            field=models.ForeignKey(null=False, on_delete=django.db.models.deletion.CASCADE, to='kirppu.Event'),
        ),
        migrations.AlterField(
            model_name='uitext',
            name='event',
            field=models.ForeignKey(null=False, on_delete=django.db.models.deletion.CASCADE, to='kirppu.Event'),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='event',
            field=models.ForeignKey(null=False, on_delete=django.db.models.deletion.CASCADE, to='kirppu.Event'),
        ),
    ]
