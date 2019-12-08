# Generated by Django 2.1.3 on 2019-10-01 15:18

from django.db import migrations

def create_default_asset_types(apps, schema_editor):
    AssetCategory = apps.get_model('airport', 'AssetCategory')
    AssetType = apps.get_model('airport', 'AssetType')

    new_types = {
        'Signs': [
            {
                "name": "Mandatory Hold Short Sign",
                "icon": "asset_types/mandatory_hold_short_sign.png"
            },
            {
                "name": "Directional Sign",
                "icon": "asset_types/directional_sign.png"
            },
            {
                "name": "Location Sign",
                "icon": "asset_types/location_sign.png"
            },
            {
                "name": "Distance Remaining",
                "icon": "asset_types/distance_remaining_sign.png"
            }
        ],
        'Lights': [
            {
                "name": "Runway Edge Light (Displaced threshold)",
                "icon": "asset_types/runway_edge_displaced_light.png"
            },
            {
                "name": "Runway Edge Light",
                "icon": "asset_types/runway_edge_bidirectional_light.png"
            },
            {
                "name": "Threshold/Runway Edge Light (Displaced threshold)",
                "icon": "asset_types/threshold_runway_edge_displaced_threshold_light.png"
            },
            {
                "name": "Taxiway Edge Light",
                "icon": "asset_types/taxiway_edge_light.png"
            },
            {
                "name": "Runway Edge Light",
                "icon": "asset_types/runway_edge_light.png"
            },
            {
                "name": "Runway Edge Light (Last 2000)",
                "icon": "asset_types/runway_edge_last_2000_light.png"
            },
            {
                "name": "Approach Light",
                "icon": "asset_types/approach_light.png"
            },
            {
                "name": "Runway End Identifier Light (REIL)",
                "icon": "asset_types/runway_end_identifier_light.png"
            },
            {
                "name": "Runway Threshold Start Light",
                "icon": "asset_types/runway_threshold_start_light.png"
            },
            {
                "name": "Runway Threshold End Light (Bidirectional)",
                "icon": "asset_types/runway_threshold_end_bidirectional_light.png"
            }
        ],
    }

    for types in new_types.items(): 
        cat = types[0]
        assettypes = types[1]
        for assettype in assettypes:
            AssetType.objects.create(
                name=assettype['name'],
                icon=assettype['icon'],
                category=AssetCategory.objects.get(name=cat)
            )

class Migration(migrations.Migration):

    dependencies = [
        ('airport', '0039_auto_20190928_1142'),
    ]

    operations = [
        migrations.RunPython(
            create_default_asset_types, migrations.RunPython.noop)
    ]