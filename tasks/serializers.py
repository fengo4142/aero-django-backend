from rest_framework_gis import serializers
from tasks.models import Task, TaskOccurrence
from users.serializers import (AerosimpleUserDisplaySerializer,
                               RoleSimpleSerializer)
from django.utils.translation import ugettext_lazy as _
from rest_framework.serializers import ValidationError, SerializerMethodField
from schedule.models import Occurrence, Rule
from inspections.serializers import InspectionListSerializer
import logging

logger = logging.getLogger('backend')


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = '__all__'


class TaskSerializer(serializers.ModelSerializer):
    assigned_user = AerosimpleUserDisplaySerializer()
    assigned_role = RoleSimpleSerializer()
    requested_by = SerializerMethodField()
    inspection = SerializerMethodField()
    rule = RuleSerializer()

    class Meta:
        model = Task
        fields = '__all__'

    def get_requested_by(self, obj):
        return AerosimpleUserDisplaySerializer(obj.creator.aerosimple_user).data

    def get_inspection(self, obj):
        if hasattr(obj, 'inspection'):
            return InspectionListSerializer(obj.inspection).data
        return None

    def validate(self, data):

        if 'assigned_user' in data and 'assigned_role' in data:
            return ValidationError(
                _("Task form cannot have assigned both role and user.")
            )

        if 'assigned_user' not in data and 'assigned_role' not in data:
            return ValidationError(
                _('Maintenance form must have an assigned role or users.')
            )
        return data


class TaskOccurrenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskOccurrence
        fields = '__all__'


class OccurrenceSerializer(serializers.ModelSerializer):
    event = TaskSerializer(source='event.task')
    task_occurrences = SerializerMethodField()

    class Meta:
        model = Occurrence
        fields = '__all__'

    def get_task_occurrences(self, obj):
        to = TaskOccurrence.objects.filter(occurrence__id=obj.id)
        if to.exists():
            return TaskOccurrenceSerializer(to.first()).data
        return None
