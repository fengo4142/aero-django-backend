# Generated by Django 2.1.3 on 2019-07-29 15:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('airport', '0028_merge_20190701_1140'),
    ]

    operations = [
        migrations.CreateModel(
            name='AirportPermission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_users', models.IntegerField(default=5)),
            ],
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=10)),
            ],
        ),
        migrations.AddField(
            model_name='airportpermission',
            name='modules',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='airport.Module'),
        ),
    ]
