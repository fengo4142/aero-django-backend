# Generated by Django 2.1.2 on 2018-10-25 19:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('airport', '0008_auto_20181025_1907'),
    ]

    operations = [
        migrations.AddField(
            model_name='surfaceshape',
            name='airport',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, related_name='surfaces', to='airport.Airport'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='surfaceshape',
            name='name',
            field=models.CharField(default='shape', max_length=100),
            preserve_default=False,
        ),
    ]