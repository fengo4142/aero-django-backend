# Generated by Django 2.1.3 on 2018-12-11 20:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inspections', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Remark',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_reference', models.CharField(max_length=50)),
                ('item_reference', models.CharField(max_length=50)),
                ('text', models.TextField()),
                ('answer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='remarks', to='inspections.InspectionAnswer')),
            ],
        ),
    ]
