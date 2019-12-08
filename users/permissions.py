import logging

from rest_framework.permissions import BasePermission

logger = logging.getLogger('backend')


# *****************************************************************************
# *****************************   INSPECTIONS   *******************************
# *****************************************************************************

class CanCreateUsers(BasePermission):
    """Allows to create a user"""

    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        # if (request.method == 'POST' and request.user.has_perm(
        #         "users.add_aerosimpleuser")):
        #     return True
        if (request.method == 'POST' and request.user.aerosimple_user and \
            request.user.aerosimple_user.has_permission("add_aerosimpleuser")):
            return True
        return False


class CanEditUsers(BasePermission):
    """Allows to edit user info."""

    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        if request.method == 'PATCH':
            if int(view.kwargs.get('pk')) == request.user.aerosimple_user.id:
                return True
            if request.user.aerosimple_user and \
                request.user.aerosimple_user.has_permission("change_aerosimpleuser"):
                    return True
        return False


class CanViewRoles(BasePermission):
    """Allows to view roles (list and retrieve)."""

    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        # if (request.method == 'GET' and request.user.has_perm(
        #         "users.view_role")):
        #     return True
        if (request.method == 'GET' and request.user.aerosimple_user and \
            request.user.aerosimple_user.has_permission("view_role")):
            return True
        return False


class CanCreateRoles(BasePermission):
    """Allows to create a Role."""

    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        # if (request.method == 'POST' and request.user.has_perm(
        #         "users.add_role")):
        if (request.method == 'POST' and request.user.aerosimple_user and \
            request.user.aerosimple_user.has_permission("add_role")):
            return True
        return False


class CanEditRoles(BasePermission):
    """Allows to edit a Role."""

    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        if (request.method == 'PATCH' and request.user.aerosimple_user and \
            request.user.aerosimple_user.has_permission("change_role")):
            return True
        # if request.user.aerosimple_user and \
        #     request.user.aerosimple_user.has_permission("add_log"):
        #     return True
        return False


class IsSuperUser(BasePermission):
    """
    Allows access only to super users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_superuser

