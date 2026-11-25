"""ViewSets DRF delgados con Routers, @action custom, filtrado lazy y documentación OpenAPI."""
import time
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.db import connection
from django.db.models import Count, Q, Avg
from django.middleware.csrf import CsrfViewMiddleware, get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import ActivoTIFilter, IncidenciaAPIFilter
from .models import ActivoTI, BitacoraAccesoAPI, Departamento, IncidenciaAPI
from .pagination import LimitOffsetAuditPagination
from .serializers import (
    ActivoTIHyperlinkedSerializer,
    BitacoraAccesoSerializer,
    CambioEstadoActivoSerializer,
    DepartamentoSerializer,
    IncidenciaAPISerializer,
    LoginAPISerializer,
    UsuarioSeguroSerializer,
)
from .throttles import BurstProbeThrottle


@extend_schema_view(
    list=extend_schema(tags=['Departamentos'], summary="Listar departamentos TI"),
    retrieve=extend_schema(tags=['Departamentos'], summary="Obtener detalle de departamento TI"),
    create=extend_schema(tags=['Departamentos'], summary="Registrar nuevo departamento TI"),
    update=extend_schema(tags=['Departamentos'], summary="Actualizar departamento TI"),
    partial_update=extend_schema(tags=['Departamentos'], summary="Actualización parcial de departamento TI"),
    destroy=extend_schema(tags=['Departamentos'], summary="Eliminar departamento TI"),
)
class DepartamentoViewSet(viewsets.ModelViewSet):
    """ViewSet CRUD para Departamentos TI heredando permisos, paginación y filtros globales."""

    serializer_class = DepartamentoSerializer
    filterset_fields = ['activo', 'codigo']
    search_fields = ['codigo', 'nombre', 'responsable_area']
    ordering_fields = ['nombre', 'sla_objetivo_horas', 'created']
    ordering = ['nombre']

    def get_queryset(self):
        return Departamento.objects.annotate(activos_count=Count('activos')).order_by('nombre')


