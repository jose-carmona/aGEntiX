# backoffice/auth/jwt_validator.py

import jwt
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel
from typing import List


class JWTClaims(BaseModel):
    """Modelo de claims JWT"""
    iss: str  # Emisor
    sub: str  # Subject (usuario)
    aud: List[str] | str  # Audiencias autorizadas
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    nbf: int  # Not before timestamp
    jti: str  # JWT ID único
    exp_id: str  # ID del expediente autorizado
    permisos: List[str]  # Permisos del agente


class JWTValidationError(Exception):
    """Error de validación de JWT"""
    def __init__(self, codigo: str, mensaje: str, detalle: str = ""):
        self.codigo = codigo
        self.mensaje = mensaje
        self.detalle = detalle
        super().__init__(f"[{codigo}] {mensaje}")


def validate_jwt(
    token: str,
    secret: str,
    algorithm: str,
    expected_expediente_id: str,
    required_permissions: List[str] = None,
    expected_issuer: Optional[str] = None,
    expected_subject: Optional[str] = None,
    required_audience: Optional[str] = None
) -> JWTClaims:
    """
    Valida un token JWT completo con todos los claims obligatorios.

    Args:
        token: Token JWT a validar
        secret: Clave secreta para verificar firma
        algorithm: Algoritmo de firma (ej: HS256)
        expected_expediente_id: ID del expediente que debe coincidir con exp_id
        required_permissions: Permisos requeridos (opcional)
        expected_issuer: Emisor esperado (usa config si no se proporciona)
        expected_subject: Subject esperado (usa config si no se proporciona)
        required_audience: Audiencia requerida (usa config si no se proporciona)

    Returns:
        JWTClaims validados

    Raises:
        JWTValidationError: Si el token es inválido o no cumple requisitos
    """
    # Importar configuración
    from backoffice.settings import settings

    # Usar configuración si no se proporcionan valores
    if expected_issuer is None:
        expected_issuer = settings.JWT_EXPECTED_ISSUER
    if expected_subject is None:
        expected_subject = settings.JWT_EXPECTED_SUBJECT
    if required_audience is None:
        required_audience = settings.JWT_REQUIRED_AUDIENCE
    try:
        # 1. Decodificar y verificar firma
        payload = jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "verify_aud": False,  # Validamos audiencia manualmente después
            }
        )

    except jwt.ExpiredSignatureError:
        raise JWTValidationError(
            codigo="AUTH_TOKEN_EXPIRED",
            mensaje="Token JWT expirado",
            detalle="El token ha superado su tiempo de validez (exp)"
        )

    except jwt.ImmatureSignatureError:
        raise JWTValidationError(
            codigo="AUTH_TOKEN_NOT_YET_VALID",
            mensaje="Token JWT aún no válido",
            detalle="El token no es válido aún (nbf en el futuro)"
        )

    except jwt.InvalidTokenError as e:
        raise JWTValidationError(
            codigo="AUTH_INVALID_TOKEN",
            mensaje="Token JWT inválido o mal formado",
            detalle=str(e)
        )

    # 2. Validar estructura de claims
    try:
        claims = JWTClaims(**payload)
    except Exception as e:
        raise JWTValidationError(
            codigo="AUTH_INVALID_TOKEN",
            mensaje="Claims JWT incompletos o mal formados",
            detalle=str(e)
        )

    # 3. Validar emisor (iss)
    if claims.iss != expected_issuer:
        raise JWTValidationError(
            codigo="AUTH_PERMISSION_DENIED",
            mensaje=f"Emisor incorrecto: esperado '{expected_issuer}', recibido '{claims.iss}'",
            detalle="El token no fue emitido por el sistema BPMN autorizado"
        )

    # 4. Validar subject (sub)
    if claims.sub != expected_subject:
        raise JWTValidationError(
            codigo="AUTH_PERMISSION_DENIED",
            mensaje=f"Subject incorrecto: esperado '{expected_subject}', recibido '{claims.sub}'",
            detalle="El token no es para ejecución automática"
        )

    # 5. Validar audiencia (aud)
    audiences = claims.aud if isinstance(claims.aud, list) else [claims.aud]
    if required_audience not in audiences:
        raise JWTValidationError(
            codigo="AUTH_PERMISSION_DENIED",
            mensaje=f"Audiencia incorrecta: debe incluir '{required_audience}'",
            detalle=f"Audiencias recibidas: {audiences}"
        )

    # 6. Validar expediente (exp_id)
    if claims.exp_id != expected_expediente_id:
        raise JWTValidationError(
            codigo="AUTH_EXPEDIENTE_MISMATCH",
            mensaje=f"Expediente no autorizado: token para '{claims.exp_id}', solicitado '{expected_expediente_id}'",
            detalle="El token no está autorizado para este expediente"
        )

    # 7. Validar permisos (si se especificaron)
    if required_permissions:
        missing_perms = set(required_permissions) - set(claims.permisos)
        if missing_perms:
            raise JWTValidationError(
                codigo="AUTH_INSUFFICIENT_PERMISSIONS",
                mensaje=f"Permisos insuficientes: faltan {missing_perms}",
                detalle=f"Permisos requeridos: {required_permissions}, disponibles: {claims.permisos}"
            )

    return claims


def get_required_permissions_for_tools(tool_names: List[str]) -> List[str]:
    """
    Determina los permisos requeridos según las herramientas solicitadas.

    Args:
        tool_names: Lista de nombres de herramientas MCP

    Returns:
        Lista de permisos requeridos
    """
    # Herramientas de solo lectura
    readonly_tools = {"consultar_expediente", "listar_documentos", "leer_documento"}

    # Herramientas que requieren escritura
    write_tools = {
        "actualizar_datos",
        "añadir_anotacion",
        "subir_documento",
        "actualizar_estado"
    }

    required_perms = set()

    for tool in tool_names:
        if tool in readonly_tools:
            required_perms.add("consulta")
        elif tool in write_tools:
            required_perms.add("gestion")

    # Si hay herramientas de escritura, incluir también consulta
    if "gestion" in required_perms:
        required_perms.add("consulta")

    return list(required_perms)
