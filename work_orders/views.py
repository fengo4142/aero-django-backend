from botocore.exceptions import ClientError
import boto3
import json
import logging
import random
import os
from datetime import date
from airport.models import Airport, AssetImage
from django import template
from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from botocore.client import Config
from django.db import transaction
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from forms.utils import DRAFT, PUBLISHED
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from django.utils.translation import ugettext_lazy as _

from work_orders.models import COMPLETED, OPERATION, WorkOrder, \
    WorkOrderForm, WorkOrderSchema, HIGH, MEDIUM, LOW, \
    NEW, MAINTENANCE
from work_orders.serializers import MaintenanceImageSerializer, \
    MaintenanceSchemaSerializer, MaintenanceSerializer, \
    OperationsImageSerializer, OperationsSchemaSerializer, \
    OperationsSerializer, WorkOrderDetailSerializer,\
    WorkOrderImageSerializer, WorkOrderListSerializer, \
    WorkOrderSchemaSerializer, WorkOrderSerializer, \
    WorkOrderSchemaSaveSerializer, MaintenanceSchemaSaveSerializer, \
    OperationsSchemaSaveSerializer, MaintenanceFormSerializer, \
    OperationsFormSerializer, MobileWorkOrderSerializer, \
    WorkOrderWebSerializer, WorkOrderListWebSerializer, \
    WorkOrderDetailWebSerializer, MaintenanceSchemaAssignmentSerializer, \
    OperationsSchemaAssignmentSerializer

from airport.permissions import AirportHasWorkOrderPermission, AirportHasNotamsPermission

from rest_framework.permissions import IsAuthenticated, IsAdminUser
from work_orders.permissions import CanCreateWorkOrders,  CanViewWorkOrders, \
    CanEditWorkOrderSchema, CanFillMaintenanceForm, CanFillOperationsForm
from users.models import AerosimpleUser, Role
from django.db.models import Q, Case, When
from collections import OrderedDict
from django.conf import settings

from django import template
from django.template.loader import render_to_string
from work_orders.models import WorkOrder, WorkOrderImage, Maintenance, OperationsSchema, MaintenanceForm, WorkOrderForm, Operations, MaintenanceImage
from users.serializers import AerosimpleUserSimpleSerializer, UserSerializer


register = template.Library()


_BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME
_PREFIX = settings.APP_IMAGES_PREFIX
client = boto3.client('s3', config=Config(signature_version='s3v4'))


def ListFiles(client):
    """List files in specific S3 URL"""
    response = client.list_objects(Bucket=_BUCKET_NAME, Prefix=_PREFIX)
    for content in response.get('Contents', []):
        yield content.get('Key')


register = template.Library()

logger = logging.getLogger('backend')


def get_permission_for_action(action):
    switcher = {
        'list': [IsAuthenticated, CanViewWorkOrders, AirportHasWorkOrderPermission],
        'retrieve': [IsAuthenticated, CanViewWorkOrders, AirportHasWorkOrderPermission],
        'create': [IsAuthenticated, CanCreateWorkOrders, AirportHasWorkOrderPermission],
        'destroy': [IsAuthenticated, CanCreateWorkOrders, AirportHasWorkOrderPermission],
        'get_schema': [IsAuthenticated, CanViewWorkOrders, AirportHasWorkOrderPermission],
        'update_schemas': [IsAuthenticated, CanEditWorkOrderSchema, AirportHasWorkOrderPermission],
        'assignment': [IsAuthenticated, CanEditWorkOrderSchema, AirportHasWorkOrderPermission],
        'maintenance_review': [IsAuthenticated, CanFillMaintenanceForm, AirportHasWorkOrderPermission],
        'operations_review': [IsAuthenticated, CanFillOperationsForm, AirportHasWorkOrderPermission],
        'get_notams': [IsAuthenticated, AirportHasNotamsPermission,AirportHasWorkOrderPermission],
    }
    return switcher.get(action, [IsAdminUser])

