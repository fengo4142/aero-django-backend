# Generated by Django 2.1.3 on 2019-01-18 20:09

from django.contrib.auth.management import create_permissions
from users.models import PermissionConfig, Permission

def fill_config_with_all_permissions():
    if not Permission.objects.exists():
        for app_config in apps.get_app_configs():
            app_config.models_module = True
            create_permissions(app_config, apps=apps, verbosity=0)
            app_config.models_module = None

    permissions_to_show = ['add_inspectionparent', 'view_inspection', 'change_inspection', 'view_role',
        'add_inspectionanswer', 'view_inspectionanswer',
        # 'add_inspection', 
        'can_modify_airport_settings', 'view_workorder', 'add_workorder',
        # 'add_workorderschema', 
        'add_operations', 'add_maintenance', 
        'change_airport',
        # 'view_surfacetype', 'add_surfacetype', 'add_surfaceshape', 'view_surfaceshape',
        'view_asset', 'add_asset', 'view_log', 'add_log', 'add_role', 'change_role',
        'add_aerosimpleuser', 'change_aerosimpleuser', 'view_aerosimpleuser']

    # existing permissions config items

    config = PermissionConfig.objects.first()
    config.permissions.clear()

    for p in permissions_to_show:
        config.permissions.add(Permission.objects.get(
            codename=p
        ))
