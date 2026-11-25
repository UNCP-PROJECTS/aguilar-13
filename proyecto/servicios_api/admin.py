"""Configuración operativa del panel Django Admin para TechGrid RESTful API."""
from django.contrib import admin
from django.utils.html import format_html
from .models import Departamento, ActivoTI, IncidenciaAPI, BitacoraAccesoAPI


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'sla_objetivo_horas', 'responsable_area', 'activo', 'created')
    list_filter = ('activo',)
    search_fields = ('codigo', 'nombre', 'responsable_area')


@admin.register(ActivoTI)
class ActivoTIAdmin(admin.ModelAdmin):
    list_display = (
        'codigo_activo',
        'nombre',
        'tipo',
        'status_badge',
        'criticidad_badge',
        'departamento',
        'sla_horas',
        'responsable',
        'created',
    )
    list_filter = ('status', 'criticidad', 'tipo', 'departamento')
    search_fields = ('codigo_activo', 'nombre', 'departamento__nombre')
    readonly_fields = ('codigo_activo', 'created', 'updated')
    actions = ['marcar_activos', 'enviar_a_mantenimiento']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('departamento', 'responsable')

    @admin.display(description="Estado", ordering="status")
    def status_badge(self, obj):
        colores = {
            'activo': '#15803d',
            'mantenimiento': '#b45309',
            'degradado': '#b91c1c',
            'inactivo': '#475569',
        }
        return format_html(
            '<span style="padding:2px 8px;border-radius:4px;color:#fff;font-weight:600;font-size:11px;background:{};">{}</span>',
            colores.get(obj.status, '#475569'),
            obj.get_status_display(),
        )

    @admin.display(description="Criticidad", ordering="criticidad")
    def criticidad_badge(self, obj):
        colores = {'BAJA': '#334155', 'MEDIA': '#1d4ed8', 'ALTA': '#b45309', 'CRITICA': '#b91c1c'}
        return format_html(
            '<span style="padding:2px 8px;border-radius:4px;color:#fff;font-weight:600;font-size:11px;background:{};">{}</span>',
            colores.get(obj.criticidad, '#334155'),
            obj.get_criticidad_display(),
        )

    @admin.action(description="Marcar activos seleccionados como ACTIVO")
    def marcar_activos(self, request, queryset):
        count = queryset.update(status='activo')
        self.message_user(request, f"{count} activo(s) actualizados a estado ACTIVO.")

    @admin.action(description="Enviar activos seleccionados a MANTENIMIENTO")
    def enviar_a_mantenimiento(self, request, queryset):
        count = queryset.update(status='mantenimiento')
        self.message_user(request, f"{count} activo(s) enviados a MANTENIMIENTO.")


@admin.register(IncidenciaAPI)
class IncidenciaAPIAdmin(admin.ModelAdmin):
    list_display = ('codigo_ticket', 'titulo', 'activo', 'status', 'prioridad', 'horas_estimadas', 'created')
    list_filter = ('status', 'prioridad', 'created')
    search_fields = ('codigo_ticket', 'titulo', 'activo__nombre')
    readonly_fields = ('codigo_ticket', 'created', 'updated')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('activo', 'reportado_por')


@admin.register(BitacoraAccesoAPI)
class BitacoraAccesoAPIAdmin(admin.ModelAdmin):
    list_display = ('created', 'metodo', 'ruta', 'usuario', 'ip_origen', 'codigo_estado', 'latencia_ms')
    list_filter = ('metodo', 'codigo_estado')
    search_fields = ('ruta', 'usuario', 'ip_origen')
    readonly_fields = ('metodo', 'ruta', 'usuario', 'ip_origen', 'codigo_estado', 'latencia_ms', 'origen_cors', 'created')

    def has_add_permission(self, request):
        return False
