# Generated by Django 2.1.3 on 2019-11-12 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_auto_20190917_1314'),
    ]

    operations = [
        migrations.AddField(
            model_name='aerosimpleuser',
            name='designation',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
