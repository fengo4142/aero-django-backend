from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from forms.models import Form, Version, Answer
from users.models import AerosimpleUser, Role
from forms.utils import PUBLISHED


# ******************************************************************
# ********************** WORK ORDER SCHEMA  ************************
# ******************************************************************
class WorkOrderForm(Form):
    airport = models.OneToOneField(
        "airport.Airport", related_name="work_order_schema",
        on_delete=models.CASCADE
    )

    class Meta:

        permissions = (
            ("can_modify_workorder_schema", "Can modify Work Order Schema"),
        )


class WorkOrderSchema(Version):
    form = models.ForeignKey(
        WorkOrderForm, related_name="versions", on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        from airport.models import Translation
        translations = Translation.objects.filter(airport=self.form.airport)

        for tr in translations:
            tr.updateTranslationMap('WorkOrder', self.schema['fields'])
        super(WorkOrderSchema, self).save(*args, **kwargs)


class MaintenanceForm(Form):
    work_order = models.OneToOneField(
        WorkOrderForm, related_name="maintenance_form",
        on_delete=models.CASCADE)
    assigned_role = models.ForeignKey(
        Role, related_name="maintenance_assigned_role", on_delete=models.CASCADE,
        null=True, blank=True
    )
    assigned_users = models.ManyToManyField(
        AerosimpleUser, related_name='maintenance_assigned_users', blank=True
    )


class MaintenanceSchema(Version):
    form = models.ForeignKey(
        MaintenanceForm, related_name="versions", on_delete=models.CASCADE)


class OperationsForm(Form):
    work_order = models.OneToOneField(
        WorkOrderForm, related_name="operations_form",
        on_delete=models.CASCADE)
    assigned_role = models.ForeignKey(
        Role, related_name="operations_assigned_role", on_delete=models.CASCADE,
        null=True, blank=True
    )
    assigned_users = models.ManyToManyField(
        AerosimpleUser, related_name='operations_assigned_users', blank=True
    )


class OperationsSchema(Version):
    form = models.ForeignKey(
        OperationsForm, related_name="versions", on_delete=models.CASCADE)


# Form status constants
HIGH = 2
MEDIUM = 1
LOW = 0

# These are the possible priorities for a workorder
PRIORITY = (
    (HIGH, _("High")),
    (MEDIUM, _("Medium")),
    (LOW, _("Low"))
)

# Work order status constants
NEW = 0
MAINTENANCE = 1
OPERATION = 2
COMPLETED = 3

# These are the possible priorities for a workorder
STATUS = (
    (NEW, _("New")),
    (MAINTENANCE, _("Pending Maintenance Review")),
    (OPERATION, _("Pending Operations Review")),
    (COMPLETED, _("Completed")),
)


@receiver(post_save, sender=WorkOrderForm)
def create_stage_schemas(sender, instance, created, **kwargs):
    if created:
        work_order_version = WorkOrderSchema()
        work_order_version.form = instance
        work_order_version.status = PUBLISHED
        work_order_version.save()
        maintenance_form = MaintenanceForm.objects.create(
            work_order=instance,
            title="{} Maintenance schema".format(instance.airport.code)
        )
        maintenance_version = MaintenanceSchema()
        maintenance_version.form = maintenance_form
        maintenance_version.status = PUBLISHED
        maintenance_version.save()
        operations_form = OperationsForm.objects.create(
            work_order=instance,
            title="{} Operations schema".format(instance.airport.code)
        )
        operations_version = OperationsSchema()
        operations_version.form = operations_form
        operations_version.status = PUBLISHED
        operations_version.save()


# ******************************************************************
# ************************  WORK ORDERS **************************U*
# ******************************************************************
class WorkOrder(Answer):
    form = models.ForeignKey(
        WorkOrderSchema,
        related_name="work_orders",
        on_delete=models.CASCADE)

    logged_by = models.ForeignKey(
        AerosimpleUser, related_name="logged_work_orders",
        on_delete=models.CASCADE
    )
    priority = models.IntegerField(choices=PRIORITY, default=LOW)
    status = models.IntegerField(choices=STATUS, default=MAINTENANCE)
    category = models.CharField(max_length=100, null=True)
    subcategory = models.CharField(max_length=100, null=True)
    category_id = models.CharField(max_length=10, null=True)
    subcategory_id = models.CharField(max_length=10, null=True)
    report_date = models.DateTimeField()
    location = models.PointField(blank=True, null=True)
    assets = models.ManyToManyField(
        "airport.Asset", blank=True,  related_name='workorder_assets')
    notams = JSONField(default=dict, null=True)
    problem_description = models.TextField()
    # location_zoom = models.IntegerField(blank=True, null=True)
    zoom_level = models.IntegerField(blank=True, null=True)


class WorkOrderImage(models.Model):
    work_order = models.ForeignKey(
        WorkOrder, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to='work_orders/', blank=True, null=True)


# ******************************************************************
# *************** WORK ORDERS - MAINTENANCE STAGE ******************
# ******************************************************************

class Maintenance(Answer):
    work_order = models.ForeignKey(
        WorkOrder, related_name="maintenance_answer",
        on_delete=models.CASCADE
    )
    version = models.ForeignKey(
        MaintenanceSchema, related_name="answers",
        on_delete=models.CASCADE
    )
    completed_by = models.ForeignKey(
        AerosimpleUser, related_name="maintenance_completed",
        on_delete=models.CASCADE
    )
    completed_on = models.DateTimeField()
    work_description = models.TextField()

    class Meta:
        verbose_name = "Maintenance Answer"
        verbose_name_plural = 'Maintenance Answers'


class MaintenanceImage(models.Model):
    maintenance_form = models.ForeignKey(
        Maintenance, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to='work_orders/', blank=True, null=True)


# ******************************************************************
# **************** WORK ORDERS - OPERATIONS STAGE ******************
# ******************************************************************


class Operations(Answer):
    work_order = models.ForeignKey(
        WorkOrder, related_name="operations_answer",
        on_delete=models.CASCADE)

    version = models.ForeignKey(
        OperationsSchema, related_name="answers",
        on_delete=models.CASCADE
    )
    completed_by = models.ForeignKey(
        AerosimpleUser, related_name="operations_completed",
        on_delete=models.CASCADE
    )
    completed_on = models.DateTimeField()
    review_report = models.TextField()

    class Meta:
        verbose_name = "Operations Answer"
        verbose_name_plural = 'Operations Answers'


class OperationsImage(models.Model):
    operations_form = models.ForeignKey(
        Operations, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to='work_orders/', blank=True, null=True)
