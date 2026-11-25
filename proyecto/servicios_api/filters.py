"""FilterSets declarativos ejecutados sobre QuerySets SQL (lazy evaluation)."""
import django_filters
from .models import ActivoTI, IncidenciaAPI


class ActivoTIFilter(django_filters.FilterSet):
    """Filtros combinados sobre campos indexados de ActivoTI sin materializar en memoria."""

    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    criticidad = django_filters.CharFilter(field_name='criticidad', lookup_expr='iexact')
    tipo = django_filters.CharFilter(field_name='tipo', lookup_expr='iexact')
    departamento = django_filters.NumberFilter(field_name='departamento_id')
    departamento_codigo = django_filters.CharFilter(field_name='departamento__codigo', lookup_expr='iexact')
    sla_horas_min = django_filters.NumberFilter(field_name='sla_horas', lookup_expr='gte')
    sla_horas_max = django_filters.NumberFilter(field_name='sla_horas', lookup_expr='lte')
    created_after = django_filters.IsoDateTimeFilter(field_name='created', lookup_expr='gte')

    class Meta:
        model = ActivoTI
        fields = [
            'status',
            'criticidad',
            'tipo',
            'departamento',
            'departamento_codigo',
            'sla_horas_min',
            'sla_horas_max',
            'created_after',
        ]


class IncidenciaAPIFilter(django_filters.FilterSet):
    """Filtros combinados sobre IncidenciaAPI mediante evaluación diferida del ORM."""

    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    prioridad = django_filters.CharFilter(field_name='prioridad', lookup_expr='iexact')
    activo = django_filters.NumberFilter(field_name='activo_id')
    horas_max = django_filters.NumberFilter(field_name='horas_estimadas', lookup_expr='lte')

    class Meta:
        model = IncidenciaAPI
        fields = ['status', 'prioridad', 'activo', 'horas_max']
