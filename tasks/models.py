from django.db import models
from django.utils.translation import ugettext_lazy as _
from schedule.models import Event, Occurrence


class Task(Event):
    due_date = models.DateField(blank=True, null=True)
    due_time = models.TimeField(blank=True, null=True)
    attached = models.FileField(upload_to='tasks/', blank=True, null=True)
    label = models.CharField(max_length=50, blank=True, null=True)
    assigned_user = models.ForeignKey(
        'users.AerosimpleUser', related_name='assigned_tasks',
        on_delete=models.CASCADE, null=True, blank=True)
    assigned_role = models.ForeignKey(
        'users.Role', related_name="assigned_tasks", on_delete=models.CASCADE,
        null=True, blank=True
    )
    airport = models.ForeignKey(
        'airport.Airport', related_name='tasks', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return "{}".format(self.title)


class TaskOccurrence(models.Model):
    completed = models.BooleanField(default=False)
    task = models.ForeignKey(
        Task, related_name="task_occurrences", on_delete=models.CASCADE
    )
    occurrence = models.OneToOneField(
        Occurrence, related_name="task_occurrences", on_delete=models.CASCADE
    )
