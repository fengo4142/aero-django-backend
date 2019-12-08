import jwt
import boto3

from django.contrib.auth import get_user_model
from django.utils.encoding import smart_text
from django.utils.translation import ugettext as _
from rest_framework import exceptions
from rest_framework.authentication import (
    BaseAuthentication, get_authorization_header
)

from rest_framework_jwt.settings import api_settings
from django.conf import settings
from users.models import AerosimpleUser
from airport.models import Airport

import logging
logger = logging.getLogger('backend')

jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER


class BaseJSONWebTokenAuthentication(BaseAuthentication):
    """
    Token based authentication using the JSON Web Token standard.
    """

    def authenticate(self, request):
        """
        Returns a two-tuple of `User` and token if a valid signature has been
        supplied using JWT-based authentication.  Otherwise returns `None`.
        """
        jwt_value = self.get_jwt_value(request)
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

        user = self.authenticate_credentials(payload)

        return (user, jwt_value)

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
            try:
                # create user
                client = boto3.client('cognito-idp', region_name=settings.AWS_DEFAULT_REGION)
                cognito_user = client.admin_get_user(
                    UserPoolId=settings.COGNITO_USER_POOL_ID,
                    Username=username
                )
                logger.info(cognito_user)
                user = User()
                user.email = username + '@aerosimple.com'
                for attr in cognito_user['UserAttributes']:
                    if(attr['Name'] == 'email'):
                        user.email = attr['Value']
                    if(attr['Name'] == 'family_name'):
                        user.last_name = attr['Value']
                    if(attr['Name'] == 'given_name'):
                        user.first_name = attr['Value']
                user.username = username
                user.save()
                aero_user = AerosimpleUser()
                aero_user.user = user
                aero_user.airport = Airport.objects.filter(code='AAAA')[0]
                aero_user.first_name = user.first_name
                aero_user.first_name = user.last_name
                aero_user.fullname = user.first_name + ' ' + user.last_name
                aero_user.system_generated = True
                aero_user.save()            
            except Exception as e:
                logging.error('Error at user creation', exc_info=e)
                msg = _('Problem in backend user creation')
                raise exceptions.AuthenticationFailed(msg)

        if not user.is_active:
            msg = _('User account is disabled.')
            raise exceptions.AuthenticationFailed(msg)

        return user


class JSONWebTokenAuthentication(BaseJSONWebTokenAuthentication):
    """
    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string specified in the setting
    `JWT_AUTH_HEADER_PREFIX`. For example:

        Authorization: JWT eyJhbGciOiAiSFMyNTYiLCAidHlwIj
    """
    www_authenticate_realm = 'api'

    def get_jwt_value(self, request):
        auth = get_authorization_header(request).split()
        auth_header_prefix = api_settings.JWT_AUTH_HEADER_PREFIX.lower()

        if not auth:
            if api_settings.JWT_AUTH_COOKIE:
                return request.COOKIES.get(api_settings.JWT_AUTH_COOKIE)
            return None

        if smart_text(auth[0].lower()) != auth_header_prefix:
            return None

        if len(auth) == 1:
            msg = _('Invalid Authorization header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid Authorization header. Credentials string '
                    'should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        return auth[1]

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        return '{0} realm="{1}"'.format(api_settings.JWT_AUTH_HEADER_PREFIX, self.www_authenticate_realm)