@extend_schema_view(
    list=extend_schema(
        tags=['Activos TI'],
        summary="Listar activos y microservicios TI (Paginado, Filtrado y HATEOAS)",
        parameters=[
            OpenApiParameter(name='status', description='Filtrar por estado (activo, mantenimiento, degradado, inactivo)', required=False, type=str),
            OpenApiParameter(name='criticidad', description='Filtrar por criticidad (BAJA, MEDIA, ALTA, CRITICA)', required=False, type=str),
            OpenApiParameter(name='ordering', description='Ordenar por campo (ej. -created, sla_horas)', required=False, type=str),
        ],
    ),
    retrieve=extend_schema(tags=['Activos TI'], summary="Obtener recurso Activo TI con enlaces HATEOAS"),
    create=extend_schema(tags=['Activos TI'], summary="Registrar nuevo Activo TI"),
    update=extend_schema(tags=['Activos TI'], summary="Reemplazar Activo TI"),
    partial_update=extend_schema(tags=['Activos TI'], summary="Actualizar parcialmente Activo TI"),
    destroy=extend_schema(tags=['Activos TI'], summary="Eliminar Activo TI"),
)
class ActivoTIViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet principal de Activos TI y Microservicios.
    Hereda permission_classes, filter_backends y pagination_class desde settings.REST_FRAMEWORK.
    """

    serializer_class = ActivoTIHyperlinkedSerializer
    filterset_class = ActivoTIFilter
    search_fields = ['codigo_activo', 'nombre', 'descripcion', 'departamento__nombre']
    ordering_fields = ['created', 'updated', 'sla_horas', 'costo_mensual', 'criticidad', 'nombre']
    ordering = ['-created']

    def get_queryset(self):
        return (
            ActivoTI.objects.select_related('departamento', 'responsable')
            .annotate(
                incidencias_activas_total=Count(
                    'incidencias',
                    filter=Q(incidencias__status__in=['activo', 'en_progreso']),
                )
            )
            .order_by('-created')
        )

    def perform_create(self, serializer):
        responsable = self.request.user if self.request.user.is_authenticated else None
        serializer.save(responsable=responsable)

    @extend_schema(
        tags=['Activos TI'],
        summary="Cambiar estado operativo de un Activo TI",
        request=CambioEstadoActivoSerializer,
        responses={200: ActivoTIHyperlinkedSerializer},
    )
    @action(detail=True, methods=['post'], url_path='cambiar-estado')
    def cambiar_estado(self, request, pk=None):
        """Endpoint @action(detail=True) para transición controlada de estado operativo."""
        activo = self.get_object()
        validador = CambioEstadoActivoSerializer(data=request.data)
        validador.is_valid(raise_exception=True)

        activo.status = validador.validated_data['status']
        motivo = validador.validated_data.get('motivo')
        if motivo:
            activo.descripcion = f"{activo.descripcion}\n[Cambio estado: {motivo}]".strip()
        activo.save(update_fields=['status', 'descripcion', 'updated'])

        salida = self.get_serializer(activo)
        return Response(salida.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Activos TI'],
        summary="Listar incidencias asociadas a un Activo TI (Navegación HATEOAS)",
        responses={200: IncidenciaAPISerializer(many=True)},
    )
    @action(detail=True, methods=['get'], url_path='incidencias')
    def incidencias(self, request, pk=None):
        """Endpoint @action(detail=True) que expone la colección hija sin consultas en memoria."""
        activo = self.get_object()
        qs = IncidenciaAPI.objects.select_related('activo', 'reportado_por').filter(activo=activo).order_by('-created')
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = IncidenciaAPISerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = IncidenciaAPISerializer(qs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Activos TI'],
        summary="Resumen de métricas agregadas calculadas en base de datos",
        responses={200: OpenApiResponse(description="Métricas agregadas SQL sin filtrado en memoria")},
    )
    @action(detail=False, methods=['get'], url_path='resumen-metricas')
    def resumen_metricas(self, request):
        """Agregación SQL pura (COUNT/AVG) vía ORM sin cargar listas en memoria."""
        agregados = ActivoTI.objects.aggregate(
            total_activos=Count('id'),
            activos_operativos=Count('id', filter=Q(status='activo')),
            activos_criticos=Count('id', filter=Q(criticidad='CRITICA')),
            activos_degradados=Count('id', filter=Q(status='degradado')),
            sla_promedio_horas=Avg('sla_horas'),
        )
        incidencias_abiertas = IncidenciaAPI.objects.filter(status__in=['activo', 'en_progreso']).count()
        return Response(
            {
                'total_activos': agregados['total_activos'] or 0,
                'activos_operativos': agregados['activos_operativos'] or 0,
                'activos_criticos': agregados['activos_criticos'] or 0,
                'activos_degradados': agregados['activos_degradados'] or 0,
                'sla_promedio_horas': round(agregados['sla_promedio_horas'] or 0.0, 2),
                'incidencias_abiertas': incidencias_abiertas,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=['Activos TI'],
        summary="Endpoint de diagnóstico de Throttling (Límite 5 peticiones/min)",
        responses={
            200: OpenApiResponse(description="Solicitud dentro de cuota permitida"),
            429: OpenApiResponse(description="Too Many Requests - Límite de tasa excedido"),
        },
    )
    @action(
        detail=False,
        methods=['get'],
        url_path='throttle-probe',
        throttle_classes=[BurstProbeThrottle],
    )
    def throttle_probe(self, request):
        """Endpoint @action(detail=False) con BurstProbeThrottle estricto (5/min) para demostrar 429."""
        return Response(
            {
                'status': 'ok',
                'politica_throttle': 'burst_probe (5 peticiones/minuto)',
                'mensaje': 'Cuota vigente. Exceder 5 solicitudes por minuto retornará HTTP 429 Too Many Requests.',
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    list=extend_schema(tags=['Incidencias'], summary="Listar incidencias operativas"),
    retrieve=extend_schema(tags=['Incidencias'], summary="Obtener detalle de incidencia con HATEOAS"),
    create=extend_schema(tags=['Incidencias'], summary="Registrar nueva incidencia operativa"),
    update=extend_schema(tags=['Incidencias'], summary="Actualizar incidencia"),
    partial_update=extend_schema(tags=['Incidencias'], summary="Actualización parcial de incidencia"),
    destroy=extend_schema(tags=['Incidencias'], summary="Eliminar incidencia"),
)
class IncidenciaAPIViewSet(viewsets.ModelViewSet):
    """ViewSet CRUD para tickets de incidencia vinculados a ActivoTI."""

    serializer_class = IncidenciaAPISerializer
    filterset_class = IncidenciaAPIFilter
    search_fields = ['codigo_ticket', 'titulo', 'correo_contacto', 'activo__nombre']
    ordering_fields = ['created', 'prioridad', 'horas_estimadas', 'status']
    ordering = ['-created']

    def get_queryset(self):
        return IncidenciaAPI.objects.select_related('activo', 'activo__departamento', 'reportado_por').order_by('-created')

    def perform_create(self, serializer):
        reportado_por = self.request.user if self.request.user.is_authenticated else None
        serializer.save(reportado_por=reportado_por)

    @extend_schema(
        tags=['Incidencias'],
        summary="Marcar incidencia como resuelta",
        request=None,
        responses={200: IncidenciaAPISerializer},
    )
    @action(detail=True, methods=['post'], url_path='resolver')
    def resolver(self, request, pk=None):
        """Transiciona el ticket al estado resuelto mediante @action(detail=True)."""
        incidencia = self.get_object()
        incidencia.status = 'resuelto'
        incidencia.save(update_fields=['status', 'updated'])
        serializer = self.get_serializer(incidencia)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(tags=['Bitácora'], summary="Consultar bitácora de auditoría HTTP (Requiere Auth)"),
    retrieve=extend_schema(tags=['Bitácora'], summary="Obtener evento individual de bitácora"),
)
class BitacoraAccesoViewSet(viewsets.ReadOnlyModelViewSet):
    """ReadOnlyModelViewSet protegido con paginación LimitOffsetPagination."""

    queryset = BitacoraAccesoAPI.objects.all().order_by('-created')
    serializer_class = BitacoraAccesoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetAuditPagination
    filterset_fields = ['metodo', 'codigo_estado']
    search_fields = ['ruta', 'usuario', 'ip_origen']
    ordering_fields = ['created', 'latencia_ms', 'codigo_estado']


class AuthSessionViewSet(viewsets.ViewSet):
    """
    ViewSet dedicado para gestión de CSRF en SPA/AJAX, autenticación de sesión
    y emisión de tokens DRF stateless sin exponer campos sensibles.
    """

    @extend_schema(
        tags=['Autenticación & CSRF'],
        summary="Obtener cookie y token CSRF para clientes SPA/AJAX",
        responses={200: OpenApiResponse(description="Cookie csrftoken emitida y token retornado en JSON")},
    )
    @method_decorator(ensure_csrf_cookie)
    @action(detail=False, methods=['get'], url_path='csrf', permission_classes=[AllowAny])
    def csrf(self, request):
        # # IA: Error 403 Forbidden en peticiones POST AJAX desde SPA desacoplada -> Solución manual: Exponer endpoint público con @ensure_csrf_cookie para emitir csrftoken y permitir envío en cabecera X-CSRFToken.
        token = get_token(request)
        return Response({'csrfToken': token}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Autenticación & CSRF'],
        summary="Autenticación de sesión SPA (valida X-CSRFToken) y retorno de Token DRF",
        request=LoginAPISerializer,
        responses={200: OpenApiResponse(description="Sesión iniciada y token emitido")},
    )
    @action(detail=False, methods=['post'], url_path='login', permission_classes=[AllowAny])
    def login_spa(self, request):
        # Verificación explícita de protección CSRF para login por sesión SPA/AJAX
        csrf_check = CsrfViewMiddleware(lambda req: None)
        csrf_reason = csrf_check.process_view(request._request, None, (), {})
        if csrf_reason is not None:
            return Response(
                {'detail': 'CSRF verification failed. Envíe cookie csrftoken y cabecera X-CSRFToken.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = LoginAPISerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request=request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if not user:
            return Response(
                {'detail': 'Credenciales inválidas.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        auth_login(request, user)
        token_obj, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                'detail': 'Autenticación de sesión exitosa.',
                'token': token_obj.key,
                'user': UsuarioSeguroSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=['Autenticación & CSRF'],
        summary="Emisión de Token DRF stateless para clientes API/Postman/cURL",
        request=LoginAPISerializer,
        responses={200: OpenApiResponse(description="Token DRF retornado sin requerir cookies de sesión")},
    )
    @action(
        detail=False,
        methods=['post'],
        url_path='token',
        permission_classes=[AllowAny],
        authentication_classes=[],
    )
    def obtener_token(self, request):
        serializer = LoginAPISerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request=request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if not user:
            return Response(
                {'detail': 'Credenciales inválidas para emisión de token.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        token_obj, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                'token': token_obj.key,
                'scheme': 'Token',
                'user': UsuarioSeguroSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=['Autenticación & CSRF'],
        summary="Cerrar sesión SPA activa",
        request=None,
        responses={200: OpenApiResponse(description="Sesión finalizada")},
    )
    @action(detail=False, methods=['post'], url_path='logout', permission_classes=[IsAuthenticated])
    def logout_spa(self, request):
        auth_logout(request)
        return Response({'detail': 'Sesión finalizada correctamente.'}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Autenticación & CSRF'],
        summary="Consultar perfil seguro del usuario autenticado",
        responses={200: UsuarioSeguroSerializer},
    )
    @action(detail=False, methods=['get'], url_path='me', permission_classes=[IsAuthenticated])
    def me(self, request):
        return Response(UsuarioSeguroSerializer(request.user).data, status=status.HTTP_200_OK)


class HealthCheckViewSet(viewsets.ViewSet):
    """Sonda de salud del servicio RESTful orientada a contenedores y microservicios (Semana 14)."""

    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Infraestructura'],
        summary="Health check de disponibilidad y latencia de base de datos",
        responses={200: OpenApiResponse(description="Servicio operativo y listo para balanceador/Docker")},
    )
    def list(self, request):
        t0 = time.perf_counter()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        return Response(
            {
                'status': 'healthy',
                'service': 'techgrid-restful-api',
                'version': '1.0.0',
                'database': 'connected',
                'db_latency_ms': db_ms,
                'microservice_readiness': {
                    'stateless_token_auth': True,
                    'cors_restricted': True,
                    'openapi_schema': '/api/schema/',
                    'swagger_ui': '/api/docs/',
                },
            },
            status=status.HTTP_200_OK,
        )
