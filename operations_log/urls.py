from rest_framework import routers
from operations_log.views import LogViewSet


router = routers.SimpleRouter()
router.register(r'operations_logs', LogViewSet, base_name='operations_logs')

router.register(r'mobile/operations_logs', LogViewSet, base_name='mobile_operations_logs')

urlpatterns = [
]
