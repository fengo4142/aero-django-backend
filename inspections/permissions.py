import logging

from rest_framework.permissions import BasePermission


logger = logging.getLogger('backend')


# *****************************************************************************
# *****************************   INSPECTIONS   *******************************
# *****************************************************************************


class SafetySelfInspectionPermission(BasePermission):
    """
        Allows to see the safety self inspection
    """
    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        # if request.user.has_perm("airport.change_airport"):
        #     return True
        if request.user.aerosimple_user and \
            request.user.aerosimple_user.has_permission("change_airport"):
            return True
        return False



class CanViewInspections(BasePermission):
    """Allows to see the inspection list"""

    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        # if request.method == 'GET' and request.user.has_perm(
        #         "inspections.view_inspection"):
        #     return True
        if request.method == 'GET' and request.user.aerosimple_user and \
            request.user.aerosimple_user.has_permission("view_inspection"):
            return True
        return False


class CanCreateInspections(BasePermission):
    """Allows to create an inspection"""

    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        # if (request.method == 'POST' and request.user.has_perm(
        #         "inspections.add_inspectionparent")):
        #     return True
        if request.method == 'POST' and request.user.aerosimple_user and \
            request.user.aerosimple_user.has_permission("add_inspectionparent"):
            return True
        return False


class CanModifyInspections(BasePermission):
    """Allows to create an inspection version."""

    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        # if (request.method == 'POST' and request.user.has_perm(
        #         "inspections.add_inspection")):
        #     return True
        if request.method == 'POST' and request.user.aerosimple_user and \
            request.user.aerosimple_user.has_permission("add_inspection"):
            return True
        return False


class CanCompleteInspections(BasePermission):
    """Allows to complete an inspection
     (Create an InspectionAnswer instance)."""

    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        # if (request.method == 'POST' and request.user.has_perm(
        #         "inspections.add_inspectionanswer")):
        #     return True
        if request.method == 'POST' and request.user.aerosimple_user and \
            request.user.aerosimple_user.has_permission("add_inspectionanswer"):
            return True
        return False


class CanEditInspections(BasePermission):
    """
        Has edit permissions
    """
    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        # if request.user.has_perm("inspections.change_inspection"):
        #     return True
        if request.user.aerosimple_user and request.user.aerosimple_user.has_permission(
            "change_inspection"):
            return True
        return False


class CanAddInspections(BasePermission):
    """
        Has add permissions
    """
    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        # if request.user.has_perm("inspections.add_inspection"):
        #     return True
        if request.user.aerosimple_user and request.user.aerosimple_user.has_permission(
            "add_inspection"):
            return True
        return False


class CanViewInspectionAnswers(BasePermission):
    """
        Has view inspection answer permissions
    """
    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        if request.user.aerosimple_user and request.user.aerosimple_user.has_permission(
            "view_inspectionanswer"):
            return True
        return False


class CanViewInspectionTemplate(BasePermission):
    """
        Has view inspection template permissions
    """
    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        # if request.user.has_perm("inspections.view_inspectiontemplateform"):
        #     return True
        if request.user.aerosimple_user and request.user.aerosimple_user.has_permission(
            "view_inspectiontemplateform"):
            return True
        return False

