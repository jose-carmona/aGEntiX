# api/routers/auth.py

"""
Endpoints de autenticación para el dashboard de administración.

Implementa dos sistemas de autenticación:
1. Token de Admin (API_ADMIN_TOKEN): Para acceso al dashboard frontend
2. JWT de Agente: Para ejecutar agentes (ver agent.py)

IMPORTANTE:
- El token de admin es un string simple, NO es JWT
- Se usa SOLO para proteger el dashboard web (métricas, logs, panel de pruebas)
- Los endpoints de agentes usan JWT separado con 10 claims validados
"""

import logging
import jwt
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Union
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field

from backoffice.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Modelos Pydantic
# ============================================================================

class TokenValidationRequest(BaseModel):
    """Request para validar token de administración"""
    token: str

    class Config:
        json_schema_extra = {
            "example": {
                "token": "agentix-admin-dev-token-2024"
            }
        }


class TokenValidationResponse(BaseModel):
    """Response de validación de token"""
    valid: bool
    message: str

    class Config:
        json_schema_extra = {
            "examples": [
                {"valid": True, "message": "Token válido"},
                {"valid": False, "message": "Token inválido"}
            ]
        }


class GenerateJWTRequest(BaseModel):
    """Request para generar JWT de prueba"""
    exp_id: str = Field(
        ...,
        description="ID del expediente",
        examples=["EXP-2024-001"]
    )
    exp_tipo: str = Field(
        default="SUBVENCIONES",
        description="Tipo de expediente"
    )
    tarea_id: str = Field(
        default="TAREA-TEST-001",
        description="ID de la tarea BPMN"
    )
    tarea_nombre: str = Field(
        default="TAREA_TEST",
        description="Nombre de la tarea BPMN"
    )
    permisos: List[str] = Field(
        default=["consulta"],
        description="Lista de permisos (consulta, gestion)"
    )
    mcp_servers: Optional[List[str]] = Field(
        default=None,
        description="Lista de servidores MCP autorizados (default: solo expedientes)"
    )
    exp_hours: int = Field(
        default=1,
        description="Horas hasta expiración del token",
        ge=1,
        le=24
    )

    class Config:
        json_schema_extra = {
            "example": {
                "exp_id": "EXP-2024-001",
                "exp_tipo": "SUBVENCIONES",
                "tarea_id": "TAREA-TEST-001",
                "tarea_nombre": "VALIDAR_DOCUMENTACION",
                "permisos": ["consulta", "gestion"],
                "mcp_servers": ["agentix-mcp-expedientes"],
                "exp_hours": 1
            }
        }


class GenerateJWTResponse(BaseModel):
    """Response con JWT generado y claims decodificados"""
    token: str = Field(..., description="Token JWT firmado")
    claims: dict = Field(..., description="Claims decodificados del JWT")

    class Config:
        json_schema_extra = {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "claims": {
                    "sub": "Automático",
                    "iss": "agentix-bpmn",
                    "aud": "agentix-mcp-expedientes",
                    "exp_id": "EXP-2024-001",
                    "exp_tipo": "SUBVENCIONES",
                    "permisos": ["consulta", "gestion"]
                }
            }
        }


# ============================================================================
# Dependencies
# ============================================================================

