from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
import logging
import boto3
import os
from django.contrib.postgres.fields import JSONField
import time

from forms.models import PasswordModelField

logger = logging.getLogger('backend')


class Role(models.Model):
    name = models.CharField(max_length=100)
    airport = models.ForeignKey(
        'airport.Airport', related_name='roles', on_delete=models.CASCADE)
    permission_group = models.ForeignKey(
        Group, related_name='roles', on_delete=models.CASCADE)
    system_generated = models.BooleanField(default=False)

    def __str__(self):
        return "{} ({})".format(self.name, self.airport.code)


class SingletonModel(models.Model):

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class PermissionConfig(SingletonModel):
    permissions = models.ManyToManyField(Permission, related_name='config')


class AerosimpleUser(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name="aerosimple_user",
        on_delete=models.CASCADE)

    fullname = models.CharField(max_length=100, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)

    airport = models.ForeignKey('airport.Airport', related_name='users', on_delete=models.SET_NULL, 
        null=True, blank=True)

    authorized_airports = models.ManyToManyField('airport.Airport')

    roles = models.ManyToManyField(Role, related_name='users')
    language = models.CharField(max_length=10, default="en")

    image = models.ImageField(upload_to='profile/', blank=True, null=True)
    phone = models.CharField(max_length=16, blank=True, null=True, help_text='Contact phone number')

    system_generated = models.BooleanField(default=False)

    designation = models.CharField(max_length=100, blank=True, null=True)

    notification_preferences = JSONField(default=dict, null=True, blank=True)

    # access_pin = PasswordModelField(max_length=128, def)
    access_pin = models.CharField(max_length=4, default='0000')

    def __str__(self):
        return "{} ({})".format(self.fullname, self.airport_codes())

    def email(self):
        return self.user.email

    # def set_access_pin(self, raw_pin):
    #     import random
    #     algo = 'sha1'
    #     salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
    #     hsh = get_hexdigest(algo, salt, raw_password)
    #     self.access_pin = '%s$%s$%s' % (algo, salt, hsh)

    def airport_codes(self):
        try:
            codes_str = ''
            for airport in self.authorized_airports.all():
                codes_str += ', ' + airport.code
            if len(codes_str) > 0:
                return codes_str[2:]
            else:
                return '_'
        except:
            return '_'

    def has_permission(self, perm):
        """
            Returns airport level permission
        """
        current_airport_roles = self.roles.filter(airport=self.airport).filter(
            permission_group__permissions__codename=perm)
        if current_airport_roles:
            return True
        return False

    def save(self, *args, **kwargs):
        if self.pk is None:
            client = boto3.client('cognito-idp', region_name=settings.AWS_DEFAULT_REGION)
            # try:
            #     # Check if the user exists in Cognito
            #     existing_user = client.admin_get_user(Username=self.user.email,
            #         UserPoolId=settings.COGNITO_USER_POOL_ID)
            # except client.exceptions.UserNotFoundException:
            #     pass
            try:
                # if not existing_user:
                response = client.admin_create_user(
                    UserPoolId=settings.COGNITO_USER_POOL_ID,
                    Username=self.user.email,
                    DesiredDeliveryMediums=['EMAIL'],
                    UserAttributes=[
                        {
                            'Name': 'custom:backend_url',
                            'Value': settings.BACKEND_API_URL
                        },
                        {
                            'Name': 'custom:backend_id',
                            'Value': settings.BACKEND_ID
                        },
                        {
                            'Name': 'email_verified',
                            'Value': 'true'
                        },
                        {
                            'Name': 'email',
                            'Value': self.user.email
                        },
                        {
                            'Name': 'family_name',
                            'Value': self.last_name if self.last_name else ' '
                        },
                        {
                            'Name': 'given_name',
                            'Value': self.first_name if self.first_name else ' '
                        },
                        {
                            'Name': 'phone_number',
                            'Value': self.phone if self.phone else ' '
                        },
                    ],
                )
                self.user.username = response['User']['Username']
                if(len(response['User']['Username']) < 3):
                    logger.error("empty response from cognito for email - " + self.user.email)
                    logger.error(response)
                    self.user.delete()
                else:
                    self.user.save()
                # else:
                    # self.user.username = existing_user['Username']
                    # self.user.save()
            except client.exceptions.UsernameExistsException:
                # existing_user = client.admin_get_user(Username=self.user.email,UserPoolId=settings.COGNITO_USER_POOL_ID)
                existing_user = client.admin_get_user(
                    UserPoolId=settings.COGNITO_USER_POOL_ID,
                    Username=self.user.email
                )
                self.user.username = existing_user['Username']
                self.user.save()
            except Exception as e:
                logger.error(
                    "there was an error trying to create cognito user", e)
                self.user.delete()
        # else:
        #     if self.airport is not None:
        #         self.authorized_airports.add(self.airport)
        client = boto3.client('cognito-idp', region_name=settings.AWS_DEFAULT_REGION)
        response = client.admin_update_user_attributes(
                        UserPoolId=settings.COGNITO_USER_POOL_ID,
                        Username=self.user.email,
                        UserAttributes=[
                            {
                                'Name': 'email_verified',
                                'Value': 'true'
                            },
                            {
                                'Name': 'email',
                                'Value': self.user.email
                            },
                            {
                                'Name': 'family_name',
                                'Value': self.last_name if self.last_name else ' '
                            },
                            {
                                'Name': 'given_name',
                                'Value': self.first_name if self.first_name else ' '
                            },
                            {
                                'Name': 'phone_number',
                                'Value': self.phone if self.phone else ' '
                            },
                        ],
                )
        # dynamodb create/update user record with userId self.user.username
        timestamp = int(time.time() * 1000)
        airportDetails = []
        permissions = []
        permission_for_role = set()
        if self.pk is not None:
            for airport in self.authorized_airports.all():
                for role in self.roles.all():
                    if airport.code == role.airport.code:
                        for permission in role.permission_group.permissions.all():
                            permission_for_role.add(permission.codename)
                        permissions.append({'permissions': permission_for_role, 'rolename': role.name})
                        permission_for_role = set()
                airportDetails.append({'id': airport.id, 'code': airport.code, 'name': airport.name, 'permissions': permissions})
                permissions = []
        tableName = settings.APP_PREFIX + settings.BACKEND_ID + '_users'
        dynamodb = boto3.resource('dynamodb')
        user_table = dynamodb.Table(tableName)
        checkUser = user_table.get_item(
            Key = {
                'userId':self.user.username
            }
        )
        if 'Item' in checkUser:
            updateExp = "SET lastName = :lastName, firstName = :firstName, #language = :language, phone = :phone, title = :title, airportId = :airportId, updatedAt = :updatedAt "
            item = {}
            item[':lastName'] = self.last_name if self.last_name else ' '
            item[':firstName'] = self.first_name if self.first_name else ' '
            item[':language'] = self.language if self.language else ' '
            item[':phone'] = self.phone if self.phone else ' '
            item[':title'] = self.designation if self.designation else ' '
            item[':updatedAt'] = timestamp
            item[':airportId'] = self.airport.code if self.airport else 'AAAA'
            try:
                item[':profilePicture'] = self.image.url if self.image and self.image.url else ' '
                updateExp += ', profilePicture=:profilePicture'
            except:
                pass
            updateExpNames = {}
            updateExpNames['#language'] = 'language'
            user_table.update_item(
                Key =  {
                            'userId': self.user.username
                    },
                    ExpressionAttributeValues=item,
                    UpdateExpression=updateExp,
                    ExpressionAttributeNames=updateExpNames,
            )
        else:
            item = {}
            item['userId'] = self.user.username
            item['email'] = self.user.email
            item['lastName'] = self.last_name if self.last_name else ' '
            item['firstName'] = self.first_name if self.first_name else ' '
            item['airportId'] = self.airport.code if self.airport else 'AAAA'
            item['language'] = self.language if self.language else ' '
            item['phone'] = self.phone if self.phone else ' '
            item['title'] = self.designation if self.designation else ' '
            item['createdAt'] = timestamp
            item['updatedAt'] = timestamp
            try:
                item['profilePicture'] = self.image.url if self.image and self.image.url else ' '
            except:
                pass
            item['airportDetails'] = airportDetails
            user_table.put_item(Item=item)
        super(AerosimpleUser, self).save(*args, **kwargs)

    @staticmethod
    def update_dynamodb(instance):
        tableName = settings.APP_PREFIX + settings.BACKEND_ID + '_users'
        dynamodb = boto3.resource('dynamodb')
        user_table = dynamodb.Table(tableName)
        timestamp = int(time.time() * 1000)
        airportDetails = []
        permissions = []
        permission_for_role = set()
        for airport in instance.authorized_airports.all():
            for role in instance.roles.all():
                if airport.code == role.airport.code:
                    for permission in role.permission_group.permissions.all():
                        permission_for_role.add(permission.codename)
                    permissions.append({'permissions': permission_for_role, 'rolename': role.name})
                    permission_for_role = set()
            airportDetails.append({'id': airport.id, 'code': airport.code, 'name': airport.name, 'permissions': permissions})
            permissions = []
        updateExp = "SET airportDetails = :airportDetails, updatedAt = :updatedAt"
        item = {}
        item[':airportDetails'] = airportDetails
        item[':updatedAt'] = timestamp
        user_table.update_item(
            Key = {
                'userId': instance.user.username
            },
            ExpressionAttributeValues=item,
            UpdateExpression=updateExp,
        )


@receiver(m2m_changed, sender=AerosimpleUser.roles.through)
def add_permissions(sender, instance, action, **kwargs):
    instance.user.groups.clear()
    for role in instance.roles.all():
        instance.user.groups.add(role.permission_group)
    #dynamodb update airport permissions
    AerosimpleUser.update_dynamodb(instance)

@receiver(m2m_changed, sender=AerosimpleUser.authorized_airports.through)
def update_authorized_airport_data(sender, instance, action, **kwargs):
    if len(instance.authorized_airports.all()) > 0:
        instance.airport = instance.authorized_airports.first()
        instance.save()
        instance.user.language = instance.airport.default_language
        instance.user.save()
    # dynamodb update authorized airport
    AerosimpleUser.update_dynamodb(instance)