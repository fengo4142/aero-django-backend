import os
import boto3
from botocore.client import Config
import botocore.session
from boto3.s3.transfer import S3Transfer
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from django.db import models
from airport.models import Airport
from inspections.models import Inspection, InspectionAnswer
from django import template
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.conf.urls.static import static
from  work_orders.models import WorkOrder
import logging

logger = logging.getLogger('backend')

register = template.Library()
@register.simple_tag

def exportInspection(request):
        airport = Airport.objects.filter(id=1).first()
        published_version = Inspection.objects.get(id=4).schema
        context = {
            'airport': airport,
            "pages": published_version['pages'],
            "fields": published_version['fields'],
            "sections": published_version['sections'],
            "title": published_version['id'],
        }
        html_string = render_to_string('empty-inspection.html', context=context)
        fileData = airport.code+'-' +published_version['id']+'.pdf'
        html = HTML(string=html_string)
        html.write_pdf(target=os.environ['DJANGO_MEDIA_DIR']+'/pdf/'+fileData)
        key =os.environ['DJANGO_MEDIA_DIR']+'/pdf/'+fileData
        bucket = 'as-pdf-demo'
        client = boto3.client('s3')
        try:
            emptyfile = client.upload_file(
                key,
               'as-pdf-demo',
               '/inspections/'+fileData
            )
            url = client.generate_presigned_url('get_object', 
                                    Params={'Bucket':bucket ,'Key':'/inspections/'+fileData},ExpiresIn = 86500)  
        except Exception as e:
            logger.error("there was an error trying to upload file")
        return HttpResponse(url)    


def exportInspectionAnswer(request):
        airport = Airport.objects.filter(id=1).first()
        work_orders = WorkOrder.objects.all()
        published_version = Inspection.objects.get(id=4).schema
        insp_answer = InspectionAnswer.objects.filter(id=4).last().response        
        context = {
            'airport': airport,
            'work_orders':work_orders,
            'insp_answer': insp_answer,
            "pages": published_version['pages'],
            "fields": published_version['fields'],
            "sections": published_version['sections'],
            "title": published_version['id'],    
        }
        html_string = render_to_string('checkdata.html', context=context)
        fileName = airport.code + '-' + published_version['id'] + '-answer.pdf'    
        html = HTML(string=html_string)
        html.write_pdf(target=os.environ['DJANGO_MEDIA_DIR']+'/pdf/'+fileName)
        key=os.environ['DJANGO_MEDIA_DIR']+'/pdf/'+fileName
        bucket = 'as-pdf-demo'
        client = boto3.client('s3', config =Config(signature_version='s3v4'))
        try:
            response = client.upload_file(
                key,
                'as-pdf-demo',
               '/inspections/'+fileName

            )
            
            url = client.generate_presigned_url('get_object', 
                                    Params={'Bucket':bucket ,'Key':'/inspections/'+fileName},ExpiresIn = 86500)  
        except Exception as e:
            logger.error("there was an error trying to upload file")
        #LocationConstraint ='us-east-1'    
        #location =boto3.client('s3').get_bucket_location(Bucket=bucket)['LocationConstraint']
        #url = "https://%s.s3.amazonaws.com/%s/%s" %(location,bucket,'/inspection/'+fileName)

        return HttpResponse(url)
