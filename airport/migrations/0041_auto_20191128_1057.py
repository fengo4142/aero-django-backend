# Generated by Django 2.1.3 on 2019-11-28 10:57

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('airport', '0040_auto_20191001_1518'),
    ]

    operations = [
        migrations.AlterField(
            model_name='airport',
            name='types_for_self_inspection',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default={}, null=True),
        ),
    ]
