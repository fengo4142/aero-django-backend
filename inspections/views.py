from django.db import transaction

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from airport.models import Airport, AssetImage, AssetType
from inspections.models import (
    Inspection, InspectionParent, InspectionAnswer,
    Remark, InspectionTemplateForm, AirportTemplatesRelation
)
from inspections.serializers import (
    InspectionEditSerializer, InspectionDetailSerializer, RemarkSerializer,
    InspectionListSerializer, InspectionDetailEditSerializer,
    InspectionAnswerDetailSerializer, InspectionAnswerSerializer,
    InspectionTemplateListSerializer, InspectionTemplateDetailSerializer, InspectionTypeSerializer,
    MobileInspectionListSerializer, MobileInspectionDetailSerializer,
    MobileInspectionDetailEditSerializer, MobileInspectionsDetailSerializer, MobileInspectionsSerializer
)
from inspections.filters import InspectionAnswerFilter
from inspections.tasks import update_templates, fetch_templates
from users.models import AerosimpleUser
from work_orders.models import WorkOrder, COMPLETED, WorkOrderImage

from inspections.permissions import CanViewInspections, \
    CanCompleteInspections, CanCreateInspections, SafetySelfInspectionPermission, \
    CanEditInspections, CanAddInspections, CanViewInspectionAnswers, CanViewInspectionTemplate

from airport.permissions import AirportHasInspectionPermission

from forms.utils import DRAFT, PUBLISHED
from forms.serializers import AnswerSerializer,MobileAnswerSerializer
from tasks.utils import create_task

from tasks.models import Task, TaskOccurrence
from inspections.utils import build_schema
from operations_log.models import Log, LogForm
from airport.utils import DynamoDbModuleUtility

from datetime import datetime, timedelta
from django.utils import timezone
import logging
import os
import boto3
from botocore.client import Config
import botocore.session
from boto3.s3.transfer import S3Transfer
from django import template
from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.db import models
from django.conf import settings
from django.conf.urls.static import static
from django.db.models import Q
import requests
import xmltodict
import random
from collections import namedtuple, OrderedDict
from tasks.views import TaskViewSet
from django.db.models import OuterRef, Subquery, Max, F
import json
register = template.Library()

logger = logging.getLogger('backend')

_BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME
_PREFIX = settings.APP_IMAGES_PREFIX
client = boto3.client('s3', config =Config(signature_version='s3v4'))


def ListFiles(client):
    """List files in specific S3 URL"""
    response = client.list_objects(Bucket=_BUCKET_NAME, Prefix=_PREFIX)
    for content in response.get('Contents', []):
        yield content.get('Key')



