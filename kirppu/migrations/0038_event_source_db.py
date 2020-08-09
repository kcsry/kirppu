from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0037_adjust_clerk_managers'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='source_db',
            field=models.CharField(blank=True, max_length=250, null=True, unique=True),
        ),
        migrations.CreateModel(
            name='RemoteEvent',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('kirppu.event',),
        ),
    ]
