from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db.models.signals import post_save
from django.contrib.postgres.fields import JSONField
from django.dispatch import receiver
from forms.utils import PUBLISHED
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Group, User, Permission
from django.conf import settings

from airport.validators import logo_validator
from work_orders.models import WorkOrderForm
from operations_log.models import LogForm, LogVersion, LogType, LogSubType
from forms.models import Form, Version, Answer
from users.models import Role, AerosimpleUser


class Airport(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=4, unique=True, validators=[MinLengthValidator(4)], help_text='ICAO Code')
    iata_code = models.CharField(max_length=3, blank=True, default='')
    country_code = models.CharField(max_length=3, validators=[MinLengthValidator(2)], default='USA')
    website = models.URLField()
    safety_self_inspection = models.OneToOneField(
        'inspections.InspectionParent',
        related_name="associated_airport",
        on_delete=models.SET_NULL,
        blank=True, null=True,
    )
    location = models.PointField(default='POINT(0.0 0.0)')
    types_for_self_inspection = JSONField(null=True, blank=True, default={})
    default_language = models.CharField(max_length=10, default="en")
    logo = models.FileField(upload_to='airport_logos/',
                            validators=[logo_validator])

    class Meta:
        ordering = ['name']

        permissions = (
            ("can_modify_airport_settings", "Can modify Airport Settings"),
        )

    def __str__(self):
        return "{} ({})".format(self.name, self.code)


def create_default_log_types_subtypes(instance):
    LogType.objects.create(
            name='Inspections', airport=instance, i18n_id='type_0', system_generated=True)
    data = {
        "Daily Activities":[
            "New User",
            "Airport Beacon",
            "Ramp Lighting (remark Off / On)",
            "ARFF Vehicles Setup, Inspected, & Exercised",
            "Radio Check ( 60-Control/ WCPD)",
            "Crash Horn Test Completed",
            "OPS Vehicles Inspected & Serviced",
            "Roving Security Coordinator Shift Change",
            "Terminal Inspection Completed",
            "Terminal Opening Completed",
            "Terminal Shutdown Completed",
            "Misc"
        ],
        "Periodic Activities":[
            "Contractors on Site",
            "FOD Found on Airfield",
            "Fuel Spill Reported",
            "Environmental Reports Filled",
            "Heavy Aircraft Arrival",
            "Heavy Aircraft Departure",
            "Medical Response Requested",
            "Medical Response Requested (Aided Case)",
            "NOTAM(s) Issued",
            "NOTAM(s) Canceled",
            "Terminal Ramp Closed",
            "Terminal Ramp Opened",
            "Wildlife Dispersed",
            "Wildlife Observed",
            "Wildlife Strike"
        ],
        "Security Activities":[
            "Airport Perimeter Inspection Completed w/ WCPD",
            "Airport Perimeter Inspection Completed w/ AOA",
            "AOA / SIDA Security Inspections Completed & Submitted",
            "Baggage Belts Shutdown",
            "Baggage Belts Secured",
            "C*Cure Volume Set to 20%",
            "CCTV Functional Tests Completed",
            "SIDA Access Points Verified Secure",
            "TSA Checkpoint Opened - Departure Lounge sweep completed",
            "TSA Checkpoint Secured - Departure Lounge sweep completed"
        ],
        "Emergency Activities":[
            "Aircraft Alert ",
            "Airport Closed",
            "Airport Open",
            "Power Outage",
            "Terminal Fire Alarm Activated"
        ],
        "Infrequent Activities":[
            "Snow & Ice Control Plan Activated ",
            "Snow & Ice Control Plan Inspection Completed",
            "SA CAT II On",
            "SA CAT II Off"
        ],
    }
    j = 1
    for i, t in enumerate(data.keys()):
        actype = LogType.objects.create(
            name=t, airport=instance, i18n_id='type_{}'.format(i+1), system_generated=False)
        for st in data[t]:
            j += 1
            LogSubType.objects.create(
                activity_type=actype, name=st, i18n_id='subtype_{}'.format(j))

