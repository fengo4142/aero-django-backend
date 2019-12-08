import logging

from rest_framework_gis import serializers
from rest_framework.serializers import JSONField, IntegerField, \
    ValidationError, SerializerMethodField

from inspections.models import Inspection, InspectionParent, InspectionAnswer,\
    Remark, InspectionTemplateVersion, InspectionTemplateForm, \
    AirportTemplatesRelation
from pulpoforms.forms import Form as PulpoForm
from forms.utils import EXPIRED, PUBLISHED
from inspections.models import IN_PROGRESS
from forms.serializers import VersionSerializer, MobileDetailVersionSerializer
from users.serializers import AerosimpleUserSimpleSerializer
from work_orders.models import WorkOrder, COMPLETED
from work_orders.serializers import WorkOrderIDListSerializer
from inspections.utils import build_schema

logger = logging.getLogger('backend.inspections.serializers')


class InspectionTemplateDetailSerializer(serializers.ModelSerializer):
    schema = SerializerMethodField()
    new_version_available = SerializerMethodField()
    selected_version_id = SerializerMethodField()
    title = SerializerMethodField()

    class Meta:
        model = InspectionTemplateForm
        fields = '__all__'

    def get_title(self, obj):
        airport = self.context['request'].user.aerosimple_user.airport_id

        relation = AirportTemplatesRelation.objects.get(
            airport=airport, form=obj
        )
        return obj.versions.get(number=relation.selected_version).title

    def get_schema(self, obj):
        airport = self.context['request'].user.aerosimple_user.airport_id

        relation = AirportTemplatesRelation.objects.get(
            airport=airport, form=obj
        )
        return obj.versions.get(number=relation.selected_version).schema

    def get_new_version_available(self, obj):
        airport = self.context['request'].user.aerosimple_user.airport_id

        relation = AirportTemplatesRelation.objects.get(
            airport=airport, form=obj
        )
        last_version = obj.versions.latest('number').number
        return last_version > relation.selected_version

    def get_selected_version_id(self, obj):
        airport = self.context['request'].user.aerosimple_user.airport_id

        relation = AirportTemplatesRelation.objects.get(
            airport=airport, form=obj
        )
        return obj.versions.get(number=relation.selected_version).id


class InspectionTemplateVersionDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = InspectionTemplateVersion
        fields = '__all__'


class InspectionEditSerializer(serializers.ModelSerializer):
    schema = JSONField(write_only=True, required=False)
    status = IntegerField(write_only=True, required=False)

    class Meta:
        model = InspectionParent
        exclude = ('created_by', 'airport')

    def validate_schema(self, value):
        form = PulpoForm(value)
        if not form.is_valid():
            raise ValidationError(form.errors)

        if len(value['pages']) != 2:
            raise ValidationError(
                "An Inspection schema must have exactly two pages"
            )

        for p in value['pages']:
            if len(p['sections']) != 1:
                raise ValidationError(
                    "An Inspection page must have exactly one section"
                )

        if len(value['sections'][1]['fields']) == 0:
            raise ValidationError(
                    "The inspection checklist must contain at least one item"
                )

        for f in value['sections'][1]['fields']:
            val = filter(
                lambda x: (x['id'] == f and x['type'] == 'inspection'),
                value['fields']
            )

            if len(list(val)) == 0:
                raise ValidationError(
                    "All fields in second page must be of type inspection"
                )

        return value

    def create(self, validated_data):
        i = InspectionParent()
        i.title = validated_data['title']
        i.icon = validated_data['icon']

        if 'template' in validated_data:
            i.template = validated_data['template']
            i.airport_changes = validated_data['airport_changes']

        if 'additionalInfo' in validated_data:
            i.additionalInfo = validated_data['additionalInfo']

        i.created_by = self.context['request'].user.aerosimple_user
        i.airport = self.context['request'].user.aerosimple_user.airport
        i.task = validated_data['task']
        i.save()

        v = i.versions.first()
        schema = {}
        if 'template' in validated_data:
            template = validated_data['template']
            changes = validated_data['airport_changes']
            schema = build_schema(changes, template)
        else:
            schema = validated_data['schema']

        v.title = i.title
        v.icon = i.icon
        v.schema = schema
        v.additionalInfo = i.additionalInfo
        v.status = validated_data['status']
        v.save()

        return i


class InspectionSchemaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Inspection
        fields = ("id","form_id", "schema")


class InspectionDetailSerializer(serializers.ModelSerializer):
    form = SerializerMethodField()
    open_workorders = SerializerMethodField()

    class Meta:
        model = Inspection
        fields = '__all__'

    def get_form(self, obj):    
        v = VersionSerializer(obj.versions.get(status=PUBLISHED))
        return v.data

    def get_open_workorders(self, obj):
        wos = []
        if hasattr(obj, 'associated_airport'):
            wos = WorkOrder.objects.filter(
                form__form__airport__id=obj.airport.id
            ).exclude(status=COMPLETED)

        return WorkOrderIDListSerializer(wos, many=True).data


class InspectionVersionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Inspection
        fields = ('title', 'icon', 'additionalInfo')


class InspectionDetailEditSerializer(serializers.ModelSerializer):
    form = SerializerMethodField()
    task = SerializerMethodField()
    template = InspectionTemplateVersionDetailSerializer()
    new_version_available = SerializerMethodField()

    class Meta:
        model = InspectionParent
        fields = '__all__'

    def get_task(self, obj):
        from tasks.serializers import TaskSerializer
        return TaskSerializer(obj.task).data

    def get_form(self, obj):
        version = obj.versions.latest('id')
        serialized_version = VersionSerializer(version).data
        serialized_version.update(InspectionVersionSerializer(version).data)
        return serialized_version

    def get_new_version_available(self, obj):
        if obj.template is not None:
            latest_template = obj.template.form.versions.latest('number').number
            current_template = obj.template.number

            return latest_template > current_template
        else:
            return False


class InspectionListSerializer(serializers.ModelSerializer):
    version_status = SerializerMethodField()
    answer_status = SerializerMethodField()
    class Meta:
        model = InspectionParent
        fields = ('id', 'title', 'icon', 'airport_id', 'version_status', 'answer_status')

    def get_version_status(self, obj):
        return obj.versions.exclude(status=EXPIRED).values_list(
            'status', flat=True).distinct()
    def get_answer_status(self, obj):
        answer = InspectionAnswer.objects.filter(inspection_id__form_id = obj.id).last()
        if(answer):
            return answer.status
        return ""

class InspectionAnswerSerializer(serializers.ModelSerializer):
    inspected_by = AerosimpleUserSimpleSerializer()
    inspection = SerializerMethodField()

    class Meta:
        model = InspectionAnswer
        fields = '__all__'

    def get_inspection(self, obj):
        return obj.inspection.title


class InspectionAnswerDetailSerializer(serializers.ModelSerializer):
    inspected_by = AerosimpleUserSimpleSerializer()
    version = InspectionSchemaSerializer(source="inspection")
    inspection = SerializerMethodField()
    icon = SerializerMethodField()
    remarks = SerializerMethodField()
    open_workorders = SerializerMethodField()

    class Meta:
        model = InspectionAnswer
        fields = '__all__'

    def get_inspection(self, obj):
        return obj.inspection.title
    def get_icon(self,obj):
        return obj.inspection.icon

    def get_remarks(self, obj):
        return RemarkSerializer(obj.remarks, many=True).data

    def get_open_workorders(self, obj):
        wos = []
        if hasattr(obj.inspection.form, 'associated_airport'):
            wos = WorkOrder.objects.filter(
                form__form__airport__id=obj.inspection.form.airport.id
            ).exclude(status=COMPLETED)

        return WorkOrderIDListSerializer(wos, many=True).data


