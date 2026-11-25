"""Suite automatizada de pruebas unitarias e integración para TechGrid RESTful API."""
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from .models import ActivoTI, BitacoraAccesoAPI, Departamento, IncidenciaAPI


class TechGridAPITests(APITestCase):
    """Cobertura integral: Serialización, HATEOAS, ViewSets, Filtros, Throttling, CORS/CSRF y OpenAPI."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username='ing_osorio',
            email='osorio@uncp.edu.pe',
            password='PasswordSeguro2026!',
            first_name='José',
            last_name='Osorio',
        )
        self.token, _ = Token.objects.get_or_create(user=self.user)

        self.depto = Departamento.objects.create(
            codigo='DEV-API',
            nombre='Desarrollo de APIs y Microservicios',
            sla_objetivo_horas=6,
            responsable_area='Ing. José Osorio',
            activo=True,
        )
        self.depto_inactivo = Departamento.objects.create(
            codigo='LEG-OFF',
            nombre='Departamento Legado Deshabilitado',
            sla_objetivo_horas=48,
            responsable_area='Sin asignar',
            activo=False,
        )

        # Creamos 7 activos 'activo' para probar paginación (?status=activo&page=2) con page_size=5
        self.activos_creados = []
        for idx in range(1, 8):
            activo = ActivoTI.objects.create(
                nombre=f"Microservicio Core Nodo {idx}",
                tipo='MICROSERVICIO',
                status='activo',
                criticidad='ALTA' if idx % 2 == 0 else 'MEDIA',
                departamento=self.depto,
                sla_horas=6 + idx,
                costo_mensual=250 + idx * 10,
                endpoint_health=f"https://api.uncp.edu.pe/nodo{idx}/health",
                responsable=self.user,
            )
            self.activos_creados.append(activo)

        self.activo_inactivo = ActivoTI.objects.create(
            nombre="Servidor Legacy Descontinuado",
            tipo='SERVIDOR',
            status='inactivo',
            criticidad='BAJA',
            departamento=self.depto,
            sla_horas=72,
            costo_mensual=50,
            responsable=self.user,
        )

    def test_hipervinculos_hateoas_y_campos_readonly(self):
        """Verifica HyperlinkedModelSerializer (url, departamento_url, _links) y ReadOnlyField."""
        url_lista = reverse('servicios_api:activoti-list')
        resp = self.client.get(url_lista)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)
        primero = resp.data['results'][0]

        self.assertTrue(primero['codigo_activo'].startswith('SRV-2026-'))
        self.assertTrue(primero['url'].startswith('http://'))
        self.assertTrue(primero['departamento_url'].startswith('http://'))
        self.assertIn('departamento_detalle', primero)
        self.assertIn('_links', primero)
        for rel in ('self', 'collection', 'departamento', 'incidencias', 'cambiar_estado'):
            self.assertIn(rel, primero['_links'])
            self.assertIsNotNone(primero['_links'][rel])

    def test_seguridad_no_expone_campos_sensibles(self):
        """Garantiza que password, is_staff e is_superuser jamás se serialicen."""
        resp = self.client.post(
            reverse('servicios_api:auth-obtener-token'),
            {'username': 'ing_osorio', 'password': 'PasswordSeguro2026!'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        user_data = resp.data['user']
        self.assertEqual(user_data['username'], 'ing_osorio')
        for campo_sensible in ('password', 'is_staff', 'is_superuser', 'user_permissions'):
            self.assertNotIn(campo_sensible, user_data)

    def test_validacion_cruzada_y_sanitizacion_xss(self):
        """Comprueba validación en serializador (SLA crítico máx 12h, health obligatorio, escape XSS)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        url_lista = reverse('servicios_api:activoti-list')

        # 1. Rechazo por SLA > 12 en criticidad CRITICA
        resp_err = self.client.post(
            url_lista,
            {
                'nombre': 'Microservicio Pagos Crítico',
                'tipo': 'MICROSERVICIO',
                'status': 'activo',
                'criticidad': 'CRITICA',
                'departamento': self.depto.id,
                'sla_horas': 24,
                'costo_mensual': '500.00',
                'endpoint_health': 'https://api.uncp.edu.pe/pagos/health',
            },
            format='json',
        )
        self.assertEqual(resp_err.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('sla_horas', resp_err.data)

        # 2. Creación válida con sanitización XSS en nombre/descripción
        resp_ok = self.client.post(
            url_lista,
            {
                'nombre': '<script>xss()</script> Servicio Validado',
                'tipo': 'MICROSERVICIO',
                'status': 'activo',
                'criticidad': 'ALTA',
                'departamento': self.depto.id,
                'sla_horas': 8,
                'costo_mensual': '300.00',
                'endpoint_health': 'https://api.uncp.edu.pe/validado/health',
                'descripcion': '<b>Descripción segura</b> validada en serializador.',
            },
            format='json',
        )
        self.assertEqual(resp_ok.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('<script>', resp_ok.data['nombre'])
        self.assertIn('&lt;script&gt;', resp_ok.data['nombre'])

    def test_validacion_anidada_incidencia_sobre_activo_inactivo(self):
        """Impide crear incidencias activas contra un activo en estado inactivo."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        url_inc = reverse('servicios_api:incidenciaapi-list')

        resp_fail = self.client.post(
            url_inc,
            {
                'activo': self.activo_inactivo.id,
                'titulo': 'Fallo en servidor dado de baja',
                'descripcion': 'Intento de abrir incidencia sobre un equipo inactivo en catálogo.',
                'status': 'activo',
                'prioridad': 'MEDIA',
                'horas_estimadas': 4,
                'correo_contacto': 'soporte@uncp.edu.pe',
            },
            format='json',
        )
        self.assertEqual(resp_fail.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('activo', resp_fail.data)

        resp_ok = self.client.post(
            url_inc,
            {
                'activo': self.activos_creados[0].id,
                'titulo': 'Latencia elevada en endpoint de salud',
                'descripcion': 'Las sondas reportan latencia superior a 600ms en horario punta.',
                'status': 'activo',
                'prioridad': 'ALTA',
                'horas_estimadas': 6,
                'correo_contacto': 'soporte@uncp.edu.pe',
            },
            format='json',
        )
        self.assertEqual(resp_ok.status_code, status.HTTP_201_CREATED)
        self.assertIn('activo_detalle', resp_ok.data)
        self.assertTrue(resp_ok.data['codigo_ticket'].startswith('TKT-2026-'))

    def test_filtrado_busqueda_ordenamiento_y_paginacion(self):
        """Prueba query params exactos de la guía: ?status=activo&page=2&ordering=-created."""
        url_lista = reverse('servicios_api:activoti-list')
        resp_p2 = self.client.get(f"{url_lista}?status=activo&page=2&ordering=-created")
        self.assertEqual(resp_p2.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_p2.data['count'], 7)
        self.assertEqual(len(resp_p2.data['results']), 2)
        for item in resp_p2.data['results']:
            self.assertEqual(item['status'], 'activo')

        # LimitOffsetPagination en bitácora (requiere autenticación)
        BitacoraAccesoAPI.objects.create(
            metodo='GET', ruta='/api/v1/activos/', usuario='ing_osorio',
            ip_origen='127.0.0.1', codigo_estado=200, latencia_ms=5.2,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        resp_bit = self.client.get(reverse('servicios_api:bitacora-list') + '?limit=5&offset=0')
        self.assertEqual(resp_bit.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp_bit.data)

    def test_acciones_custom_viewset_router(self):
        """Prueba @action(detail=True/False) en ViewSet registrado en DefaultRouter."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        activo = self.activos_creados[0]

        url_estado = reverse('servicios_api:activoti-cambiar-estado', kwargs={'pk': activo.pk})
        resp = self.client.post(url_estado, {'status': 'mantenimiento', 'motivo': 'Parche de seguridad'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'mantenimiento')

        url_metricas = reverse('servicios_api:activoti-resumen-metricas')
        resp_m = self.client.get(url_metricas)
        self.assertEqual(resp_m.status_code, status.HTTP_200_OK)
        self.assertIn('total_activos', resp_m.data)
        self.assertIn('sla_promedio_horas', resp_m.data)

    def test_permisos_globales_y_crud_token(self):
        """Comprueba IsAuthenticatedOrReadOnly global: anónimo solo GET; Token habilita POST/PATCH/DELETE."""
        url_lista = reverse('servicios_api:activoti-list')
        resp_anon = self.client.post(url_lista, {'nombre': 'No autorizado'}, format='json')
        self.assertIn(resp_anon.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        activo = self.activos_creados[1]
        url_det = reverse('servicios_api:activoti-detail', kwargs={'pk': activo.pk})
        resp_patch = self.client.patch(url_det, {'sla_horas': 10}, format='json')
        self.assertEqual(resp_patch.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_patch.data['sla_horas'], 10)

        resp_del = self.client.delete(url_det)
        self.assertEqual(resp_del.status_code, status.HTTP_204_NO_CONTENT)

    def test_throttling_burst_probe_429(self):
        """Verifica que BurstProbeThrottle (5/min) retorne HTTP 429 en la 6ta petición."""
        url_probe = reverse('servicios_api:activoti-throttle-probe')
        for _ in range(5):
            r = self.client.get(url_probe)
            self.assertEqual(r.status_code, status.HTTP_200_OK)
        r_blocked = self.client.get(url_probe)
        self.assertEqual(r_blocked.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_cors_preflight_headers_y_origen_restringido(self):
        """Verifica preflight OPTIONS para origen permitido y bloqueo de origen no autorizado."""
        url_lista = reverse('servicios_api:activoti-list')

        # Origen permitido (Vite SPA localhost:5173)
        resp_ok = self.client.options(
            url_lista,
            HTTP_ORIGIN='http://localhost:5173',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='content-type,x-csrftoken',
        )
        self.assertEqual(resp_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_ok.headers.get('Access-Control-Allow-Origin'), 'http://localhost:5173')
        self.assertEqual(resp_ok.headers.get('Access-Control-Allow-Credentials'), 'true')

        # Origen malicioso no listado en CORS_ALLOWED_ORIGINS
        resp_bad = self.client.options(
            url_lista,
            HTTP_ORIGIN='https://atacante-externo.example',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
        )
        self.assertIsNone(resp_bad.headers.get('Access-Control-Allow-Origin'))

    def test_csrf_enforced_en_spa_login_y_session_post(self):
        """Verifica protección CSRF obligatoria en autenticación por sesión SPA/AJAX."""
        csrf_client = APIClient(enforce_csrf_checks=True)
        url_csrf = reverse('servicios_api:auth-csrf')
        url_login = reverse('servicios_api:auth-login-spa')

        # 1. Sin token CSRF -> 403 Forbidden
        resp_no_csrf = csrf_client.post(
            url_login,
            {'username': 'ing_osorio', 'password': 'PasswordSeguro2026!'},
            format='json',
        )
        self.assertEqual(resp_no_csrf.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Obteniendo cookie CSRF y enviando cabecera X-CSRFToken -> 200 OK
        resp_cookie = csrf_client.get(url_csrf)
        self.assertEqual(resp_cookie.status_code, status.HTTP_200_OK)
        csrf_token = resp_cookie.cookies['csrftoken'].value

        resp_login = csrf_client.post(
            url_login,
            {'username': 'ing_osorio', 'password': 'PasswordSeguro2026!'},
            format='json',
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(resp_login.status_code, status.HTTP_200_OK)
        self.assertIn('token', resp_login.data)

        # 3. Con sesión activa, POST a /api/v1/activos/ sin X-CSRFToken debe dar 403 Forbidden
        url_activos = reverse('servicios_api:activoti-list')
        payload_activo = {
            'nombre': 'Microservicio Sesión CSRF Test',
            'tipo': 'MICROSERVICIO',
            'status': 'activo',
            'criticidad': 'MEDIA',
            'departamento': self.depto.id,
            'sla_horas': 10,
            'costo_mensual': '150.00',
            'endpoint_health': 'https://api.uncp.edu.pe/csrf/health',
        }
        resp_post_sin_csrf = csrf_client.post(url_activos, payload_activo, format='json')
        self.assertEqual(resp_post_sin_csrf.status_code, status.HTTP_403_FORBIDDEN)

        # 4. Enviando X-CSRFToken actualizado desde la cookie -> 201 Created
        csrf_token_auth = csrf_client.cookies['csrftoken'].value
        resp_post_con_csrf = csrf_client.post(
            url_activos,
            payload_activo,
            format='json',
            HTTP_X_CSRFTOKEN=csrf_token_auth,
        )
        self.assertEqual(resp_post_con_csrf.status_code, status.HTTP_201_CREATED)

    def test_openapi_schema_swagger_redoc_y_health(self):
        """Valida OpenAPI 3.0 (/api/schema/, /api/docs/, /api/redoc/), consola SPA y /api/v1/health/."""
        for route_name in ('schema', 'swagger-ui', 'redoc', 'consola_api'):
            resp = self.client.get(reverse(route_name))
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp_health = self.client.get(reverse('servicios_api:health-list'))
        self.assertEqual(resp_health.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_health.data['status'], 'healthy')
        self.assertIn('X-Response-Time-Ms', resp_health.headers)
        self.assertEqual(resp_health.headers.get('X-API-Version'), 'v1')
