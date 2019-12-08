from django_filters import rest_framework as filters
# from django_filters import FilterSet, DateRangeFilter, DateFilter, CharFilter
import logging
from inspections.models import InspectionAnswer
from datetime import datetime, timedelta
from django.db.models import Q

logger = logging.getLogger('backend')


class InspectionAnswerFilter(filters.FilterSet):
    s = filters.DateFilter(method="filter_start")
    f = filters.DateFilter(method='filter_end')
    n = filters.CharFilter(
        field_name='inspection__title', lookup_expr='iexact')
    query = filters.CharFilter(method='filter_query')

    def filter_start(self, queryset, name, value):
        fdate = datetime.combine(value, datetime.min.time())
        return queryset.filter(inspection_date__gte=fdate)

    def filter_end(self, queryset, name, value):
        fdate = datetime.combine(value, datetime.max.time())
        return queryset.filter(inspection_date__lte=fdate)

    def filter_query(self, queryset, name, value):
        return queryset.filter(
            Q(inspection_type__icontains=value)
            | Q(inspected_by__first_name__icontains=value)
            | Q(inspected_by__last_name__icontains=value)
            | Q(weather_conditions__icontains=value)
            | Q(inspection__title__icontains=value)
            | Q(inspection_date__icontains=value)
        )
    class Meta:
        model = InspectionAnswer
        fields = ('inspection_date', 'inspection__title',)
