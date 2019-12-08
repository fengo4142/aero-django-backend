"""Settings for  development enviroment."""

from .settings_base import *  # noqa: F403,F401
from celery.schedules import crontab

import os
import json
import requests
import boto3

from jwt.algorithms import RSAAlgorithm

ROOT_URLCONF = 'backend.urls_development'
DEBUG = True

EXTERNAL_BACKEND_HOST = os.environ.get('EXTERNAL_BACKEND_HOST')

ALLOWED_HOSTS = ['*']

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

CORS_ORIGIN_WHITELIST = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ['DJANGO_DATABASE_NAME'],
        'USER': os.environ['DJANGO_DATABASE_USERNAME'],
        'PASSWORD': os.environ['DJANGO_DATABASE_PASSWORD'],
        'HOST': 'postgres',
    }
}

MEDIA_URL = 'http://localhost:8000/media/'
MEDIA_ROOT = os.environ['DJANGO_MEDIA_DIR']
MEDIA_URL_PATH = '/media/'

LOGGING = {
    # Version del logging
    'version': 1,
    # Flag que deshabilita los loggers por defecto de Django
    'disable_existing_loggers': False,
    # Se define el formato de los logs para cada handler.
    'formatters': {
        'verbose': {
            'format':
            '%(levelname)s | %(asctime)s | %(name)s | %(process)d | %(thread)d | '
            '%(module)s | %(filename)s | %(funcName)s | %(lineno)d | %(message)s',
            'datefmt':
            "%d/%b/%Y %H:%M:%S"
        },
        # Este formato se pretende usar para imprimir en consola, a modo de debug
        'simple': {
            'format':
            '%(levelname)s | %(name)s | %(filename)s | %(funcName)s | %(lineno)d | '
            '%(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
    },
    # Se definen dos handlers para develop: Console y File.
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    # Se redefinen dos loggers para satisfacer los requisitos
    'loggers': {
        'backend': {
            'handlers': [
                'console',
            ],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django': {
            'handlers': [
                'console',
            ],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',  # change debug level as appropiate
            'propagate': False,
        },
    }
}

CENTRAL_REPO_URL = 'http://nginx:8001'

# In production use this should not use .get but dict access (['CENTRAL_REPO_API_KEY'])
CENTRAL_REPO_API_KEY = os.environ.get('CENTRAL_REPO_API_KEY')
# ###########################################################################
# Celery
# ###########################################################################
# BROKER_URL = 'redis://redis:6379'
CELERY_IGNORE_RESULT = True
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ['application/json']

CELERYBEAT_SCHEDULE = {
    'fetch_templates': {
        'task': 'fetch_templates',
        'schedule': crontab(hour='*/1'),
    }
}

BACKEND_API_URL = 'http://localhost:8000/api'
APP_PREFIX = 'aero_dev_'
MAIN_APP_PREFIX = 'aero_dev_'
AWS_S3_REGION_NAME = 'us-east-1'

COGNITO_USER_POOL_ID = 'us-east-1_UvLhMSQa4'
AWS_STORAGE_BUCKET_NAME = 'aero-dev-local-static'
ATTACHMENTS_BUCKET_NAME = 'aero-dev-local-attachments'
#EXPIRY_FOR_EXPORT_DOCUMENT in seconds
EXPIRY_FOR_EXPORT_DOCUMENT = 300
UI_DOMAIN = 'localhost'

# no plans for local mode
AIRPORT_PLAN_ENABLE = False

ADMIN_AUTHORIZED = True
