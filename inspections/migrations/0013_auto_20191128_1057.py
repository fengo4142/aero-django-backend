# Generated by Django 2.1.3 on 2019-11-28 10:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inspections', '0012_auto_20191022_1200'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inspectionparent',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inspection_parents', to='users.AerosimpleUser'),
        ),
    ]
