import logging

from rest_framework.permissions import BasePermission


logger = logging.getLogger('backend')


# *****************************************************************************
# *****************************   INSPECTIONS   *******************************
# *****************************************************************************


class CanViewOperationLog(BasePermission):
    """Allows to see the Operation list"""

    def has_permission(self, request, view):
        # print(request.user.user_permissions.all())
        # if request.user.has_perm("operations_log.view_log"):
        #     return True
        if request.user.aerosimple_user and \
            request.user.aerosimple_user.has_permission("view_log"):
            return True
        return False


class CanAddOperationLog(BasePermission):
    """Allows to add the operation log"""

    def has_permission(self, request, view):
        # print(request.user.user_permissions.all())
        # if request.user.has_perm("operations_log.add_log"):
        #     return True
        if request.user.aerosimple_user and \
            request.user.aerosimple_user.has_permission("add_log"):
            return True
        return False

