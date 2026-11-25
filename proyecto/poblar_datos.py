"""Script idempotente de poblado inicial para TechGrid RESTful API (UNCP FIS)."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from servicios_api.models import ActivoTI, BitacoraAccesoAPI, Departamento, IncidenciaAPI


def poblar():
    print("[*] Iniciando poblado de datos para TechGrid RESTful API...")

    # 1. Usuarios y Tokens DRF
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@uncp.edu.pe',
            'first_name': 'José',
            'last_name': 'Osorio Mallqui',
            'is_staff': True,
            'is_superuser': True,
        },
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
    admin_token, _ = Token.objects.get_or_create(user=admin_user)

    operador_user, created = User.objects.get_or_create(
        username='operador1',
        defaults={
            'email': 'operador1@uncp.edu.pe',
            'first_name': 'Operador',
            'last_name': 'Sistemas FIS',
            'is_staff': False,
        },
    )
    if created:
        operador_user.set_password('operador123')
        operador_user.save()
    operador_token, _ = Token.objects.get_or_create(user=operador_user)

    auditor_user, created = User.objects.get_or_create(
        username='auditor_api',
        defaults={
            'email': 'auditoria@uncp.edu.pe',
            'first_name': 'Auditor',
            'last_name': 'REST API',
            'is_staff': False,
        },
    )
    if created:
        auditor_user.set_password('auditor123')
        auditor_user.save()
    Token.objects.get_or_create(user=auditor_user)

    print(f"  [+] Usuarios listos: admin (token {admin_token.key[:8]}...), operador1 (token {operador_token.key[:8]}...), auditor_api")

    # 2. Departamentos TI
    departamentos_data = [
        {
            'codigo': 'DEV-MICRO',
            'nombre': 'Arquitectura de Microservicios y APIs',
            'sla_objetivo_horas': 4,
            'responsable_area': 'Ing. José Osorio Mallqui',
            'activo': True,
        },
        {
            'codigo': 'SEG-SOC',
            'nombre': 'Centro de Operaciones de Ciberseguridad (SOC)',
            'sla_objetivo_horas': 6,
            'responsable_area': 'Ing. Miguel Aguilar',
            'activo': True,
        },
        {
            'codigo': 'DBA-CLOUD',
            'nombre': 'Ingeniería de Datos y Persistencia Cloud',
            'sla_objetivo_horas': 8,
            'responsable_area': 'Ing. Carlos Huamán',
            'activo': True,
        },
        {
            'codigo': 'INF-CORE',
            'nombre': 'Infraestructura Troncal y Redes Campus',
            'sla_objetivo_horas': 12,
            'responsable_area': 'Ing. Lucía Quispe',
            'activo': True,
        },
    ]

    deps = {}
    for d in departamentos_data:
        obj, _ = Departamento.objects.get_or_create(codigo=d['codigo'], defaults=d)
        deps[d['codigo']] = obj
    print(f"  [+] Departamentos verificados: {Departamento.objects.count()}")

    # 3. Activos TI (12 registros: 8 activos, 2 mantenimiento, 1 degradado, 1 inactivo -> paginación ?status=activo&page=2)
    activos_data = [
        ('Gateway Autenticación OAuth2 / JWT', 'GATEWAY', 'activo', 'CRITICA', 'DEV-MICRO', 4, 420.00, 'https://api.uncp.edu.pe/auth/health', admin_user),
        ('Microservicio Matrícula Académica v2', 'MICROSERVICIO', 'activo', 'CRITICA', 'DEV-MICRO', 6, 580.00, 'https://api.uncp.edu.pe/matricula/health', admin_user),
        ('Microservicio Pagos y Tesorería', 'MICROSERVICIO', 'activo', 'CRITICA', 'DEV-MICRO', 4, 650.00, 'https://api.uncp.edu.pe/pagos/health', admin_user),
        ('Clúster PostgreSQL Académico Primario', 'BASE_DATOS', 'activo', 'CRITICA', 'DBA-CLOUD', 4, 890.00, 'https://db.uncp.edu.pe/primary/health', admin_user),
        ('Microservicio Notificaciones Push & Email', 'MICROSERVICIO', 'activo', 'ALTA', 'DEV-MICRO', 8, 240.00, 'https://api.uncp.edu.pe/notify/health', operador_user),
        ('WAF Perimetral & Filtro Anti-DDoS', 'SERVIDOR', 'activo', 'CRITICA', 'SEG-SOC', 2, 740.00, 'https://sec.uncp.edu.pe/waf/health', admin_user),
        ('Portal Web Institucional FIS UNCP', 'APLICACION', 'activo', 'ALTA', 'INF-CORE', 12, 310.00, 'https://fis.uncp.edu.pe/health', operador_user),
        ('Microservicio Auditoría y Trazas SIEM', 'MICROSERVICIO', 'activo', 'ALTA', 'SEG-SOC', 6, 490.00, 'https://sec.uncp.edu.pe/siem/health', auditor_user),
        ('Caché Redis Distribuido Sesiones', 'BASE_DATOS', 'mantenimiento', 'ALTA', 'DBA-CLOUD', 8, 210.00, 'https://cache.uncp.edu.pe/health', operador_user),
        ('Balanceador HAProxy Pabellón C', 'SERVIDOR', 'degradado', 'CRITICA', 'INF-CORE', 4, 360.00, 'https://lb.uncp.edu.pe/health', admin_user),
        ('Microservicio Reportería BI Legacy', 'MICROSERVICIO', 'mantenimiento', 'MEDIA', 'DBA-CLOUD', 24, 180.00, 'https://bi.uncp.edu.pe/health', operador_user),
        ('Servidor Monolítico FTP Histórico', 'SERVIDOR', 'inactivo', 'BAJA', 'INF-CORE', 72, 95.00, '', operador_user),
    ]

    activos_objs = []
    for nombre, tipo, st, crit, dep_cod, sla, costo, health, resp in activos_data:
        obj, _ = ActivoTI.objects.get_or_create(
            nombre=nombre,
            defaults={
                'tipo': tipo,
                'status': st,
                'criticidad': crit,
                'departamento': deps[dep_cod],
                'sla_horas': sla,
                'costo_mensual': costo,
                'endpoint_health': health,
                'responsable': resp,
                'descripcion': f"Componente productivo {tipo} administrado por {dep_cod} con SLA de {sla}h.",
            },
        )
        activos_objs.append(obj)
    print(f"  [+] Activos TI verificados: {ActivoTI.objects.count()} (activos={ActivoTI.objects.filter(status='activo').count()})")

    # 4. Incidencias API
    incidencias_data = [
        (activos_objs[9], 'Pérdida intermitente de health-check en HAProxy nodo 2', 'Se detectan timeouts >1500ms en el pool backend durante picos de matrícula.', 'activo', 'CRITICA', 4, 'infra@uncp.edu.pe'),
        (activos_objs[0], 'Incremento de latencia en validación de tokens JWT', 'El endpoint de introspección supera los 180ms bajo carga concurrente.', 'en_progreso', 'ALTA', 8, 'auth@uncp.edu.pe'),
        (activos_objs[3], 'Saturación temporal de conexiones en pool PgBouncer', 'Pico de conexiones inactivas desde microservicio de reportes.', 'activo', 'CRITICA', 6, 'dba@uncp.edu.pe'),
        (activos_objs[5], 'Ajuste de reglas Rate-Limit para tráfico móvil externo', 'Falsos positivos en subredes móviles de estudiantes durante inscripción.', 'resuelto', 'ALTA', 5, 'soc@uncp.edu.pe'),
        (activos_objs[1], 'Error 502 ocasional al consultar constancias PDF', 'Timeout en worker secundario durante generación síncrona de constancias.', 'activo', 'ALTA', 10, 'matricula@uncp.edu.pe'),
        (activos_objs[4], 'Cola de correos SMTP con reintentos diferidos', 'Retraso de 3 minutos en despacho de notificaciones de recuperación.', 'en_progreso', 'MEDIA', 16, 'notify@uncp.edu.pe'),
        (activos_objs[7], 'Rotación programada de índices semanales en SIEM', 'Optimización de particiones para consultas REST de bitácora.', 'resuelto', 'MEDIA', 12, 'siem@uncp.edu.pe'),
        (activos_objs[6], 'Actualización de certificados TLS Let’s Encrypt', 'Renovación automatizada verificada en entorno staging y producción.', 'cerrado', 'BAJA', 4, 'webmaster@uncp.edu.pe'),
    ]

    for activo, titulo, desc, st, prio, horas, correo in incidencias_data:
        IncidenciaAPI.objects.get_or_create(
            titulo=titulo,
            defaults={
                'activo': activo,
                'descripcion': desc,
                'status': st,
                'prioridad': prio,
                'horas_estimadas': horas,
                'correo_contacto': correo,
                'reportado_por': admin_user,
            },
        )
    print(f"  [+] Incidencias API verificadas: {IncidenciaAPI.objects.count()}")

    # 5. Bitácora base si está vacía
    if BitacoraAccesoAPI.objects.count() == 0:
        BitacoraAccesoAPI.objects.bulk_create([
            BitacoraAccesoAPI(metodo='GET', ruta='/api/v1/activos/?status=activo&page=1', usuario='admin', ip_origen='127.0.0.1', codigo_estado=200, latencia_ms=11.42, origen_cors='http://localhost:5173'),
            BitacoraAccesoAPI(metodo='OPTIONS', ruta='/api/v1/activos/', usuario='Anonimo', ip_origen='127.0.0.1', codigo_estado=200, latencia_ms=2.15, origen_cors='http://localhost:3000'),
            BitacoraAccesoAPI(metodo='POST', ruta='/api/v1/incidencias/', usuario='operador1', ip_origen='127.0.0.1', codigo_estado=201, latencia_ms=18.70, origen_cors='http://127.0.0.1:8000'),
            BitacoraAccesoAPI(metodo='GET', ruta='/api/v1/activos/throttle-probe/', usuario='Anonimo', ip_origen='127.0.0.1', codigo_estado=429, latencia_ms=1.84, origen_cors=''),
        ])
    print("[OK] Base de datos poblada exitosamente.")


if __name__ == '__main__':
    poblar()
