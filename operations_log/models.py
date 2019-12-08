from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from forms.models import Form, Version, Answer
from users.models import AerosimpleUser


class LogType(models.Model):
    name = models.CharField(max_length=100, null=True)
    # for i18n purposes
    i18n_id = models.CharField(max_length=20, null=True)
    system_generated = models.BooleanField(default=False)
    airport = models.ForeignKey(
        "airport.Airport", related_name="log_types",
        on_delete=models.CASCADE
    )

    def __str__(self):
        return "{} ({})".format(self.name, self.airport.code)


class LogSubType(models.Model):
    name = models.CharField(max_length=100, null=True)
    # for i18n purposes
    i18n_id = models.CharField(max_length=20, null=True)
    activity_type = models.ForeignKey(
          LogType, related_name="subtypes",
          on_delete=models.CASCADE
    )

    def __str__(self):
        return "{} ({})".format(self.name, self.activity_type.airport.code)


class LogForm(Form):
    airport = models.OneToOneField(
        "airport.Airport", related_name="log_form",
        on_delete=models.CASCADE
    )


class LogVersion(Version):
    form = models.ForeignKey(
        LogForm, related_name="versions", on_delete=models.CASCADE)


class Log(Answer):
    form = models.ForeignKey(
        LogVersion,
        related_name="operation_logs",
        on_delete=models.CASCADE)

    logged_by = models.ForeignKey(
        AerosimpleUser, related_name="operations_logs",
        on_delete=models.SET_NULL,
        null=True
    )
    report_date = models.DateTimeField()

    # type = models.ForeignKey(
    #     LogType, related_name="operations_logs",
    #     on_delete=models.SET_NULL,
    #     null=True
    # )
    # subtype = models.ForeignKey(
    #     LogSubType, related_name="operations_logs",
    #     on_delete=models.SET_NULL,
    #     null=True
    # )
    type = models.TextField(blank=True, null=True)
    subtype = models.TextField(blank=True, null=True)
    description = models.TextField()

    # for generic relationships
    content_type = models.ForeignKey(ContentType, blank=True, null=True, on_delete=models.SET_NULL)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
