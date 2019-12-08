# Generated by Django 2.1.2 on 2018-10-19 15:09

import airport.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('airport', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Airport',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, primary_key=True, serialize=False,
                    verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=4)),
                ('website', models.URLField()),
                ('logo', models.FileField(
                    upload_to='airport_logos/',
                    validators=[airport.validators.logo_validator])),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]