@receiver(post_save, sender=Airport)
def update_airport_data(sender, instance, created, **kwargs):
    if created:
        group_names = ['Operations Supervisor', 'Operations Staff', 'Maintenance Staff',
            'Airport Manager', 'System Admin']
        groups = Group.objects.filter(name__in=group_names)
        for group in groups:
            # create new group, and use it
            airGroup = Group(name='{}-{}'.format(
                group.name,
                instance
            ))
            airGroup.save()

            permissions = Permission.objects.filter(group=group)
            for permission in permissions:
                airGroup.permissions.add(permission)
                    

            Role.objects.create(
                airport=instance,
                permission_group=airGroup,
                name=group.name,
                system_generated=True)

        woform = WorkOrderForm.objects.create(
            airport=instance,
            title="{} Work Order form".format(instance.code)
        )
        woform.maintenance_form.assigned_role = Role.objects.get(
            airport=instance, permission_group__name='Maintenance Staff-{}'.format(instance))
        woform.maintenance_form.save()
        woform.operations_form.assigned_role = Role.objects.get(
            airport=instance, permission_group__name='Maintenance Staff-{}'.format(instance))
        woform.operations_form.save()
        all_asset_categories = AssetCategory.objects.all()
        for cat in all_asset_categories:
            af = AssetForm.objects.create(
                title="{} {} form".format(instance.name, cat.name),
                airport=instance,
                category=cat
            )
            AssetVersion.objects.create(form=af, status=1)
        log_form = LogForm.objects.create(
            airport=instance,
            title="{} Operations log form".format(instance.code)
        )
        create_default_log_types_subtypes(instance)
        LogVersion.objects.create(form=log_form, status=PUBLISHED)
        SurfaceType.objects.create(
            name="Runway",
            color=r"#3A61A8",
            airport=instance
        )
        SurfaceType.objects.create(
            name="Taxiway",
            color=r"#A6E50F",
            airport=instance
        )
        SurfaceType.objects.create(
            name="Ramp",
            color=r"#FFE4E1",
            airport=instance
        )
        enable_admin_for_email('admin.{0}@aerosimple.com'.format(settings.STAGE), instance)
        create_staff_user(instance)


def enable_admin_for_email(admin_email, airport):
    admin_user = User.objects.filter(email=admin_email)[0]
    aeroAdminUsers = AerosimpleUser.objects.filter(user=admin_user)
    if len(aeroAdminUsers) > 0:
        aeroAdminUser = aeroAdminUsers[0]
    else:
        aeroAdminUser = AerosimpleUser()
        aeroAdminUser.user = admin_user
        aeroAdminUser.fullname = 'Aero Admin'
        aeroAdminUser.airport = airport
        aeroAdminUser.save()
    aeroAdminUser.authorized_airports.add(airport)
    admin = Role.objects.filter(
            airport=airport,
            permission_group__name='System Admin-{}'.format(airport))
    aeroAdminUser.roles.add(admin[0])
    aeroAdminUser.save()


def create_staff_user(airport):
    user = User()
    user.email = 'admin.{0}+{1}@aerosimple.com'.format(settings.STAGE, airport.code.lower())
    user.first_name = 'Admin ' + airport.code
    user.is_staff = True
    user.save()
    aero_user = AerosimpleUser()
    aero_user.user = user
    aero_user.fullname = 'Aero Admin ' + airport.code
    aero_user.airport = airport
    aero_user.system_generated = True
    aero_user.save()
    enable_admin_for_email(user.email, airport)


