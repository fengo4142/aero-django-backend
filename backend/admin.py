from django.contrib.gis.admin import AdminSite
from .login import AerosimpleLoginForm
from django.utils.translation import ugettext_lazy as _

class AerosimpleAdminSite(AdminSite):
    site_title = _('Aerosimple Admin')
    site_header = _('Administration')
    index_title = _('Aerosimple Login')
    #registering Custom login form for the Login interface
    #this login form uses CustomBackend
    login_form = AerosimpleLoginForm

#create a Admin_site object to register models
site = AerosimpleAdminSite()
