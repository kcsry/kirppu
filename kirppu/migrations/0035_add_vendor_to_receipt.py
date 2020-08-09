from django.db import migrations, models
import django.db.models.deletion


# noinspection PyPep8Naming
def detect_provision(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    Receipt = apps.get_model("kirppu", "Receipt")
    compensations = (
        Receipt.objects.using(db_alias)
        .filter(type="COMPENSATION")
        .annotate(src_vendor=models.F("receiptitem__item__vendor_id"))
        .only("id")
        .distinct()
    )
    for c in compensations:
        c.vendor_id = c.src_vendor
        c.save(update_fields=("vendor",))


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0034_provision_dsl'),
    ]

    operations = [
        migrations.AddField(
            model_name='receipt',
            name='vendor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='kirppu.Vendor'),
        ),
        migrations.RunPython(detect_provision),
    ]
