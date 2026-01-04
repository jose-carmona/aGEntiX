# api/services/mcp_client.py

"""
Cliente MCP para comunicación desde el backend API.

Este servicio encapsula la comunicación JSON-RPC 2.0 con el servidor MCP,
permitiendo que el API REST actúe como proxy para el frontend.

El backend genera internamente los JWT necesarios para autenticarse con el MCP.
"""

import httpx
import logging
from typing import Any, Dict, List, Optional

from backoffice.settings import settings
from backoffice.auth.jwt_generator import generate_jwt

logger = logging.getLogger(__name__)

# URL del servidor MCP (desde configuración o default)
MCP_BASE_URL = getattr(settings, 'MCP_BASE_URL', 'http://localhost:8000')


class MCPClientError(Exception):
    """Error en comunicación con MCP"""
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(message)


async def _get_internal_jwt(expediente_id: str = "*") -> str:
    """
    Genera un JWT interno para comunicación backend -> MCP.

    El backend actúa con permisos elevados para poder consultar
    cualquier expediente en nombre del admin.
    """
    result = generate_jwt(
        expediente_id=expediente_id,
        tarea_id="TAREA-API-INTERNAL",
        permisos=["consulta", "gestion"],
        expediente_tipo="INTERNAL",
        tarea_nombre="API_PROXY",
        expiration_hours=1
    )
    return result.token


async def _call_mcp_rpc(
    method: str,
    params: Optional[Dict[str, Any]] = None,
    jwt_token: Optional[str] = None
) -> Any:
    """
    Realiza una llamada JSON-RPC 2.0 al servidor MCP.

    Args:
        method: Método RPC (tools/list, tools/call, resources/list, etc.)
        params: Parámetros del método
        jwt_token: Token JWT para autenticación (se genera uno si no se proporciona)

    Returns:
        Resultado de la llamada RPC

    Raises:
        MCPClientError: Si hay error en la comunicación o respuesta
    """
    if jwt_token is None:
        jwt_token = await _get_internal_jwt()

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method
    }

    if params:
        payload["params"] = params

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{MCP_BASE_URL}/rpc",
                json=payload,
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Content-Type": "application/json"
                }
            )

            if response.status_code != 200:
                logger.error(f"MCP error HTTP {response.status_code}: {response.text}")
                raise MCPClientError(
                    f"Error HTTP del servidor MCP: {response.status_code}",
                    code=response.status_code
                )

            data = response.json()

            if "error" in data:
                error = data["error"]
                logger.error(f"MCP RPC error: {error}")
                raise MCPClientError(
                    error.get("message", "Error desconocido del MCP"),
                    code=error.get("code", 500)
                )

            return data.get("result")

    except httpx.RequestError as e:
        logger.error(f"Error de conexión con MCP: {e}")
        raise MCPClientError(f"No se puede conectar con el servidor MCP: {e}", code=503)


# ============================================================================
# Funciones públicas para expedientes
# ============================================================================

async def get_expedientes_list() -> List[Dict[str, Any]]:
    """
    Obtiene la lista de todos los expedientes disponibles.

    Returns:
        Lista de expedientes con sus datos básicos
    """
    # Primero obtenemos la lista de resources para saber qué expedientes hay
    result = await _call_mcp_rpc("resources/list")
    resources = result.get("resources", [])

    # Filtrar solo los expedientes principales
    expediente_ids = []
    for r in resources:
        uri = r.get("uri", "")
        # Solo expedientes principales, no sub-resources
        if uri.startswith("expediente://") and uri.count("/") == 2:
            exp_id = uri.replace("expediente://", "")
            expediente_ids.append(exp_id)

    # Obtener datos de cada expediente
    expedientes = []
    for exp_id in expediente_ids:
        try:
            exp_data = await get_expediente(exp_id)
            if exp_data:
                expedientes.append(exp_data)
        except MCPClientError as e:
            logger.warning(f"No se pudo cargar expediente {exp_id}: {e.message}")

    return expedientes


async def get_expediente(expediente_id: str) -> Dict[str, Any]:
    """
    Obtiene los datos de un expediente específico.

    Args:
        expediente_id: ID del expediente (ej: "EXP-2024-001")

    Returns:
        Datos del expediente
    """
    jwt_token = await _get_internal_jwt(expediente_id)

    result = await _call_mcp_rpc(
        "tools/call",
        params={
            "name": "consultar_expediente",
            "arguments": {"expediente_id": expediente_id}
        },
        jwt_token=jwt_token
    )

    # Parsear el contenido JSON de la respuesta
    content = result.get("content", [])
    if content and len(content) > 0:
        import json
        text = content[0].get("text", "{}")
        return json.loads(text)

    return {}


async def get_expediente_documentos(expediente_id: str) -> List[Dict[str, Any]]:
    """
    Obtiene la lista de documentos de un expediente.

    Args:
        expediente_id: ID del expediente

    Returns:
        Lista de documentos del expediente
    """
    jwt_token = await _get_internal_jwt(expediente_id)

    result = await _call_mcp_rpc(
        "tools/call",
        params={
            "name": "listar_documentos",
            "arguments": {"expediente_id": expediente_id}
        },
        jwt_token=jwt_token
    )

    content = result.get("content", [])
    if content and len(content) > 0:
        import json
        text = content[0].get("text", "[]")
        return json.loads(text)

    return []


async def get_documento_texto(expediente_id: str, documento_id: str) -> Dict[str, Any]:
    """
    Obtiene el texto markdown de un documento.

    Args:
        expediente_id: ID del expediente
        documento_id: ID del documento

    Returns:
        Dict con documento_id y texto_markdown
    """
    jwt_token = await _get_internal_jwt(expediente_id)

    result = await _call_mcp_rpc(
        "tools/call",
        params={
            "name": "obtener_texto_documento",
            "arguments": {
                "expediente_id": expediente_id,
                "documento_id": documento_id
            }
        },
        jwt_token=jwt_token
    )

    content = result.get("content", [])
    if content and len(content) > 0:
        import json
        text = content[0].get("text", "{}")
        return json.loads(text)

    return {"documento_id": documento_id, "texto_markdown": None}


async def get_documento_metadatos(expediente_id: str, documento_id: str) -> Dict[str, Any]:
    """
    Obtiene los metadatos extraídos de un documento.

    Args:
        expediente_id: ID del expediente
        documento_id: ID del documento

    Returns:
        Dict con documento_id y metadatos_extraidos
    """
    jwt_token = await _get_internal_jwt(expediente_id)

    result = await _call_mcp_rpc(
        "tools/call",
        params={
            "name": "obtener_metadatos_documento",
            "arguments": {
                "expediente_id": expediente_id,
                "documento_id": documento_id
            }
        },
        jwt_token=jwt_token
    )

    content = result.get("content", [])
    if content and len(content) > 0:
        import json
        text = content[0].get("text", "{}")
        return json.loads(text)

    return {"documento_id": documento_id, "metadatos_extraidos": None}


async def check_mcp_health() -> bool:
    """
    Verifica si el servidor MCP está disponible.

    Returns:
        True si está disponible, False en caso contrario
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{MCP_BASE_URL}/health")
            return response.status_code == 200
    except Exception:
        return False
