# Generated by Django 2.1.3 on 2019-11-29 11:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inspections', '0013_auto_20191128_1057'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inspectionparent',
            name='template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inspections', to='inspections.InspectionTemplateVersion'),
        ),
    ]
