# Generated by Django 2.1.3 on 2019-03-01 19:09

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('airport', '0024_auto_20190228_1436'),
        ('work_orders', '0006_auto_20190204_1729'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='assets',
            field=models.ManyToManyField(blank=True, related_name='workorder_assets', to='airport.Asset'),
        ),
        migrations.AlterField(
            model_name='workorder',
            name='location',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326),
        ),
    ]
