from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from forms.utils import DRAFT, PUBLISHED
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from operations_log.models import (
    LogVersion, Log, LogForm, LogType, LogSubType
)
from operations_log.serializer import (
    LogListSerializer, LogSerializer, LogDetailSerializer,
    LogVersionSerializer, LogVersionSaveSerializer,
    LogTypeSerializer, LogSubTypeSerializer
)
from operations_log.pagination import LogPaginationClass
from operations_log.filters import LogFilter
from operations_log.permissions import CanViewOperationLog, CanAddOperationLog
import logging

logger = logging.getLogger('backend')


class LogViewSet(viewsets.ModelViewSet):

    pagination_class = LogPaginationClass
    filter_class = LogFilter

    def get_permission_for_action(self, action):
        switcher = {
            'list': [IsAuthenticated, CanViewOperationLog],
            'retrieve': [IsAuthenticated, CanViewOperationLog],
            'create': [IsAuthenticated, CanAddOperationLog],
            'destroy': [IsAuthenticated, CanAddOperationLog],
            'update': [IsAuthenticated, CanAddOperationLog],
            'partial_update': [IsAuthenticated, CanAddOperationLog],
            'update_schema': [IsAuthenticated, CanAddOperationLog],
            'update_types': [IsAuthenticated, CanAddOperationLog],
            'get_schema': [IsAuthenticated, CanViewOperationLog]
        }
        return switcher.get(action, [IsAdminUser])

    def get_permissions(self):
        self.permission_classes = self.get_permission_for_action(self.action)
        return super(self.__class__, self).get_permissions()

    def get_queryset(self):
        if self.request.user:
            versions = LogVersion.objects.filter(
                form__airport__id=self.request.user.aerosimple_user.airport_id
            ).exclude(status=DRAFT)

            result = Log.objects.none()
            for v in versions:
                result = result | v.operation_logs.order_by('-id').all()
            return result.all()

        return Log.objects.none()

    def get_serializer_class(self):
        """Return different serializers in list action."""
        if self.action == 'list':
            return LogListSerializer
        elif self.action == 'retrieve':
            return LogDetailSerializer
        return LogSerializer

    def create(self, request):
        data = request.data.copy()
        published_version = LogVersion.objects.filter(
            form__airport__id=self.request.user.aerosimple_user.airport_id,
            status=PUBLISHED).first()
        if published_version is None:
            return Response(
                "no_published_log_version",
                status=status.HTTP_400_BAD_REQUEST)
        data['form'] = published_version.id
        serializer = LogSerializer(data=data, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def get_schema(self, request):
        if not self.request.user.is_authenticated:
            return Response(status=status.HTTP_403_FORBIDDEN)

        form = LogForm.objects.get(
            airport__id=self.request.user.aerosimple_user.airport_id)

        categoryList = LogType.objects.filter(
            airport__id=self.request.user.aerosimple_user.airport_id,
            system_generated=False
        )
        subcategoryList = LogSubType.objects.filter(
            activity_type__in=categoryList
        )

        try:
            log_version = form.versions.get(status=PUBLISHED)
            return Response({
                'schema': LogVersionSerializer(log_version).data,
                'types': LogTypeSerializer(
                    categoryList, many=True).data,
                'subtypes': LogSubTypeSerializer(
                    subcategoryList, many=True).data
            })
        except LogVersion.DoesNotExist:
            return Response({})

    @action(detail=False, methods=['post'])
    def update_schema(self, request):
        if not self.request.user.is_authenticated:
            return Response(status=status.HTTP_403_FORBIDDEN)

        form = LogForm.objects.get(
            airport__id=self.request.user.aerosimple_user.airport_id)

        form_data = {
            "form": form.id,
            "schema": request.data,
            "status": PUBLISHED
        }
        log_schema = LogVersionSaveSerializer(data=form_data)
        valid = log_schema.is_valid()

        if (valid):
            log_schema.save()
        else:
            return Response(
                log_schema.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def update_types(self, request):
        if not self.request.user.is_authenticated:
            return Response(status=status.HTTP_403_FORBIDDEN)

        data = request.data
        # List of type id for track deleted
        types_id = []
        subtypes_id = []

        for t in data['types']:
            if 'id' in t:
                toChange = LogType.objects.get(id=t['id'])
                if t['name'] is not '':
                    toChange.name = t['name']
                    toChange.i18n_id = None
                toChange.save()
            else:
                sys_type = LogType.objects.filter(name=t['name'], system_generated=True,
                                airport=self.request.user.aerosimple_user.airport)
                if len(sys_type) == 0:
                    toChange = LogType.objects.create(
                        name=t['name'],
                        airport=self.request.user.aerosimple_user.airport
                    )
            types_id.append(toChange.id)

            ref = t['id'] if ('id' in t) else t['ref']
            if ref in data['subtypes']:
                for st in data['subtypes'][ref]:
                    if 'id' in st:
                        toChangeSub = LogSubType.objects.get(id=st['id'])
                        if st['name'] is not '':
                            toChangeSub.name = st['name']
                            toChangeSub.i18n_id = None
                        toChangeSub.save()
                    else:
                        toChangeSub = LogSubType.objects.create(
                            name=st['name'], activity_type=toChange)
                    subtypes_id.append(toChangeSub.id)

        # Now we are deleting all types and subtypes that aren't present
        # in the request.
        toDelete = LogType.objects.filter(
            airport=self.request.user.aerosimple_user.airport,
            system_generated=False
        ).exclude(id__in=types_id)
        toDelete.delete()

        toDeleteSub = LogSubType.objects.exclude(id__in=subtypes_id)
        toDeleteSub.delete()

        return Response(status=status.HTTP_200_OK)
