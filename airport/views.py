from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
import logging
import json
import boto3
from django.contrib.gis.geos import Point
from forms.utils import DRAFT, PUBLISHED
from backend.utils import status_json

from airport.models import (SurfaceType, Airport, SurfaceShape, AssetType,
                            Asset, AssetForm, AssetImage, AssetVersion,
                            Translation, AssetCategory)

from airport.serializers import (SurfaceTypeSerializer, AirportSerializer, AirportDetailSerializer,
                                 SurfaceShapeSerializer, AssetSerializer,
                                 SurfaceShapeDetailSerializer,
                                 AssetTypeSerializer, AssetListSerializer,
                                 AssetVersionSerializer, AssetImageSerializer,
                                 AssetVersionSaveSerializer, AirportCreateSerializer,
                                 AssetCreateSerializer, MobileAssetTypeSerializer,
                                 MobileSurfaceTypeSerializer, MobileAirportAssetSerializer,
                                 AssetConfigurationSerializer, AssetListWebSerializer)

from airport.permissions import CanEditAirportSettings, CanViewAirportSettings, \
    AirportHasAssetPermission, CanViewSurfaceTypes, CanAddSurfaceTypes, CanAddSurfaceShapes, \
    CanViewSurfaceShapes, CanViewAssets, CanAddAssets, CanAddAirport

from airport.utils import DynamoDbModuleUtility

from inspections.models import InspectionParent, Inspection

from users.permissions import IsSuperUser
from users.models import Role, AerosimpleUser
from users.views import AerosimpleUserViewSet
from users.serializers import AerosimpleCreateUserSerializer

from forms.utils import PUBLISHED
from django.db.models import Q
from django.contrib.auth.models import User
from django.conf import settings
from collections import namedtuple, OrderedDict


logger = logging.getLogger('backend')


class SurfaceTypeViewSet(viewsets.ModelViewSet):
    serializer_class = SurfaceTypeSerializer

    def get_permission_for_action(self, action):
        """
            SurfaceTypeViewSet permissions.
        """
        switcher = {
            'retrieve': [IsAuthenticated, CanViewSurfaceTypes],
            'list': [IsAuthenticated, CanViewSurfaceTypes],
            'destroy': [IsAuthenticated, CanAddSurfaceTypes],
            'create': [IsAuthenticated, CanAddSurfaceTypes],
            'partial_update': [IsAuthenticated, CanAddSurfaceTypes],
            'update': [IsAuthenticated, CanAddSurfaceTypes],
        }
        return switcher.get(action, [IsAdminUser])

    def get_queryset(self):
        if self.request.user:
            return SurfaceType.objects.filter(
                airport=self.request.user.aerosimple_user.airport)

        return SurfaceType.objects.none()

    def get_permissions(self):
        self.permission_classes = self.get_permission_for_action(self.action)
        return super(self.__class__, self).get_permissions()


