# Generated by Django 2.1.3 on 2019-05-07 17:59

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import forms.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('users', '0005_auto_20190118_2009'),
        ('airport', '0025_assetimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now=True)),
                ('response', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('report_date', models.DateTimeField()),
                ('description', models.TextField()),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LogForm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('airport', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='log_form', to='airport.Airport')),
            ],
            options={
                'ordering': ('title',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LogSubType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, null=True)),
                ('i18n_id', models.CharField(max_length=20, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='LogType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, null=True)),
                ('i18n_id', models.CharField(max_length=20, null=True)),
                ('airport', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='log_types', to='airport.Airport')),
            ],
        ),
        migrations.CreateModel(
            name='LogVersion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField(default=1)),
                ('schema', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=forms.models.version_default)),
                ('status', models.IntegerField(choices=[(0, 'Draft'), (1, 'Published'), (2, 'Expired')], default=0)),
                ('publish_date', models.DateTimeField(blank=True, null=True)),
                ('expiry_date', models.DateTimeField(blank=True, null=True)),
                ('form', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='operations_log.LogForm')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='logsubtype',
            name='activity_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subtypes', to='operations_log.LogType'),
        ),
        migrations.AddField(
            model_name='log',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='operations_logs', to='operations_log.LogType'),
        ),
        migrations.AddField(
            model_name='log',
            name='content_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='log',
            name='form',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='operation_logs', to='operations_log.LogVersion'),
        ),
        migrations.AddField(
            model_name='log',
            name='logged_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='operations_logs', to='users.AerosimpleUser'),
        ),
        migrations.AddField(
            model_name='log',
            name='subcategory',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='operations_logs', to='operations_log.LogSubType'),
        ),
    ]