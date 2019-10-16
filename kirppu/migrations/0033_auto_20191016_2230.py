from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0032_eventpermission'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendor',
            name='person',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='kirppu.Person'),
        ),
    ]
