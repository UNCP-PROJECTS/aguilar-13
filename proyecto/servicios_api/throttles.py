"""Clases de limitación de tasa (Throttling) para protección contra abuso y scraping."""
from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle, UserRateThrottle


class BurstProbeThrottle(SimpleRateThrottle):
    """Límite estricto (5/min) por IP o usuario para endpoints sensibles y prueba 429."""

    scope = 'burst_probe'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class StrictAnonThrottle(AnonRateThrottle):
    """Límite dedicado para clientes no autenticados."""

    scope = 'anon'


class StandardUserThrottle(UserRateThrottle):
    """Límite ampliado para usuarios autenticados con sesión o token."""

    scope = 'user'
