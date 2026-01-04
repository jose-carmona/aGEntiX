# api/routers/expedientes.py

"""
Endpoints para consulta de expedientes y documentos.

Estos endpoints actúan como proxy entre el frontend y el servidor MCP,
permitiendo que el dashboard web acceda a los datos de expedientes
usando autenticación de admin token (en lugar de JWT directo al MCP).

Todos los endpoints requieren token de administración.
"""

import logging
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from .auth import verify_admin_token
from ..services.mcp_client import (
    get_expedientes_list,
    get_expediente,
    get_expediente_documentos,
    get_documento_texto,
    get_documento_metadatos,
    check_mcp_health,
    MCPClientError
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Modelos Pydantic
# ============================================================================

class ExpedienteResumen(BaseModel):
    """Resumen de un expediente para listados"""
    id: str
    tipo: str
    estado: str
    fecha_inicio: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "EXP-2024-001",
                "tipo": "SUBVENCIONES",
                "estado": "EN_TRAMITE",
                "fecha_inicio": "2024-01-15T08:30:00+00:00"
            }
        }


class DocumentoResumen(BaseModel):
    """Resumen de un documento para listados"""
    id: str
    nombre: str
    tipo: str
    fecha: str
    validado: bool | None = None
    tamano_bytes: int

    class Config:
        json_schema_extra = {
            "example": {
                "id": "DOC-001",
                "nombre": "solicitud.pdf",
                "tipo": "SOLICITUD",
                "fecha": "2024-01-15T08:30:00Z",
                "validado": True,
                "tamano_bytes": 245678
            }
        }


class DocumentoTexto(BaseModel):
    """Contenido markdown de un documento"""
    documento_id: str
    texto_markdown: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "documento_id": "DOC-001",
                "texto_markdown": "# Solicitud de Subvención\n\n## Datos del Solicitante\n..."
            }
        }


class DocumentoMetadatos(BaseModel):
    """Metadatos extraídos de un documento"""
    documento_id: str
    metadatos_extraidos: Dict[str, Any] | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "documento_id": "DOC-002",
                "metadatos_extraidos": {
                    "tipo_documento": "DNI",
                    "numero_documento": "12345678A",
                    "nombre_completo": "María García López"
                }
            }
        }


class MCPStatusResponse(BaseModel):
    """Estado del servidor MCP"""
    available: bool
    message: str


# ============================================================================
# Endpoints
# ============================================================================

@router.get(
    "/mcp-status",
    response_model=MCPStatusResponse,
    summary="Estado del servidor MCP",
    description="Verifica si el servidor MCP está disponible para consultas."
)
async def mcp_status(_token: str = Depends(verify_admin_token)):
    """
    Verifica la disponibilidad del servidor MCP.

    Útil para mostrar estado en el frontend antes de cargar expedientes.
    """
    available = await check_mcp_health()
    return MCPStatusResponse(
        available=available,
        message="Servidor MCP disponible" if available else "Servidor MCP no disponible"
    )


