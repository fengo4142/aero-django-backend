# Generated by Django 2.1.3 on 2019-05-10 18:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inspections', '0007_auto_20190506_1937'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inspectionparent',
            name='activity_subtype',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inspection_parents', to='operations_log.LogSubType'),
        ),
        migrations.AlterField(
            model_name='inspectionparent',
            name='activity_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inspection_parents', to='operations_log.LogType'),
        ),
    ]
