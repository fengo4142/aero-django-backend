import logging
import json
import itertools

from operator import itemgetter
from django.db import transaction
from django.conf import settings
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import Group, Permission, User
from rest_framework.serializers import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.core.serializers.json import DjangoJSONEncoder

from users.permissions import CanViewRoles, CanCreateRoles, CanEditRoles, \
    CanCreateUsers, CanEditUsers
from users.models import AerosimpleUser, Role, PermissionConfig
from users.serializers import AerosimpleUserSimpleSerializer, RoleSerializer, \
    PermissionSerializer, AerosimpleUserUpdateSerializer, \
    AerosimpleUserSerializer, AerosimpleCreateUserSerializer, \
    UserTypeSerializer, MobileAerosimpleUserSerializer, AerosimpleUserProfileSerializer,\
    AerosimpleMobileProfileSerializer
from users.filters import UserFilter
from users.pagination import UserPagination
from collections import OrderedDict
from airport.utils import DynamoDbModuleUtility
from airport.models import Airport

logger = logging.getLogger('backend')


def get_user_permission_for_action(action):
    switcher = {
        'list': [IsAuthenticated],
        'retrieve': [IsAuthenticated],
        'create': [IsAuthenticated, CanCreateUsers],
        'partial_update': [IsAuthenticated, CanEditUsers],
        'profile': [IsAuthenticated],
        'update_language': [IsAuthenticated],
    }
    return switcher.get(action, [IsAdminUser])


