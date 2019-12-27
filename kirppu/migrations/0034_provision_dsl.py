import logging
from functools import partial
from django.db import migrations

logger = logging.getLogger(__name__)


# noinspection PyPep8Naming
def detect_provision(apps, schema_editor, forward):
    db_alias = schema_editor.connection.alias
    Event = apps.get_model("kirppu", "Event")
    events = (
        Event.objects.using(db_alias)
        .filter(provision_function__isnull=False)
        .only("id", "name", "provision_function")
    )
    if events:
        if forward:
            way = "new lisp"
        else:
            way = "old python"
        logger.warning("  ** You may need to migrate provision function scripts to %s format for following events: %s",
                       way,
                       ", ".join("%d/%s" % (event.id, repr(event.name))
                                 for event in events
                                 if event.provision_function.strip() != ""))


_fwd = partial(detect_provision, forward=True)
_rev = partial(detect_provision, forward=False)


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0033_auto_20191016_2230'),
    ]

    operations = [
        migrations.RunPython(_fwd, _rev),
    ]
