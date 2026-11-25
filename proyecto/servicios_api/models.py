"""Modelos relacionales indexados para la API RESTful de Servicios e Incidentes TI."""
import uuid
from django.db import models
from django.contrib.auth.models import User


class Departamento(models.Model):
    """Unidad organizacional o dominio funcional propietario de activos y servicios TI."""

    codigo = models.CharField(
        max_length=16,
        unique=True,
        db_index=True,
        verbose_name="Código de Unidad",
    )
    nombre = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="Nombre del Departamento",
    )
    sla_objetivo_horas = models.PositiveIntegerField(
        default=24,
        verbose_name="SLA Objetivo (Horas)",
    )
    responsable_area = models.CharField(
        max_length=100,
        verbose_name="Responsable de Área",
    )
    activo = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Unidad Activa",
    )
    created = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Fecha de Creación",
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización",
    )

    class Meta:
        verbose_name = "Departamento TI"
        verbose_name_plural = "Departamentos TI"
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['activo', 'nombre']),
        ]

    def __str__(self):
        return f"[{self.codigo}] {self.nombre}"


class ActivoTI(models.Model):
    """Recurso tecnológico, microservicio o componente de infraestructura monitoreado vía API."""

    TIPO_CHOICES = [
        ('MICROSERVICIO', 'Microservicio REST/gRPC'),
        ('BASE_DATOS', 'Motor de Base de Datos'),
        ('SERVIDOR', 'Servidor / Nodo Compute'),
        ('GATEWAY', 'API Gateway / Proxy'),
        ('APLICACION', 'Aplicación Web Institucional'),
    ]

    STATUS_CHOICES = [
        ('activo', 'Activo'),
        ('mantenimiento', 'En Mantenimiento'),
        ('degradado', 'Degradado'),
        ('inactivo', 'Inactivo'),
    ]

    CRITICIDAD_CHOICES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica'),
    ]

    codigo_activo = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Código de Activo",
    )
    nombre = models.CharField(
        max_length=140,
        db_index=True,
        verbose_name="Nombre del Activo / Servicio",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='MICROSERVICIO',
        db_index=True,
        verbose_name="Tipo de Recurso",
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='activo',
        db_index=True,
        verbose_name="Estado Operativo",
    )
    criticidad = models.CharField(
        max_length=10,
        choices=CRITICIDAD_CHOICES,
        default='MEDIA',
        db_index=True,
        verbose_name="Nivel de Criticidad",
    )
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.PROTECT,
        related_name='activos',
        verbose_name="Departamento Propietario",
    )
    sla_horas = models.PositiveIntegerField(
        default=12,
        verbose_name="SLA Comprometido (Horas)",
    )
    costo_mensual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Costo Operativo Mensual (S/.)",
    )
    endpoint_health = models.URLField(
        max_length=255,
        blank=True,
        verbose_name="URL de Health Check",
    )
    responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activos_asignados',
        verbose_name="Ingeniero Responsable",
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción Técnica",
    )
    created = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Fecha de Registro",
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización",
    )

    class Meta:
        verbose_name = "Activo TI"
        verbose_name_plural = "Activos TI"
        ordering = ['-created']
        indexes = [
            models.Index(fields=['status', '-created']),
            models.Index(fields=['departamento', 'criticidad']),
            models.Index(fields=['tipo', 'status']),
        ]

    def save(self, *args, **kwargs):
        if not self.codigo_activo:
            self.codigo_activo = f"SRV-2026-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def calcular_nivel_riesgo(self):
        """Evalúa el riesgo operativo combinando criticidad y umbral de SLA."""
        pesos = {'BAJA': 1, 'MEDIA': 2, 'ALTA': 3, 'CRITICA': 4}
        score = pesos.get(self.criticidad, 1)
        if self.status in ('degradado', 'inactivo'):
            score += 1
        if score >= 4:
            return "Severo"
        if score == 3:
            return "Alto"
        if score == 2:
            return "Moderado"
        return "Controlado"

    def __str__(self):
        return f"[{self.codigo_activo}] {self.nombre} ({self.status})"


class IncidenciaAPI(models.Model):
    """Ticket de contingencia vinculado a un Activo TI y expuesto vía endpoints RESTful."""

    STATUS_CHOICES = [
        ('activo', 'Activo / Abierto'),
        ('en_progreso', 'En Progreso'),
        ('resuelto', 'Resuelto'),
        ('cerrado', 'Cerrado'),
    ]

    PRIORIDAD_CHOICES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica'),
    ]

    codigo_ticket = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Código de Ticket",
    )
    activo = models.ForeignKey(
        ActivoTI,
        on_delete=models.CASCADE,
        related_name='incidencias',
        verbose_name="Activo TI Afectado",
    )
    titulo = models.CharField(
        max_length=150,
        db_index=True,
        verbose_name="Título de la Incidencia",
    )
    descripcion = models.TextField(
        verbose_name="Descripción Técnica",
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='activo',
        db_index=True,
        verbose_name="Estado del Ticket",
    )
    prioridad = models.CharField(
        max_length=10,
        choices=PRIORIDAD_CHOICES,
        default='MEDIA',
        db_index=True,
        verbose_name="Prioridad",
    )
    horas_estimadas = models.PositiveIntegerField(
        default=4,
        verbose_name="Horas Estimadas de Resolución",
    )
    correo_contacto = models.EmailField(
        verbose_name="Correo de Notificación",
    )
    reportado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidencias_reportadas_api',
        verbose_name="Usuario Registrador",
    )
    created = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Fecha de Apertura",
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización",
    )

    class Meta:
        verbose_name = "Incidencia API"
        verbose_name_plural = "Incidencias API"
        ordering = ['-created']
        indexes = [
            models.Index(fields=['status', '-created']),
            models.Index(fields=['prioridad', 'status']),
        ]

    def save(self, *args, **kwargs):
        if not self.codigo_ticket:
            self.codigo_ticket = f"TKT-2026-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.codigo_ticket}] {self.titulo} ({self.prioridad})"


class BitacoraAccesoAPI(models.Model):
    """Registro inmutable de trazabilidad y latencia de peticiones hacia la API REST."""

    metodo = models.CharField(max_length=10, db_index=True, verbose_name="Método HTTP")
    ruta = models.CharField(max_length=255, db_index=True, verbose_name="Endpoint")
    usuario = models.CharField(max_length=150, default='Anonimo', verbose_name="Identidad")
    ip_origen = models.GenericIPAddressField(verbose_name="IP Cliente")
    codigo_estado = models.IntegerField(db_index=True, verbose_name="Status Code")
    latencia_ms = models.FloatField(verbose_name="Latencia (ms)")
    origen_cors = models.CharField(max_length=150, blank=True, verbose_name="Origin Header")
    created = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Timestamp")

    class Meta:
        verbose_name = "Bitácora de Acceso API"
        verbose_name_plural = "Bitácoras de Acceso API"
        ordering = ['-created']
        indexes = [
            models.Index(fields=['codigo_estado', '-created']),
        ]

    def __str__(self):
        return f"{self.metodo} {self.ruta} [{self.codigo_estado}] ({self.latencia_ms:.2f}ms)"
