# Generated by Django 2.1.3 on 2019-08-28 17:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_auto_20190828_1440'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aerosimpleuser',
            name='airport',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='users', to='airport.Airport'),
        ),
        migrations.AlterField(
            model_name='aerosimpleuser',
            name='authorized_airports',
            field=models.ManyToManyField(to='airport.Airport'),
        ),
    ]