@router.get(
    "/",
    response_model=List[ExpedienteResumen],
    summary="Listar todos los expedientes",
    description=(
        "Obtiene la lista de todos los expedientes disponibles en el sistema.\n\n"
        "Retorna datos básicos de cada expediente para mostrar en listados."
    )
)
async def listar_expedientes(_token: str = Depends(verify_admin_token)):
    """
    Lista todos los expedientes disponibles.

    El backend se comunica internamente con el MCP para obtener
    la lista de expedientes, generando JWT internos según sea necesario.
    """
    logger.info("Solicitando lista de expedientes")

    try:
        expedientes = await get_expedientes_list()
        logger.info(f"Recuperados {len(expedientes)} expedientes")

        # Convertir a modelo de respuesta
        return [
            ExpedienteResumen(
                id=exp.get("id", ""),
                tipo=exp.get("tipo", ""),
                estado=exp.get("estado", ""),
                fecha_inicio=exp.get("fecha_inicio", "")
            )
            for exp in expedientes
        ]

    except MCPClientError as e:
        logger.error(f"Error MCP al listar expedientes: {e.message}")
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        logger.error(f"Error inesperado al listar expedientes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{expediente_id}",
    response_model=Dict[str, Any],
    summary="Obtener expediente completo",
    description="Obtiene todos los datos de un expediente específico."
)
async def obtener_expediente(
    expediente_id: str,
    _token: str = Depends(verify_admin_token)
):
    """
    Obtiene los datos completos de un expediente.

    Args:
        expediente_id: ID del expediente (ej: EXP-2024-001)
    """
    logger.info(f"Solicitando expediente: {expediente_id}")

    try:
        expediente = await get_expediente(expediente_id)

        if not expediente:
            raise HTTPException(status_code=404, detail=f"Expediente {expediente_id} no encontrado")

        return expediente

    except MCPClientError as e:
        logger.error(f"Error MCP al obtener expediente {expediente_id}: {e.message}")
        raise HTTPException(status_code=e.code, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado al obtener expediente: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{expediente_id}/documentos",
    response_model=List[DocumentoResumen],
    summary="Listar documentos de un expediente",
    description="Obtiene la lista de documentos asociados a un expediente."
)
async def listar_documentos(
    expediente_id: str,
    _token: str = Depends(verify_admin_token)
):
    """
    Lista los documentos de un expediente.

    Args:
        expediente_id: ID del expediente
    """
    logger.info(f"Solicitando documentos del expediente: {expediente_id}")

    try:
        documentos = await get_expediente_documentos(expediente_id)
        logger.info(f"Recuperados {len(documentos)} documentos para {expediente_id}")

        return [
            DocumentoResumen(
                id=doc.get("id", ""),
                nombre=doc.get("nombre", ""),
                tipo=doc.get("tipo", ""),
                fecha=doc.get("fecha", ""),
                validado=doc.get("validado"),
                tamano_bytes=doc.get("tamano_bytes", 0)
            )
            for doc in documentos
        ]

    except MCPClientError as e:
        logger.error(f"Error MCP al listar documentos: {e.message}")
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        logger.error(f"Error inesperado al listar documentos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{expediente_id}/documentos/{documento_id}/texto",
    response_model=DocumentoTexto,
    summary="Obtener texto markdown de un documento",
    description=(
        "Obtiene el contenido markdown renderizable de un documento.\n\n"
        "El texto markdown puede mostrarse directamente en el frontend "
        "usando un componente de renderizado de markdown."
    )
)
async def obtener_documento_texto(
    expediente_id: str,
    documento_id: str,
    _token: str = Depends(verify_admin_token)
):
    """
    Obtiene el texto markdown de un documento.

    Args:
        expediente_id: ID del expediente
        documento_id: ID del documento
    """
    logger.info(f"Solicitando texto del documento {documento_id} en {expediente_id}")

    try:
        result = await get_documento_texto(expediente_id, documento_id)
        return DocumentoTexto(
            documento_id=result.get("documento_id", documento_id),
            texto_markdown=result.get("texto_markdown")
        )

    except MCPClientError as e:
        logger.error(f"Error MCP al obtener texto documento: {e.message}")
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        logger.error(f"Error inesperado al obtener texto documento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{expediente_id}/documentos/{documento_id}/metadatos",
    response_model=DocumentoMetadatos,
    summary="Obtener metadatos de un documento",
    description=(
        "Obtiene los metadatos extraídos de un documento.\n\n"
        "Los metadatos incluyen información estructurada extraída del documento, "
        "como datos de identificación, fechas, importes, etc."
    )
)
async def obtener_documento_metadatos(
    expediente_id: str,
    documento_id: str,
    _token: str = Depends(verify_admin_token)
):
    """
    Obtiene los metadatos extraídos de un documento.

    Args:
        expediente_id: ID del expediente
        documento_id: ID del documento
    """
    logger.info(f"Solicitando metadatos del documento {documento_id} en {expediente_id}")

    try:
        result = await get_documento_metadatos(expediente_id, documento_id)
        return DocumentoMetadatos(
            documento_id=result.get("documento_id", documento_id),
            metadatos_extraidos=result.get("metadatos_extraidos")
        )

    except MCPClientError as e:
        logger.error(f"Error MCP al obtener metadatos documento: {e.message}")
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        logger.error(f"Error inesperado al obtener metadatos documento: {e}")
        raise HTTPException(status_code=500, detail=str(e))
