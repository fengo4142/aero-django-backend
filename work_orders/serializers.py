from rest_framework_gis import serializers
from rest_framework.serializers import Field
from rest_framework.serializers import SerializerMethodField, ValidationError
from django.utils.translation import ugettext_lazy as _

from pulpoforms.forms import Form as PulpoForm

from work_orders.models import WorkOrder, WorkOrderForm, WorkOrderImage, \
    MaintenanceSchema, OperationsSchema, WorkOrderSchema, Maintenance, \
    MaintenanceImage, Operations, OperationsImage, MaintenanceForm, \
    OperationsForm

from users.serializers import AerosimpleUserDisplaySerializer, \
    AerosimpleUserSimpleSerializer, AerosimpleUserAssignmentSerializer
from users.models import AerosimpleUser

from airport.serializers import AssetSerializer
from forms.utils import PUBLISHED
import json
import logging
logger = logging.getLogger('backend')


class MultipartM2MField(Field):
    def to_representation(self, obj):
        return AssetSerializer(obj.all(), many=True).data

    def to_internal_value(self, data):
        return json.loads(data) if data else None


# ****************************************************************
# ******************** WORK ORDER SERIALIZERS ********************
# ****************************************************************
class WorkOrderSerializer(serializers.ModelSerializer):
    location = SerializerMethodField()
    assets = MultipartM2MField(allow_null=True, required=False)

    class Meta:
        model = WorkOrder
        exclude = ("status",)
        geo_field = 'location'

    def get_location(self, obj):
        if obj.location:
            return {'coordinates': [{'lon': obj.location.x, 'lat': obj.location.y}]}
        else:
            return None

    def validate(self, data):
        user = self.context['request'].user
        published_version = WorkOrderSchema.objects.filter(
            form__airport__id=user.aerosimple_user.airport_id,
            status=PUBLISHED).first()

        form = PulpoForm(published_version.schema)
        result = form.check_answers(data['response'])

        if result['result'] != 'OK':
            raise ValidationError(result.errors)

        return data


class WorkOrderListSerializer(serializers.ModelSerializer):
    location = SerializerMethodField()
    assets = SerializerMethodField()

    class Meta:
        model = WorkOrder
        fields = ('id', 'category', 'status', 'report_date', 'priority',
                  'location', 'subcategory', 'assets')
           
    def get_location(self, obj):
        if obj.location:
            return {'coordinates': [{'lon': obj.location.x, 'lat': obj.location.y}]}
        else:
            return None

    def get_assets(self, obj):
        res = []
        for asset in obj.assets.all():
            res.append({'coordinates': [{
                'lon': asset.geometry.x,
                'lat': asset.geometry.y
            }]})
        return res


class WorkOrderIDListSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkOrder
        fields = ('id', 'category_id', 'subcategory_id', 'problem_description',
                  'priority', 'status', 'notams')


class WorkOrderFormSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkOrderForm
        fields = "__all__"


class WorkOrderImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkOrderImage
        fields = "__all__"


class WorkOrderSchemaSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkOrderSchema
        fields = ('id', 'schema')


class WorkOrderSchemaSaveSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkOrderSchema
        fields = '__all__'

    def validate_schema(self, value):
        form = PulpoForm(value)
        if not form.is_valid():
            raise ValidationError(form.errors)

        if len(value['pages']) > 1:
            raise ValidationError(
                "A Work Order Schema can't have more than one page"
            )

        for p in value['pages']:
            if len(p['sections']) != 1:
                raise ValidationError(
                    "A Work Order Schema page must have exactly one section"
                )

        return value


class WorkOrderDetailSerializer(serializers.ModelSerializer):
    location = SerializerMethodField()
    assets = SerializerMethodField()
    priority = SerializerMethodField()
    answer_schema = SerializerMethodField()
    maintenance_answer = SerializerMethodField()
    operations_answer = SerializerMethodField()
    logged_by = AerosimpleUserDisplaySerializer()
    images = WorkOrderImageSerializer(many=True)

    class Meta:
        model = WorkOrder
        exclude = ("date", )

    def get_location(self, obj):
        if obj.location:
            return {'coordinates': [{'lon': obj.location.x, 'lat': obj.location.y}]}
        else:
            return None

    def get_assets(self, obj):
        res = []
        for asset in obj.assets.all():
            res.append({'coordinates': [{
                'lon': asset.geometry.x,
                'lat': asset.geometry.y
            }]})
        return res

    def get_priority(self, obj):
        return obj.get_priority_display()

    def get_answer_schema(self, obj):
        return obj.form.schema

    def get_maintenance_answer(self, obj):
        maintenance = obj.maintenance_answer
        if maintenance.exists():
            return MaintenanceDetailSerializer(maintenance.latest('id')).data
        return None

    def get_operations_answer(self, obj):
        operations = obj.operations_answer
        if operations.exists():
            return OperationsDetailSerializer(operations.latest('id')).data
        return None


