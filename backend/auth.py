import jwt
import boto3

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend, UserModel
from django.utils.encoding import smart_text
from django.utils.translation import ugettext as _
from rest_framework import exceptions
from django.conf import settings

from rest_framework.authentication import (
    BaseAuthentication, get_authorization_header
)

from rest_framework_jwt.settings import api_settings
from django.contrib.auth.models import User

jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER

import logging
logger = logging.getLogger('backend')

class AerosimpleBackend(ModelBackend):

    @staticmethod
    def checkAdmin(username):
        if settings.ADMIN_AUTHORIZED:
            return {'sub': username}
        if username is not None and len(username) > 0:
            logger.info('Auth username is {}'.format(username))
            client = boto3.client('cognito-idp', settings.AWS_DEFAULT_REGION)
            existing_user = client.admin_list_groups_for_user(
                            UserPoolId=settings.COGNITO_USER_POOL_ID,
                            Username=username
                        )
            if len(existing_user['Groups']) > 0:
                if len(list(filter(lambda grp: 'AeroAdmin' in grp['GroupName'], existing_user['Groups']))) > 0:
                    return {'sub': username}
        return None

    def authenticate(self, request=None, username=None, password=None, **kwargs):

        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if password is None:
            password = kwargs.get(UserModel.PASSWORD_FIELD)

        # user = super().authenticate(request, username, password)
        # if user is not None:
        #     return user

        jwt_value = password
        if jwt_value is None:
            return None

        try:
            payload = jwt_decode_handler(jwt_value)
        except jwt.ExpiredSignature:
            msg = _('Signature has expired.')
            raise exceptions.AuthenticationFailed(msg)
        except jwt.DecodeError:
            msg = _('Error decoding signature.')
            raise exceptions.AuthenticationFailed(msg)
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed()

        logger.info(payload)
        user = self.authenticate_credentials(payload)

        if user.email == username:
            return user
        else:
            msg = _('Email provided does not match with the user')
            raise exceptions.AuthenticationFailed(msg)

    def authenticate_credentials(self, payload):
        """
        Returns an active user that matches the payload's user id and email.
        """
        User = get_user_model()
        username = jwt_get_username_from_payload(payload)

        if not username:
            msg = _('Invalid payload.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            user = User.objects.get_by_natural_key(username)
        except User.DoesNotExist:
            msg = _('User does not exist.')
            raise exceptions.AuthenticationFailed(msg)

        if not user.is_active:
            msg = _('User account is disabled.')
            raise exceptions.AuthenticationFailed(msg)

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except Exception:
            #Djano Admin treats None user as anonymous your who have no right at all.
            logger.error('problem fetching user')
            return None

