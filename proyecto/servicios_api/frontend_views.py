"""Vista web ligera para servir la consola SPA/AJAX cliente de la API RESTful."""
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import ActivoTI, Departamento, IncidenciaAPI


@ensure_csrf_cookie
def consola_api_view(request):
    """Renderiza el cliente SPA institucional que consume /api/v1/ vía AJAX con X-CSRFToken."""
    contexto = {
        'total_departamentos': Departamento.objects.count(),
        'total_activos': ActivoTI.objects.count(),
        'activos_operativos': ActivoTI.objects.filter(status='activo').count(),
        'incidencias_activas': IncidenciaAPI.objects.filter(status__in=['activo', 'en_progreso']).count(),
    }
    return render(request, 'servicios_api/consola_api.html', contexto)
