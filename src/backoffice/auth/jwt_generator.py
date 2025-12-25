# backoffice/auth/jwt_generator.py

"""
Generador centralizado de tokens JWT para aGEntiX.

Este módulo es el ÚNICO punto de generación de tokens JWT del sistema.
Debe usarse por:
- API endpoint /api/v1/auth/generate-jwt
- Scripts de testing (test-agent.sh)
- Tests unitarios

Para validación de tokens, usar jwt_validator.py del mismo paquete.
"""

import jwt
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class JWTGeneratorConfig(BaseModel):
    """Configuración para generación de JWT"""
    secret: str
    algorithm: str = "HS256"
    issuer: str = "agentix-bpmn"
    subject: str = "Automático"
    default_audience: str = "agentix-mcp-expedientes"
    default_expiration_hours: int = 1


class GeneratedJWT(BaseModel):
    """Resultado de generación de JWT"""
    token: str
    claims: Dict[str, Any]


def get_generator_config() -> JWTGeneratorConfig:
    """
    Obtiene la configuración del generador desde settings.

    Returns:
        JWTGeneratorConfig con valores de settings
    """
    from backoffice.settings import settings

    return JWTGeneratorConfig(
        secret=settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
        issuer=settings.JWT_EXPECTED_ISSUER,
        subject=settings.JWT_EXPECTED_SUBJECT,
        default_audience=settings.JWT_REQUIRED_AUDIENCE
    )


def generate_jwt(
    expediente_id: str,
    tarea_id: str = "TAREA-TEST-001",
    permisos: Optional[List[str]] = None,
    expediente_tipo: str = "SUBVENCIONES",
    tarea_nombre: str = "TAREA_TEST",
    audiences: Optional[List[str]] = None,
    expiration_hours: int = 1,
    config: Optional[JWTGeneratorConfig] = None
) -> GeneratedJWT:
    """
    Genera un token JWT válido para ejecución de agentes.

    Este es el punto centralizado de generación de JWT. Usa la configuración
    de settings para garantizar consistencia con la validación.

    Args:
        expediente_id: ID del expediente (ej: "EXP-2024-001")
        tarea_id: ID de la tarea BPMN
        permisos: Lista de permisos (default: ["consulta"])
        expediente_tipo: Tipo de expediente (default: "SUBVENCIONES")
        tarea_nombre: Nombre de la tarea BPMN
        audiences: Lista de audiencias/MCP servers autorizados
        expiration_hours: Horas hasta expiración (default: 1, max: 24)
        config: Configuración opcional (si None, usa settings)

    Returns:
        GeneratedJWT con token firmado y claims

    Example:
        >>> from backoffice.auth.jwt_generator import generate_jwt
        >>> result = generate_jwt(
        ...     expediente_id="EXP-2024-001",
        ...     permisos=["consulta", "gestion"]
        ... )
        >>> print(result.token)
        eyJhbGciOiJIUzI1NiIs...
    """
    # Obtener configuración
    if config is None:
        config = get_generator_config()

    # Defaults
    if permisos is None:
        permisos = ["consulta"]

    if audiences is None:
        audiences = [config.default_audience]

    # Limitar expiración a 24 horas máximo
    expiration_hours = min(max(1, expiration_hours), 24)

    # Timestamps
    now = datetime.utcnow()
    iat = int(now.timestamp())
    exp = int((now + timedelta(hours=expiration_hours)).timestamp())
    nbf = int(now.timestamp())

    # Construir payload
    payload = {
        "sub": config.subject,
        "iat": iat,
        "exp": exp,
        "nbf": nbf,
        "iss": config.issuer,
        "aud": audiences[0] if len(audiences) == 1 else audiences,
        "jti": str(uuid.uuid4()),
        "exp_id": expediente_id,
        "exp_tipo": expediente_tipo,
        "tarea_id": tarea_id,
        "tarea_nombre": tarea_nombre,
        "permisos": permisos
    }

    # Firmar token
    token = jwt.encode(payload, config.secret, algorithm=config.algorithm)

    return GeneratedJWT(token=token, claims=payload)


def decode_jwt_unsafe(
    token: str,
    config: Optional[JWTGeneratorConfig] = None
) -> Dict[str, Any]:
    """
    Decodifica un JWT sin validar (solo para inspección/debug).

    ADVERTENCIA: No usar para validación de seguridad.
    Para validación, usar jwt_validator.validate_jwt()

    Args:
        token: Token JWT a decodificar
        config: Configuración opcional

    Returns:
        Payload decodificado
    """
    if config is None:
        config = get_generator_config()

    return jwt.decode(
        token,
        config.secret,
        algorithms=[config.algorithm],
        options={
            "verify_exp": False,
            "verify_aud": False
        }
    )


def format_jwt_info(token: str, config: Optional[JWTGeneratorConfig] = None) -> str:
    """
    Formatea información de un JWT para visualización.

    Args:
        token: Token JWT
        config: Configuración opcional

    Returns:
        String formateado con información del token
    """
    payload = decode_jwt_unsafe(token, config)

    lines = [
        "=" * 60,
        "TOKEN JWT",
        "=" * 60,
        "",
        "Claims estándar:",
        f"  Subject (sub):        {payload.get('sub')}",
        f"  Emisor (iss):         {payload.get('iss')}",
        f"  Audiencia (aud):      {payload.get('aud')}",
        f"  Token ID (jti):       {payload.get('jti')}",
        "",
        "Claims de Expediente:",
        f"  Expediente ID:        {payload.get('exp_id')}",
        f"  Tipo:                 {payload.get('exp_tipo')}",
        "",
        "Claims de Tarea BPMN:",
        f"  Tarea ID:             {payload.get('tarea_id')}",
        f"  Tarea Nombre:         {payload.get('tarea_nombre')}",
        "",
        "Permisos:",
        f"  {', '.join(payload.get('permisos', []))}",
        "",
        "Timestamps:",
        f"  Emitido (iat):        {datetime.fromtimestamp(payload.get('iat')).isoformat()}",
        f"  Válido desde (nbf):   {datetime.fromtimestamp(payload.get('nbf')).isoformat()}",
        f"  Expira (exp):         {datetime.fromtimestamp(payload.get('exp')).isoformat()}",
        "",
        "Token:",
        f"  {token[:80]}..." if len(token) > 80 else f"  {token}",
        "",
        "=" * 60
    ]

    return "\n".join(lines)
