from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0036_add_receipt_vendor_constraint'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='clerk',
            options={'default_manager_name': 'prefetch_manager', 'permissions': (('oversee', 'Can perform overseer actions'),)},
        ),
        migrations.AlterModelManagers(
            name='clerk',
            managers=[
                ('prefetch_manager', django.db.models.manager.Manager()),
            ],
        ),
    ]
