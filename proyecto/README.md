# TechGrid RESTful API Gateway (`/proyecto`)
## UNCP FIS - Desarrollo de Aplicaciones Web (Semana 13)

### Instalación y Ejecución Local
```powershell
cd C:\Users\USUARIO\Documents\!UNCP-DESARROLLO\aguilar-13\proyecto
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe poblar_datos.py
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

### Rutas de la API RESTful (`/api/v1/`)
| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `GET, POST` | `/api/v1/activos/` | Listado paginado, filtrado (`?status=activo&page=2&ordering=-created`), búsqueda y creación de Activos TI con HATEOAS `_links` |
| `GET, PUT, PATCH, DELETE` | `/api/v1/activos/{id}/` | Operación individual sobre recurso Activo TI |
| `POST` | `/api/v1/activos/{id}/cambiar-estado/` | `@action(detail=True)` para transición controlada de estado |
| `GET` | `/api/v1/activos/{id}/incidencias/` | `@action(detail=True)` colección hija HATEOAS |
| `GET` | `/api/v1/activos/resumen-metricas/` | `@action(detail=False)` métricas agregadas SQL (`COUNT`/`AVG`) |
| `GET` | `/api/v1/activos/throttle-probe/` | `@action(detail=False)` con `BurstProbeThrottle` (`5/min -> HTTP 429`) |
| `GET, POST` | `/api/v1/departamentos/` | CRUD de Departamentos TI |
| `GET, POST` | `/api/v1/incidencias/` | CRUD de Incidencias con validación anidada |
| `POST` | `/api/v1/incidencias/{id}/resolver/` | `@action(detail=True)` cierre operativo |
| `GET` | `/api/v1/bitacora/` | `ReadOnlyModelViewSet` autenticado con `LimitOffsetPagination` |
| `GET` | `/api/v1/auth/csrf/` | Emite cookie `csrftoken` y token JSON para SPA/AJAX |
| `POST` | `/api/v1/auth/login/` | Login de sesión SPA con validación obligatoria `X-CSRFToken` |
| `POST` | `/api/v1/auth/token/` | Emisión de Token DRF stateless (`Authorization: Token <key>`) |
| `GET` | `/api/v1/auth/me/` | Perfil seguro sin exponer `password` ni `is_staff` |
| `GET` | `/api/v1/health/` | Sonda de disponibilidad y latencia BD (Semana 14 Microservicios) |
| `GET` | `/api/docs/` | Swagger UI interactivo (OpenAPI 3.0) |
| `GET` | `/api/redoc/` | Documentación ReDoc |
| `GET` | `/api/schema/` | Esquema OpenAPI 3.0 (`schema.yml`) |

### Colección Postman y Contenedores (Semana 14)
- Importar `postman_collection.json` en Postman o Thunder Client.
- Despliegue contenedorizado listo con `Dockerfile` y `docker-compose.yml`.
