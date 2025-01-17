# Generated by Django 2.1.3 on 2019-01-17 20:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
        ('airport', '0012_auto_20190117_2027'),
        ('users', '0002_aerosimpleuser_fullname'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('airport', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='roles', to='airport.Airport')),
                ('permission_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='roles', to='auth.Group')),
            ],
        ),
        migrations.AddField(
            model_name='aerosimpleuser',
            name='roles',
            field=models.ManyToManyField(related_name='users', to='users.Role'),
        ),
    ]
