# Generated by Django 2.1.3 on 2019-02-18 18:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('airport', '0019_assetcategory'),
    ]

    operations = [
        migrations.AddField(
            model_name='assettype',
            name='category',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, related_name='types', to='airport.AssetCategory'),
            preserve_default=False,
        ),
    ]
