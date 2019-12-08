from django.views import View
from django.http import HttpResponse
from django.core.management import execute_from_command_line

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
import airport, backend, forms, inspections, work_orders, tasks
import operations_log, notification, users, logging
from backend.perm_config import fill_config_with_all_permissions
from backend.init_roles import init_groups, create_super_user
from backend.auth import AerosimpleBackend
from airport.views import AirportViewSet
import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

logger = logging.getLogger('backend')

class CreateMigrate(View):
    def get(self, request):
        # transfer any static images as needed here 
        args = ['manage.py', 'migrate']
        execute_from_command_line(args)
        fill_config_with_all_permissions()
        init_groups()
        create_super_user()
        return HttpResponse('Done')

class RunCollectStatic(View):
    def get(self, request):
        args = ['manage.py', 'collectstatic', '--noinput']
        execute_from_command_line(args)
        return HttpResponse('Done')

class RunViewSet(viewsets.ViewSet):
    def get_permissions(self):
        self.permission_classes = [IsAuthenticated]
        return super(self.__class__, self).get_permissions()
    def list(self, request):
        if AerosimpleBackend.checkAdmin(request.user.username) is not None:
            return HttpResponse(eval(request.GET['expr']))
        else:
            return HttpResponse("No no no...")

class VersionUtil(View):
    def get(self, request):
        return HttpResponse(settings.PROJECT_VERSION)

class BuildUtil(View):
    def get(self, request):
        return HttpResponse(settings.PROJECT_VERSION + '-' + settings.BUILD_VERSION)

class StaticImages(View):
    def get(self, request):
        # transfer any static asset types as needed here
        client = boto3.client('s3', config =Config(signature_version='s3v4'))

        #transfer asset type images to Static Bucket
        assetDir = os.path.realpath(os.path.dirname(__file__)) + settings.ASSET_IMAGES_PATH
        assets = os.listdir( assetDir )
        for asset in assets:
            try:
                client.upload_file(os.path.join(assetDir, asset), settings.AWS_STORAGE_BUCKET_NAME, settings.ASSET_IMAGES_PREFIX + asset)
            except Exception as e:
                logger.error("there was an error trying to upload file: " + e )
        
        #transfer common images to Static Bucket
        commonDir = os.path.realpath(os.path.dirname(__file__)) + settings.NOTIFICATION_IMAGES_PATH
        commonImgs = os.listdir( commonDir )
        for img in commonImgs:
            try:
                client.upload_file(os.path.join(commonDir, img), settings.AWS_STORAGE_BUCKET_NAME, settings.NOTIFICATION_IMAGES_PREFIX + img)
            except Exception as e:
                logger.error("there was an error trying to upload file: " + e )

        return HttpResponse('Done')
            