class InspectionMixin:

    @staticmethod
    def create_empty_inspection(self, user):
        inspection = self.get_object()
        published_version = inspection.versions.filter(
            status=PUBLISHED
        ).first()

        insp_answer = InspectionAnswer()
        insp_answer.inspection = published_version
        insp_answer.response = {}
        insp_answer.inspection_date = timezone.now()
        insp_answer.weather_conditions = {}
        insp_answer.status = 0
        insp_answer.inspected_by = user.aerosimple_user
        insp_answer.created_by = user.aerosimple_user
        insp_answer.inspection_type = ''
        insp_answer.issues = 0
        insp_answer.save()
        
        return Response({
            'result': 'Answer created',
            'id': insp_answer.id,
            'status': insp_answer.status,
            'type':insp_answer.inspection_type,
            'response':insp_answer.response
        })

    @action(detail=True, methods=['post'])
    def save_draft_inspection(self, request, pk=None):
        draft_data = request.data
        inspection = Inspection.objects.filter(form_id = pk).get(status = PUBLISHED)
        draft_version = InspectionAnswer.objects.filter(inspection_id = inspection.id).last()
        
        draft_version.response = draft_data['response']
        draft_version.inspection_type = draft_data['type']
        draft_version.save()
        return Response({
            'result': 'Answer updated',
            'id': draft_version.id,
            'status': draft_version.status
        })

    @action(detail=True, methods=['POST'])
    def start_inspection(self, request, pk=None):
        inspection = Inspection.objects.filter(form_id = pk).get(status = PUBLISHED)
        draft_data = InspectionAnswer.objects.filter(inspected_by = self.request.user.aerosimple_user).filter(
            inspection_id = inspection.id).filter(status = '0').last()
        response = {}
        if draft_data is not None:
            response['id'] = draft_data.id
            response['response'] = draft_data.response
            response['type'] = draft_data.inspection_type
            response['status'] = draft_data.status
            return Response(response)
        else:
            return InspectionViewSet.create_empty_inspection(self, self.request.user)

    @action(detail=False, methods=['get'])
    def safety_self_inspection(self, request):
        if self.request.user:
            airport = Airport.objects.get(
                id=self.request.user.aerosimple_user.airport_id
            )
            res = InspectionDetailEditSerializer(airport.safety_self_inspection)
            return Response(res.data)

        return InspectionParent.objects.none()

    
    @action(detail=True, methods=['post'])
    def complete_inspection(self, request, pk):
        # inspection = self.get_object()
        inspection = InspectionParent.objects.get(id=pk)
        published_version = inspection.versions.filter(status=PUBLISHED).first()
        answer_data = {
            "schema": published_version.schema,
            "status": published_version.status,
            "response": request.data['response']
            
        }
        serializer = AnswerSerializer(data=answer_data)
        if serializer.is_valid():
            # getting inspections field ids
            ids = [c['id'] for c in published_version.schema['fields']
                   if c['type'] == 'inspection']

            # check if there are no true answers for fields with a work order.
            # if form has associated airport the is the Airport safety self
            # inspection.
            if hasattr(inspection, 'associated_airport'):                
                work_orders = WorkOrder.objects.filter(
                    form__form__airport=request.user.aerosimple_user.airport
                ).exclude(status=COMPLETED).values(
                    'category_id', 'subcategory_id').distinct()

                for w in work_orders:
                    category = w['category_id']
                    subcategory = w['subcategory_id']
                    if category in request.data['response'] and request.data['response'][category][subcategory]:
                        return Response(
                            {'inspection_answer':
                                [('The item with Category {} and subcategory '
                                  '{} has a workorder associated, thus '
                                  'response must be false.').format(
                                    category, subcategory)]},
                            status=status.HTTP_400_BAD_REQUEST)

            # calculate issues number from response
            issues = 0
            for i in ids:
                issues += len(
                    [c for c in request.data['response'][i]
                        if request.data['response'][i][c] is False])

            try:
                # inspection answer must be created when starting filling the
                # form
                insp_answer = InspectionAnswer.objects.get(
                    pk=request.data['answer_id']
                )

            except InspectionAnswer.DoesNotExist:
                return Response(
                    {'inspection_answer': ["'answer_id' field is not valid"]},
                    status=status.HTTP_400_BAD_REQUEST)

            insp_answer.inspection = published_version
            insp_answer.status = 1
            insp_answer.response = answer_data['response']
            #insp_answer.weather_conditions = request.data['weather']
            try:
                user = AerosimpleUser.objects.get(
                    id=request.data['inspected_by'],
                    airport=request.user.aerosimple_user.airport
                )
            except AerosimpleUser.DoesNotExist:
                return Response(
                    {'inspected_by': ["'Inspected by' user does not exist"]},
                    status=status.HTTP_400_BAD_REQUEST)
            insp_answer.inspected_by = user
            insp_answer.created_by = request.user.aerosimple_user
            insp_answer.inspection_type = request.data['type']
            insp_answer.issues = issues
            inspection_date = datetime.strptime(
                request.data['date'],
                '%Y-%m-%dT%H:%M:%S.%fZ'
            )
            inspectionDate = datetime.strftime(
                insp_answer.inspection_date,
                '%Y-%m-%d %H:%M:%S'
            )

            if inspectionDate != inspection_date:
                # get weather from dynamo weather table and fill the weather_conditions if found
                try:
                    dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_DEFAULT_REGION)
                    table = dynamodb.Table(settings.MAIN_APP_PREFIX + 'weather')
                    icao_code = request.user.aerosimple_user.airport.code
                    max_diff = 24
                    response = None
                    for diff in range(max_diff):
                        date = inspection_date - timedelta(hours = diff - 1)
                        key = icao_code + '_' + str(date.year) + '_' + str(date.month) + '_' + str(date.day) + '_' + str(date.hour)
                        response = table.get_item(
                            Key={
                                'id': key
                            }
                        )
                        if 'Item' in response:
                            insp_answer.weather_conditions['current_obs'] = response['Item']
                            insp_answer.weather_conditions['title'] = response['Item']['metar']['summary']
                            break
                except Exception as ex:
                    logger.error(ex)
                    # show weather only if availabe, so do nothing
                    pass
            insp_answer.inspection_date = inspection_date
            try:
                with transaction.atomic():
                    insp_answer.save()
                    insp_answer.create_log_entry()

                    if 'task_details' in request.data:
                        data = request.data['task_details']
                        if len(data.keys()) > 0:
                            task = Task.objects.get(pk=data['taskid'])
                            date = datetime.strptime(
                                data['date'], '%Y-%m-%dT%H:%M:%SZ')
                            occurrence = task.get_occurrence(date)
                            occurrence.save()
                            t_occ, created = TaskOccurrence.objects.get_or_create(
                                task=task,
                                occurrence=occurrence
                            )
                            t_occ.completed = True
                            t_occ.save()
            except Exception:
                # Any exception should be handled by DRF, like a normal action
                raise

            return Response({
                'result': 'Answer updated',
                'id': insp_answer.id,
                'status': insp_answer.status
            })
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)





class InspectionViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet,
                        InspectionMixin):

    def get_queryset(self):
        if self.request.user:
            user_inspections = InspectionParent.objects.filter(
                airport__id=self.request.user.aerosimple_user.airport_id)
            #to retreive daily/monthly/yearly inspections
            query = self.request.GET.get("query")
            if query is not None:
                if(query.lower() == 'daily'):
                    rule_task_data = Task.objects.filter(label = 'inspections').filter(rule = '1').filter(airport_id = self.request.user.aerosimple_user.airport_id)
                if(query.lower() == 'weekdays'):
                    rule_task_data = Task.objects.filter(label = 'inspections').filter(rule = '2').filter(airport_id = self.request.user.aerosimple_user.airport_id)
                if(query.lower() == 'weekly'):
                    rule_task_data = Task.objects.filter(label = 'inspections').filter(rule = '3').filter(airport_id = self.request.user.aerosimple_user.airport_id)
                if(query.lower() == 'monthly'):
                    rule_task_data = Task.objects.filter(label = 'inspections').filter(rule = '4').filter(airport_id = self.request.user.aerosimple_user.airport_id)
                if(query.lower() == 'yearly'):
                    rule_task_data = Task.objects.filter(label = 'inspections').filter(rule = '5').filter(airport_id = self.request.user.aerosimple_user.airport_id)
                rule_inspection = []
                for index in range(len(rule_task_data)):
                    inspection_data = InspectionParent.objects.get(task = rule_task_data[index].id)
                    rule_inspection.insert(index,inspection_data)
                
                return rule_inspection
            return user_inspections.filter(versions__status=PUBLISHED)

        return InspectionParent.objects.none()
    
    def get_permission_for_action(self, action):
        switcher = {
            'list': [IsAuthenticated, CanViewInspections, AirportHasInspectionPermission],
            'summary': [IsAuthenticated,CanViewInspections,AirportHasInspectionPermission],
            'retrieve': [IsAuthenticated, CanViewInspections, AirportHasInspectionPermission],
            'create': [IsAuthenticated, CanCreateInspections, AirportHasInspectionPermission],
            'complete_inspection': [IsAuthenticated, CanCompleteInspections, AirportHasInspectionPermission],
            'save_draft_inspection': [IsAuthenticated, CanCompleteInspections, AirportHasInspectionPermission],
            'safety_self_inspection': [IsAuthenticated, SafetySelfInspectionPermission, AirportHasInspectionPermission],
            'start_inspection': [IsAuthenticated, CanCompleteInspections, AirportHasInspectionPermission]
        }
        return switcher.get(action, [IsAdminUser])

    def get_serializer_class(self):
        """Return different serializers in list action."""
        if self.action == 'list':
            return InspectionListSerializer
        return InspectionDetailSerializer

    def get_permissions(self):
        self.permission_classes = self.get_permission_for_action(self.action)
        return super(self.__class__, self).get_permissions()

    

    @action(detail=False, methods=['get'])
    def summary(self, request):
        if self.request.user:
            weather_summary = {}
            dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_DEFAULT_REGION)
            table = dynamodb.Table(settings.MAIN_APP_PREFIX + 'weather')
            icao_code = request.user.aerosimple_user.airport.code
            max_diff = 24
            response = None
            for diff in range(max_diff):
                date = datetime.now() - timedelta(hours = diff - 1)
                key = icao_code + '_' + str(date.year) + '_' + str(date.month) + '_' + str(date.day) + '_' + str(date.hour)
                response = table.get_item(
                    Key={
                        'id': key
                    }
                )
                if 'Item' in response:
                    weather_summary = response['Item']['metar']
                    weather_summary['temperature'] = weather_summary['temperature'].replace('Temperature ', '')
                    break
            task_summary = ''
            occurences = TaskViewSet.get_task_occurences(self.request.user)
            for oc in occurences:
                if oc['event']['inspection'] != None:
                    task_summary = oc['event']['inspection']['title']
                    break
                    
            return Response({'weather': weather_summary, 'task': task_summary})

        return None



