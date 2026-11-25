# UNCP FIS - Desarrollo de Aplicaciones Web (IS093A)
## Guía Práctica 13: Diseño de APIs RESTful con Django REST Framework (DRF)

* **Estudiante:** José Pablo Osorio Mallqui (`2022200839H`)
* **Docente Titular:** Ing. Miguel Aguilar
* **Semestre Académico:** 2026-II
* **Fecha:** 25 de noviembre de 2026
* **Repositorio GitHub:** [https://github.com/UNCP-PROJECTS/aguilar-13](https://github.com/UNCP-PROJECTS/aguilar-13)
* **Arquitectura:** Django 5.2 + Django REST Framework 3.18 + `django-cors-headers` + `django-filter` + `drf-spectacular` (OpenAPI 3.0) + Python 3.12 + SQLite

---

### Resumen del Proyecto: TechGrid RESTful API Gateway

Plataforma backend production-ready para la gestión, monitoreo y trazabilidad de **Activos TI, Microservicios, Departamentos e Incidencias Operativas**, aplicando los principios arquitectónicos REST (*stateless, cacheable, layered system, uniform interface, client-server*), estilo **HATEOAS** y preparación para contenedores/microservicios (Semana 14).

#### Capacidades Implementadas por Fase:
1. **Setup & Configuración Centralizada (`config/settings.py`):**
   - Permisos globales en `REST_FRAMEWORK` (`IsAuthenticatedOrReadOnly`), autenticación dual (`SessionAuthentication` + `TokenAuthentication`), paginación estándar, filtros backend, límites de tasa y esquema `drf-spectacular`.
2. **Serialización Avanzada & HATEOAS (`servicios_api/serializers.py`):**
   - `HyperlinkedModelSerializer` con `HyperlinkedIdentityField`, `HyperlinkedRelatedField`, `ReadOnlyField`, `SerializerMethodField`, anidamiento controlado (`departamento_detalle`, `activo_detalle`) y enlaces hipervinculados `_links` (`self`, `collection`, `departamento`, `incidencias`, `cambiar_estado`).
   - Validación en serializador (SLA crítico máx. 12h, `endpoint_health` obligatorio para microservicios activos, sanitización XSS `html.escape()`), sin exposición de campos sensibles (`password`, `is_staff`, `is_superuser`).
3. **ViewSets, Routers & Acciones Custom (`servicios_api/views.py`, `urls.py`):**
   - `ModelViewSet` (`DepartamentoViewSet`, `ActivoTIViewSet`, `IncidenciaAPIViewSet`) y `ReadOnlyModelViewSet` (`BitacoraAccesoViewSet`) registrados en `DefaultRouter` bajo `/api/v1/`.
   - Endpoints personalizados con `@action(detail=True/False)`: `cambiar-estado`, `incidencias`, `resumen-metricas`, `throttle-probe`, `resolver`.
4. **Filtrado Lazy, Paginación & Throttling (`filters.py`, `pagination.py`, `throttles.py`):**
   - `DjangoFilterBackend`, `SearchFilter` y `OrderingFilter` sobre campos indexados (`db_index=True` y `Meta.indexes`).
   - `StandardResultsSetPagination` (`PageNumberPagination`, 5 por página) y `LimitOffsetAuditPagination` (`LimitOffsetPagination`).
   - Protección contra abuso con `AnonRateThrottle` (`60/min`), `UserRateThrottle` (`240/min`) y `BurstProbeThrottle` (`5/min` retornando `429 Too Many Requests`).
5. **CORS, CSRF, OpenAPI/Swagger & Microservices Readiness (Valor Agregado):**
   - `CorsMiddleware` restringido a orígenes explícitos (`CORS_ALLOWED_ORIGINS`, `CORS_ALLOW_CREDENTIALS = True`).
   - Protección CSRF obligatoria en sesión SPA/AJAX (`/api/v1/auth/csrf/`, cabecera `X-CSRFToken`).
   - Documentación OpenAPI 3.0 automatizada en `/api/docs/` (Swagger UI), `/api/redoc/` (ReDoc), `/api/schema/` y `schema.yml`.
   - Consola interactiva SPA/AJAX en `/` (`templates/servicios_api/consola_api.html`), colección exportada `postman_collection.json`, sonda `/api/v1/health/`, `Dockerfile` y `docker-compose.yml` listos para Semana 14.

---

### Credenciales y URLs Locales
* **Consola SPA & Explorador HATEOAS:** `http://127.0.0.1:8000/`
* **Swagger UI (OpenAPI 3.0):** `http://127.0.0.1:8000/api/docs/`
* **ReDoc:** `http://127.0.0.1:8000/api/redoc/`
* **DRF Browsable API Root:** `http://127.0.0.1:8000/api/v1/`
* **Health Check Microservicio:** `http://127.0.0.1:8000/api/v1/health/`
* **Django Admin:** `http://127.0.0.1:8000/admin/`
* **Credenciales:**
  - Superusuario: `admin` / `admin123`
  - Operador: `operador1` / `operador123`

---

### Pruebas Automatizadas y Validación
```bash
cd proyecto
.venv\Scripts\python.exe manage.py test servicios_api -v 2
.venv\Scripts\python.exe manage.py spectacular --validate --file schema.yml
```
**Resultado:** 11 de 11 pruebas unitarias/integración aprobadas (`OK`) y esquema OpenAPI 3.0 validado con 0 errores y 0 advertencias.

---

### Informe Académico y Evidencias
* **Informe Compilado (LaTeX UNCP FIS):** [INFORME_OSORIO_AGUILAR_13.pdf](informe/INFORME_OSORIO_AGUILAR_13.pdf)
* **Fuente LaTeX:** [INFORME_OSORIO_AGUILAR_13.tex](informe/INFORME_OSORIO_AGUILAR_13.tex)
* **Capturas y Evidencias:** Carpeta `assets/` y `informe/assets/`
* **Colección Postman:** `proyecto/postman_collection.json`
