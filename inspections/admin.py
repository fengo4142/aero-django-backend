from django.contrib.gis import admin

from inspections.models import (
    InspectionParent, Inspection, InspectionAnswer, Remark,
    InspectionTemplateVersion, InspectionTemplateForm, AirportTemplatesRelation
)


admin.site.register(InspectionParent)
admin.site.register(Inspection)
admin.site.register(InspectionTemplateForm)
admin.site.register(InspectionTemplateVersion)
admin.site.register(InspectionAnswer)
admin.site.register(Remark)
admin.site.register(AirportTemplatesRelation)
