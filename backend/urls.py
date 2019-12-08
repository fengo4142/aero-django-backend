"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import routers

from airport.urls import router as airport_router
from forms.urls import router as forms_router
from users.urls import router as users_router
from inspections.urls import router as inspections_router
from work_orders.urls import router as work_orders_router
from tasks.urls import router as tasks_router
from operations_log.urls import router as operations_log_router
from notification.urls import router as notification_router
from backend.views import CreateMigrate, RunViewSet, RunCollectStatic, VersionUtil, BuildUtil, StaticImages

router = routers.DefaultRouter()
router.registry.extend(airport_router.registry)
router.registry.extend(forms_router.registry)
router.registry.extend(users_router.registry)
router.registry.extend(inspections_router.registry)
router.registry.extend(work_orders_router.registry)
router.registry.extend(tasks_router.registry)
router.registry.extend(operations_log_router.registry)
router.registry.extend(notification_router.registry)

runRouter = routers.SimpleRouter()
runRouter.register(r'run', RunViewSet, base_name='run')
router.registry.extend(runRouter.registry)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('migrate/', CreateMigrate.as_view()),
    path('collectstatic/', RunCollectStatic.as_view()),
    path('version/', VersionUtil.as_view()),
    path('build/', BuildUtil.as_view()),
    path('transferstatic/', StaticImages.as_view()),
]
