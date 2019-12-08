from django.contrib.gis import admin
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from work_orders.models import WorkOrderForm, MaintenanceForm, \
  OperationsForm, Maintenance, Operations, WorkOrder, WorkOrderImage


class MaintenanceSchemaForm(forms.ModelForm):
    class Meta:
        model = MaintenanceForm
        fields = '__all__'

    def clean(self):
        """
        Checks that role and users assigned are mutually exclusive
        """
        assigned_role = self.cleaned_data.get('assigned_role')
        assigned_users = self.cleaned_data.get('assigned_users')
        if assigned_role and assigned_users:
            raise ValidationError(
                _('Maintenance form cannot have assigned both role and users.')
            )
        elif (not assigned_role and not assigned_users):
            raise ValidationError(
                _('Maintenance form must have an assigned role or users.')
            )
        return self.cleaned_data


class MaintenanceFormInline(admin.TabularInline):
    model = MaintenanceForm
    form = MaintenanceSchemaForm


class OperationsFormInline(admin.TabularInline):
    model = OperationsForm


class WorkOrderFormAdmin(admin.ModelAdmin):
    inlines = [MaintenanceFormInline, OperationsFormInline]


class WorkOrderImageInline(admin.TabularInline):
    model = WorkOrderImage
    extra = 1


class WorkOrderAdmin(admin.ModelAdmin):
    inlines = [WorkOrderImageInline, ]




admin.site.register(WorkOrderForm, WorkOrderFormAdmin)
admin.site.register(WorkOrder, WorkOrderAdmin)
admin.site.register(Operations)
admin.site.register(Maintenance)
