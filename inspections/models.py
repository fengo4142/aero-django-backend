from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.contenttypes.fields import GenericRelation
from users.models import AerosimpleUser
from forms.models import Form, Version, Answer
from airport.models import Airport
from django.db.models.signals import post_save
from django.dispatch import receiver
from forms.utils import PUBLISHED
from django.utils.translation import ugettext_lazy as _
from operations_log.models import LogType, LogSubType, Log, LogForm
import logging

logger = logging.getLogger('backend')

class InspectionTemplateForm(Form):
    """
    Model for Inspection Forms
    """
    title = models.CharField(max_length=100, null=True)
    repo_id = models.IntegerField()


class InspectionTemplateVersion(Version):
    title = models.CharField(max_length=100)
    icon = models.CharField(max_length=100)
    additionalInfo = models.TextField(blank=True, null=True)
    form = models.ForeignKey(InspectionTemplateForm, related_name="versions",
                             on_delete=models.CASCADE)

    def __str__(self):
        return "{} - Version {}".format(self.form.title, self.number)


class AirportTemplatesRelation(models.Model):
    """
    Model to store the last version accepted for an airport
    """
    airport = models.ForeignKey(
        Airport, related_name="template_relation", on_delete=models.CASCADE)
    selected_version = models.IntegerField(default=1)
    form = models.ForeignKey(
        InspectionTemplateForm,
        related_name="template_relations", on_delete=models.CASCADE
    )


class InspectionParent(Form):
    """
    Model for Inspection Forms
    """

    created_by = models.ForeignKey(
        AerosimpleUser, related_name="inspection_parents",
        on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=100, null=True)
    icon = models.CharField(max_length=100, null=True)

    template = models.ForeignKey(
        InspectionTemplateVersion, related_name="inspections",
        on_delete=models.SET_NULL, null=True, blank=True)
    airport_changes = JSONField(default=dict, null=True, blank=True)

    additionalInfo = models.TextField(blank=True, null=True)
    airport = models.ForeignKey(
        Airport, related_name="inspection_parents", on_delete=models.CASCADE)
    task = models.OneToOneField(
        "tasks.Task", related_name="inspection", on_delete=models.SET_NULL,
        null=True, blank=True)

    activity_type = models.ForeignKey(
        LogType, related_name="inspection_parents", on_delete=models.SET_NULL,
        null=True, blank=True)
    activity_subtype = models.ForeignKey(
        LogSubType, related_name="inspection_parents", on_delete=models.SET_NULL,
        null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.activity_type = LogType.objects.get(
                name="Inspections",
                airport=self.airport
            )
            subtype = LogSubType.objects.create(
                activity_type=self.activity_type,
                name=self.title
            )
            subtype.i18n_id = 'subtype_'+str(subtype.id+1)
            subtype.save(update_fields=['i18n_id'])
            self.activity_subtype = subtype
        super(InspectionParent, self).save(*args, **kwargs)
    
    def __str__(self):
        return "{} - ({})".format(
            self.title, self.airport.code)


class Inspection(Version):
    title = models.CharField(max_length=100)
    icon = models.CharField(max_length=100)
    additionalInfo = models.TextField(blank=True, null=True)
    form = models.ForeignKey(InspectionParent, related_name="versions",
                             on_delete=models.CASCADE)

    def __str__(self):
        return "{} - Version {} ({})".format(
            self.form.title, self.number, self.form.airport.code)

    def save(self, *args, **kwargs):
        from airport.models import Translation
        translations = Translation.objects.filter(airport=self.form.airport)

        for tr in translations:
            tr.updateTranslationMap(self.title, self.schema['fields'])
        super(Inspection, self).save(*args, **kwargs)


# method for updating
@receiver(post_save, sender=InspectionParent,
          dispatch_uid="inspection_default_version")
def create_default_version(sender, instance, created, **kwargs):
    if created:
        version = Inspection()
        version.form = instance
        version.save()


# Form status constants
IN_PROGRESS = 0
COMPLETED = 1

# These are the possible status for a form
STATUS = (
    (IN_PROGRESS, _("In progress")),
    (COMPLETED, _("Completed"))
)


class InspectionAnswer(Answer):
    inspection = models.ForeignKey(
        Inspection,
        related_name="inspections_answer",
        on_delete=models.CASCADE)
    inspection_date = models.DateTimeField()
    status = models.IntegerField(choices=STATUS, default=IN_PROGRESS)
    created_date = models.DateTimeField(auto_now_add=True)
    weather_conditions = JSONField(default=dict)
    inspected_by = models.ForeignKey(
        AerosimpleUser, related_name="inspection_answers",
        on_delete=models.CASCADE
    )

    created_by = models.ForeignKey(
        AerosimpleUser, related_name="answers_created",
        on_delete=models.CASCADE
    )

    inspection_type = models.CharField(max_length=100)
    # calculated property
    issues = models.IntegerField()

    logs = GenericRelation(Log)

    def __str__(self):
        return "{} ({})".format(
            self.inspection.title,
            self.inspection_date
        )

    def create_log_entry(self):
        # Do not create another instance of Log for this object if one
        # already exists
        if not self.logs.exists():
            log = Log()
            log_form = LogForm.objects.get(airport=self.created_by.airport)

            log.form = log_form.versions.get(status=PUBLISHED)
            log.logged_by = self.inspected_by
            log.report_date = self.inspection_date
            log.type = self.inspection.form.activity_type.name
            log.subtype = self.inspection.form.activity_subtype.name
            log.description = self.inspection.title
            log.content_object = self
            log.save()


class Remark(models.Model):
    answer = models.ForeignKey(
        InspectionAnswer, related_name="remarks", on_delete=models.CASCADE)
    field_reference = models.CharField(max_length=50)
    item_reference = models.CharField(max_length=50)
    text = models.TextField()
    image = models.ImageField(upload_to='remarks/', blank=True, null=True)
