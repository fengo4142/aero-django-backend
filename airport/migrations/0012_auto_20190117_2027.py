# Generated by Django 2.1.3 on 2019-01-17 20:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('airport', '0011_airport_location'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='airport',
            options={'ordering': ['name'], 'permissions': (('can_modify_airport_settings', 'Can modify Airport Settings'),)},
        ),
    ]
