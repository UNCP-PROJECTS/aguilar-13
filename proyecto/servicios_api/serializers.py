"""Serializadores DRF avanzados con validación en pipeline, representación anidada e HATEOAS."""
import html
from rest_framework import serializers
from rest_framework.reverse import reverse
from django.contrib.auth.models import User
from .models import Departamento, ActivoTI, IncidenciaAPI, BitacoraAccesoAPI


def sanitizar_texto(valor):
    """Normaliza espacios y escapa entidades HTML para mitigar XSS en cargas JSON."""
    if valor is None:
        return ""
    return html.escape(str(valor).strip())


class UsuarioSeguroSerializer(serializers.ModelSerializer):
    """Serializador seguro de usuario: excluye explícitamente password, is_staff y is_superuser."""

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')
        read_only_fields = ('id', 'username')


class DepartamentoResumenSerializer(serializers.ModelSerializer):
    """Representación compacta de solo lectura para anidar en recursos ActivoTI."""

    class Meta:
        model = Departamento
        fields = ('id', 'codigo', 'nombre', 'sla_objetivo_horas', 'activo')


class DepartamentoSerializer(serializers.HyperlinkedModelSerializer):
    """Serializador hipervinculado para departamentos TI con métricas agregadas."""

    url = serializers.HyperlinkedIdentityField(view_name='servicios_api:departamento-detail')
    total_activos = serializers.SerializerMethodField()
    _links = serializers.SerializerMethodField()

    class Meta:
        model = Departamento
        fields = (
            'id',
            'url',
            'codigo',
            'nombre',
            'sla_objetivo_horas',
            'responsable_area',
            'activo',
            'total_activos',
            '_links',
            'created',
            'updated',
        )
        read_only_fields = ('id', 'created', 'updated')

    def validate_codigo(self, value):
        limpio = sanitizar_texto(value).upper()
        if len(limpio) < 2:
            raise serializers.ValidationError("El código del departamento debe tener al menos 2 caracteres.")
        return limpio

    def validate_nombre(self, value):
        limpio = sanitizar_texto(value)
        if len(limpio) < 4:
            raise serializers.ValidationError("El nombre del departamento debe tener al menos 4 caracteres.")
        return limpio

    def get_total_activos(self, obj) -> int:
        if hasattr(obj, 'activos_count'):
            return obj.activos_count
        return obj.activos.count()

    def get__links(self, obj) -> dict:
        request = self.context.get('request')
        return {
            'self': reverse('servicios_api:departamento-detail', kwargs={'pk': obj.pk}, request=request),
            'collection': reverse('servicios_api:departamento-list', request=request),
            'activos_asociados': f"{reverse('servicios_api:activoti-list', request=request)}?departamento={obj.pk}",
        }


class ActivoTIHyperlinkedSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializador avanzado con HyperlinkedModelSerializer, campos read-only,
    anidamiento controlado, validación cruzada e hipervínculos HATEOAS.
    """

    # # IA: Error en HyperlinkedModelSerializer cuando urls.py usa app_name -> Solución manual: Declarar explícitamente view_name='servicios_api:<recurso>-detail' y propagar context={'request': request} en ViewSets y acciones para evitar URLs nulas.
    url = serializers.HyperlinkedIdentityField(view_name='servicios_api:activoti-detail')
    departamento_url = serializers.HyperlinkedRelatedField(
        source='departamento',
        view_name='servicios_api:departamento-detail',
        read_only=True,
    )
    departamento = serializers.PrimaryKeyRelatedField(queryset=Departamento.objects.all())
    departamento_detalle = DepartamentoResumenSerializer(source='departamento', read_only=True)
    codigo_activo = serializers.ReadOnlyField()
    departamento_nombre = serializers.ReadOnlyField(source='departamento.nombre')
    responsable_username = serializers.ReadOnlyField(source='responsable.username', default='Sin asignar')
    nivel_riesgo = serializers.SerializerMethodField()
    incidencias_activas_count = serializers.SerializerMethodField()
    _links = serializers.SerializerMethodField()

    class Meta:
        model = ActivoTI
        fields = (
            'id',
            'url',
            'codigo_activo',
            'nombre',
            'tipo',
            'status',
            'criticidad',
            'departamento',
            'departamento_url',
            'departamento_nombre',
            'departamento_detalle',
            'sla_horas',
            'costo_mensual',
            'endpoint_health',
            'responsable_username',
            'descripcion',
            'nivel_riesgo',
            'incidencias_activas_count',
            '_links',
            'created',
            'updated',
        )
        read_only_fields = ('id', 'codigo_activo', 'created', 'updated')

    def validate_nombre(self, value):
        limpio = sanitizar_texto(value)
        if len(limpio) < 5:
            raise serializers.ValidationError("El nombre del activo TI debe contener al menos 5 caracteres.")
        return limpio

    def validate_descripcion(self, value):
        return sanitizar_texto(value)

    def validate_sla_horas(self, value):
        if value < 1 or value > 168:
            raise serializers.ValidationError("El SLA comprometido debe oscilar entre 1 y 168 horas.")
        return value

    def validate_costo_mensual(self, value):
        if value < 0:
            raise serializers.ValidationError("El costo operativo mensual no puede ser negativo.")
        return value

    def validate(self, attrs):
        """Validación cruzada e integridad relacional antes de persistir."""
        instance = getattr(self, 'instance', None)
        criticidad = attrs.get('criticidad', instance.criticidad if instance else 'MEDIA')
        sla_horas = attrs.get('sla_horas', instance.sla_horas if instance else 12)
        tipo = attrs.get('tipo', instance.tipo if instance else 'MICROSERVICIO')
        status_val = attrs.get('status', instance.status if instance else 'activo')
        endpoint_health = attrs.get('endpoint_health', instance.endpoint_health if instance else '')
        departamento = attrs.get('departamento', instance.departamento if instance else None)

        if departamento and not departamento.activo:
            raise serializers.ValidationError({
                'departamento': "No es posible asignar activos a un departamento marcado como inactivo."
            })

        if criticidad == 'CRITICA' and sla_horas > 12:
            raise serializers.ValidationError({
                'sla_horas': "Política SLA: un activo con criticidad CRITICA no puede superar las 12 horas de SLA."
            })

        if tipo == 'MICROSERVICIO' and status_val == 'activo' and not endpoint_health:
            raise serializers.ValidationError({
                'endpoint_health': "Todo microservicio activo debe declarar una URL válida de endpoint_health."
            })

        return attrs

    def get_nivel_riesgo(self, obj) -> str:
        return obj.calcular_nivel_riesgo()

    def get_incidencias_activas_count(self, obj) -> int:
        if hasattr(obj, 'incidencias_activas_total'):
            return obj.incidencias_activas_total
        return obj.incidencias.filter(status__in=['activo', 'en_progreso']).count()

    def get__links(self, obj) -> dict:
        request = self.context.get('request')
        return {
            'self': reverse('servicios_api:activoti-detail', kwargs={'pk': obj.pk}, request=request),
            'collection': reverse('servicios_api:activoti-list', request=request),
            'departamento': reverse('servicios_api:departamento-detail', kwargs={'pk': obj.departamento_id}, request=request),
            'incidencias': reverse('servicios_api:activoti-incidencias', kwargs={'pk': obj.pk}, request=request),
            'cambiar_estado': reverse('servicios_api:activoti-cambiar-estado', kwargs={'pk': obj.pk}, request=request),
        }


class CambioEstadoActivoSerializer(serializers.Serializer):
    """Serializador de entrada para la acción custom @action cambiar-estado."""

    status = serializers.ChoiceField(choices=ActivoTI.STATUS_CHOICES)
    motivo = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def validate_motivo(self, value):
        return sanitizar_texto(value)


class ActivoResumenSerializer(serializers.ModelSerializer):
    """Resumen anidado de Activo TI dentro de IncidenciaAPISerializer."""

    class Meta:
        model = ActivoTI
        fields = ('id', 'codigo_activo', 'nombre', 'tipo', 'status', 'criticidad')


class IncidenciaAPISerializer(serializers.HyperlinkedModelSerializer):
    """Serializador para tickets de incidencia con validación anidada sobre el activo asociado."""

    url = serializers.HyperlinkedIdentityField(view_name='servicios_api:incidenciaapi-detail')
    activo = serializers.PrimaryKeyRelatedField(queryset=ActivoTI.objects.select_related('departamento'))
    activo_url = serializers.HyperlinkedRelatedField(
        source='activo',
        view_name='servicios_api:activoti-detail',
        read_only=True,
    )
    activo_detalle = ActivoResumenSerializer(source='activo', read_only=True)
    codigo_ticket = serializers.ReadOnlyField()
    reportado_por_username = serializers.ReadOnlyField(source='reportado_por.username', default='Anonimo')
    nivel_impacto = serializers.SerializerMethodField()
    _links = serializers.SerializerMethodField()

    class Meta:
        model = IncidenciaAPI
        fields = (
            'id',
            'url',
            'codigo_ticket',
            'activo',
            'activo_url',
            'activo_detalle',
            'titulo',
            'descripcion',
            'status',
            'prioridad',
            'horas_estimadas',
            'correo_contacto',
            'reportado_por_username',
            'nivel_impacto',
            '_links',
            'created',
            'updated',
        )
        read_only_fields = ('id', 'codigo_ticket', 'created', 'updated')

    def validate_titulo(self, value):
        limpio = sanitizar_texto(value)
        if len(limpio) < 8:
            raise serializers.ValidationError("El título debe describir el incidente con al menos 8 caracteres.")
        return limpio

    def validate_descripcion(self, value):
        limpio = sanitizar_texto(value)
        if len(limpio) < 15:
            raise serializers.ValidationError("La descripción técnica requiere al menos 15 caracteres válidos.")
        return limpio

    def validate_horas_estimadas(self, value):
        if value < 1 or value > 120:
            raise serializers.ValidationError("Las horas estimadas deben estar comprendidas entre 1 y 120.")
        return value

    def validate(self, attrs):
        """Validación anidada verificando estado y criticidad del ActivoTI relacionado."""
        instance = getattr(self, 'instance', None)
        activo = attrs.get('activo', instance.activo if instance else None)
        prioridad = attrs.get('prioridad', instance.prioridad if instance else 'MEDIA')
        horas = attrs.get('horas_estimadas', instance.horas_estimadas if instance else 4)
        status_val = attrs.get('status', instance.status if instance else 'activo')

        if activo and activo.status == 'inactivo' and status_val == 'activo':
            raise serializers.ValidationError({
                'activo': "No se pueden abrir incidencias activas sobre un Activo TI dado de baja (inactivo)."
            })

        if prioridad == 'CRITICA' and horas > 24:
            raise serializers.ValidationError({
                'horas_estimadas': "Las incidencias con prioridad CRITICA deben atenderse en un máximo de 24 horas."
            })

        if activo and activo.criticidad == 'CRITICA' and prioridad == 'BAJA':
            raise serializers.ValidationError({
                'prioridad': "Un activo de criticidad CRITICA no admite incidencias catalogadas como BAJA."
            })

        return attrs

    def get_nivel_impacto(self, obj) -> str:
        if obj.prioridad == 'CRITICA' or obj.activo.criticidad == 'CRITICA':
            return 'Impacto Severo'
        if obj.prioridad == 'ALTA':
            return 'Impacto Alto'
        return 'Impacto Controlado'

    def get__links(self, obj) -> dict:
        request = self.context.get('request')
        return {
            'self': reverse('servicios_api:incidenciaapi-detail', kwargs={'pk': obj.pk}, request=request),
            'collection': reverse('servicios_api:incidenciaapi-list', request=request),
            'activo': reverse('servicios_api:activoti-detail', kwargs={'pk': obj.activo_id}, request=request),
            'resolver': reverse('servicios_api:incidenciaapi-resolver', kwargs={'pk': obj.pk}, request=request),
        }


class BitacoraAccesoSerializer(serializers.ModelSerializer):
    """Serializador de solo lectura para auditar tráfico HTTP de la API."""

    class Meta:
        model = BitacoraAccesoAPI
        fields = (
            'id',
            'metodo',
            'ruta',
            'usuario',
            'ip_origen',
            'codigo_estado',
            'latencia_ms',
            'origen_cors',
            'created',
        )
        read_only_fields = fields


class LoginAPISerializer(serializers.Serializer):
    """Serializador de credenciales para autenticación SPA/AJAX o emisión de Token DRF."""

    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
