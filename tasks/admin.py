from django.contrib import admin

from tasks.models import Task, TaskOccurrence

admin.site.register(Task)
admin.site.register(TaskOccurrence)
