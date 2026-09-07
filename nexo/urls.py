from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.account.views import onboarding, signup

urlpatterns = [
    path("admin/", admin.site.urls),
    # Landing pública
    path("", include("apps.landing.urls")),
    # Auth / onboarding
    path("", include("apps.account.urls")),
    # Workspace
    path("dashboard/", include("apps.dashboard.urls")),
    path("cotizaciones/", include("apps.quotations.urls")),
    path("clientes/", include("apps.clients.urls")),
    path("pedidos/", include("apps.orders.urls")),
    path("productos/", include("apps.products.urls")),
    path("configuracion/", include("apps.settings.urls")),
    path("notificaciones/", include("apps.notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)