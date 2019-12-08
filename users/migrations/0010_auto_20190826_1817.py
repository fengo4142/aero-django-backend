# Generated by Django 2.1.3 on 2019-08-26 18:17

import boto3

from django.db import migrations, models
from django.contrib.auth.models import User, Permission
from users.models import AerosimpleUser
from airport.models import Airport
from django.conf import settings


def reverse_func(apps, schema_editor):
    user = User.objects.filter(email='admin.{0}'.format(settings.STAGE))
    user.delete()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_auto_20190823_1845'),
        ('users', '0017_aerosimpleuser_notification_preferences'),
    ]

    operations = [
        migrations.AddField(
            model_name='aerosimpleuser',
            name='system_generated',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(reverse_func),
    ]
