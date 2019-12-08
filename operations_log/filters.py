from django_filters import rest_framework as filters
# from django_filters import FilterSet, DateRangeFilter, DateFilter, CharFilter
import logging
from operations_log.models import Log
from datetime import datetime
from django.db.models import Q

logger = logging.getLogger('backend')


class LogFilter(filters.FilterSet):
    s = filters.DateFilter(method="filter_start")
    f = filters.DateFilter(method='filter_end')
    query = filters.CharFilter(method='filter_query')

    def filter_start(self, queryset, name, value):
        fdate = datetime.combine(value, datetime.min.time())
        return queryset.filter(report_date__gte=fdate)

    def filter_end(self, queryset, name, value):
        fdate = datetime.combine(value, datetime.max.time())
        return queryset.filter(report_date__lte=fdate)

    def filter_query(self, queryset, name, value):
        return queryset.filter(
            Q(description__contains=value)
            | Q(type__contains=value)
            | Q(logged_by_id__first_name__contains=value)
            | Q(logged_by_id__last_name__contains=value)
            | Q(subtype__contains=value)
            | Q(report_date__contains=value)
            # | Q(type__name__contains=value)
            # | Q(subtype__name__contains=value)
        )

    class Meta:
        model = Log
        fields = ('s', 'f')