async def verify_admin_token(authorization: str = Header(..., description="Bearer token de admin")):
    """
    Dependency para verificar el token de administración en endpoints protegidos.

    Verifica que el header Authorization contenga un Bearer token válido
    que coincida con API_ADMIN_TOKEN.

    Args:
        authorization: Header Authorization con formato "Bearer <token>"

    Returns:
        El token validado

    Raises:
        HTTPException 401: Si el token no es válido o falta

    Example:
        ```python
        @router.get("/protected", dependencies=[Depends(verify_admin_token)])
        async def protected_endpoint():
            return {"message": "Acceso permitido"}
        ```
    """
    if not authorization.startswith("Bearer "):
        logger.warning("Header Authorization sin formato Bearer")
        raise HTTPException(
            status_code=401,
            detail="Token de autorización requerido con formato: Bearer <token>"
        )

    token = authorization.replace("Bearer ", "")

    if token != settings.API_ADMIN_TOKEN:
        logger.warning("Token de admin inválido en endpoint protegido")
        raise HTTPException(
            status_code=401,
            detail="Token de administración inválido"
        )

    return token


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/validate-admin-token",
    response_model=TokenValidationResponse,
    tags=["Authentication"],
    summary="Validar token de administración",
    description=(
        "Valida el token de administración para acceso al dashboard web.\n\n"
        "**Flujo de autenticación:**\n"
        "1. Usuario introduce token en login del frontend\n"
        "2. Frontend envía POST a este endpoint\n"
        "3. Backend compara con API_ADMIN_TOKEN de .env\n"
        "4. Si coincide, frontend guarda token y permite acceso\n\n"
        "**IMPORTANTE:** Este token NO es JWT, es un string simple.\n"
        "Los endpoints de agentes usan un sistema JWT separado."
    )
)
async def validate_admin_token(request: TokenValidationRequest):
    """
    Valida el token de administración contra la variable de entorno.

    Args:
        request: Objeto con el token a validar

    Returns:
        TokenValidationResponse indicando si el token es válido

    Raises:
        HTTPException 401: Si el token no coincide con API_ADMIN_TOKEN
    """

    logger.info("Recibida solicitud de validación de token de admin")

    # Validar contra variable de entorno
    if request.token == settings.API_ADMIN_TOKEN:
        logger.info("Token de admin validado exitosamente")
        return TokenValidationResponse(
            valid=True,
            message="Token válido"
        )
    else:
        logger.warning("Intento de login con token inválido")
        raise HTTPException(
            status_code=401,
            detail={
                "valid": False,
                "message": "Token inválido"
            }
        )


@router.post(
    "/generate-jwt",
    response_model=GenerateJWTResponse,
    tags=["Authentication"],
    summary="Generar JWT de prueba para testing de agentes",
    description=(
        "Genera un token JWT válido para probar la ejecución de agentes.\n\n"
        "**Requiere autenticación:** Bearer token de admin en header Authorization\n\n"
        "**Uso típico:**\n"
        "1. Usuario autenticado accede al panel de pruebas\n"
        "2. Configura expediente_id y permisos deseados\n"
        "3. Llama a este endpoint para generar JWT\n"
        "4. Usa el JWT generado para llamar a POST /api/v1/agent/execute\n\n"
        "**Claims del JWT:**\n"
        "- sub: Siempre 'Automático'\n"
        "- iss: Siempre 'agentix-bpmn'\n"
        "- aud: Servidor(es) MCP autorizados\n"
        "- exp_id: ID del expediente\n"
        "- permisos: Lista de permisos concedidos\n"
        "- exp: Timestamp de expiración\n"
        "- iat, nbf, jti: Claims estándar JWT"
    )
)
async def generate_jwt(
    request: GenerateJWTRequest,
    _token: str = Depends(verify_admin_token)
):
    """
    Genera un JWT de prueba para testing de agentes.

    Este endpoint requiere autenticación de admin (Bearer token) y genera
    un JWT válido con los claims necesarios para ejecutar agentes.

    Args:
        request: Parámetros para generar el JWT
        _token: Token de admin (inyectado por dependency)

    Returns:
        GenerateJWTResponse con el token y claims decodificados

    Raises:
        HTTPException 401: Si el token de admin no es válido
        HTTPException 400: Si los parámetros son inválidos
    """
    logger.info(f"Generando JWT de prueba para expediente: {request.exp_id}")

    try:
        # Determinar audiencia (mcp_servers)
        mcp_servers = request.mcp_servers or ["agentix-mcp-expedientes"]

        # Generar timestamps
        now = datetime.utcnow()
        iat = int(now.timestamp())
        exp = int((now + timedelta(hours=request.exp_hours)).timestamp())
        nbf = int(now.timestamp())

        # Construir payload del JWT
        payload = {
            "sub": "Automático",
            "iat": iat,
            "exp": exp,
            "nbf": nbf,
            "iss": "agentix-bpmn",
            "aud": mcp_servers if len(mcp_servers) > 1 else mcp_servers[0],
            "jti": str(uuid.uuid4()),
            "exp_id": request.exp_id,
            "exp_tipo": request.exp_tipo,
            "tarea_id": request.tarea_id,
            "tarea_nombre": request.tarea_nombre,
            "permisos": request.permisos
        }

        # Firmar token con el secret del sistema
        token = jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )

        logger.info(
            f"JWT generado exitosamente para {request.exp_id} "
            f"con permisos: {request.permisos}"
        )

        return GenerateJWTResponse(
            token=token,
            claims=payload
        )

    except Exception as e:
        logger.error(f"Error al generar JWT: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Error al generar JWT: {str(e)}"
        )
