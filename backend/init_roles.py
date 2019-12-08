from django.contrib.auth.models import Permission, Group, User
from django.conf import settings
from users.models import AerosimpleUser
from airport.models import Airport

new_roles = {
    'Operations Supervisor': [
        'add_inspectionparent', 'view_inspection', 'change_inspection', 'view_role',
        'add_inspectionanswer', 'view_inspectionanswer', 'view_inspectiontemplateform',
        'add_inspection', 'can_modify_airport_settings', 'view_workorder', 'add_workorder',
        'add_workorderschema', 'add_operations', 'add_maintenance', 'change_airport',
        'view_surfacetype', 'add_surfacetype', 'add_surfaceshape', 'view_surfaceshape',
        'view_asset', 'add_asset', 'view_log', 'add_log'],
    'Airport Manager': ['view_inspection', 'view_role', 'view_inspectionanswer',
        'view_inspectiontemplateform', 'view_workorder', 'view_surfacetype', 'view_surfaceshape',
        'view_asset', 'view_log'],
    'Maintenance Staff': ['view_workorder', 'add_workorderschema', 'add_operations', 
        'add_maintenance'],
    'Operations Staff': ['add_inspectionanswer', 'view_inspection', 'view_workorder', 
        'add_workorder', 'view_asset'],
    'System Admin': ['add_inspectionparent', 'view_inspection', 'change_inspection', 'view_role',
        'add_inspectionanswer', 'view_inspectionanswer', 'view_inspectiontemplateform',
        'add_inspection', 'can_modify_airport_settings', 'view_workorder', 'add_workorder',
        'add_workorderschema', 'add_operations', 'add_maintenance', 'change_airport',
        'view_surfacetype', 'add_surfacetype', 'add_surfaceshape', 'view_surfaceshape',
        'view_asset', 'add_asset', 'view_log', 'add_log', 'add_role', 'change_role',
        'add_aerosimpleuser', 'change_aerosimpleuser', 'view_aerosimpleuser']
}

def create_super_user(apps=None, schema=None):
    email = 'admin.{0}@aerosimple.com'.format(settings.STAGE)
    if User.objects.get(email=email) is None:
        user = User()
        user.email = email
        user.first_name = 'Admin'
        user.is_staff = True
        user.is_superuser = True
        user.save()
        user.user_permissions.add(Permission.objects.get(codename='view_airport'))
        user.user_permissions.add(Permission.objects.get(codename='add_airport'))
        user.user_permissions.add(Permission.objects.get(codename='change_airport'))
        user.user_permissions.add(Permission.objects.get(codename='delete_airport'))
        aero_user = AerosimpleUser()
        aero_user.user = user
        aero_user.fullname = 'Aero Admin'
        aero_user.airport = Airport.objects.first()
        aero_user.system_generated = True
        aero_user.save()
        # aero_user.authorized_airports.add(Airport.objects.first())

def init_groups(apps=None, schema=None):
    for role in new_roles.items(): 
        name = role[0]
        permissions = role[1]
        group = Group.objects.get_or_create(name=name)
        for permission in permissions:
            permission = Permission.objects.filter(codename=permission)
            if permission:
                group[0].permissions.add(permission[0])