class InspectionEditViewSet(viewsets.ModelViewSet):

    def get_permissions(self):
        switcher = {
            'list': [IsAuthenticated, CanEditInspections, AirportHasInspectionPermission],
            'retrieve': [IsAuthenticated, CanEditInspections, AirportHasInspectionPermission],
            'partial_update': [IsAuthenticated, CanEditInspections, AirportHasInspectionPermission],
            'create': [IsAuthenticated, CanAddInspections, AirportHasInspectionPermission],
            'create_empty_inspection': [IsAuthenticated, CanEditInspections, AirportHasInspectionPermission],
            'discard_draft': [IsAuthenticated, CanEditInspections, AirportHasInspectionPermission],
            'update_template': [IsAuthenticated, CanEditInspections, AirportHasInspectionPermission],
        }
        self.permission_classes = switcher.get(self.action, [IsAdminUser])
        return super(self.__class__, self).get_permissions()

    def get_queryset(self):
        if self.request.user:
            return InspectionParent.objects.filter(
                airport__id=self.request.user.aerosimple_user.airport_id)

        return InspectionParent.objects.none()

    def get_serializer_class(self):
        """Return different serializers in list action."""
        if self.action == 'create':
            return InspectionEditSerializer
        if self.action == 'list':
            return InspectionListSerializer
        return InspectionDetailEditSerializer

    def create(self, request):
        inspection_data = request.data
        task_data = inspection_data.pop('task', None)

        # While creating new parent inspection check if limit has reached...
        inspection_count = InspectionParent.objects.filter(
            airport=request.user.aerosimple_user.airport).count()
        max_allowed_count = DynamoDbModuleUtility.return_module_attribute(
            request.user.aerosimple_user.airport.code, 'inspections', 'max_inspections')
        if not settings.AIRPORT_PLAN_ENABLE:
            max_allowed_count = 100
        if not max_allowed_count:
            return Response(
                    {'error': 'Configuration for airport not set'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if int(max_allowed_count) <= inspection_count:
            return Response(
                    {'error': 'Inspection count limit reached'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            with transaction.atomic():
                if task_data is not None:
                    task_data['name'] = inspection_data['title']
                    task_data['label'] = 'inspections'
                    task_data['due_date'] = timezone.now().strftime(
                        "%Y-%m-%d%z")
                    task_data['end_recurring_period'] = task_data.get(
                        'rule', {}).get('endPeriod', None)
                    task = create_task(task_data, request.user)
                    inspection_data['task'] = task.id
                serializer = self.get_serializer(data=inspection_data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED,
                    headers=headers
                )
        except Exception:
            # Any exception should be handled by DRF, like a normal action
            raise

    def partial_update(self, request, pk=None):
        inspection = self.get_object()

        task_data = request.data.pop('task', None)

        st = request.data.pop('status', None)

        data = request.data
        # IF INSPECTION IS FROM A TEMPLATE WE MUST BUILD THE
        # MERGED SCHEMA WITH AIRPORT CHANGES AND TEMPLATE FIELDS
        if inspection.template:
            data['schema'] = build_schema(
                request.data['airport_changes'],
                inspection.template
            )

        serializer = InspectionEditSerializer(
            inspection,
            data=request.data,
            context={'request': request}
        )
        title = request.data.pop('title', None)
        additionalInfo = request.data.pop('additionalInfo', None)
        icon = request.data.pop('icon', None)

        shouldUpdateInspectionParent = False
        if serializer.is_valid():
            serializer.save()
            v = serializer.instance.versions.latest('id')
            if st == DRAFT:
                shouldUpdateInspectionParent = not serializer.instance.versions.filter(
                    status=PUBLISHED).exists()
                if v.status == DRAFT:
                    v.schema = data['schema']
                    v.title = title
                    v.icon = icon
                    v.additionalInfo = additionalInfo
                    v.save()
                else:
                    newv = Inspection()
                    newv.schema = data['schema']
                    newv.form = inspection
                    newv.title = title
                    newv.icon = icon
                    newv.additionalInfo = additionalInfo
                    newv.save()
            else:
                # check for max
                inspection_count = InspectionParent.objects.filter(
                    airport=request.user.aerosimple_user.airport).count()
                max_allowed_count = DynamoDbModuleUtility.return_module_attribute(
                    request.user.aerosimple_user.airport.code, 'inspections', 'max_inspections')
                if not settings.AIRPORT_PLAN_ENABLE:
                    max_allowed_count = 100
                if not max_allowed_count:
                    return Response(
                            {'error': 'Configuration for airport not set'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                if int(max_allowed_count) <= inspection_count:
                    return Response(
                            {'error': 'Inspection count limit reached'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                shouldUpdateInspectionParent = True
                if v.status == DRAFT:
                    v.schema = data['schema']
                    v.status = PUBLISHED
                    v.title = title
                    v.icon = icon
                    v.additionalInfo = additionalInfo
                    v.save()
                else:
                    newv = Inspection()
                    newv.schema = data['schema']
                    newv.form = inspection
                    newv.status = PUBLISHED
                    newv.title = title
                    newv.icon = icon
                    newv.additionalInfo = additionalInfo
                    newv.save()

            if shouldUpdateInspectionParent:
                inspection.title = title
                inspection.icon = icon
                inspection.additionalInfo = additionalInfo
                if 'airport_changes' in data:
                    inspection.airport_changes = data['airport_changes']

                # If the parent is updated, then the task has to be updated
                # as well
                if task_data is not None:
                    task_data['name'] = title
                    task_data['label'] = 'inspections'
                    task_data['due_date'] = timezone.now().strftime(
                        "%Y-%m-%d%z")
                    task_data['end_recurring_period'] = task_data.get(
                        'rule', {}).get('endPeriod', None)

                    task = create_task(task_data, request.user)
                    if inspection.task is not None:
                        inspection.task.delete()
                    inspection.task = task

                inspection.save()

            return Response(serializer.data)
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def discard_draft(self, request, pk=None):
        inspection = self.get_object()

        inspection.versions.filter(status=DRAFT).delete()
        if not inspection.versions.exists():
            inspection.delete()

        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def update_template(self, request, pk=None):
        inspection = self.get_object()
        try:
            with transaction.atomic():
                latest_template = inspection.template.form.versions.latest(
                    'number')
                inspection.template = latest_template
                inspection.save()

                schema = build_schema(
                    inspection.airport_changes, latest_template)
                newVersion = inspection.versions.get(status=PUBLISHED)
                newVersion.id = 0
                newVersion.pk = 0
                newVersion.number = newVersion.number + 1
                newVersion.schema = schema
                newVersion.save()
                return Response(InspectionDetailEditSerializer(inspection).data)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

       
class InspectionAnswerViewSet(mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              viewsets.GenericViewSet):
    pagination_class = None
    filter_class = InspectionAnswerFilter
    # filter_fields = ('inspection_date', '' )

    def get_permissions(self):
        self.permission_classes = [CanViewInspectionAnswers, AirportHasInspectionPermission]
        return super(self.__class__, self).get_permissions()

    def get_queryset(self):
        
        if self.request.user:
            airport_id = self.request.user.aerosimple_user.airport_id
            
            filter_date = self.request.GET.get("filter_date")
            if filter_date:
                try:
                    filter_date = datetime.strptime(filter_date, '%m/%d/%y')
                except:
                    pass
            
            results = InspectionAnswer.objects.filter(
                inspection__form__airport_id=airport_id,
                status=1
            ).order_by('inspection_date')
            
            if filter_date:
                results = results.filter(inspection_date__gte=filter_date)

            return results.reverse()

        return InspectionAnswer.objects.none()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return InspectionAnswerDetailSerializer
        return InspectionAnswerSerializer


class RemarkViewSet(mixins.CreateModelMixin,
                    mixins.UpdateModelMixin,
                    viewsets.GenericViewSet):

    serializer_class = RemarkSerializer

    def get_permissions(self):
        switcher = {
            'update': [IsAuthenticated, AirportHasInspectionPermission],
            'create': [IsAuthenticated, AirportHasInspectionPermission]
        }
        self.permission_classes = switcher.get(self.action, [IsAdminUser])
        return super(self.__class__, self).get_permissions()

    def get_queryset(self):
        if self.action == 'update':
            return Remark.objects.filter(pk=self.kwargs.get('pk'))

        return Remark.objects.none()


class InspectionTemplateViewSet(mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    queryset = InspectionTemplateForm.objects.all()

    def get_permissions(self):
        switcher = {
            'retrieve': [IsAuthenticated, CanViewInspectionTemplate, AirportHasInspectionPermission],
            'list': [IsAuthenticated, CanViewInspectionTemplate, AirportHasInspectionPermission],
            'update_version': [IsAuthenticated, AirportHasInspectionPermission],
            'sync': [IsAuthenticated, CanViewInspectionTemplate, AirportHasInspectionPermission]
        }
        self.permission_classes = switcher.get(self.action, [IsAdminUser])
        return super(self.__class__, self).get_permissions()

    def get_serializer_class(self):
        """Return different serializers in list action."""
        if self.action == 'retrieve':
            return InspectionTemplateDetailSerializer
        if self.action == 'list':
            return InspectionTemplateListSerializer
        return InspectionTemplateListSerializer

    @action(detail=True, methods=['post'])
    def update_version(self, request, pk=None):
        template = self.get_object()
        airport = request.user.aerosimple_user.airport

        relation = AirportTemplatesRelation.objects.get(
            airport=airport, form=template
        )

        relation.selected_version = template.versions.latest('number').number
        relation.save()
        ser = InspectionTemplateDetailSerializer(
                template,
                context={'request': request})

        return Response(ser.data)
    
    @action(detail=False, methods=['get'])
    def sync(self, request):
        fetch_templates()
        return Response(status=status.HTTP_200_OK)

class ExportViewSet(viewsets.GenericViewSet):
    def get_permissions(self):
        switcher = {
            'inspection': [IsAuthenticated, CanViewInspectionAnswers, AirportHasInspectionPermission],
        }
        self.permission_classes = switcher.get(self.action, [IsAdminUser])
        return super(self.__class__, self).get_permissions()

    @register.simple_tag
    @action(detail=True, methods=['get'])
    def inspection(self, request, pk):
        airport = Airport.objects.filter(id=request.user.aerosimple_user.airport_id).last()
        published_version = Inspection.objects.get(id=self.kwargs.get('pk')).schema
        context = {
            'airport': airport,
            "pages": published_version['pages'],
            "fields": published_version['fields'],
            "sections": published_version['sections'],
            "title": published_version['id'],
        }
        html_string = render_to_string('empty-inspection.html', context=context)
        fileName = '{}-{}-{}.pdf'.format(airport.code, published_version['id'].replace(' ', '-'), random.randint(0,999999))
        key = '/tmp/'+fileName
        html = HTML(string=html_string)
        html.write_pdf(target=key)
        bucket = settings.ATTACHMENTS_BUCKET_NAME
        client = boto3.client('s3', config =Config(signature_version='s3v4'))
        try:
            client.upload_file(key,bucket,'inspections/'+fileName)
            os.remove(key)
            url = client.generate_presigned_url('get_object', 
                    Params={
                        'Bucket':bucket,
                        'Key':'inspections/'+fileName
                    },
                    ExpiresIn = settings.EXPIRY_FOR_EXPORT_DOCUMENT
                )  
        except Exception as e:
            logger.error("there was an error trying to upload file")
        
        return HttpResponse(url)

class ExportDataViewSet(viewsets.GenericViewSet):
    def get_permissions(self):
        switcher = {
            'inspection_data': [IsAuthenticated, CanViewInspectionAnswers, AirportHasInspectionPermission],
        }
        self.permission_classes = switcher.get(self.action, [IsAdminUser])
        return super(self.__class__, self).get_permissions()

    @register.simple_tag
    @action(detail=True, methods=['get'])
    def inspection_data(self, request, pk):
        airport = Airport.objects.filter(id=request.user.aerosimple_user.airport_id).first()
        insp_answer = InspectionAnswer.objects.filter(id=self.kwargs.get('pk')).last().response
        inspection_id = InspectionAnswer.objects.filter(id=self.kwargs.get('pk')).last().inspection_id
        inspection_date = InspectionAnswer.objects.filter(id=self.kwargs.get('pk')).last().inspection_date
        weather_conditions = InspectionAnswer.objects.filter(id=self.kwargs.get('pk')).last().weather_conditions
        inspected = InspectionAnswer.objects.filter(id=self.kwargs.get('pk')).last().inspected_by
        inspection_type = InspectionAnswer.objects.filter(id=self.kwargs.get('pk')).last().inspection_type
        issues = InspectionAnswer.objects.filter(id=self.kwargs.get('pk')).last().issues
        published_version = Inspection.objects.get(id=inspection_id).schema
        remarks = Remark.objects.filter(answer_id=self.kwargs.get('pk')).all()
        work_orders = WorkOrder.objects.filter(
                    form__form__airport=request.user.aerosimple_user.airport
                ).exclude(status=COMPLETED).order_by('id')
        logger.info(work_orders)  
        context = {
            'airport': airport,
            'work_orders':work_orders,
            'insp_answer': insp_answer,
            'weather_conditions': weather_conditions,
            'issues': issues,
            'remarks': remarks,
            'inspected': inspected,
            'inspection_type': inspection_type,
            'inspection_date': inspection_date,
            "pages": published_version['pages'],
            "fields": published_version['fields'],
            "sections": published_version['sections'],
            "titles": published_version['id'],
            "self_inspection": (airport.safety_self_inspection)
        }
        html_string = render_to_string('inspection-data.html', context=context)
        fileName = '{}-{}-with-data-{}.pdf'.format(airport.code, published_version['id'].replace(' ', '-'), random.randint(0,999999))
        key = '/tmp/'+fileName
        html = HTML(string=html_string)
        html.write_pdf(target=key)
        bucket = settings.ATTACHMENTS_BUCKET_NAME
        client = boto3.client('s3', config =Config(signature_version='s3v4'))
        try:
            client.upload_file(key, bucket, 'inspections/'+fileName)
            os.remove(key)
            url = client.generate_presigned_url('get_object', 
                    Params={
                        'Bucket':bucket,
                        'Key':'inspections/'+fileName
                    },
                    ExpiresIn = settings.EXPIRY_FOR_EXPORT_DOCUMENT
                )  
        except Exception as e:
            logger.error("there was an error trying to upload file")

        return HttpResponse(url)


class InspectionTypeViewSet(viewsets.ModelViewSet):

    def get_permissions(self):
        switcher = {
            'list': [IsAuthenticated, CanEditInspections, AirportHasInspectionPermission],
            'retrieve': [IsAuthenticated, CanEditInspections, AirportHasInspectionPermission],
            'partial_update': [IsAuthenticated, CanEditInspections, AirportHasInspectionPermission],
            'create': [IsAuthenticated, CanAddInspections, AirportHasInspectionPermission],
            'destroy': [IsAuthenticated, CanAddInspections, AirportHasInspectionPermission]
        }
        self.permission_classes = switcher.get(self.action, [IsAdminUser])
        return super(self.__class__, self).get_permissions()

    def get_queryset(self):
        if self.request.user:
            user_inspections = InspectionParent.objects.filter(
                airport__id=self.request.user.aerosimple_user.airport_id)

            return user_inspections.filter(versions__status=PUBLISHED)

        return InspectionParent.objects.none()

    def get_serializer_class(self):
        return InspectionTypeSerializer

    def get_paginated_response(self, data):
        return Response({'items': data,'status':{'code':status.HTTP_200_OK,'message':'success'}})


class MobileInspectionTypeViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    
    def get_permissions(self):
        self.permission_classes = [IsAuthenticated, CanViewInspections, AirportHasInspectionPermission]
        return super(self.__class__, self).get_permissions()

    def get_queryset(self):

        if self.request.user:
            user_inspections = InspectionParent.objects.filter(
                airport__id=self.request.user.aerosimple_user.airport_id)

            return user_inspections.filter(versions__status=PUBLISHED)

        return InspectionParent.objects.none()

    def get_serializer_class(self):
        return InspectionTypeSerializer

    def get_paginated_response(self, data):
        return Response({'items': data,'status':{'code':status.HTTP_200_OK,'message':'success'}})


class ImagesDataViewSet(viewsets.ViewSet):

    def list(self,request):
        file_list = ListFiles(client)
        image_list = []
        for file in file_list:
            if 'icon' in file:
                image_list.append(file)
        return Response({'items':image_list,'status': {'code':status.HTTP_200_OK,'message':'success'}})

    def retrieve(self, request, pk):
        file_list = ListFiles(client)
        image_list = []
        for file in file_list:
            if 'icon' in file:
                if pk in file:
                    image_list.append(file)
        return Response({'items':image_list,'status': {'code':status.HTTP_200_OK,'message':'success'}})


class MobileInspectionAnswersViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    


    def get_queryset(self):
        if self.request.user:
            airport_id = self.request.user.aerosimple_user.airport_id
            
            filter_date = self.request.GET.get("filter_date")
            if filter_date:
                try:
                    filter_date = datetime.strptime(filter_date, '%m/%d/%y')
                except:
                    pass
            
            results = InspectionAnswer.objects.filter(
                inspection__form__airport_id=airport_id,
                status=1
            ).order_by('date')
            
            if filter_date:
                results = results.filter(inspection_date__gte=filter_date)

            return results
        return InspectionAnswer.objects.none()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return InspectionAnswerDetailSerializer
        return MobileInspectionDetailSerializer
    

    def get_paginated_response(self, data):
        return Response({'items': data,'status':{'code':status.HTTP_200_OK,'message':'success'}})


class SafetySelfInspectionViewSet(viewsets.ViewSet):

    def list(self, request):
        if self.request.user:
            airport = Airport.objects.get(
                id=self.request.user.aerosimple_user.airport_id
            )
            res = MobileInspectionDetailEditSerializer(airport.safety_self_inspection)
            res_type = airport.types_for_self_inspection
            form_data = res.data
            schema = form_data['form']['schema']
            items = []
            sub_category_list = []
            category_asset_list = []
            for field in schema['fields']:    
                field_dict = {}
                if field['type'] == 'inspection':
                    field_dict['id'] = field['id']
                    field_dict['name'] = field['title']
                    check_list = field['checklist']
                    field_obj = []
                    for fld_list in check_list:
                        field_obj.append(fld_list['key'])
                        sub_category_list.append({'id':fld_list['key'],'name':fld_list['value']})
                    field_dict['sub-category'] = field_obj
                    items.append(field_dict)
            res_type_id = 1
            if res_type:
                for key, value in res_type.items():
                    for item in items:
                        if(item['id'] == key):
                            name = item['name']
                    for k, v in value.items():
                        res_type_dict = {
                            'id':res_type_id,
                            'category':key,
                            'subCategory':k,
                            'assetType':v,
                            'comment':name+':'+v
                            }
                        res_type_id += 1
                        category_asset_list.append(res_type_dict)

            return Response({'category':{'items':items},'sub-category':{'items':sub_category_list},\
                'category-assets':{'items':category_asset_list},
                'status':{'code':status.HTTP_200_OK,'message':'success'}})

        return InspectionParent.objects.none()


class AllImagesViewSet(viewsets.ViewSet):

    def list(self, request):
        airport = Airport.objects.all()
        images_list = []
        for data in airport:
            if data.logo:
                images_list.append({
                    'id':"airport_"+ data.code,
                    'title':data.name,
                    'path':data.logo.url,
                    'type':'airport'
                })
        asset_image = AssetImage.objects.all()
        for data in asset_image:
            if data.image:
                images_list.append({
                    'id':"asset_image_"+ str(data.id),
                    'title':data.asset.name,
                    'path':data.image.url,
                    'type':'assets'
                })
        asset_type = AssetType.objects.all()
        for data in asset_type:
            if data.icon:
                images_list.append({
                    'id':"asset_type_"+ str(data.id),
                    'title':data.name,
                    'path':data.icon.url,
                    'type':'asset_types'
                })
        user_data = AerosimpleUser.objects.all()
        for data in user_data:
            if data.image:
                images_list.append({
                    'id':"user_"+ data.user.username,
                    'title':data.first_name,
                    'path':data.image.url,
                    'type':'userProfile'
                })
        work_order = WorkOrderImage.objects.all()
        for data in work_order:
            if data.image:
                images_list.append({
                    'id':"workorder_" + str(data.id),
                    'title':data.work_order.category + ' - ' + data.work_order.subcategory,
                    'path':data.image.url,
                    'type':'workOrder'
                })
        return Response({'items':images_list, 'status':{'code':status.HTTP_200_OK,'message':'success'}})
    

class MobileInspectionsViewSet(viewsets.ModelViewSet,
                                InspectionMixin):

    def get_queryset(self):
        if self.request.user:
            #user_inspections = Inspection.objects.filter(form__airport__id=self.request.user.aerosimple_user.airport_id)
            """version_qs = Inspection.objects.filter(
                form_id=OuterRef("form_id")
            ).order_by("-number")
            return Inspection.objects.filter(form__airport__id=self.request.user.aerosimple_user.airport_id).filter(
                    id__in=Subquery(
                        version_qs.values('id')[:1]
                    )
                )"""
            return Inspection.objects.filter(form__airport__id=self.request.user.aerosimple_user.airport_id).annotate(
                latest_version=Max('form__versions__number')
            ).filter(number=F('latest_version'))
        return InspectionAnswer.objects.none()

    def get_serializer_class(self):
        """Return different serializers in list action."""
        if self.action == 'retrieve':
            return MobileInspectionsDetailSerializer
        return MobileInspectionsSerializer

    def get_paginated_response(self, data):
        return Response({'items': data,'status':{'code':status.HTTP_200_OK,'message':'success'}})

    
