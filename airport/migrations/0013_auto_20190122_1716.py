# Generated by Django 2.1.3 on 2019-01-22 17:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('airport', '0012_auto_20190117_2027'),
    ]

    operations = [
        migrations.AlterField(
            model_name='airport',
            name='safety_self_inspection',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='associated_airport', to='inspections.InspectionParent'),
        ),
    ]
