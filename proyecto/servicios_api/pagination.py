"""Clases de paginación estándar para evitar sobrecarga de memoria en respuestas API."""
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Paginación por número de página con tamaño configurable de forma acotada."""

    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 50


class LimitOffsetAuditPagination(LimitOffsetPagination):
    """Paginación por desplazamiento (limit/offset) orientada a bitácoras extensas."""

    default_limit = 10
    max_limit = 100
