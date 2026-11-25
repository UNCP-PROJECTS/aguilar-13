"""Middleware de telemetría de API RESTful: calcula latencia e inyecta cabeceras técnicas."""
import time
from .models import BitacoraAccesoAPI


class ApiTelemetryMiddleware:
    """Registra tiempos de respuesta y trazas para rutas /api/ sin interferir en CORS."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        inicio = time.perf_counter()
        response = self.get_response(request)
        duracion_ms = (time.perf_counter() - inicio) * 1000.0

        response['X-Response-Time-Ms'] = f"{duracion_ms:.2f}"
        response['X-API-Version'] = "v1"
        response['X-Service-Mode'] = "microservice-ready"

        if request.path.startswith('/api/') and not request.path.startswith('/api/schema/'):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            ip_cliente = (
                x_forwarded_for.split(',')[0].strip()
                if x_forwarded_for
                else request.META.get('REMOTE_ADDR', '127.0.0.1')
            )
            usuario = request.user.username if getattr(request, 'user', None) and request.user.is_authenticated else 'Anonimo'
            origen = request.META.get('HTTP_ORIGIN', '')[:148]

            try:
                BitacoraAccesoAPI.objects.create(
                    metodo=request.method[:10],
                    ruta=request.path[:254],
                    usuario=usuario[:148],
                    ip_origen=ip_cliente,
                    codigo_estado=response.status_code,
                    latencia_ms=round(duracion_ms, 2),
                    origen_cors=origen,
                )
            except Exception:
                # Evita interrumpir el flujo HTTP si las migraciones aún no han corrido
                pass

        return response