class RemarkSerializer(serializers.ModelSerializer):

    class Meta:
        model = Remark
        fields = '__all__'

    def validate(self, value):
        """
            Check if the field is present in the schema.
        """
        # Checking if inspection exists
        i = value['answer']

        # Checking if field reference exists in schema
        v = i.inspection
        ids = [c['id'] for c in v.schema['fields']]

        if value['field_reference'] not in ids:
            raise ValidationError({
                'field_reference':
                    "'{}' is not a valid field id in the version schema"
                    .format(value['field_reference']),
             })

        # Checking if field referenced is an inspection field.
        index = ids.index(value['field_reference'])

        if v.schema['fields'][index]['type'] != 'inspection':
            raise ValidationError({
                'field_reference':
                    "field '{}' must be of type inspection"
                    .format(value['field_reference']),
             })

        # Checking if item referenced present in the schema.
        checklist_ids = [c['key'] for c in
                         v.schema['fields'][index]['checklist']]

        if value['item_reference'] not in checklist_ids:
            raise ValidationError({
                'item_reference':
                    "'{}' is not a valid checklist item for that inspection"
                    .format(value['item_reference']),
             })

        return value


class InspectionTemplateListSerializer(serializers.ModelSerializer):

    class Meta:
        model = InspectionTemplateForm
        fields = ('id', 'title',)



class InspectionTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = InspectionParent
        fields = ('icon','id','title')



class MobileInspectionListSerializer(serializers.ModelSerializer):

                
    additionalInfo = SerializerMethodField()
    form = SerializerMethodField()

    class Meta:
        model = InspectionParent
        fields = ('additionalInfo','form')

    def get_form(self, obj):
        
        try:
            version = obj.versions.get(status=PUBLISHED)
        except:
            version = obj.versions.latest('id')
        serialized_version = MobileDetailVersionSerializer(version).data
        return serialized_version

    def get_additionalInfo(self, obj):
        return None if obj.template is None else obj.template.additionalInfo


class MobileInspectionDetailSerializer(serializers.ModelSerializer):
    inspected_by = SerializerMethodField()
    created_by = SerializerMethodField()
    title = SerializerMethodField()
    date = SerializerMethodField()
    type = SerializerMethodField()
    form = SerializerMethodField()
    inspection_type = SerializerMethodField()

    class Meta:
        model = InspectionAnswer
        fields = ('id','inspected_by','inspection_type','issues','created_by','title','date','type','form')

    def get_inspected_by(self, obj):
        return ({"id":obj.inspected_by.id})

    def get_created_by(self, obj):
        return ({"id":obj.created_by.id})

    def get_title(self, obj):
        return obj.inspection.title

    def get_date(self, obj):
        return obj.created_date.timestamp()

    def get_type(self, obj):
        return obj.inspection_type

    def read_inspection_answer(self, obj, field_id):
        ins_answer = obj.response
        
        answer = ''
        if ins_answer:            
            for key, val in ins_answer.items():
                if isinstance(val,dict) and field_id in val:
                    answer = val[field_id]
                    if answer == True:
                        answer = "1"
                    else:
                        answer = "2"
                elif key == field_id:
                    answer = val
                       
        return answer

    def get_form(self, obj):
        schema = obj.inspection.schema
        inspection_list = []
        sort_order = 1
        for field in schema['fields']:    
            field_dict = {}        
            if field['type'] == 'inspection':
                field_dict['sortorder'] = sort_order
                field_dict['type'] = 'section'
                field_dict['name'] = field['title']

                check_list = field['checklist']
                for fld_list in check_list:
                    field_obj = {
                        "id": fld_list['key'], 
                        "type":"inspectionBoolean", 
                        "name": fld_list['value'],
                        "indent": 1,
                        "options": [],
                        "value": self.read_inspection_answer(obj, fld_list['key'])
                    }
                    
                    options = field['status_options']
                    option_id = 1
                    for key, val in options.items():
                        if key.lower() in ['pass', 'success', 'satisfactory', 'yes', 'true', 'ok', 'good', 'positive']:
                            field_obj['options'].append({"id": str(option_id), "value": key, "positive": True})
                        else:
                            field_obj['options'].append({"id": str(option_id), "value": key})
                        option_id = option_id + 1

                    if 'fields' not in field_dict:
                        field_dict['fields'] = []

                    field_dict['fields'].append(field_obj)
                
                sort_order = sort_order+1            
                inspection_list.append(field_dict.copy())
            else:
                normal_field_obj = {
                    "id": field["id"],
                    "name": field["title"],
                    "type": field["type"],
                    "required": field['required'],
                    "value":self.read_inspection_answer(obj, field["id"])
                }
                if field["type"] in ['select','multiselect']:
                    if 'values' in field:
                        values = field['values']
                        normal_field_obj['choices'] = []
                        if values:
                            for val in values:
                                normal_field_obj['choices'].append({"id": val['key'], "value": val['value']})
                inspection_list.append(normal_field_obj)

        weather = obj.weather_conditions
        if weather:
            weather_field_obj = {
                "id": 'weather',
                "name": 'Weather',
                "type": 'string',
                "required": True,
                "value": ''
            }
            if 'title' in weather:
                weather_field_obj['value'] = weather['title']

            inspection_list.append(weather_field_obj)

        return ({"form":{"mobile_schema":{"version":str(obj.inspection.number),\
            "fields":inspection_list}}})

    def get_inspection_type(self, obj):
        return ({"id":obj.inspection.form.id})


