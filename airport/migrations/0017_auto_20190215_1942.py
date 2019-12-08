# Generated by Django 2.1.3 on 2019-02-15 19:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('airport', '0016_remove_assettype_airport'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='area',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assets', to='airport.SurfaceShape'),
        ),
    ]
