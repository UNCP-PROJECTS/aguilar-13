"""
Configuración principal del proyecto TechGrid API Gateway (UNCP FIS - Semana 13).
Diseño de API RESTful production-ready con Django REST Framework, CORS, CSRF y OpenAPI 3.0.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-lab13-uncp-fis-drf-rest-api-hateoas-openapi-key'
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('1', 'true', 'yes')

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost,testserver').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Ecosistema Django REST Framework (Fase 1 & Fase 4 & Fase 5)
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'corsheaders',
    'drf_spectacular',
    # Aplicación principal de dominio API
    'servicios_api.apps.ServiciosApiConfig',
]

# # IA: Error de preflight OPTIONS bloqueado por CommonMiddleware -> Solución manual: Ubicar CorsMiddleware inmediatamente después de SecurityMiddleware y antes de CommonMiddleware para interceptar solicitudes OPTIONS antes del enrutamiento Django.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'servicios_api.middleware.ApiTelemetryMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 6}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# CONFIGURACIÓN GLOBAL DE DJANGO REST FRAMEWORK (Fase 1, Fase 3, Fase 4)
# Prohibido hardcodear permisos en vistas; todo se gobierna centralizadamente.
# ==============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'servicios_api.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 5,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/min',
        'user': '240/min',
        'burst_probe': '5/min',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S%z',
}

# ==============================================================================
# CONFIGURACIÓN ESTRICTA DE CORS Y CSRF PARA ENTORNOS SPA/AJAX (Fase 5)
# No se usa CORS_ALLOW_ALL_ORIGINS = True; se declaran orígenes explícitos.
# ==============================================================================
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'authorization',
    'content-type',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_EXPOSE_HEADERS = [
    'X-Response-Time-Ms',
    'X-API-Version',
    'X-Service-Mode',
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# # IA: Acceso JavaScript al token CSRF en peticiones AJAX/SPA -> Solución manual: Mantener CSRF_COOKIE_HTTPONLY = False para que la SPA lea csrftoken y lo envíe explícitamente en cabecera X-CSRFToken, preservando SESSION_COOKIE_HTTPONLY = True.
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1800
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
X_FRAME_OPTIONS = 'DENY'

# ==============================================================================
# DOCUMENTACIÓN AUTOMÁTICA OPENAPI 3.0 / SWAGGER (drf-spectacular)
# ==============================================================================
SPECTACULAR_SETTINGS = {
    'TITLE': 'UNCP FIS • TechGrid RESTful API Gateway',
    'DESCRIPTION': (
        'API RESTful production-ready construida con Django REST Framework (DRF) para '
        'la gestión de Activos TI, Microservicios, Departamentos e Incidentes Operativos. '
        'Implementa navegación HATEOAS, serialización hipervinculada, filtrado lazy en BD, '
        'paginación estándar, throttling multicapa, CORS restringido, protección CSRF y '
        'telemetría de preparación para arquitectura de microservicios (Semana 14).'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {
        'name': 'José Pablo Osorio Mallqui (UNCP FIS - 2022200839H)',
        'email': '2022200839h@uncp.edu.pe',
    },
    'SCHEMA_PATH_PREFIX': r'/api/v1',
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
    # # IA: ReDoc @latest en CDN emite SyntaxError 'Cannot use import.meta outside a module' -> Solución manual: Fijar REDOC_DIST a la versión UMD estable redoc@2.2.0.
    'REDOC_DIST': 'https://cdn.jsdelivr.net/npm/redoc@2.2.0',
    'ENUM_NAME_OVERRIDES': {
        'ActivoStatusEnum': 'servicios_api.models.ActivoTI.STATUS_CHOICES',
        'IncidenciaStatusEnum': 'servicios_api.models.IncidenciaAPI.STATUS_CHOICES',
        'NivelSeveridadEnum': 'servicios_api.models.ActivoTI.CRITICIDAD_CHOICES',
    },
    'TAGS': [
        {'name': 'Departamentos', 'description': 'Unidades orgánicas y acuerdos SLA base.'},
        {'name': 'Activos TI', 'description': 'Catálogo de microservicios, servidores y bases de datos con HATEOAS.'},
        {'name': 'Incidencias', 'description': 'Gestión operativa de tickets e incidencias asociadas a activos TI.'},
        {'name': 'Bitácora', 'description': 'Trazabilidad de solo lectura de peticiones HTTP y latencia.'},
        {'name': 'Autenticación & CSRF', 'description': 'Gestión de sesión SPA, token CSRF y tokens DRF stateless.'},
        {'name': 'Infraestructura', 'description': 'Health-check y diagnóstico para despliegue en contenedores (Semana 14).'},
    ],
}
