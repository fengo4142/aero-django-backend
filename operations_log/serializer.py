from rest_framework import serializers
from operations_log.models import Log, LogVersion
from forms.utils import PUBLISHED
from pulpoforms.forms import Form as PulpoForm
from users.serializers import AerosimpleUserSimpleSerializer
from operations_log.models import LogType, LogSubType
from inspections.models import InspectionAnswer
import logging

logger = logging.getLogger('backend')


class LogSerializer(serializers.ModelSerializer):

    class Meta:
        model = Log
        fields = '__all__'

    def validate(self, data):
        user = self.context['request'].user
        if self.instance:
            form = PulpoForm(self.instance.form.schema)
        else:
            published_version = LogVersion.objects.filter(
                form__airport__id=user.aerosimple_user.airport_id,
                status=PUBLISHED).first()
            form = PulpoForm(published_version.schema)
        result = form.check_answers(data['response'])

        if result['result'] != 'OK':
            raise serializers.ValidationError(result['errors'])

        return data


class LogTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = LogType
        fields = ('id', 'name', 'i18n_id')


class LogSubTypeSerializer(serializers.ModelSerializer):
    activity_type = LogTypeSerializer()

    class Meta:
        model = LogSubType
        fields = ('id', 'name', 'i18n_id', 'activity_type')


class LogListSerializer(serializers.ModelSerializer):
    logged_by = AerosimpleUserSimpleSerializer()
    # type = LogTypeSerializer()
    # subtype = LogSubTypeSerializer()
    source = serializers.SerializerMethodField()

    class Meta:
        model = Log
        fields = ('id', 'type', 'report_date', 'description',
                  'subtype', 'logged_by', 'source', 'response')

    def get_source(self, obj):
        if obj.content_object:
            if isinstance(obj.content_object, InspectionAnswer):
                return {
                    'id': obj.content_object.id,
                    'type': 'inspection'
                }
        return None


class LogVersionSerializer(serializers.ModelSerializer):

    class Meta:
        model = LogVersion
        fields = ('id', 'schema')


class LogDetailSerializer(serializers.ModelSerializer):
    form = LogVersionSerializer()
    logged_by = AerosimpleUserSimpleSerializer()
    # type = LogTypeSerializer()
    # subtype = LogSubTypeSerializer()

    class Meta:
        model = Log
        fields = '__all__'

    def get_schema(self, obj):
        return obj.form.schema


class LogVersionSaveSerializer(serializers.ModelSerializer):

    class Meta:
        model = LogVersion
        fields = '__all__'

    def validate_schema(self, value):
        form = PulpoForm(value)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        if len(value['pages']) > 1:
            raise serializers.ValidationError(
                "A Log Version can't have more than one page"
            )

        for p in value['pages']:
            if len(p['sections']) != 1:
                raise serializers.ValidationError(
                    "A Log Version page must have exactly one section"
                )

        return value
