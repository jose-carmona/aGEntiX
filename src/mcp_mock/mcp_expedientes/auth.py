"""
Re-exportación del módulo auth compartido.

Este archivo mantiene compatibilidad con imports existentes.
La implementación real está en src/mcp_mock/auth.py
"""

# Re-exportar todo desde el módulo compartido
from ..auth import (
    AuthError,
    validate_audience,
    get_jwt_secret,
    validate_jwt,
    extract_exp_id_from_uri,
    get_required_permission,
    require_permission,
    can_read,
    can_write,
)

__all__ = [
    "AuthError",
    "validate_audience",
    "get_jwt_secret",
    "validate_jwt",
    "extract_exp_id_from_uri",
    "get_required_permission",
    "require_permission",
    "can_read",
    "can_write",
]
