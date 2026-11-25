"""Enrutador raíz del proyecto: API v1, documentación OpenAPI/Swagger, Admin y Consola SPA."""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from servicios_api.frontend_views import consola_api_view

urlpatterns = [
    path('', consola_api_view, name='consola_api'),
    path('admin/', admin.site.urls),
    path('api/v1/', include('servicios_api.urls')),
    # # IA: Integración de documentación OpenAPI 3.0 automatizada con drf-spectacular -> Solución manual: Exponer schema.yml en /api/schema/ y montar Swagger UI (/api/docs/) y ReDoc (/api/redoc/).
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

admin.site.site_header = "UNCP FIS - Consola Administrativa TechGrid API"
admin.site.site_title = "TechGrid API Portal"
admin.site.index_title = "Gestión de Activos TI, Microservicios y Trazabilidad"
