from rest_framework import routers
from work_orders.views import WorkOrderViewSet, MobileWorkOrderViewSet, ExportWorkorderData


router = routers.SimpleRouter()
router.register(r'work_orders', WorkOrderViewSet, base_name='work_orders')
router.register(r'mobile/work_orders', MobileWorkOrderViewSet,
                base_name='mobile_work_orders')
router.register(r'work_orders_data', ExportWorkorderData,
                base_name='work_orders_data')

urlpatterns = [
]
