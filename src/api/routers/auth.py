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
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

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
