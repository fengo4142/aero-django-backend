from rest_framework import routers

from users.views import AerosimpleUserViewSet, RoleViewSet, MobileAerosimpleUserViewSet, \
 UserTypeViewSet


router = routers.SimpleRouter()
router.register(r'users', AerosimpleUserViewSet, base_name='users')
router.register(r'roles', RoleViewSet, base_name='roles')
router.register(r'user_types', UserTypeViewSet, base_name='user_types')
router.register(r'mobile/users', MobileAerosimpleUserViewSet, base_name='mobile_users')

router.register(r'mobile/roles', RoleViewSet, base_name='mobile_roles')
router.register(r'mobile/user_types', UserTypeViewSet, base_name='mobile_user_types')
urlpatterns = [
]
