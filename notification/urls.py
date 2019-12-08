from rest_framework import routers
from django.conf.urls import url
from notification import views
from notification.views import exportInspection,exportInspectionAnswer



router = routers.SimpleRouter()
#router.register(r'export', NotificationViewSet, base_name='export')

urlpatterns = [
    url('exportpdf/', exportInspectionAnswer),
    url('export/',exportInspection)
]