class SurfaceType(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=10)
    airport = models.ForeignKey(
        Airport, related_name="surface_types", on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Surface Type'
        verbose_name_plural = 'Surface Types'
        ordering = ['name']

    def __str__(self):
        return "{} ({} - {})".format(self.name, self.color, self.airport.code)


class SurfaceShape(models.Model):
    name = models.CharField(max_length=100)
    airport = models.ForeignKey(
        Airport, related_name="surfaces", on_delete=models.CASCADE)
    surface_type = models.ForeignKey(
        SurfaceType, related_name="shapes", on_delete=models.CASCADE)
    geometry = models.PolygonField()

    def clean(self):
        if self.airport.id != self.surface_type.airport.id:
            raise ValidationError(
                'The surface and its type must belong to the same Airport.'
            )

    class Meta:
        verbose_name_plural = 'Surface Shapes'

    def __str__(self):
        return "{} ({})".format(self.name, self.airport.code)

# ******************************************************************
# ************************* ASSETS MODELS **************************
# ******************************************************************


class AssetCategory(models.Model):
    """
    This model refers to the main category for assets,
    the one that classifies assets types, for example,
    lights and Signs.
    """
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = 'Asset Categories'

    def __str__(self):
        return "{}".format(self.name)


class AssetType(models.Model):
    """
    This model classifies the assets in types.
    """
    name = models.CharField(max_length=50)
    icon = models.FileField(upload_to='asset_types/')
    category = models.ForeignKey(
        AssetCategory, related_name="types", on_delete=models.CASCADE)

    def __str__(self):
        return "{}_{}".format(self.name, self.category.name)


# ******************************************************************
# ****************** MODELS FOR ASSET FORMS  ***********************
# ******************************************************************

class AssetForm(Form):
    """
    Form model to manage Assets dynamic fields.
    """
    airport = models.ForeignKey(
        "airport.Airport", related_name="asset_forms",
        on_delete=models.CASCADE
    )
    category = models.ForeignKey(
        AssetCategory, related_name="forms", on_delete=models.CASCADE)


class AssetVersion(Version):
    """
    Version model to manage the different versions of Assets dynamic fields.
    """
    form = models.ForeignKey(
        AssetForm, related_name="versions", on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        translations = Translation.objects.filter(airport=self.form.airport)

        for tr in translations:
            tr.updateTranslationMap(self.title, self.schema['fields'])
        super(AssetVersion, self).save(*args, **kwargs)


class Asset(Answer):
    """
    This model has the data for a AssetVersion submit.
    """
    name = models.CharField(max_length=100)
    airport = models.ForeignKey(
        Airport, related_name="assets", on_delete=models.CASCADE)
    asset_type = models.ForeignKey(
        AssetType, related_name="assets", on_delete=models.CASCADE)
    area = models.ForeignKey(
        SurfaceShape, related_name="assets", on_delete=models.CASCADE,
        blank=True, null=True)
    label = models.CharField(max_length=100, blank=True, null=True)
    geometry = models.PointField()

    version_schema = models.ForeignKey(
        AssetVersion,
        related_name="assets",
        on_delete=models.CASCADE)

    def clean(self):
        if (self.area and self.airport.id != self.area.airport.id):
            raise ValidationError(
                _('The asset and its type and area must belong '
                  'to the same Airport.')
            )

        if (self.area is None and self.label is None):
            raise ValidationError(
                _('Asset must have an associated area or label')
            )

        if (self.area is not None and self.label is not None):
            raise ValidationError(
                _('Asset cannot have both, area and label')
            )

    def __str__(self):
        return "{} ({})".format(self.name, self.airport.code)


class AssetImage(models.Model):
    """
    Model to add multiple photos to assets.
    """
    asset = models.ForeignKey(
          Asset, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to='assets/', blank=True, null=True)

# ******************************************************************
# ****************** MODELS FOR TRANSLATIONS  **********************
# ******************************************************************


class Translation(models.Model):
    language = models.CharField(max_length=100)
    airport = models.ForeignKey(
        Airport, related_name="translations", on_delete=models.CASCADE
    )
    translation_map = JSONField(null=True, blank=True)

    def __str__(self):
        return "{} - {}".format(self.airport, self.language)

    def save(self, *args, **kwargs):
        from inspections.models import Inspection
        from work_orders.models import WorkOrderSchema
        from operations_log.models import LogVersion

        if self.pk is None:
            result = {}
            all_versions = Inspection.objects.filter(form__airport=self.airport)
            for v in all_versions:
                result[v.title] = ''
                for f in v.schema['fields']:
                    if f['type'] == 'inspection':
                        result[f['title']] = ''
                        for i in f['checklist']:
                            result[i['value']] = ''
                    else:
                        result[f['title']] = ''

            all_work_orders = WorkOrderSchema.objects.filter(form__airport=self.airport)
            for wo in all_work_orders:
                for f in wo.schema['fields']:
                    result[f['title']] = ''

            all_assets = AssetVersion.objects.filter(form__airport=self.airport)
            for asset in all_assets:
                for f in asset.schema['fields']:
                    result[f['title']] = ''

            all_ops_log = LogVersion.objects.filter(form__airport=self.airport)
            for op in all_ops_log:
                for f in op.schema['fields']:
                    result[f['title']] = ''

            self.translation_map = result
        super(Translation, self).save(*args, **kwargs)

    def updateTranslationMap(self, title, fields):
        if title not in self.translation_map:
            self.translation_map[title] = ''

        for f in fields:
            if f['title'] not in self.translation_map:
                self.translation_map[f['title']] = ''

        self.save()
        return self

