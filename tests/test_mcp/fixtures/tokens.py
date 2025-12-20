"""
Fixtures de tokens JWT para testing.

Proporciona funciones para generar diferentes tipos de tokens
para probar distintos escenarios de autenticación y autorización.
"""

from datetime import datetime, timedelta

# ELIMINADO: sys.path manipulation - ya configurado en conftest.py global
# Los imports funcionan correctamente porque src/ está en sys.path

from mcp_mock.mcp_expedientes.generate_token import generate_test_token


def token_consulta(exp_id: str = "EXP-2024-001") -> str:
    """Token válido con solo permisos de consulta"""
    return generate_test_token(
        exp_id=exp_id,
        exp_tipo="SUBVENCIONES",
        tarea_id="TAREA-TEST-001",
        tarea_nombre="TEST_CONSULTA",
        permisos=["consulta"]
    )


def token_gestion(exp_id: str = "EXP-2024-001") -> str:
    """Token válido con permisos de consulta y gestión"""
    return generate_test_token(
        exp_id=exp_id,
        exp_tipo="SUBVENCIONES",
        tarea_id="TAREA-TEST-002",
        tarea_nombre="TEST_GESTION",
        permisos=["consulta", "gestion"]
    )


def token_expirado(exp_id: str = "EXP-2024-001") -> str:
    """Token expirado (exp en el pasado)"""
    return generate_test_token(
        exp_id=exp_id,
        exp_tipo="SUBVENCIONES",
        tarea_id="TAREA-TEST-003",
        tarea_nombre="TEST_EXPIRADO",
        permisos=["consulta"],
        exp_hours=-1  # Expirado hace 1 hora
    )


def token_firma_invalida(exp_id: str = "EXP-2024-001") -> str:
    """Token con firma inválida (firmado con clave incorrecta)"""
    return generate_test_token(
        exp_id=exp_id,
        exp_tipo="SUBVENCIONES",
        tarea_id="TAREA-TEST-004",
        tarea_nombre="TEST_FIRMA_INVALIDA",
        permisos=["consulta"],
        secret="clave-incorrecta"  # Firmado con clave diferente
    )


def token_otro_expediente(exp_id: str = "EXP-2024-999") -> str:
    """Token válido pero para otro expediente"""
    return generate_test_token(
        exp_id=exp_id,
        exp_tipo="OTRO_TIPO",
        tarea_id="TAREA-TEST-005",
        tarea_nombre="TEST_OTRO_EXP",
        permisos=["consulta", "gestion"]
    )


def token_usuario_invalido(exp_id: str = "EXP-2024-001") -> str:
    """
    Token con usuario no válido (sub != "Automático").

    Nota: Esta función requiere modificar directamente el payload
    ya que generate_test_token siempre pone sub="Automático"
    """
    import jwt
    import uuid
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    payload = {
        "sub": "Usuario Humano",  # NO válido
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "nbf": int(now.timestamp()),
        "iss": "agentix-bpmn",
        "aud": ["agentix-mcp-expedientes"],
        "jti": str(uuid.uuid4()),
        "exp_id": exp_id,
        "exp_tipo": "SUBVENCIONES",
        "tarea_id": "TAREA-TEST-006",
        "tarea_nombre": "TEST_USUARIO_INVALIDO",
        "permisos": ["consulta"]
    }
    return jwt.encode(payload, "test-secret-key", algorithm="HS256")


def token_multi_mcp(exp_id: str = "EXP-2024-001") -> str:
    """Token válido para múltiples MCP servers"""
    return generate_test_token(
        exp_id=exp_id,
        exp_tipo="SUBVENCIONES",
        tarea_id="TAREA-TEST-007",
        tarea_nombre="TEST_MULTI_MCP",
        permisos=["consulta", "gestion"],
        mcp_servers=[
            "agentix-mcp-expedientes",
            "agentix-mcp-normativa",
            "agentix-mcp-documentos"
        ]
    )


def token_audiencia_incorrecta(exp_id: str = "EXP-2024-001") -> str:
    """
    Token con audiencia incorrecta (no incluye agentix-mcp-expedientes).
    """
    return generate_test_token(
        exp_id=exp_id,
        exp_tipo="SUBVENCIONES",
        tarea_id="TAREA-TEST-008",
        tarea_nombre="TEST_AUD_INCORRECTA",
        permisos=["consulta"],
        mcp_servers=["agentix-mcp-normativa"]  # No incluye expedientes
    )
