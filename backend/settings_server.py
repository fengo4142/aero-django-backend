from .settings_base import *  # noqa: F403,F401

import os
import json
import requests
import boto3

from jwt.algorithms import RSAAlgorithm

ADMINS = [('AeroAdmin', 'admin.dev@aerosimple.com')]

CORS_ALLOW_CREDENTIALS = True

CORS_ORIGIN_WHITELIST = []
CORS_ORIGIN_WHITELIST.append(UI_DOMAIN)
SYSTEM_SUBDOMAINS = [
    'app',
    'admin',
    'portal',
]
for subdomain in SYSTEM_SUBDOMAINS:
    CORS_ORIGIN_WHITELIST.append(subdomain + '.' + BASE_DOMAIN)

CORS_ORIGIN_WHITELIST.append('app.' + BASE_DOMAIN + ':8888')
CORS_ORIGIN_WHITELIST.append('app.' + BASE_DOMAIN + ':3000')

# CORS_ORIGIN_REGEX_WHITELIST = [
#     r"^https://\w+\." + BASE_DOMAIN.replace('.', r'\.') + "$",
# ]

ALLOWED_HOSTS = [
    'api.' + UI_DOMAIN,
    'backend.' + UI_DOMAIN,
    'backend.app.' + BASE_DOMAIN,
]

WSGI_APPLICATION = 'backend.wsgi_server.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ['PROJECT_DATABASE_NAME'],
        'USER': os.environ['PROJECT_DATABASE_USERNAME'],
        'PASSWORD': os.environ['PROJECT_DATABASE_PASSWORD'],
        'HOST': os.environ['PROJECT_DATABASE_HOST'],
        'OPTIONS': {
            'sslmode': 'disable'
        }
    }
}

HTTP_REQUEST_LOGGING = os.environ.get('HTTP_REQUEST_LOGGING', 'INFO')
HTTP_REQUEST_LOGGING_ENABLE = True if os.environ.get('HTTP_REQUEST_LOGGING') is not None else False

LOGGING = {
    # Version del logging
    'version': 1,
    # Flag que deshabilita los loggers por defecto de Django
    'disable_existing_loggers': False,
    # Se define el formato de los logs para cada handler.
    'formatters': {
        'verbose': {
            'format':
            ('%(levelname)s | %(asctime)s | %(thread)d | %(name)s | %(module)s' +
             ' | %(filename)s | %(process)d | %(lineno)d | %(funcName)s' +
             ' | %(message)s'),
            'datefmt':
            "%d/%m/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'email_backend': 'django.core.mail.backends.smtp.EmailBackend'
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'console_request': {
            'level': HTTP_REQUEST_LOGGING,
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'backend': {
            'handlers': ['console', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
        'django': {
            'handlers': ['console', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console_request'],
            'level': HTTP_REQUEST_LOGGING,
            'propagate': False,
        } if HTTP_REQUEST_LOGGING_ENABLE else None,
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
SERVER_EMAIL = os.environ['FROM_EMAIL_ADDRESS']
DEFAULT_FROM_EMAIL = os.environ['FROM_EMAIL_ADDRESS']

EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
EMAIL_USE_TLS = False if os.environ.get('EMAIL_DISABLE_TLS') is not None else True

DEFAULT_FILE_STORAGE = 'backend.media_s3_storage.MediaStorage'
STATICFILES_STORAGE = 'backend.static_s3_storage.StaticStorage'
AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
ATTACHMENTS_BUCKET_NAME = os.environ['ATTACHMENTS_BUCKET_NAME']
# AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
# AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_S3_FILE_OVERWRITE = False
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_REGION_NAME = AWS_REGION
AWS_DEFAULT_ACL = os.environ.get('AWS_DEFAULT_ACL')
AWS_S3_CUSTOM_DOMAIN = 'static.' + UI_DOMAIN

STATIC_ROOT = '/static/'
MEDIA_URL = 'https://static.' + UI_DOMAIN + '/media/'
STATIC_URL = 'https://static.' + UI_DOMAIN + '/static-django/'

BACKEND_API_URL = 'https://backend.' + UI_DOMAIN + '/api'
APP_PREFIX = os.environ.get('APP_PREFIX', 'aero_' + STAGE + '_')
MAIN_APP_PREFIX = os.environ.get('MAIN_APP_PREFIX', APP_PREFIX)
COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')

for inst in boto3.resource('dynamodb', region_name=AWS_DEFAULT_REGION).Table(APP_PREFIX + 'installation').scan()['Items']:
    CORS_ORIGIN_WHITELIST.append(inst['id'] + '.' + BASE_DOMAIN)

