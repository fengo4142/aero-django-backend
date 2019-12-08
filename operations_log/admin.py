from django.contrib import admin
from operations_log.models import (
  Log, LogType, LogVersion, LogForm, LogSubType
)

admin.site.register(Log)
admin.site.register(LogType)
admin.site.register(LogVersion)
admin.site.register(LogForm)
admin.site.register(LogSubType)