##########################################################
#################### Email Sending #######################
##########################################################


def sendMailToMaintenance(workOrderId, airportId, maintenanceId, type):
    emails = ''
    images = {
        'background': settings.MEDIA_URL + 'notifications/background.png',
        'logo': settings.MEDIA_URL + 'notifications/logo.png',
        'plane': settings.MEDIA_URL + 'notifications/plane.png',
        'curve': settings.MEDIA_URL + 'notifications/curve.png',
        'welcome': settings.MEDIA_URL + 'notifications/welcome-email.png',
        'rectangle': settings.MEDIA_URL + 'notifications/Rectangle.png',
    }
    if('workorder' in type):
        work_order = WorkOrder.objects.get(id=workOrderId)
        workorderimage = WorkOrderImage.objects.filter(
            work_order_id=workOrderId)
        form = WorkOrderForm.objects.get(airport__id=airportId)
        assignedUsers = MaintenanceSchemaAssignmentSerializer(
            form.maintenance_form.versions.get(status=PUBLISHED)
        ).data
        data = assignedUsers['assignment']['users']
        user = assignedUsers['assignment']['role']
        if(form.maintenance_form.assigned_role):
            for i in range(len(user)):
                emails = emails + user[i]['email'] + ','
        else:
            for j in range(len(data)):
                emails = emails + data[j]['email'] + ','

        context = {
            'work_order': work_order,
            'workorderimage': workorderimage,
            'images': images
        }
        html_string = render_to_string('work-order.html', context=context)
    elif('maintenance' in type):
        work_order = WorkOrder.objects.get(id=workOrderId)
        maintenance = Maintenance.objects.get(work_order_id=workOrderId)
        maintenanceimage = MaintenanceImage.objects.filter(
            maintenance_form_id=maintenanceId)
        form = WorkOrderForm.objects.get(airport__id=airportId)
        operations = OperationsSchemaAssignmentSerializer(
            form.operations_form.versions.get(status=PUBLISHED)
        ).data
        search = operations['assignment']['users']
        userdata = operations['assignment']['role']
        if(form.operations_form.assigned_role):
            for k in range(len(userdata)):
                emails = emails + userdata[k]['email'] + ','
        else:
            for l in range(len(search)):
                emails = emails + search[l]['email'] + ','

        context = {
            'work_order': work_order,
            'maintenanceimage': maintenanceimage,
            'maintenance': maintenance,
            'images': images
        }
        html_string = render_to_string(
            'workorder-complete.html', context=context)
    elif('operation' in type):
        work_order = WorkOrder.objects.get(id=workOrderId)
        maintenance = Maintenance.objects.get(work_order_id=workOrderId)
        operation = Operations.objects.get(work_order_id=workOrderId)
        emails = work_order.logged_by.user.email
        context = {
            'work_order': work_order,
            'maintenance': maintenance,
            'operation': operation,
            'images': images
        }
        html_string = render_to_string('work-orderfyi.html', context=context)

    if emails:
        RECIPIENT = emails.rstrip(',').split(',')
        SUBJECT = 'WorkOrder #'+str(work_order.id)
        BODY_HTML = html_string
        CHARSET = "UTF-8"
        client = boto3.client('ses', region_name=settings.AWS_REGION)
        try:
            response = client.send_email(
                Destination={
                    'ToAddresses': RECIPIENT
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': CHARSET,
                            'Data': BODY_HTML,
                        }
                    },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': SUBJECT,
                    },
                },
                Source=settings.EMAIL_HOST_USER,
                ConfigurationSetName=settings.CONFIGURATION_SET,
            )
        except ClientError as e:
            logger.info(e.response['Error']['Message'])
        else:
            logger.info("Email sent! Message ID:"),
            logger.info(response['MessageId'])
        return True
    else:
        return True


