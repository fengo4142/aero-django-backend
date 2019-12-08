from django.conf import settings
from django.conf.urls.static import static
from .urls import urlpatterns as base_urlpatterns


static_url = static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
media_url = static(settings.MEDIA_URL_PATH, document_root=settings.MEDIA_ROOT)
urlpatterns = base_urlpatterns + media_url + static_url
