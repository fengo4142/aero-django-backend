from rest_framework import routers

from tasks.views import TaskViewSet, RuleViewSet

router = routers.SimpleRouter()
router.register(r'tasks', TaskViewSet, base_name='tasks')
router.register(r'rules', RuleViewSet, base_name='rules')

router.register(r'mobile/tasks', TaskViewSet, base_name='mobile_tasks')
router.register(r'mobile/rules', RuleViewSet, base_name='mobile_rules')

urlpatterns = [
]
