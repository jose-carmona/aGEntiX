# api/routers/health.py

"""
Endpoints de health check y utilidades.

- GET /health: Verifica estado de la API y dependencias
"""

from fastapi import APIRouter
from datetime import datetime, timezone
import httpx

from ..models import HealthResponse
from backoffice.settings import settings

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check de la API",
    description="Verifica que la API y sus dependencias estén operativas"
)
async def health_check():
    """
    Health check endpoint.

    Verifica:
    - API funcionando
    - Conectividad con MCP servers (opcional)
    """

    version = "1.0.0"
    timestamp = datetime.now(timezone.utc).isoformat()

    # Check MCP servers (opcional, puede ser costoso)
    # Por ahora solo retornamos "not_checked"
    dependencies = {
        "mcp_expedientes": "not_checked",
        "database": "not_applicable"
    }

    # TODO: En producción, podríamos hacer ping a los MCP servers
    # Para esto necesitaríamos parsear mcp_servers.yaml y hacer requests

    return HealthResponse(
        status="healthy",
        timestamp=timestamp,
        version=version,
        dependencies=dependencies
    )
