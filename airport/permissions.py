import logging

from rest_framework.permissions import BasePermission

from airport.utils import DynamoDbModuleUtility
from backend.auth import AerosimpleBackend

logger = logging.getLogger('backend')


# *****************************************************************************
# *******************************   AIRPORT    ********************************
# *****************************************************************************

class CanAddAirport(BasePermission):
    """
        Can Add Surface Shapes
    """

    def has_permission(self, request, view):
        # if request.user.has_perm("airport.add_airport"):
        #     return True
        return request.method != 'GET' and \
            AerosimpleBackend.checkAdmin(request.user.username) is not None


class CanEditAirportSettings(BasePermission):
    """Allows to create a user"""

    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        # if ((request.method != 'GET')
        #         and request.user.has_perm(
        #             "airport.can_modify_airport_settings")):
        #     return True
        if request.method != 'GET' and request.user.aerosimple_user and \
                request.user.aerosimple_user.has_permission("can_modify_airport_settings"):
            return True
        return False


class CanViewAirportSettings(BasePermission):
    """Allows to create a user"""

    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        # if (request.method == 'GET' and request.user.has_perm(
        #         "airport.can_modify_airport_settings")):
        #     return True
        if request.method == 'GET' and request.user.aerosimple_user and \
                request.user.aerosimple_user.has_permission("can_modify_airport_settings"):
            return True
        return False


class CanViewSurfaceTypes(BasePermission):
    """
        View Surface Types Permission
    """

    def has_permission(self, request, view):
        # if request.user.has_perm("airport.view_surfacetype"):
        #     return True
        if request.user.aerosimple_user and \
                request.user.aerosimple_user.has_permission("view_surfacetype"):
            return True
        return False


class CanAddSurfaceTypes(BasePermission):
    """
        Can Add Surface Types Permission
    """

    def has_permission(self, request, view):
        # if request.user.has_perm("airport.add_surfacetype"):
        #     return True
        if request.user.aerosimple_user and \
                request.user.aerosimple_user.has_permission("add_surfacetype"):
            return True
        return False


class CanAddSurfaceShapes(BasePermission):
    """
        Can Add Surface Shapes
    """

    def has_permission(self, request, view):
        # if request.user.has_perm("airport.add_surfaceshape"):
        #     return True
        if request.user.aerosimple_user and \
                request.user.aerosimple_user.has_permission("add_surfaceshape"):
            return True
        return False


class CanViewSurfaceShapes(BasePermission):
    """
        Can Add Surface Shapes
    """

    def has_permission(self, request, view):
        # if request.user.has_perm("airport.view_surfaceshape"):
        #     return True
        if request.user.aerosimple_user and \
                request.user.aerosimple_user.has_permission("view_surfaceshape"):
            return True
        return False


class CanViewAssets(BasePermission):
    """
        Can Add Surface Shapes
    """

    def has_permission(self, request, view):
        if request.user.aerosimple_user and \
                request.user.aerosimple_user.has_permission("view_asset"):
            return True
        # if request.user.has_perm("airport.view_asset"):
        #     return True
        return False


class CanAddAssets(BasePermission):
    """
        Can Add Surface Shapes
    """

    def has_permission(self, request, view):
        # if request.user.has_perm("airport.add_asset"):
        #     return True
        if request.user.aerosimple_user and \
                request.user.aerosimple_user.has_permission("add_asset"):
            return True
        return False


# *****************************************************************************
# ******************   AIRPORT MODULE LEVEL PERMISSIONS    ********************
# *****************************************************************************


class AirportHasInspectionPermission(BasePermission):
    """Allows to see the inspection module"""

    def has_permission(self, request, view):
        if request.user and request.user.aerosimple_user and request.user.aerosimple_user.airport:
            return DynamoDbModuleUtility.has_module_permissions(
                request.user.aerosimple_user.airport.code, 'inspections')
        return False


class AirportHasWorkOrderPermission(BasePermission):
    """Allows to see the work order module"""

    def has_permission(self, request, view):
        if request.user and request.user.aerosimple_user and request.user.aerosimple_user.airport:
            return DynamoDbModuleUtility.has_module_permissions(
                request.user.aerosimple_user.airport.code, 'work_orders')
        return False


class AirportHasTaskPermission(BasePermission):
    """Allows to see the task module"""

    def has_permission(self, request, view):
        if request.user and request.user.aerosimple_user and request.user.aerosimple_user.airport:
            return DynamoDbModuleUtility.has_module_permissions(
                request.user.aerosimple_user.airport.code, 'tasks')
        return False


class AirportHasAssetPermission(BasePermission):
    """Allows to see the asset module"""

    def has_permission(self, request, view):
        if request.user and request.user.aerosimple_user and request.user.aerosimple_user.airport:
            return DynamoDbModuleUtility.has_module_permissions(
                request.user.aerosimple_user.airport.code, 'assets')
        return False


class AirportHasNotamsPermission(BasePermission):
    """Allows to see the inspection module"""

    def has_permission(self, request, view):
        if request.user and request.user.aerosimple_user and request.user.aerosimple_user.airport:
            return AirportHasNotamsPermission.check(request.user.aerosimple_user.airport.code)
        return False

    @staticmethod
    def check(code):
        return DynamoDbModuleUtility.has_sources_permissions(code, 'notams')