# ****************************************************************
# ******************* MAINTENANCE SERIALIZERS ********************
# ****************************************************************
class MaintenanceFormSerializer(serializers.ModelSerializer):

    class Meta:
        model = MaintenanceForm
        fields = '__all__'


class MaintenanceSchemaSerializer(serializers.ModelSerializer):
    assignment = SerializerMethodField()

    class Meta:
        model = MaintenanceSchema
        fields = ('id', 'schema', 'assignment')

    def get_assignment(self, obj):
        return {
            'role': getattr(obj.form.assigned_role, 'pk', None),
            'users': AerosimpleUserSimpleSerializer(
                obj.form.assigned_users.all(), many=True).data
        }


class MaintenanceSchemaSaveSerializer(serializers.ModelSerializer):

    class Meta:
        model = MaintenanceSchema
        fields = '__all__'

    def validate_schema(self, value):
        form = PulpoForm(value)
        if not form.is_valid():
            raise ValidationError(form.errors)

        if len(value['pages']) > 1:
            raise ValidationError(
                "A Maintenance Schema can't have more than one page"
            )

        for p in value['pages']:
            if len(p['sections']) != 1:
                raise ValidationError(
                    "A Operations Schema page must have exactly one section"
                )

        return value


class MaintenanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Maintenance
        fields = '__all__'

    def validate(self, data):
        user = self.context['request'].user
        published_version = MaintenanceSchema.objects.filter(
            form__work_order__airport__id=user.aerosimple_user.airport_id,
            status=PUBLISHED).first()

        form = PulpoForm(published_version.schema)
        result = form.check_answers(data['response'])

        if result['result'] != 'OK':
            raise ValidationError(result.errors)

        return data


class MaintenanceImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = MaintenanceImage
        fields = "__all__"


class MaintenanceDetailSerializer(serializers.ModelSerializer):
    completed_by = AerosimpleUserDisplaySerializer()
    answer_schema = SerializerMethodField()
    images = MaintenanceImageSerializer(many=True)

    class Meta:
        model = Maintenance
        fields = "__all__"

    def get_answer_schema(self, obj):
        return obj.version.schema


# ****************************************************************
# ******************* OPERATIONS SERIALIZERS *********************
# ****************************************************************
class OperationsFormSerializer(serializers.ModelSerializer):

    class Meta:
        model = OperationsForm
        fields = '__all__'


class OperationsSchemaSerializer(serializers.ModelSerializer):
    assignment = SerializerMethodField()

    class Meta:
        model = OperationsSchema
        fields = ('id', 'schema', 'assignment')

    def get_assignment(self, obj):
        return {
            'role': getattr(obj.form.assigned_role, 'pk', None),
            'users': AerosimpleUserSimpleSerializer(
                obj.form.assigned_users.all(), many=True).data
        }

    def validate(self, data):
        user = self.context['request'].user
        published_version = OperationsSchema.objects.filter(
            form__work_order__airport__id=user.aerosimple_user.airport_id,
            status=PUBLISHED).first()

        form = PulpoForm(published_version.schema)
        result = form.check_answers(data['response'])

        if result['result'] != 'OK':
            raise ValidationError(result.errors)

        return data


class OperationsSchemaSaveSerializer(serializers.ModelSerializer):

    class Meta:
        model = OperationsSchema
        fields = '__all__'

    def validate_schema(self, value):
        form = PulpoForm(value)
        if not form.is_valid():
            raise ValidationError(form.errors)

        if len(value['pages']) > 1:
            raise ValidationError(
                "A Operations Schema can't have more than one page"
            )

        for p in value['pages']:
            if len(p['sections']) != 1:
                raise ValidationError(
                    "A Operations Schema page must have exactly one section"
                )

        return value


class OperationsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Operations
        fields = '__all__'


class OperationsImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = OperationsImage
        fields = "__all__"


class OperationsDetailSerializer(serializers.ModelSerializer):
    completed_by = AerosimpleUserDisplaySerializer()
    answer_schema = SerializerMethodField()
    images = OperationsImageSerializer(many=True)

    class Meta:
        model = Operations
        fields = "__all__"

    def get_answer_schema(self, obj):
        return obj.version.schema


class MobileWorkOrderSerializer(serializers.ModelSerializer):
    location = SerializerMethodField()
    images = SerializerMethodField()
    created_by = SerializerMethodField()
    asset = SerializerMethodField()
    report_date = SerializerMethodField()

    class Meta:
        model = WorkOrder
        fields = ('id', 'category', 'status', 'report_date', 'priority', 'images',
                  'location', 'subcategory', 'created_by', 'asset', 'problem_description')

    def get_report_date(self, obj):
        return obj.report_date.timestamp()

    def get_location(self, obj):
        if obj.location:
            return [{
                'lon': obj.location.x,
                'lat': obj.location.y
            }]
        elif len(obj.assets.all()) > 0:
            return {'coordinates': [{'lon': obj.assets.first().geometry.x, 'lat': obj.assets.first().geometry.y}]}
        else:
            return [{
                'lon': obj.form.form.airport.location.x,
                'lat': obj.form.form.airport.location.y
            }]

    def get_created_by(self, obj):
        if obj.logged_by:
            return obj.logged_by.user.id

    def get_asset(self, obj):
        res = []
        for asset in obj.assets.all():
            res.append(asset.id)
        return res

    def get_images(self, obj):
        res = []
        images = WorkOrderImage.objects.filter(work_order=obj)
        for image in images:
            res.append({
                'id': 'workorder_' + str(image.id)
            })
        return res

