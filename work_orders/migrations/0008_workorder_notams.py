# Generated by Django 2.1.3 on 2019-07-11 13:15

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('work_orders', '0007_auto_20190301_1909'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='notams',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict, null=True),
        ),
    ]