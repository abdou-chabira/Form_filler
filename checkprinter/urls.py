from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from . import admin as project_admin  # noqa: F401

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("paycheck.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