# ****************************************************************
# *************** WORKORDERS SERIALIZERS WEB API *****************
# ****************************************************************


class WorkOrderWebSerializer(serializers.ModelSerializer):
    # location = SerializerMethodField()
    assets = MultipartM2MField(allow_null=True, required=False)

    class Meta:
        model = WorkOrder
        exclude = ("status",)
        geo_field = 'location'

    def get_location(self, obj):
        if obj.location:
            return [{
                'lon': obj.location.x,
                'lat': obj.location.y
            }]
        else:
            return None

    def validate(self, data):
        user = self.context['request'].user
        published_version = WorkOrderSchema.objects.filter(
            form__airport__id=user.aerosimple_user.airport_id,
            status=PUBLISHED).first()

        form = PulpoForm(published_version.schema)
        result = form.check_answers(data['response'])

        if result['result'] != 'OK':
            raise ValidationError(result.errors)
        if isinstance(data['location'], list):
            data['location'] = data['location'][0]
        return data


class WorkOrderListWebSerializer(serializers.ModelSerializer):
    location = SerializerMethodField()
    assets = SerializerMethodField()
    # logger.info(location)

    class Meta:
        model = WorkOrder
        fields = ('id', 'category', 'status', 'report_date', 'priority',
                  'location', 'subcategory', 'assets')

    def get_location(self, obj):
        if obj.location:
            return [{
                'lon': obj.location.x,
                'lat': obj.location.y
            }]
        else:
            if len(obj.assets.all()) > 0:
                asset = obj.assets.first()
                return [{
                    'lon': asset.geometry.x,
                    'lat': asset.geometry.y
                }]
            else:
                return None

    def get_assets(self, obj):
        res = []
        for asset in obj.assets.all():
            res.append({
                'lon': asset.geometry.x,
                'lat': asset.geometry.y
            })
        return res


class WorkOrderDetailWebSerializer(serializers.ModelSerializer):
    location = SerializerMethodField()
    assets = SerializerMethodField()
    priority = SerializerMethodField()
    answer_schema = SerializerMethodField()
    maintenance_answer = SerializerMethodField()
    operations_answer = SerializerMethodField()
    logged_by = AerosimpleUserDisplaySerializer()
    images = WorkOrderImageSerializer(many=True)

    class Meta:
        model = WorkOrder
        exclude = ("date", )

    def get_location(self, obj):
        if obj.location:
            return [{
                'lon': obj.location.x,
                'lat': obj.location.y
            }]
        else:
            if len(obj.assets.all()) > 0:
                asset = obj.assets.first()
                return [{
                    'lon': asset.geometry.x,
                    'lat': asset.geometry.y
                }]
            else:
                return None

    def get_assets(self, obj):
        res = []
        for asset in obj.assets.all():
            res.append({
                'id': asset.id,
                'name': asset.name,
                'lon': asset.geometry.x,
                'lat': asset.geometry.y
            })
        return res

    def get_priority(self, obj):
        return obj.get_priority_display()

    def get_answer_schema(self, obj):
        return obj.form.schema

    def get_maintenance_answer(self, obj):
        maintenance = obj.maintenance_answer
        if maintenance.exists():
            return MaintenanceDetailSerializer(maintenance.latest('id')).data
        return None

    def get_operations_answer(self, obj):
        operations = obj.operations_answer
        if operations.exists():
            return OperationsDetailSerializer(operations.latest('id')).data
        return None


class MaintenanceSchemaAssignmentSerializer(serializers.ModelSerializer):
    assignment = SerializerMethodField()

    class Meta:
        model = MaintenanceSchema
        fields = ('id', 'schema', 'assignment')

    def get_assignment(self, obj):
        return {
            'role': AerosimpleUserAssignmentSerializer(
                AerosimpleUser.objects.filter(roles=obj.form.assigned_role), many=True
            ).data,
            'users': AerosimpleUserAssignmentSerializer(
                obj.form.assigned_users.all(), many=True).data
        }


class OperationsSchemaAssignmentSerializer(serializers.ModelSerializer):
    assignment = SerializerMethodField()

    class Meta:
        model = OperationsSchema
        fields = ('id', 'schema', 'assignment')

    def get_assignment(self, obj):
        return {
            'role': AerosimpleUserAssignmentSerializer(
                AerosimpleUser.objects.filter(roles=obj.form.assigned_role), many=True
            ).data,
            'users': AerosimpleUserAssignmentSerializer(
                obj.form.assigned_users.all(), many=True).data
        }
