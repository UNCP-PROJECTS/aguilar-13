"""Enrutamiento automático DRF mediante DefaultRouter con namespace explícito para HATEOAS."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ActivoTIViewSet,
    AuthSessionViewSet,
    BitacoraAccesoViewSet,
    DepartamentoViewSet,
    HealthCheckViewSet,
    IncidenciaAPIViewSet,
)

app_name = 'servicios_api'

router = DefaultRouter()
router.register(r'departamentos', DepartamentoViewSet, basename='departamento')
router.register(r'activos', ActivoTIViewSet, basename='activoti')
router.register(r'incidencias', IncidenciaAPIViewSet, basename='incidenciaapi')
router.register(r'bitacora', BitacoraAccesoViewSet, basename='bitacora')
router.register(r'auth', AuthSessionViewSet, basename='auth')
router.register(r'health', HealthCheckViewSet, basename='health')

urlpatterns = [
    path('', include(router.urls)),
]
