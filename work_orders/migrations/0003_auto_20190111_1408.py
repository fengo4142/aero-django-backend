# Generated by Django 2.1.3 on 2019-01-11 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('work_orders', '0002_auto_20190102_1715'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='category_id',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='workorder',
            name='subcategory_id',
            field=models.CharField(max_length=10, null=True),
        ),
    ]