# Generated by Django 2.1.3 on 2019-09-17 13:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_auto_20190828_1748'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aerosimpleuser',
            name='airport',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='users', to='airport.Airport'),
        ),
    ]
