from django_filters import rest_framework as filters
from django.contrib.auth.models import User, Permission
from django.db.models import Q

from users.models import AerosimpleUser


class UserFilter(filters.FilterSet):
    q = filters.CharFilter(
      field_name='fullname', lookup_expr='icontains'
    )

    r = filters.CharFilter(method='filter_published')

    def filter_published(self, queryset, name, value):
        perm = None
        if value == 'maintenance':
            perm = Permission.objects.get(codename='add_maintenance')   

        if value == 'operations':
            perm = Permission.objects.get(codename='add_operations')   

        users = User.objects.filter(
            Q(groups__permissions=perm) | Q(user_permissions=perm)
        ).distinct()
        return queryset.filter(user__in=users)

        return queryset

    class Meta:
        model = AerosimpleUser
        fields = ['fullname']
