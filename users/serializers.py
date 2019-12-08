from rest_framework import serializers

from django.contrib.auth.models import User, Permission
from rest_framework.serializers import ValidationError, SerializerMethodField
from django.utils.translation import ugettext_lazy as _

from users.models import AerosimpleUser, Role
from airport.serializers import AirportSerializer, AirportWebSerializer
import logging
from airport.models import Airport
from django.conf import settings
from airport.utils import DynamoDbModuleUtility

logger = logging.getLogger('backend')


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'email',)


class MobileUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id',)


# class PrivilegeListSerializer(serializers.ListSerializer):
#     def add_cat(self, validated_data):

        # class PrivilegeSerializer(serializers.Serializer):
        #     #id: serializers.Integer

        #     def get_permissions(self, obj):
        #         return obj.permission_group.permissions.all()


class PermissionSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()

    class Meta:
        model = Permission
        fields = ('id', 'codename', 'content_type_id', 'category')

    def get_category(self, obj):
        return settings.PRIVILEGE_TYPES.get(obj.content_type_id, 'Default')

    def get_permissions(self, obj):
        return obj.permission_group.permissions.all()


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ('id', 'name', 'permissions', 'system_generated')

    def get_permissions(self, obj):
        return PermissionSerializer(
            obj.permission_group.permissions.all(), many=True).data


class RoleSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Role
        fields = ('id', 'name', 'airport_id')


class AerosimpleUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AerosimpleUser
        fields = ('fullname', 'first_name', 'last_name', 'language', 'image', 'phone', 'designation', 'notification_preferences')



class AerosimpleUserSerializer(serializers.ModelSerializer):
    airport = AirportWebSerializer()
    user = UserSerializer()
    roles = serializers.SerializerMethodField()
    authorized_airports = AirportSerializer(many=True)
    airport_permissions = serializers.SerializerMethodField()

    def get_roles(self, obj):
        serializer = RoleSerializer(
            obj.roles.filter(airport=obj.airport), many=True)
        return serializer.data

    def get_airport_permissions(self, obj):
        return DynamoDbModuleUtility.get_plan_data(obj.airport.code)

    class Meta:
        model = AerosimpleUser
        fields = '__all__'


class AerosimpleUserProfileSerializer(serializers.ModelSerializer):
    airport = AirportSerializer()
    user = MobileUserSerializer()

    class Meta:
        model = AerosimpleUser
        fields = '__all__'


class AerosimpleCreateUserSerializer(serializers.ModelSerializer):
    email = serializers.CharField(write_only=True)

    class Meta:
        model = AerosimpleUser
        fields = ('fullname', 'first_name', 'last_name', 'email', 'roles')

    def validate(self, data):
        exists = User.objects.filter(email=data['email']).exists()
        if exists:
            raise ValidationError({'email': _('this email is already in use')})

        return data

    def create(self, validated_data):
        u = User()
        u.email = validated_data['email']
        u.save()

        aerouser = AerosimpleUser()
        aerouser.user = u
        aerouser.airport = self.context['request'].user.aerosimple_user.airport
        aerouser.first_name = validated_data['first_name']
        aerouser.last_name = validated_data['last_name']
        aerouser.fullname = aerouser.first_name + ' ' + aerouser.last_name
        aerouser.save()
        aerouser.authorized_airports.add(
            self.context['request'].user.aerosimple_user.airport)
        if 'roles' in validated_data:
            for r in validated_data['roles']:
                aerouser.roles.add(r)
        # aerouser.save()
        return validated_data


class AerosimpleUserSimpleSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()

    def get_roles(self, obj):
        serializer = RoleSerializer(obj.roles.filter(
            airport=self.context['request'].user.aerosimple_user.airport), many=True)
        return serializer.data

    class Meta:
        model = AerosimpleUser
        fields = ('id', 'fullname', 'first_name', 'last_name', 'email', 'roles')

    def get_email(self, obj):
        return '{}'.format(obj.user.email)


class AerosimpleUserDisplaySerializer(serializers.ModelSerializer):

    class Meta:
        model = AerosimpleUser
        fields = ('fullname', 'first_name', 'last_name', 'id')


class UserTypeSerializer(serializers.ModelSerializer):
    description = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ('id', 'name', 'description')

    def get_description(self, obj):
        return '{}'.format(obj.name)


class MobileAerosimpleUserSerializer(serializers.ModelSerializer):
    roles = RoleSimpleSerializer(many=True)

    class Meta:
        model = AerosimpleUser
        fields = ('id', 'fullname', 'first_name', 'last_name', 'roles')


class MobileProfileUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id']


class MobileAirportSerializer(serializers.ModelSerializer):
    location = SerializerMethodField()
    iataCode = SerializerMethodField()
    countryCode = SerializerMethodField()
    typesForSelfInspection = SerializerMethodField()
    defaultLanguage = SerializerMethodField()

    class Meta:
        model = Airport
        fields = ('id', 'location', 'name', 'code', 'iataCode', 'countryCode', 'website', 'typesForSelfInspection',
                  'defaultLanguage', 'logo')

    def get_location(self, obj):
        if obj.location:
            return {'coordinates': [{'lon': obj.location.x, 'lat': obj.location.y}]}
        else:
            return None

    def get_iataCode(self, obj):
        return obj.iata_code

    def get_countryCode(self, obj):
        return obj.country_code

    def get_typesForSelfInspection(self, obj):
        return obj.types_for_self_inspection

    def get_defaultLanguage(self, obj):
        return obj.default_language


class AerosimpleMobileProfileSerializer(serializers.ModelSerializer):
    airport = MobileAirportSerializer()
    user = MobileProfileUserSerializer()
    roles = SerializerMethodField()
    users = SerializerMethodField()
    permissions = SerializerMethodField()

    class Meta:
        model = AerosimpleUser
        fields = ('airport', 'user', 'roles', 'users', 'permissions')

    def get_roles(self, obj):
        role_list = []
        role_dict = {}
        for user in AerosimpleUser.objects.filter(id=obj.id):
            for role in user.roles.all():
                role_dict['id'] = role.id
                role_dict['name'] = role.name
                role_dict['airport_id'] = role.airport.id
                permission_list = []
                for permission in role.permission_group.permissions.all():
                    permission_list.append(permission.id)
                role_dict['permissions'] = permission_list
                role_list.append(role_dict.copy())
        return role_list

    def get_users(self, obj):
        users = []
        airport_data = AerosimpleUser.objects.filter(authorized_airports__in=[obj.airport.id])
        for user in airport_data:
            role_list = []
            #if user.id != obj.id:
            if user.image:
                image = user.image.url
            else:
                image = None
            for role in user.roles.all():
                role_list.append(role.id)
            users.append({"id": user.id, "firstName": user.first_name, "lastName": user.last_name,
                            "dateJoined": user.user.date_joined, "email": user.user.email, "phone": user.phone,
                            "language": user.language, "image": image, "roles": role_list})

        return users

    def get_permissions(self, obj):
        permission_list = []
        permissions = set()
        for user in AerosimpleUser.objects.filter(id=obj.id):
            for role in user.roles.all():
                for permission in role.permission_group.permissions.all():
                    if permission.name not in permissions:
                        permissions.add(permission.name)
                        permission_list.append(
                            {"id": permission.id, "codename": permission.name})

        return permission_list


class AerosimpleUserAssignmentSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()

    class Meta:
        model = AerosimpleUser
        fields = ('id', 'fullname', 'first_name', 'last_name', 'email')

    def get_email(self, obj):
        return '{}'.format(obj.user.email)
