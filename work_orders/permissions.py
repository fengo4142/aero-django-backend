import logging

from rest_framework.permissions import BasePermission
from work_orders.models import WorkOrderForm

logger = logging.getLogger('backend')


# *****************************************************************************
# *****************************   WORK ORDERS   *******************************
# *****************************************************************************

class CanCreateWorkOrders(BasePermission):
    """Allows to create a work order"""

    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        # if (request.method == 'POST' and request.user.has_perm(
        #         "work_orders.add_workorder")):
        #     return True
        if (request.method == 'POST' and request.user.aerosimple_user and \
            request.user.aerosimple_user.has_permission("add_workorder")):
            return True
        return False


class CanViewWorkOrders(BasePermission):
    """Allows to view work orders list and detail """

    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        # if (request.method == 'GET' and request.user.has_perm(
        #         "work_orders.view_workorder")):
        #     return True
        if (request.method == 'GET' and request.user.aerosimple_user and \
            request.user.aerosimple_user.has_permission("view_workorder")):
            return True
        return False


class CanFillMaintenanceForm(BasePermission):
    """Allows to create a Maintenance form"""

    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False

        woform = WorkOrderForm.objects.get(
            airport__id=request.user.aerosimple_user.airport_id)

        role = woform.maintenance_form.assigned_role
        users = woform.maintenance_form.assigned_users

        has_role = role in request.user.aerosimple_user.roles.all()
        is_assigned = request.user.aerosimple_user in users.all()

        if (request.method == 'POST' and request.user.aerosimple_user
            and request.user.aerosimple_user.has_permission("add_maintenance")
            and request.user.aerosimple_user.has_permission("view_workorder")
                and (has_role or is_assigned)):
                return True
        return False


class CanFillOperationsForm(BasePermission):
    """Allows to create a Operations form"""

    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False

        woform = WorkOrderForm.objects.get(
            airport__id=request.user.aerosimple_user.airport_id)

        role = woform.operations_form.assigned_role
        users = woform.operations_form.assigned_users

        has_role = role in request.user.aerosimple_user.roles.all()
        is_assigned = request.user.aerosimple_user in users.all()

        if (request.method == 'POST' and request.user.aerosimple_user
            and request.user.aerosimple_user.has_permission("add_operations")
            and request.user.aerosimple_user.has_permission("view_workorder")
                and (has_role or is_assigned)):
                return True
        return False


class CanEditWorkOrderSchema(BasePermission):
    """Allows to create work order schema instances"""

    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            return False
        # if (request.method == 'POST' and request.user.has_perm(
        #         "work_orders.add_workorderschema")):
        #     return True
        if (request.method == 'POST' and request.user.aerosimple_user and \
            request.user.aerosimple_user.has_permission("add_workorderschema")):
            return True
        return False