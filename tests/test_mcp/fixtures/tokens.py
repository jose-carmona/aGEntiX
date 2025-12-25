"""
Fixtures de tokens JWT para testing.

Proporciona funciones para generar diferentes tipos de tokens
para probar distintos escenarios de autenticación y autorización.

IMPORTANTE: Para tokens VÁLIDOS, usar backoffice.auth.jwt_generator.
Para tokens INVÁLIDOS (expirados, firma incorrecta), generar directamente
con jwt ya que el generador centralizado no permite crear tokens inválidos.
"""

import jwt
import uuid
from datetime import datetime, timedelta

# Usar el generador centralizado para tokens válidos
from backoffice.auth.jwt_generator import generate_jwt


def token_consulta(exp_id: str = "EXP-2024-001") -> str:
    """Token válido con solo permisos de consulta"""
    result = generate_jwt(
        expediente_id=exp_id,
        expediente_tipo="SUBVENCIONES",
        tarea_id="TAREA-TEST-001",
        tarea_nombre="TEST_CONSULTA",
        permisos=["consulta"]
    )
    return result.token


def token_gestion(exp_id: str = "EXP-2024-001") -> str:
    """Token válido con permisos de consulta y gestión"""
    result = generate_jwt(
        expediente_id=exp_id,
        expediente_tipo="SUBVENCIONES",
        tarea_id="TAREA-TEST-002",
        tarea_nombre="TEST_GESTION",
        permisos=["consulta", "gestion"]
    )
    return result.token


def token_expirado(exp_id: str = "EXP-2024-001") -> str:
    """
    Token expirado (exp en el pasado).

    NOTA: Generado directamente con jwt porque el generador centralizado
    no permite crear tokens inválidos (esto es correcto por seguridad).
    """
    from backoffice.settings import settings

    now = datetime.utcnow()
    payload = {
        "sub": "Automático",
        "iat": int((now - timedelta(hours=2)).timestamp()),  # Emitido hace 2 horas
        "exp": int((now - timedelta(hours=1)).timestamp()),  # Expiró hace 1 hora
        "nbf": int((now - timedelta(hours=2)).timestamp()),
        "iss": "agentix-bpmn",
        "aud": "agentix-mcp-expedientes",
        "jti": str(uuid.uuid4()),
        "exp_id": exp_id,
        "exp_tipo": "SUBVENCIONES",
        "tarea_id": "TAREA-TEST-003",
        "tarea_nombre": "TEST_EXPIRADO",
        "permisos": ["consulta"]
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def token_firma_invalida(exp_id: str = "EXP-2024-001") -> str:
    """
    Token con firma inválida (firmado con clave incorrecta).

    NOTA: Generado directamente con jwt con una clave diferente
    para probar que la validación rechaza firmas inválidas.
    """
    now = datetime.utcnow()
    payload = {
        "sub": "Automático",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "nbf": int(now.timestamp()),
        "iss": "agentix-bpmn",
        "aud": "agentix-mcp-expedientes",
        "jti": str(uuid.uuid4()),
        "exp_id": exp_id,
        "exp_tipo": "SUBVENCIONES",
        "tarea_id": "TAREA-TEST-004",
        "tarea_nombre": "TEST_FIRMA_INVALIDA",
        "permisos": ["consulta"]
    }
    # Firmado con clave INCORRECTA (diferente a JWT_SECRET)
    return jwt.encode(payload, "clave-incorrecta-para-testing", algorithm="HS256")


def token_otro_expediente(exp_id: str = "EXP-2024-999") -> str:
    """Token válido pero para otro expediente"""
    result = generate_jwt(
        expediente_id=exp_id,
        expediente_tipo="OTRO_TIPO",
        tarea_id="TAREA-TEST-005",
        tarea_nombre="TEST_OTRO_EXP",
        permisos=["consulta", "gestion"]
    )
    return result.token


def token_usuario_invalido(exp_id: str = "EXP-2024-001") -> str:
    """
    Token con usuario no válido (sub != "Automático").

    NOTA: Generado directamente porque el generador centralizado
    siempre usa sub="Automático" (correcto por seguridad).
    """
    from backoffice.settings import settings

    now = datetime.utcnow()
    payload = {
        "sub": "Usuario Humano",  # NO válido - debe ser "Automático"
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "nbf": int(now.timestamp()),
        "iss": "agentix-bpmn",
        "aud": "agentix-mcp-expedientes",
        "jti": str(uuid.uuid4()),
        "exp_id": exp_id,
        "exp_tipo": "SUBVENCIONES",
        "tarea_id": "TAREA-TEST-006",
        "tarea_nombre": "TEST_USUARIO_INVALIDO",
        "permisos": ["consulta"]
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def token_multi_mcp(exp_id: str = "EXP-2024-001") -> str:
    """Token válido para múltiples MCP servers"""
    result = generate_jwt(
        expediente_id=exp_id,
        expediente_tipo="SUBVENCIONES",
        tarea_id="TAREA-TEST-007",
        tarea_nombre="TEST_MULTI_MCP",
        permisos=["consulta", "gestion"],
        audiences=[
            "agentix-mcp-expedientes",
            "agentix-mcp-normativa",
            "agentix-mcp-documentos"
        ]
    )
    return result.token


def token_audiencia_incorrecta(exp_id: str = "EXP-2024-001") -> str:
    """
    Token con audiencia incorrecta (no incluye agentix-mcp-expedientes).
    """
    result = generate_jwt(
        expediente_id=exp_id,
        expediente_tipo="SUBVENCIONES",
        tarea_id="TAREA-TEST-008",
        tarea_nombre="TEST_AUD_INCORRECTA",
        permisos=["consulta"],
        audiences=["agentix-mcp-normativa"]  # No incluye expedientes
    )
    return result.token