class AirportViewSet(mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = AirportSerializer

    def get_permission_for_action(self, action):
        switcher = {
            'retrieve': [IsAuthenticated, CanViewAirportSettings],
            'update': [IsAuthenticated, CanEditAirportSettings],
            'update_self_inspection_types': [
                IsAuthenticated, CanEditAirportSettings],
            'partial_update': [IsAuthenticated, CanEditAirportSettings],
            'translations': [IsAuthenticated],
            'create': [IsAdminUser, CanAddAirport],
            'default_airport': [IsAuthenticated],
            'authorized_airports': [IsAuthenticated],
            'new_airport': [CanAddAirport],
            'sync_airport': [CanAddAirport]
        }
        return switcher.get(action, [IsAdminUser])
    
    def get_serializer_class(self):
        """Return different serializers in list action."""
        if self.action == 'create':
            return AirportSerializer
        if self.action == 'new_airport':
            return AerosimpleCreateUserSerializer
        return AirportDetailSerializer
    
    #to update types_self_inspection while saving the inspections in settings
    def update_types_self_inspection(self):
        data = self.request.data
        airport = Airport.objects.get(id=self.request.user.aerosimple_user.airport_id)
        inspection_parent = InspectionParent.objects.get(id = data['safety_self_inspection'])
        inspection = Inspection.objects.filter(title = inspection_parent.title).get(status = PUBLISHED)
        airport.types_for_self_inspection = inspection.schema
        airport.save()


    def get_queryset(self):
        if self.request.user:
            return Airport.objects.filter(
                id=self.request.user.aerosimple_user.airport_id)
        return Airport.objects.none()

    def get_permissions(self):
        self.permission_classes = self.get_permission_for_action(self.action)
        return super(self.__class__, self).get_permissions()

    @action(detail=False, methods=['post'])
    def new_airport(self, request, *args, **kwargs):
        return AirportViewSet.create_airport(self.request, request, self.get_serializer(data=request.data))

    @staticmethod
    def create_airport(view_request, request, user_serializer):
        airportdata = request.data
        airport = AirportCreateSerializer(
            data=airportdata, context={'request': request})
        if not airport.is_valid():
            return Response(
                airport.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        airport.save()

        airport = Airport.objects.get(
            code=airport.instance.code)
        location = request.data['loc'].split(',')
        airport.location = Point(float(location[1]), float(location[0]))
        airport.save()
        
        if 'email' in request.data:
            users = User.objects.filter(email=request.data['email'])
            aero_user = None
            if len(users) > 0:
                user = users[0]
                aero_user = AerosimpleUser.objects.filter(user=user)
                if len(aero_user) == 0:
                    aero_user = AerosimpleUser()
                    aero_user.user = user
                else:
                    aero_user = aero_user[0]
                    aero_user.system_generated = False
            else:
                user = User()
                user.email = request.data['email']
                user.save()
                aero_user = AerosimpleUser()
                aero_user.user = user

            aero_user.first_name = request.data['first_name']
            aero_user.last_name = request.data['last_name']
            aero_user.fullname = aero_user.first_name + ' ' + aero_user.last_name
            aero_user.save()
            aero_user.authorized_airports.add(airport)
            admin_role = Role.objects.filter(
                    airport=airport,
                    permission_group__name='System Admin-{}'.format(airport))
            aero_user.roles.add(admin_role[0])

        if 'enableAdmin' in request.data and request.data['enableAdmin'] == 'true':
            view_request.user.aerosimple_user.authorized_airports.add(airport)
            admin_role = Role.objects.filter(
                    airport=airport,
                    permission_group__name='System Admin-{}'.format(airport))
            view_request.user.aerosimple_user.roles.add(admin_role[0])
            # view_request.user.aerosimple_user.system_generated = False
            # view_request.user.aerosimple_user.save()
            # view_request.user.is_staff = True
            view_request.user.save()

        if request.data['createInspections'] == 'true':
            request.data['code'] = airport.code
            AirportViewSet.create_inspection_templates(request)

        return Response(AirportSerializer(airport).data)
    
    @action(detail=False, methods=['post'])
    def sync_airport(self, request):
        # all sync operations
        return AirportViewSet.create_inspection_templates(request)

    @staticmethod
    def create_inspection_templates(request):
        response = {}
        code = request.data.get('code')
        max_allowed_count = request.data.get('max_inspections')
        if code:
            airport = Airport.objects.filter(code=code).first()
            if airport:
                dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_DEFAULT_REGION)
                template_table = dynamodb.Table(settings.APP_PREFIX + 'template')
                standard_table = dynamodb.Table(settings.APP_PREFIX + 'standard')
                airport_key = '{0}_{1}'.format(airport.code, 'eu')
                airport_table = dynamodb.Table(settings.APP_PREFIX + 'airport')
                airport_object = airport_table.get_item(Key={"id": airport_key})
                inspection_count = InspectionParent.objects.filter(
                    airport=airport).count()
                if max_allowed_count is None:
                    max_allowed_count = 2
                else:
                    max_allowed_count = int(max_allowed_count)
                if not settings.AIRPORT_PLAN_ENABLE:
                    max_allowed_count = 100
                try:
                    regulatory = airport_object['Item']['regulatory']
                except:
                    regulatory = 'FAA'
                all_template_data = template_table.scan()
                all_standard_data = standard_table.scan()
                for std in all_standard_data['Items']:
                    if std['regulatory'] == regulatory:
                        workorder_base = std['default_template']
                        self_inspection_types = std['self_inspection_types'] if 'self_inspection_types' in std else {}
                status = 1
                count = 0
                if 'Items' in all_template_data:
                    for item in all_template_data['Items']:
                        if item['regulatory'] == regulatory:
                            if inspection_count >= max_allowed_count:
                                status = 0
                            existing_parent = InspectionParent.objects.filter(title=item['title'], airport=airport).exists()
                            if not existing_parent:
                                inspection_parent = InspectionParent.objects.create(
                                    created_by=request.user.aerosimple_user,
                                    title=item['title'],
                                    icon="icon-2",
                                    additionalInfo=item['additionalInfo'],
                                    airport=airport
                                )
                                v = inspection_parent.versions.first()
                                v.title = inspection_parent.title
                                v.icon = inspection_parent.icon
                                v.schema = json.loads(json.dumps(item['schema'],cls=DjangoJSONEncoder))
                                v.additionalInfo = inspection_parent.additionalInfo
                                v.status = status
                                v.save()
                                inspection_count += 1
                                count += 1
                                if inspection_parent.title == workorder_base:
                                    airport.safety_self_inspection = inspection_parent
                                    airport.types_for_self_inspection = self_inspection_types
                                    airport.save()
                return Response({'status': 1, 'count': count})
        return Response(response)

    @action(detail=False, methods=['post'])
    def update_self_inspection_types(self, request):
        airport = Airport.objects.get(
            id=self.request.user.aerosimple_user.airport_id)
        airport.types_for_self_inspection = request.data
        airport.save()
        return Response(AirportSerializer(airport).data)

    @action(detail=False, methods=['get'])
    def translations(self, request):
        if self.request.user:
            translations = Translation.objects.filter(
                airport=self.request.user.aerosimple_user.airport)
            result = {}
            for tr in translations:
                result[tr.language] = tr.translation_map
            return Response(result, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=True, methods=['post'])
    def default_airport(self, request, pk=None):
        if self.request.user and self.request.user.aerosimple_user:
            user = self.request.user.aerosimple_user
            new_default_airport = user.authorized_airports.filter(id=pk)
            if new_default_airport:
                user.airport = new_default_airport[0]
                user.save()
                return Response(status_json(200, True, 'Successfully updated airport'), status=status.HTTP_200_OK)
            return Response(status_json(200, True, 'Airport not authorized'), status=status.HTTP_401_UNAUTHORIZED)

        return Response(status_json(200, True, 'Invalid user'), status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['get'])
    def authorized_airports(self, request, pk=None):
        if self.request.user and self.request.user.aerosimple_user:
            authorized_airports = self.request.user.aerosimple_user.authorized_airports.all()
            serialized_data = AirportSerializer(authorized_airports, many=True)
            result = {
                'default_airport': self.request.user.aerosimple_user.airport_id,
                'authorized_airport': serialized_data.data
            }
            return Response(result, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_401_UNAUTHORIZED)


class SurfaceShapeViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        if self.request.user:
            query = self.request.GET.get("query")
            if query:
                return SurfaceShape.objects.filter(
                    airport=self.request.user.aerosimple_user.airport, name__contains=query)
            else:
                return SurfaceShape.objects.filter(
                    airport=self.request.user.aerosimple_user.airport)

        return SurfaceShape.objects.none()
    
    def get_permission_for_action(self, action):
        switcher = {
            'list': [IsAuthenticated, CanViewSurfaceShapes],
            'retrieve': [IsAuthenticated, CanViewSurfaceShapes],
            'update': [IsAuthenticated, CanAddSurfaceShapes],
            'partial_update': [IsAuthenticated, CanAddSurfaceShapes],
            'destroy': [IsAuthenticated, CanAddSurfaceShapes],
            'create': [IsAuthenticated, CanAddSurfaceShapes]
        }
        return switcher.get(action, [IsAdminUser])

    def get_serializer_class(self):
        """Return different serializers in list action."""
        if self.action == 'list':
            return SurfaceShapeDetailSerializer
        return SurfaceShapeSerializer

    def get_permissions(self):
        self.permission_classes = self.get_permission_for_action(self.action)
        return super(self.__class__, self).get_permissions()


class AssetTypeViewSet(viewsets.ModelViewSet):
    serializer_class = AssetTypeSerializer
    queryset = AssetType.objects.all()

    def get_permissions(self):
        switcher = {
            'create': [IsAuthenticated, CanAddAssets, AirportHasAssetPermission],
            'list': [IsAuthenticated, CanViewAssets,AirportHasAssetPermission],
            'destroy': [IsAuthenticated, CanAddAssets, AirportHasAssetPermission],
            'retrieve': [IsAuthenticated, CanViewAssets,AirportHasAssetPermission],
            'update': [IsAuthenticated, CanAddAssets, AirportHasAssetPermission],
            'partial_update': [IsAuthenticated, CanAddAssets, AirportHasAssetPermission],
        }
        self.permission_classes = switcher.get(self.action, [IsAdminUser])
        return super(self.__class__, self).get_permissions()


class AssetViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        if self.request.user:
            query = self.request.GET.get("query")
            if query:     
                return Asset.objects.filter(
                    airport=self.request.user.aerosimple_user.airport).filter( Q(name__contains=query) | Q(label__contains= query) | Q(asset_type_id__name__contains=query) | Q(asset_type_id__category_id__name__contains=query))
            else:
                return Asset.objects.filter(
                    airport=self.request.user.aerosimple_user.airport)

        return Asset.objects.none()

    def get_serializer_class(self):
        """Return different serializers in list action."""
        if self.action == 'list':
            return AssetListWebSerializer
        return AssetSerializer

    def get_permissions(self):
        switcher = {
            'list': [IsAuthenticated, CanViewAssets,AirportHasAssetPermission],
            'retrieve': [IsAuthenticated, CanViewAssets,AirportHasAssetPermission],
            'get_schemas': [IsAuthenticated, CanViewAssets,AirportHasAssetPermission],
            'update_schemas': [IsAuthenticated, CanAddAssets, AirportHasAssetPermission],
            'destroy': [IsAuthenticated, CanAddAssets, AirportHasAssetPermission],
            'update': [IsAuthenticated, CanAddAssets, AirportHasAssetPermission],
            'partial_update': [IsAuthenticated, CanAddAssets, AirportHasAssetPermission],
            'create': [IsAuthenticated, CanAddAssets, AirportHasAssetPermission],
        }
        self.permission_classes = switcher.get(self.action, [IsAdminUser])
        return super(self.__class__, self).get_permissions()

    def create(self, request):
        assetdata = request.data
        photos = []
        if "photos" in assetdata:
            photos = assetdata.pop('photos', [])
        asset = AssetCreateSerializer(
            data=assetdata, context={'request': request})
        if not asset.is_valid():
            return Response(
                asset.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        asset.save()

        # Get the latest published version for the work order
        try:
            with transaction.atomic():
                for photo in photos:
                    serializer_photo = AssetImageSerializer(
                        data={'asset': asset.instance.id, 'image': photo})
                    serializer_photo.is_valid(raise_exception=True)
                    serializer_photo.save()
        except ValidationError:
            raise
        return Response(AssetListWebSerializer(asset.instance).data)

    def partial_update(self, request, *args, **kwargs):
        asset = self.get_object()
        asset.name = request.data['name']
        asset.asset_type = AssetType.objects.get(pk=request.data['asset_type'])

        area = request.data.get('area', None)
        if area is not None:
            asset.area = SurfaceShape.objects.get(pk=area)
        asset.label = request.data['label']
        asset.geometry = request.data['geometry']
        asset.version_schema = AssetVersion.objects.get(
            pk=request.data['version_schema'])
        asset.save()

        if ('photosToRemove' in request.data):
            photosToRemove = request.data['photosToRemove'].split(',')
            for p in photosToRemove:
                photo = AssetImage.objects.get(pk=p)
                photo.delete()

        if 'photos' in request.data and len(request.data['photos']) > 0:
            photos = request.data.pop('photos', [])
            # Get the latest published version for the work order
            try:
                with transaction.atomic():
                    for photo in photos:
                        serializer_photo = AssetImageSerializer(
                            data={'asset': asset.id, 'image': photo})
                        serializer_photo.is_valid(raise_exception=True)
                        serializer_photo.save()
            except ValidationError:
                raise

        return Response(AssetListWebSerializer(asset).data)

    @action(detail=False, methods=['get'])
    def get_schemas(self, request):

        forms = AssetForm.objects.filter(
            airport__id=self.request.user.aerosimple_user.airport_id)

        signs = AssetVersionSerializer(
            forms.get(category__name="Signs").versions.get(status=PUBLISHED)
        )
        lights = AssetVersionSerializer(
            forms.get(category__name="Lights").versions.get(status=PUBLISHED)
        )
        result = {
            'signs': signs.data,
            'lights': lights.data
        }
        return Response(result)

    @action(detail=False, methods=['post'])
    def update_schemas(self, request):
        forms = AssetForm.objects.filter(
            airport__id=self.request.user.aerosimple_user.airport_id)

        signs_form = forms.get(category__name="Signs")
        lights_form = forms.get(category__name="Lights")

        lights_data = {
            "form": lights_form.id,
            "schema": request.data['lights'],
            "status": PUBLISHED
        }

        signs_data = {
            "form": signs_form.id,
            "schema": request.data['signs'],
            "status": PUBLISHED
        }

        lights_schema = AssetVersionSaveSerializer(data=lights_data)
        signs_schema = AssetVersionSaveSerializer(data=signs_data)

        valid1 = lights_schema.is_valid()
        valid2 = signs_schema.is_valid()

        if (valid1 and valid2):
            try:
                with transaction.atomic():
                    lights_schema.save()
                    signs_schema.save()
            except ValidationError:
                raise
        else:
            errors = (lights_schema.errors +
                      signs_schema.errors)
            return Response(
                errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_200_OK)


class MobileAssetTypeViewSet(viewsets.ModelViewSet):
    serializer_class = MobileAssetTypeSerializer
    queryset = AssetType.objects.all()

    def get_permissions(self):
        switcher = {
            'create': [IsAuthenticated, CanAddAssets, AirportHasAssetPermission],
            'list': [IsAuthenticated, CanViewAssets,AirportHasAssetPermission],
            'destroy': [IsAuthenticated, CanAddAssets, AirportHasAssetPermission],
            'retrieve': [IsAuthenticated, CanViewAssets,AirportHasAssetPermission],
            'update': [IsAuthenticated, CanAddAssets, AirportHasAssetPermission],
            'partial_update': [IsAuthenticated, CanAddAssets, AirportHasAssetPermission],
        }
        self.permission_classes = switcher.get(self.action, [IsAdminUser])
        return super(self.__class__, self).get_permissions()

    def get_paginated_response(self, data):
        return Response(OrderedDict([('items', data)]))


class MobileSurfaceTypeViewSet(viewsets.ModelViewSet):
    serializer_class = MobileSurfaceTypeSerializer

    def get_queryset(self):
        if self.request.user:
            return SurfaceType.objects.filter(
                airport=self.request.user.aerosimple_user.airport)

        return SurfaceType.objects.none()

    def get_permissions(self):
        switcher = {
            'retrieve': [IsAuthenticated, CanViewSurfaceTypes],
            'list': [IsAuthenticated, CanViewSurfaceTypes],
            'destroy': [IsAuthenticated, CanAddSurfaceTypes],
            'create': [IsAuthenticated, CanAddSurfaceTypes],
            'partial_update': [IsAuthenticated, CanAddSurfaceTypes],
            'update': [IsAuthenticated, CanAddSurfaceTypes],
        }
        self.permission_classes = switcher.get(self.action, [IsAdminUser])
        return super(self.__class__, self).get_permissions()

    def get_paginated_response(self, data):
        return Response(OrderedDict([('items', data)]))


class MobileAirportAssetViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        if self.request.user:
            query = self.request.GET.get("query")
            if query:
                return Asset.objects.filter(
                    airport=self.request.user.aerosimple_user.airport, name__contains=query)
            else:
                return Asset.objects.filter(
                    airport=self.request.user.aerosimple_user.airport)

        return Asset.objects.none()

    def get_serializer_class(self):
        """Return different serializers in list action."""
        if self.action == 'list':
            return MobileAirportAssetSerializer
        return AssetSerializer


    def get_paginated_response(self, data):
        return Response(OrderedDict([('items', data)]))

    def get_permissions(self):
        switcher = {
            'list': [IsAuthenticated, CanViewAirportSettings,AirportHasAssetPermission],
            'get_schemas': [IsAuthenticated, CanViewAirportSettings,AirportHasAssetPermission],
            'retrieve': [IsAuthenticated, CanEditAirportSettings,AirportHasAssetPermission],
            'delete': [IsAuthenticated, CanEditAirportSettings, AirportHasAssetPermission],
            'update': [IsAuthenticated, CanEditAirportSettings, AirportHasAssetPermission],
            'partial_update': [IsAuthenticated, CanEditAirportSettings, AirportHasAssetPermission],
        }
        self.permission_classes = switcher.get(self.action, [IsAdminUser])
        return super(self.__class__, self).get_permissions()


class MobileSurfaceShapeViewSet(viewsets.ModelViewSet):
    serializer_class = SurfaceShapeDetailSerializer

    def get_queryset(self):
        if self.request.user:
            query = self.request.GET.get("query")
            if query:
                return SurfaceShape.objects.filter(
                    airport=self.request.user.aerosimple_user.airport, name__contains=query)
            else:
                return SurfaceShape.objects.filter(
                    airport=self.request.user.aerosimple_user.airport)

        return SurfaceShape.objects.none()

    def get_permissions(self):
        switcher = {
            'list': [IsAuthenticated, CanViewSurfaceShapes],
            'retrieve': [IsAuthenticated, CanViewSurfaceShapes],
            'update': [IsAuthenticated, CanAddSurfaceShapes],
            'partial_update': [IsAuthenticated, CanAddSurfaceShapes],
            'destroy': [IsAuthenticated, CanAddSurfaceShapes],
            'create': [IsAuthenticated, CanAddSurfaceShapes]
        }
        self.permission_classes = switcher.get(self.action, [IsAdminUser])
        return super(self.__class__, self).get_permissions()


class AssetConfigurationViewSet(viewsets.ViewSet):

    def list(self, request):
        Configuration = namedtuple('config', ('category', 'category_assets'))
        if self.request.user:
            category_assets = Asset.objects.filter(airport=self.request.user.aerosimple_user.airport)
            category = AssetCategory.objects.all()
        else:
            category_assets = Asset.objects.none()
            category = AssetCategory.objects.none()

        assetConfiguration = Configuration(
            category=category,
            category_assets=category_assets,
        )

        serializer = AssetConfigurationSerializer(assetConfiguration)
        return Response(serializer.data)

    def get_permissions(self):
        self.permission_classes = [IsAuthenticated, CanViewAssets]
        return super(self.__class__, self).get_permissions()