class AerosimpleUserViewSet(mixins.CreateModelMixin,
                            mixins.UpdateModelMixin,
                            viewsets.ReadOnlyModelViewSet):
    filter_class = UserFilter
    pagination_class = UserPagination

    @staticmethod
    def create_user(request, airport, serializer):
        users = User.objects.filter(email=request.data['email'])
        if len(users) > 0:
            user = users[0]
            aero_user = AerosimpleUser.objects.filter(user=user)
            if len(aero_user) == 0:
                aero_user = AerosimpleUser()
                aero_user.user = user
            else:
                aero_user = aero_user[0]
            aero_user.first_name = request.data['first_name']
            aero_user.last_name = request.data['last_name']
            aero_user.fullname = aero_user.first_name + ' ' + aero_user.last_name
            aero_user.system_generated = False
            aero_user.save()
            aero_user.authorized_airports.add(
                request.user.aerosimple_user.airport)
            aero_user.authorized_airports.remove(
                Airport.objects.filter(code='AAAA')[0])
            if 'roles' in request.data:
                for r in request.data['roles']:
                    aero_user.roles.add(r)
            return Response('User added to airport', status=status.HTTP_201_CREATED)
        user_count = AerosimpleUser.objects.filter(
            system_generated=False,
            airport=airport).count()
        if settings.AIRPORT_PLAN_ENABLE:
            if user_count >= int(settings.AIRPORT_PLANS[
                    request.user.aerosimple_user.airport.code].get('users', 2)):
                return Response(
                    'The user creation count limit has been reached.',
                    status=status.HTTP_403_FORBIDDEN
                )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        return AerosimpleUserViewSet.create_user(request, 
            self.request.user.aerosimple_user.airport, self.get_serializer(data=request.data))

    def partial_update(self, request, *args, **kwargs):
        # add extra roles
        user = AerosimpleUser.objects.get(pk=request.path.split('/')[-2])
        if 'roles' in request.data:
            for rl in user.roles.all():
                if rl.airport.code != self.request.user.aerosimple_user.airport.code:
                    request.data['roles'].append(rl.id)
        user.fullname=request.data['first_name'] +" " + request.data['last_name']
        self.view_object = user
        return super(AerosimpleUserViewSet, self).partial_update(request, *args, **kwargs)

    def get_object(self):
        if self.view_object:
            return self.view_object
        return super(AerosimpleUserViewSet, self).get_object()

    def get_queryset(self):
        if self.request.user:
            logger.info(self.request.user)
            users = AerosimpleUser.objects.filter(
                authorized_airports__in=[self.request.user.aerosimple_user.airport_id],
                user__is_staff=False
            ).order_by('fullname')
            return users
        return AerosimpleUser.objects.none()

    def get_permissions(self):
        self.permission_classes = get_user_permission_for_action(self.action)
        return super(self.__class__, self).get_permissions()

    def get_serializer_class(self):
        """Return different serializers in update action."""
        if self.action == 'partial_update':
            return AerosimpleUserUpdateSerializer
        if self.action == 'create':
            return AerosimpleCreateUserSerializer
        return AerosimpleUserSimpleSerializer

    @action(detail=False, methods=['get'])
    def profile(self, request):
        if self.request.user:
            if request.user.aerosimple_user.airport is None:
                request.user.aerosimple_user.airport = request.user.aerosimple_user.authorized_airports.first()
                request.user.aerosimple_user.save()
            airport = request.user.aerosimple_user.airport
            if airport:
                DynamoDbModuleUtility.fetch_module_permissions(airport.code)
            return Response(
                AerosimpleUserSerializer(
                    self.request.user.aerosimple_user).data,
                status=status.HTTP_200_OK)

        return Response(status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'])
    def update_language(self, request):
        aerouser = AerosimpleUser.objects.get(user=self.request.user)
        aerouser.language = request.data.pop('language')
        aerouser.save()
        return Response(
            AerosimpleUserSerializer(
                self.request.user.aerosimple_user).data,
            status=status.HTTP_200_OK)


def get_roles_permission_for_action(action):
    switcher = {
        'list': [IsAuthenticated, CanViewRoles],
        'retrieve': [IsAuthenticated, CanViewRoles],
        'create': [IsAuthenticated, CanCreateRoles],
        'partial_update': [IsAuthenticated, CanEditRoles],
        'get_privileges': [IsAuthenticated, CanViewRoles],
    }
    return switcher.get(action, [IsAdminUser])


class RoleViewSet(viewsets.ModelViewSet):
    serializer_class = RoleSerializer

    def get_queryset(self):
        if self.request.user:
            return Role.objects.filter(
                airport__id=self.request.user.aerosimple_user.airport_id
            )
        return Role.objects.none()

    def get_permissions(self):
        self.permission_classes = get_roles_permission_for_action(self.action)
        return super(self.__class__, self).get_permissions()

    def create(self, request):
        data = request.data.copy()
        permissions = data.pop('permissions', [])

        if not self.request.user.has_perm('users.add_role'):
            return Response(
                "User has no permissions to create a Role",
                status=status.HTTP_403_FORBIDDEN
            )

        all_permissions_group = PermissionConfig.objects.first()
        try:
            with transaction.atomic():
                group = Group(name='{}-{}'.format(
                    data['name'],
                    request.user.aerosimple_user.airport
                ))

                group.save()

                for perm in permissions:
                    p = Permission.objects.get(id=perm)

                    if p in all_permissions_group.permissions.all():
                        group.permissions.add(p)
                    else:
                        group.delete()
                        return Response(
                            "id {} is not a valid Permission".format(p.id),
                            status=status.HTTP_400_BAD_REQUEST)

                role = Role(name=data['name'])
                role.permission_group = group
                role.airport = request.user.aerosimple_user.airport
                role.save()

        except ValidationError:
            raise

        return Response(
            RoleSerializer(role).data,
            status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        role = self.get_object()
        
        try:
            with transaction.atomic():
                if 'name' in request.data:
                    role.permission_group.name = request.data['name']
                    role.permission_group.save()
                    if role.system_generated is False:
                        role.name = request.data['name']
                    role.save()

                permissions = request.data.pop('permissions', [])
                all_permissions_group = PermissionConfig.objects.first()
                if len(permissions) > 0:
                    role.permission_group.permissions.clear()

                for perm in permissions:
                    p = Permission.objects.get(id=perm)

                    if p in all_permissions_group.permissions.all():
                        role.permission_group.permissions.add(p)
                    else:
                        return Response(
                            "id {} is not a valid Permission".format(p.id),
                            status=status.HTTP_400_BAD_REQUEST)

        except ValidationError:
            raise

        return Response(RoleSerializer(role).data)

    
    # @action(detail=False, methods=['get'])
    # def get_privileges(self, request):
    #     config = PermissionConfig.objects.first()
    #     return Response(PermissionSerializer(
    #         config.permissions, many=True).data)
    @action(detail=False, methods=['get'])
    def get_privileges(self, request):
        config = PermissionConfig.objects.first()
        role_data = sorted(json.loads(json.dumps(PermissionSerializer(
            config.permissions, many=True).data)), key=itemgetter('category'))
        l = []
        f = {}
        for key, value in itertools.groupby(role_data, key=itemgetter('category')):
            key = str(key)
            for data in value:
                l.append(data)
                f[key] = l
            l = []
        logger.warning(json.loads(json.dumps(f)))
        return Response(json.loads(json.dumps(f)))


class UserTypeViewSet(viewsets.ModelViewSet):

    serializer_class = UserTypeSerializer

    def get_queryset(self):
        if self.request.user:
            return Role.objects.filter(
                airport__id=self.request.user.aerosimple_user.airport_id
            )
        return Role.objects.none()

    def get_permissions(self):
        self.permission_classes = get_roles_permission_for_action(self.action)
        return super(self.__class__, self).get_permissions()


class MobileAerosimpleUserViewSet(mixins.CreateModelMixin,
                                  mixins.UpdateModelMixin,
                                  viewsets.ReadOnlyModelViewSet):

    serializer_class = MobileAerosimpleUserSerializer

    def get_queryset(self):
        if self.request.user:
            return AerosimpleUser.objects.filter(
                airport__id=self.request.user.aerosimple_user.airport_id
            ).order_by('fullname')
        return AerosimpleUser.objects.none()

    def get_permissions(self):
        self.permission_classes = get_user_permission_for_action(self.action)
        return super(self.__class__, self).get_permissions()

    @action(detail=False, methods=['get'])
    def profile(self, request):
        if self.request.user:
            if request.user.aerosimple_user.airport is None:
                request.user.aerosimple_user.airport = request.user.aerosimple_user.authorized_airports.first()
                request.user.aerosimple_user.save()
            airport = request.user.aerosimple_user.airport
            if airport:
                DynamoDbModuleUtility.fetch_module_permissions(airport.code)
            return Response({'items': AerosimpleMobileProfileSerializer(self.request.user.aerosimple_user).data,
                             'status': {'code': status.HTTP_200_OK, 'message': 'success'}},
                            status=status.HTTP_200_OK)

        return Response(status={'code': status.HTTP_401_UNAUTHORIZED, 'message': 'Unauthorized'})

    @action(detail=False, methods=['post'])
    def update_language(self, request):
        aerouser = AerosimpleUser.objects.get(user=self.request.user)
        aerouser.language = request.data.pop('language')
        aerouser.save()
        return Response(
            AerosimpleUserSerializer(
                self.request.user.aerosimple_user).data,
            status=status.HTTP_200_OK)