class WorkOrderMixin:

    @action(detail=False, methods=['get'])
    def get_schema(self, request):
        if not self.request.user.is_authenticated:
            return Response(status=status.HTTP_403_FORBIDDEN)

        icaoId = request.user.aerosimple_user.airport.code
        form = WorkOrderForm.objects.get(
            airport__id=self.request.user.aerosimple_user.airport_id)
        maintenance = MaintenanceSchemaSerializer(
            form.maintenance_form.versions.get(status=PUBLISHED)
        )
        operations = OperationsSchemaSerializer(
            form.operations_form.versions.get(status=PUBLISHED)
        )
        result = {
            'notamsEnabled': AirportHasNotamsPermission.check(icaoId),
            'maintenance': maintenance.data,
            'operations': operations.data,
            'workorder': WorkOrderSchemaSerializer(
                form.versions.get(status=PUBLISHED)
            ).data,
        }
        return Response(result)

    @action(detail=False, methods=['post'])
    def update_schemas(self, request):
        if not self.request.user.is_authenticated:
            return Response(status=status.HTTP_403_FORBIDDEN)

        form = WorkOrderForm.objects.get(
            airport__id=self.request.user.aerosimple_user.airport_id)
        maintenance_from = form.maintenance_form
        operations_from = form.operations_form

        workorder_data = {
            "form": form.id,
            "schema": request.data['workorder'],
            "status": PUBLISHED
        }
        maintenance_data = {
            "form": maintenance_from.id,
            "schema": request.data['maintenance'],
            "status": PUBLISHED
        }
        operations_data = {
            "form": operations_from.id,
            "schema": request.data['operations'],
            "status": PUBLISHED
        }
        work_order_schema = WorkOrderSchemaSaveSerializer(
            data=workorder_data)
        maintenance_schema = MaintenanceSchemaSaveSerializer(
            data=maintenance_data)
        operations_schema = OperationsSchemaSaveSerializer(
            data=operations_data)

        valid1 = work_order_schema.is_valid()
        valid2 = maintenance_schema.is_valid()
        valid3 = operations_schema.is_valid()

        if (valid1 and valid2 and valid3):
            try:
                with transaction.atomic():
                    work_order_schema.save()
                    maintenance_schema.save()
                    operations_schema.save()
            except ValidationError:
                raise
        else:
            errors = (work_order_schema.errors +
                      maintenance_schema.errors +
                      operations_schema.errors)
            return Response(
                errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def assignment(self, request):
        data = request.data
        if 'type' not in data:
            return Response(
                _("Type is missing."),
                status=status.HTTP_400_BAD_REQUEST)

        woform = WorkOrderForm.objects.get(
            airport__id=self.request.user.aerosimple_user.airport_id)

        if data['type'] == 'maintenance':
            form = woform.maintenance_form
        elif data['type'] == 'operations':
            form = woform.operations_form

        if 'users' in data and 'role' in data:
            return Response(
                _("Maintenance form cannot have assigned both role and users."),
                status=status.HTTP_400_BAD_REQUEST)

        if 'users' not in data and 'role' not in data:
            return Response(
                _('Maintenance form must have an assigned role or users.'),
                status=status.HTTP_400_BAD_REQUEST)

        if 'role' in data:
            form.assigned_users.clear()
            try:
                form.assigned_role = Role.objects.get(
                    pk=data['role'])
            except ObjectDoesNotExist:
                text = _('This role does not exists.')
                return Response(
                    '{}: {text}'.format(data['role'], text=text),
                    status=status.HTTP_400_BAD_REQUEST)

            form.save()
            if data['type'] == 'maintenance':
                return Response(
                    MaintenanceFormSerializer(form).data,
                    status=status.HTTP_200_OK
                )
            return Response(
                OperationsFormSerializer(form).data,
                status=status.HTTP_200_OK
            )

        if 'users' in data:
            form.assigned_users.clear()
            form.assigned_role = None
            form.save()

            for u in data['users']:
                try:
                    to_add = AerosimpleUser.objects.get(pk=u)
                except ObjectDoesNotExist:

                    text = _('This user does not exists.')
                    return Response('{}: {text}'.format(u, text=text),
                                    status=status.HTTP_400_BAD_REQUEST)

                # check if the user has permissions to fill maintenance form
                if data['type'] == 'maintenance':
                    perm = 'work_orders.add_maintenance'
                    text = _('This user does not have permissions to fill '
                             'maintenance forms.')
                else:
                    perm = 'work_orders.add_operations'
                    text = _('This user does not have permissions to fill '
                             'operations forms.')

                if to_add.user.has_perm(perm):
                    form.assigned_users.add(to_add)
                else:
                    return Response(
                        {"id": u, "message": text},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            if data['type'] == 'maintenance':
                return Response(
                    MaintenanceFormSerializer(form).data,
                    status=status.HTTP_200_OK
                )
            return Response(
                OperationsFormSerializer(form).data,
                status=status.HTTP_200_OK
            )

    @action(detail=True, methods=['post'])
    def maintenance_review(self, request, pk=None):
        workorder = self.get_object()
        images = []
        if "images" in request.data:
            images = request.data.pop('images', [])
        data = request.data.copy()
        data = request.data.copy()
        data['work_order'] = workorder.id

        published_version = (
            workorder.form.form.maintenance_form.versions.filter(
                status=PUBLISHED).first()
        )
        if published_version is None:
            return Response(
                "no_published_work_order_version",
                status=status.HTTP_400_BAD_REQUEST)

        data['version'] = published_version.id
        serializer = MaintenanceSerializer(
            data=data, context={'request': request})
        try:
            with transaction.atomic():
                serializer.is_valid(raise_exception=True)
                serializer.save()

                workorder.status = OPERATION
                workorder.save()

                for image in images:
                    serializer_image = MaintenanceImageSerializer(
                        data={
                            'maintenance_form': serializer.instance.id,
                            'image': image
                        })
                    serializer_image.is_valid(raise_exception=True)
                    serializer_image.save()
        except ValidationError:
            raise
        # sendMailToOperation(workorder.id, self.request.user.aerosimple_user.airport_id)
        sendMailToMaintenance(
            workorder.id, self.request.user.aerosimple_user.airport_id, serializer.instance.id, "maintenance")
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def operations_review(self, request, pk=None):
        workorder = self.get_object()
        images = []
        if "images" in request.data:
            images = request.data.pop('images', [])
        data = request.data.copy()
        data['work_order'] = workorder.id
        published_version = (
            workorder.form.form.operations_form.versions.filter(
                status=PUBLISHED).first()
        )
        if published_version is None:
            return Response(
                "no_published_work_order_version",
                status=status.HTTP_400_BAD_REQUEST)
        data['version'] = published_version.id
        serializer = OperationsSerializer(
            data=data, context={'request': request})
        try:
            with transaction.atomic():
                serializer.is_valid(raise_exception=True)
                serializer.save()

                workorder.status = COMPLETED
                workorder.save()

                for image in images:
                    serializer_image = OperationsImageSerializer(
                        data={
                            'operations_form': serializer.instance.id,
                            'image': image
                        })
                    serializer_image.is_valid(raise_exception=True)
                    serializer_image.save()
        except ValidationError:
            raise
        # sendmailComplete(workorder.id, self.request.user.aerosimple_user.airport_id)
        sendMailToMaintenance(
            workorder.id, self.request.user.aerosimple_user.airport_id, '', "operation")
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def get_notams(self, request):
        # if not self.request.user.is_authenticated:
        #     return Response(status=status.HTTP_403_FORBIDDEN)
        # icaoId = icaoId+"_"
        icaoId = request.user.aerosimple_user.airport.code
        dynamodb = boto3.resource(
            'dynamodb', region_name=settings.AWS_DEFAULT_REGION)
        table = dynamodb.Table(settings.MAIN_APP_PREFIX + 'notam')
        sourceIds = ['D', 'I']
        item = []
        for x in sourceIds:
            response = table.get_item(
                Key={
                    'notamKey': icaoId+"_"+x
                }
            )
            if "Item" in response:
                for record in response['Item']['records']:
                    item.append(response['Item']['records'][record])
        return Response(item)


class WorkOrderViewSet(mixins.CreateModelMixin,
                       mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet,
                       WorkOrderMixin):
    # def workorder_Export(self,work_order_id):

    def get_queryset(self):
        if self.request.user:
            forms = WorkOrderSchema.objects.filter(
                form__airport__id=self.request.user.aerosimple_user.airport_id
            ).exclude(status=DRAFT)

            result = WorkOrder.objects.none()
            query = self.request.GET.get("query")
            ws = self.request.GET.get("ws")
            sdate = self.request.GET.get("s")
            fdate = self.request.GET.get("f")
            priorityquery =Q(priority__in=[])
            for f in forms:
                if query:
                    maintenanceList = ["maintenance review", "review", "maintenance"]
                    operationList = ["operation review", "review", "operation" ] 
                    """
                    Check If query searched by Priority & Status
                    """
                    if query.lower() == 'low':
                        priorityquery = Q(priority=LOW)
                    elif query.lower() == 'medium':
                        priorityquery = Q(priority=MEDIUM)
                    elif query.lower() == 'high':
                        priorityquery = Q(priority=HIGH)
                    elif query.lower() == 'new':
                        priorityquery = Q(status=NEW)
                    elif query.lower() == 'completed':
                        priorityquery = Q(status=COMPLETED)
                    else:
                        pass
                        # priorityquery = Q(priority__in=[LOW, MEDIUM, HIGH])
                    for i in range(len(maintenanceList)):
                        if maintenanceList[i] == query.lower():
                            priorityquery = Q(status=MAINTENANCE)
                            break
                    for j in range(len(operationList)):
                        if operationList[j] == query.lower():
                            priorityquery = Q(status=OPERATION)
                            break
                    if "review" == query.lower():
                            priorityquery = Q(status=MAINTENANCE) | Q(status=OPERATION)

                    result = result | f.work_orders.filter(Q(category__icontains=query) | Q(subcategory__icontains=query) | Q(
                        problem_description__icontains=query) | Q(report_date__icontains=query) | priorityquery).order_by('-id').all()
                elif (ws and sdate):
                    result = result | f.work_orders.filter(Q(status__in=ws.split(",")), Q(
                        date__range=[sdate, fdate])).order_by('-id').all()
                elif ws:
                    result = result | f.work_orders.filter(
                        Q(status__in=ws.split(","))).order_by('-id').all()
                else:
                    result = result | f.work_orders.order_by('-id').all()

            return result.all()

        return WorkOrder.objects.none()

    def get_serializer_class(self):
        """Return different serializers in list action."""
        if self.action == 'list':
            return WorkOrderListWebSerializer
        elif self.action == 'retrieve':
            return WorkOrderDetailWebSerializer
        return WorkOrderWebSerializer

    def get_permissions(self):
        self.permission_classes = get_permission_for_action(self.action)
        return super(self.__class__, self).get_permissions()

    def create(self, request):
        photos = []
        if "photos" in request.data:
            photos = request.data.pop('photos', [])
        data = request.data.copy()
        if "location" in request.data:
            location = data.pop('location', '')
            data['location'] = json.loads(location[0])
        if "assets" in request.data:
            asset = data.pop('assets', '')
            asset = json.loads(asset[0])
            assetlenth = len(asset)-1
            assets = {}
            asset1 = []
            asset1.append(asset[assetlenth])
            data['assets'] = json.dumps(asset1)
            data.update(data)
        published_version = WorkOrderSchema.objects.filter(
            form__airport__id=self.request.user.aerosimple_user.airport_id,
            status=PUBLISHED).first()
        if published_version is None:
            return Response(
                "no_published_work_order_version",
                status=status.HTTP_400_BAD_REQUEST)
        data['form'] = published_version.id
        serializer = WorkOrderWebSerializer(
            data=data,
            context={'request': request}
        )

        # Get the latest published version for the work order
        try:
            with transaction.atomic():
                serializer.is_valid(raise_exception=True)
                workorder = serializer.save()

                for photo in photos:
                    serializer_photo = WorkOrderImageSerializer(
                        data={'work_order': workorder.id, 'image': photo})
                    serializer_photo.is_valid(raise_exception=True)
                    serializer_photo.save()

                if "assets" in request.data:
                    assets = data.pop('assets', '')
                    # for asset in json.loads(assets):
                    for asset in range(0, len(assets)):
                        s = json.loads(assets[asset])
                        workorder.assets.add(s[0])

        except ValidationError:
            raise
        sendMailToMaintenance(
            workorder.id, self.request.user.aerosimple_user.airport_id, '', "workorder")
        return Response(
            serializer.data, status=status.HTTP_201_CREATED)


class MobileWorkOrderViewSet(viewsets.ModelViewSet,
                             WorkOrderMixin):

    def get_queryset(self):
        if self.request.user:
            forms = WorkOrderSchema.objects.filter(
                form__airport__id=self.request.user.aerosimple_user.airport_id
            ).exclude(status=DRAFT)

            result = WorkOrder.objects.none()
            query = self.request.GET.get("query")

            filter_date = self.request.GET.get("filter_date")
            if filter_date:
                try:
                    filter_date = datetime.strptime(filter_date, '%m/%d/%y')
                except:
                    pass

            for f in forms:
                if query:
                    """
                    Check If query searched by Priority & Status
                    """
                    if query.lower() == 'low':
                        priorityquery = Q(priority=LOW)
                    elif query.lower() == 'medium':
                        priorityquery = Q(priority=MEDIUM)
                    elif query.lower() == 'high':
                        priorityquery = Q(priority=HIGH)
                    else:
                        priorityquery = Q(priority__in=[LOW, MEDIUM, HIGH])

                    result = result | f.work_orders.filter(Q(category__icontains=query) | Q(subcategory__icontains=query) | Q(
                        problem_description__icontains=query) | Q(report_date__icontains=query) | priorityquery).order_by('-id').all()
                else:
                    result = result | f.work_orders.order_by('-id').all()

                if filter_date:
                    result = result.filter(report_date__gte=filter_date)

            return result.all()

        return WorkOrder.objects.none()
    
    def get_serializer_class(self):
        """Return different serializers in list action."""
        if self.action == 'list':
            return MobileWorkOrderSerializer
        elif self.action == 'retrieve':
            return WorkOrderDetailWebSerializer

    def get_paginated_response(self, data):
        return Response(OrderedDict([('items', data)]))

    def get_permissions(self):
        self.permission_classes = get_permission_for_action(self.action)
        return super(self.__class__, self).get_permissions()

    def create(self, request):
        photos = []
        if "photos" in request.data:
            photos = request.data.pop('photos', [])
        data = request.data.copy()
        if "location" in request.data:
            location = data.pop('location', '')
            data['location'] = json.loads(location[0])

        published_version = WorkOrderSchema.objects.filter(
            form__airport__id=self.request.user.aerosimple_user.airport_id,
            status=PUBLISHED).first()
        if published_version is None:
            return Response(
                "no_published_work_order_version",
                status=status.HTTP_400_BAD_REQUEST)
        data['form'] = published_version.id
        serializer = WorkOrderWebSerializer(
            data=data,
            context={'request': request}
        )

        # Get the latest published version for the work order
        try:
            with transaction.atomic():
                serializer.is_valid(raise_exception=True)
                workorder = serializer.save()

                for photo in photos:
                    serializer_photo = WorkOrderImageSerializer(
                        data={'work_order': workorder.id, 'image': photo})
                    serializer_photo.is_valid(raise_exception=True)
                    serializer_photo.save()

                if "assets" in request.data:
                    assets = data.pop('assets', '')
                    for asset in json.loads(assets[0]):
                        workorder.assets.add(asset)
        except ValidationError:
            raise
        sendMailToMaintenance(
            workorder.id, self.request.user.aerosimple_user.airport_id, '', "workorder")
        return Response(
            serializer.data, status=status.HTTP_201_CREATED)


class ExportWorkorderData(viewsets.GenericViewSet):

    def get_permissions(self):
        logger.warning("in workorder pdf")
        switcher = {
            'workorder_data_view': [IsAuthenticated, AirportHasWorkOrderPermission, CanViewWorkOrders],
        }
        logger.warning(switcher)
        self.permission_classes = switcher.get(self.action, [IsAdminUser])
        return super(self.__class__, self).get_permissions()

    @register.simple_tag
    @action(detail=True, methods=['get'])
    def workorder_data_view(self, request, pk):
        date_now = date.today()
        airport = Airport.objects.filter(
            id=request.user.aerosimple_user.airport_id).first()
        workorderdata = WorkOrder.objects.filter(id=pk).get()
        logged_By_id = workorderdata.logged_by_id
        logged_By = AerosimpleUser.objects.filter(
            id=logged_By_id).last().fullname
        notams = workorderdata.notams
        assets = workorderdata.assets.all()
        asset = []
        for a in assets:
            asset.append(a.name)
        notam = []
        for k, v in notams.items():
            notam.append(v)
        context = {
            'airport': airport,
            'workid': workorderdata.id,
            'logby': logged_By,
            'date1': workorderdata.date,
            'location' :workorderdata.location,
            'priority': workorderdata.priority,
            'cat': workorderdata.category,
            'subcat': workorderdata.subcategory,
            'desc1': workorderdata.problem_description,
            'assets': asset,
            'notams': notam,
            'date': date_now,
        }
       
        if Maintenance.objects.filter(work_order_id=pk):
            maintaindata = Maintenance.objects.filter(work_order_id=pk).get()
            mancompid = maintaindata.completed_by_id
            mintenanceCompletedby = AerosimpleUser.objects.filter(
                id=mancompid).last().fullname
            context['maincompby'] = mintenanceCompletedby
            context['date2'] = maintaindata.completed_on
            context['desc2'] = maintaindata.work_description
            context['date'] = date_now
        if Operations.objects.filter(work_order_id=pk):
            operationdata = Operations.objects.filter(work_order_id=pk).get()
            operbyid = operationdata.completed_by_id
            operationsCompletedby = AerosimpleUser.objects.filter(
                id=operbyid).last().fullname
            context['opcompby'] = operationsCompletedby
            context['date3'] = operationdata.completed_on
            context['desc3'] = operationdata.review_report
            context['date'] = date_now
        html_string = render_to_string(
            'workorder-data.html', context=context)
        fileName = '{}-{}-with-data-{}.pdf'.format(
            airport, workorderdata.id, random.randint(0, 999999))
        key = '/tmp/'+fileName
        html = HTML(string=html_string)
        html.write_pdf(target=key)
        bucket = settings.ATTACHMENTS_BUCKET_NAME
        client = boto3.client(
            's3', config=Config(signature_version='s3v4'))
        try:
            client.upload_file(key, bucket, 'workorders/'+fileName)
            os.remove(key)
            url = client.generate_presigned_url('get_object',
                                                Params={
                                                    'Bucket': bucket,
                                                    'Key': 'workorders/'+fileName
                                                },
                                                ExpiresIn=settings.EXPIRY_FOR_EXPORT_DOCUMENT
                                                )
        except Exception as e:
            logger.error("there was an error trying to upload file")

        return HttpResponse(url)
