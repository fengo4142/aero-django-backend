# Generated by Django 2.1.3 on 2019-06-14 20:42

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('airport', '0025_assetimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='Translation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(max_length=100)),
                ('translation_map', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('airport', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='airport.Airport')),
            ],
        ),
    ]
