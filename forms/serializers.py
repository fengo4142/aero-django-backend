from rest_framework import serializers
from pulpoforms.forms import Form as PulpoForm

from forms.models import Form, Version
from forms.utils import DRAFT, PUBLISHED
import logging

logger = logging.getLogger('backend')


class FormSerializer(serializers.Serializer):
    title = serializers.CharField()


class VersionSerializer(serializers.Serializer):
    status = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    number = serializers.IntegerField()
    schema = serializers.JSONField()
    publish_date = serializers.DateTimeField()
    expiry_date = serializers.DateTimeField()

    def get_status(self, obj):
        return obj.get_status_display()

    def get_title(self, obj):
        return obj.form.title


class VersionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Version
        exclude = ('number', 'status', 'publish_date', 'expiry_date')

    def validate_schema(self, value):
        form = PulpoForm(value)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)
        return value

    def validate(self, data):
        previous = Version.objects.filter(form=data['form'], status=DRAFT)
        if previous.exists():
            raise serializers.ValidationError(
                "There is a previous draft pending for this Form"
            )
        return data


class VersionUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Version
        exclude = ('form', 'number', 'status', 'publish_date', 'expiry_date')

    def validate_schema(self, value):
        form = PulpoForm(value)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)
        return value

    def validate(self, data):
        if self.instance.status != DRAFT:
            raise serializers.ValidationError(
                "You cannot edit a version that has already been published"
            )
        return data


# class FormTemplateSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = FormTemplate
#         fields = '__all__'


class AnswerSerializer(serializers.Serializer):
    status = serializers.IntegerField()
    schema = serializers.JSONField()
    response = serializers.JSONField()
    
    def validate(self, data):
        """Check that the answers are appropiate for the version."""
        if data['status'] != PUBLISHED:
            raise serializers.ValidationError(
                "Can not submit a response for an unpublished version.")

       
        form = PulpoForm(data['schema'])
        result = form.check_answers(data['response'])
        if result['result'] != 'OK':
            raise serializers.ValidationError(result['errors'])

        return data

class MobileAnswerSerializer(serializers.Serializer):
    status = serializers.IntegerField()
    schema = serializers.JSONField()
    response = serializers.JSONField()

    def validate(self, data):
        """Check that the answers are appropiate for the version."""
        if data['status'] != PUBLISHED:
            raise serializers.ValidationError(
                "Can not submit a response for an unpublished version.")

        form = PulpoForm(data['schema'])
        result = form.check_answers(data['response'])
        if result['result'] != 'OK':
            raise serializers.ValidationError(result['errors'])

        return data

# class DetailAnswerSerializer(serializers.ModelSerializer):
#     version = VersionSerializer()

#     class Meta:
#         model = Answer
#         fields = '__all__'


class DetailVersionSerializer(serializers.Serializer):

    schema = serializers.JSONField()
    title = serializers.SerializerMethodField()
    number = serializers.IntegerField()
    publish_date = serializers.DateTimeField()

    def get_status(self, obj):
        return obj.get_status_display()

    def get_title(self, obj):
        return obj.form.title



class MobileDetailVersionSerializer(serializers.Serializer):

    schema = serializers.JSONField()

    def get_status(self, obj):
        return obj.get_status_display()

    def get_name(self, obj):
        return obj.form.title