class MobileInspectionDetailEditSerializer(serializers.ModelSerializer):
    
    form = SerializerMethodField()

    class Meta:
        model = InspectionParent
        fields = ['form']
    
    def get_form(self, obj):
        version = obj.versions.latest('id')
        serialized_version = VersionSerializer(version).data
        return serialized_version


class MobileInspectionsDetailSerializer(serializers.ModelSerializer):
    form = SerializerMethodField()
    open_workorders = SerializerMethodField()

    class Meta:
        model = Inspection
        fields = '__all__'

    def get_form(self, obj):    
        parent = InspectionParent.objects.get(id = obj.form_id)
        v = VersionSerializer(parent.versions.get(status=PUBLISHED))
        return v.data

    def get_open_workorders(self, obj):
        wos = []
        if hasattr(obj, 'associated_airport'):
            wos = WorkOrder.objects.filter(
                form__form__airport__id=obj.airport.id
            ).exclude(status=COMPLETED)

        return WorkOrderIDListSerializer(wos, many=True).data



class MobileInspectionsSerializer(serializers.ModelSerializer):
    date = SerializerMethodField()
    form = SerializerMethodField()
    
    class Meta:
        model = Inspection
        fields = ('id','title', 'icon','date','form','form_id')


    def get_date(self, obj):
        return int(obj.publish_date.timestamp()) if obj.publish_date else None


    def get_form(self, obj):
        schema = obj.schema
        inspection_list = []
        sort_order = 1
        for field in schema['fields']:    
            field_dict = {}        
            if field['type'] == 'inspection':
                field_dict['sortorder'] = sort_order
                field_dict['type'] = 'section'
                field_dict['name'] = field['title']

                check_list = field['checklist']
                for fld_list in check_list:
                    field_obj = {
                        "id": fld_list['key'], 
                        "type":"inspectionBoolean", 
                        "name": fld_list['value'],
                        "indent": 1,
                        "options": []
                    }
                    
                    options = field['status_options']
                    option_id = 1
                    for key, val in options.items():
                        if key.lower() in ['pass', 'success', 'satisfactory', 'yes', 'true', 'ok', 'good', 'positive']:
                            field_obj['options'].append({"id": str(option_id), "value": key, "positive": True})
                        else:
                            field_obj['options'].append({"id": str(option_id), "value": key})
                        option_id = option_id + 1

                    if 'fields' not in field_dict:
                        field_dict['fields'] = []

                    field_dict['fields'].append(field_obj)
                
                sort_order = sort_order+1            
                inspection_list.append(field_dict.copy())
            else:
                normal_field_obj = {
                    "id": field["id"],
                    "name": field["title"],
                    "type": field["type"],
                    "required": field['required']
                }
                if field["type"] in ['select','multiselect']:
                    if 'values' in field:
                        values = field['values']
                        normal_field_obj['choices'] = []
                        if values:
                            for val in values:
                                normal_field_obj['choices'].append({"id": val['key'], "value": val['value']})
                inspection_list.append(normal_field_obj)

        
        weather_field_obj = {
            "id": 'weather',
            "name": 'Weather',
            "type": 'string',
            "required": True
        }

        inspection_list.append(weather_field_obj)

        return ({"form":{"mobile_schema":{"version":str(obj.number),\
            "fields":inspection_list}}})

    
