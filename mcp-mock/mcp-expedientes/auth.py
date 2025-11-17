"""
Sistema de autenticación y autorización basado en JWT.

Valida tokens JWT con claims completos y verifica permisos
según la arquitectura de propagación de permisos de aGEntiX.
"""

import os
import jwt
from datetime import datetime
from typing import Optional, List, Dict, Any
from models import JWTClaims


class AuthError(Exception):
    """Error de autenticación o autorización"""
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def validate_audience(token_payload: dict, server_id: str = "agentix-mcp-expedientes") -> bool:
    """
    Valida que el servidor esté autorizado en el token.
    Soporta tanto string como array en el claim 'aud'.

    Args:
        token_payload: Payload decodificado del JWT
        server_id: ID del servidor MCP (default: agentix-mcp-expedientes)

    Returns:
        True si el servidor está autorizado, False en caso contrario
    """
    aud = token_payload.get("aud")

    if isinstance(aud, str):
        return aud == server_id
    elif isinstance(aud, list):
        return server_id in aud
    else:
        return False


def get_jwt_secret() -> str:
    """
    Obtiene la clave secreta para validar JWT desde variable de entorno.

    Returns:
        Clave secreta JWT

    Raises:
        AuthError: Si no se encuentra la variable de entorno JWT_SECRET
    """
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        raise AuthError("JWT_SECRET no configurado", 500)
    return secret


async def validate_jwt(
    token: Optional[str],
    resource_uri: Optional[str] = None,
    tool_name: Optional[str] = None,
    tool_args: Optional[dict] = None,
    server_id: str = "agentix-mcp-expedientes"
) -> JWTClaims:
    """
    Valida un token JWT y verifica permisos.

    Validaciones realizadas:
    1. Token presente
    2. Firma válida
    3. No expirado (exp > now)
    4. Not before válido (nbf <= now)
    5. Audiencia correcta (servidor en aud)
    6. Subject correcto (sub == "Automático")
    7. Expediente autorizado (si aplica)
    8. Permisos suficientes (si aplica)

    Args:
        token: Token JWT a validar
        resource_uri: URI del recurso solicitado (opcional)
        tool_name: Nombre de la tool invocada (opcional)
        tool_args: Argumentos de la tool (opcional)
        server_id: ID del servidor MCP

    Returns:
        Claims validados del token

    Raises:
        AuthError: Si la validación falla
    """
    # 1. Verificar que el token está presente
    if not token:
        raise AuthError("Token JWT no proporcionado", 401)

    try:
        # 2. Decodificar y validar firma
        secret = get_jwt_secret()
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True
            }
        )

        # Validar estructura con Pydantic
        claims = JWTClaims(**payload)

    except jwt.ExpiredSignatureError:
        raise AuthError("Token expirado", 401)
    except jwt.InvalidSignatureError:
        raise AuthError("Firma inválida", 401)
    except jwt.ImmatureSignatureError:
        raise AuthError("Token aún no válido (nbf)", 401)
    except jwt.InvalidTokenError as e:
        raise AuthError(f"Token inválido: {str(e)}", 401)
    except Exception as e:
        raise AuthError(f"Error al validar token: {str(e)}", 401)

    # 4. Validar audiencia
    if not validate_audience(payload, server_id):
        raise AuthError(
            f"Audiencia inválida: servidor '{server_id}' no autorizado",
            403
        )

    # 5. Validar subject
    if claims.sub != "Automático":
        raise AuthError("Usuario no autorizado: solo se permite 'Automático'", 403)

    # 6. Validar emisor
    if claims.iss != "agentix-bpmn":
        raise AuthError("Emisor de token no válido", 403)

    # 7. Validar acceso al expediente
    if resource_uri:
        exp_id = extract_exp_id_from_uri(resource_uri)
        if exp_id and exp_id != claims.exp_id:
            raise AuthError(
                f"Acceso no autorizado al expediente {exp_id}. "
                f"Token solo autoriza {claims.exp_id}",
                403
            )

    if tool_args and "expediente_id" in tool_args:
        exp_id = tool_args["expediente_id"]
        if exp_id != claims.exp_id:
            raise AuthError(
                f"Acceso no autorizado al expediente {exp_id}. "
                f"Token solo autoriza {claims.exp_id}",
                403
            )

    # 8. Validar permisos para la operación
    if tool_name:
        required_permission = get_required_permission(tool_name)
        if required_permission and required_permission not in claims.permisos:
            raise AuthError(
                f"Permiso insuficiente: se requiere '{required_permission}' "
                f"para ejecutar '{tool_name}'",
                403
            )

    return claims


def extract_exp_id_from_uri(uri: str) -> Optional[str]:
    """
    Extrae el ID del expediente de una URI de recurso.

    Args:
        uri: URI del recurso (ej: "expediente://EXP-2024-001" o "expediente://EXP-2024-001/documentos")

    Returns:
        ID del expediente o None si no se puede extraer
    """
    if not uri.startswith("expediente://"):
        return None

    # Remover el esquema
    path = uri.replace("expediente://", "")

    # Tomar la primera parte (ID del expediente)
    parts = path.split("/")
    if parts:
        return parts[0]

    return None


def get_required_permission(tool_name: str) -> Optional[str]:
    """
    Determina el permiso requerido para ejecutar una tool.

    Args:
        tool_name: Nombre de la tool

    Returns:
        Permiso requerido ("consulta" o "gestion") o None si no requiere permiso específico
    """
    # Tools de solo lectura: requieren "consulta"
    read_tools = [
        "consultar_expediente",
        "listar_documentos",
        "obtener_documento"
    ]

    # Tools de escritura: requieren "gestion"
    write_tools = [
        "añadir_documento",
        "actualizar_datos",
        "añadir_anotacion"
    ]

    if tool_name in read_tools:
        return "consulta"
    elif tool_name in write_tools:
        return "gestion"

    return None


def require_permission(claims: JWTClaims, permission: str) -> None:
    """
    Verifica que los claims tengan un permiso específico.

    Args:
        claims: Claims del JWT
        permission: Permiso requerido

    Raises:
        AuthError: Si el permiso no está presente
    """
    if permission not in claims.permisos:
        raise AuthError(
            f"Permiso '{permission}' no disponible en el token",
            403
        )


def can_read(claims: JWTClaims) -> bool:
    """Verifica si el token tiene permiso de lectura"""
    return "consulta" in claims.permisos


def can_write(claims: JWTClaims) -> bool:
    """Verifica si el token tiene permiso de escritura"""
    return "gestion" in claims.permisos
