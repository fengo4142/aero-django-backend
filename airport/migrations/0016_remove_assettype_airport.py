# Generated by Django 2.1.3 on 2019-02-14 18:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('airport', '0015_asset'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='assettype',
            name='airport',
        ),
    ]