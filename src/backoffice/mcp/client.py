# backoffice/mcp/client.py

import httpx
from typing import Dict, Any, List
from ..config.models import MCPServerConfig
from .exceptions import MCPConnectionError, MCPToolError, MCPAuthError, MCPError


class MCPClient:
    """
    Cliente MCP HTTP simple que propaga errores al sistema BPMN.

    NO implementa reintentos complejos - esa responsabilidad es del BPMN.
    """

    def __init__(self, server_config: MCPServerConfig, token: str):
        """
        Inicializa el cliente MCP.

        Args:
            server_config: Configuración del servidor MCP
            token: Token JWT completo
        """
        self.server_config = server_config
        self.server_id = server_config.id
        self.token = token
        self._request_id = 0

        # Cliente HTTP con timeout configurado
        # El BPMN tiene timeouts de tarea más sofisticados
        self.client = httpx.AsyncClient(
            base_url=str(server_config.url),
            timeout=float(server_config.timeout),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )

    def _next_request_id(self) -> int:
        """Genera ID único para request JSON-RPC"""
        self._request_id += 1
        return self._request_id

    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta una tool en el servidor MCP.

        NO reintenta - el sistema BPMN maneja reintentos a nivel de tarea.

        Args:
            name: Nombre de la tool (ej: "consultar_expediente")
            arguments: Argumentos de la tool

        Returns:
            Contenido de la respuesta

        Raises:
            MCPConnectionError: Error de conexión con servidor
            MCPAuthError: Error de autenticación/autorización
            MCPToolError: Error al ejecutar la tool
        """
        try:
            response = await self.client.post(
                self.server_config.endpoint,
                json={
                    "jsonrpc": "2.0",
                    "id": self._next_request_id(),
                    "method": "tools/call",
                    "params": {
                        "name": name,
                        "arguments": arguments
                    }
                }
            )

            # Lanzar excepción si status code indica error
            response.raise_for_status()

            # Parsear respuesta JSON-RPC
            data = response.json()

            # Verificar si hay error en respuesta JSON-RPC
            if "error" in data:
                raise MCPToolError(
                    codigo="MCP_TOOL_ERROR",
                    mensaje=f"Error en tool '{name}': {data['error']['message']}",
                    detalle=str(data['error'])
                )

            # Retornar result
            return data.get("result", {})

        except httpx.TimeoutException as e:
            raise MCPConnectionError(
                codigo="MCP_TIMEOUT",
                mensaje=f"Timeout al ejecutar tool '{name}' en MCP '{self.server_id}' (>{self.server_config.timeout}s)",
                detalle=str(e)
            )

        except httpx.ConnectError as e:
            raise MCPConnectionError(
                codigo="MCP_CONNECTION_ERROR",
                mensaje=f"No se puede conectar al servidor MCP '{self.server_id}': {self.server_config.url}",
                detalle=str(e)
            )

        except httpx.HTTPStatusError as e:
            status = e.response.status_code

            if status == 401:
                raise MCPAuthError(
                    codigo="AUTH_INVALID_TOKEN",
                    mensaje="Token JWT inválido o expirado",
                    detalle=e.response.text
                )

            elif status == 403:
                raise MCPAuthError(
                    codigo="AUTH_PERMISSION_DENIED",
                    mensaje="Permisos insuficientes para ejecutar tool",
                    detalle=e.response.text
                )

            elif status == 404:
                raise MCPToolError(
                    codigo="MCP_TOOL_NOT_FOUND",
                    mensaje=f"Tool '{name}' no encontrada en servidor MCP",
                    detalle=e.response.text
                )

            elif status in [502, 503, 504]:
                raise MCPConnectionError(
                    codigo="MCP_SERVER_UNAVAILABLE",
                    mensaje=f"Servidor MCP no disponible (HTTP {status})",
                    detalle=e.response.text
                )

            else:
                raise MCPToolError(
                    codigo="MCP_TOOL_ERROR",
                    mensaje=f"Error al ejecutar tool '{name}' (HTTP {status})",
                    detalle=e.response.text
                )

        except MCPError:
            # Re-lanzar errores MCP ya clasificados
            raise

        except Exception as e:
            raise MCPConnectionError(
                codigo="MCP_UNEXPECTED_ERROR",
                mensaje=f"Error inesperado al llamar a MCP: {type(e).__name__}",
                detalle=str(e)
            )

    async def list_tools(self) -> Dict[str, Any]:
        """
        Lista todas las tools disponibles en el servidor MCP.

        Returns:
            Diccionario con lista de tools disponibles

        Raises:
            MCPConnectionError: Error de conexión
            MCPAuthError: Error de autenticación
        """
        try:
            response = await self.client.post(
                self.server_config.endpoint,
                json={
                    "jsonrpc": "2.0",
                    "id": self._next_request_id(),
                    "method": "tools/list"
                }
            )

            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise MCPToolError(
                    codigo="MCP_TOOL_ERROR",
                    mensaje=f"Error al listar tools: {data['error']['message']}",
                    detalle=str(data['error'])
                )

            return data.get("result", {})

        except httpx.HTTPError as e:
            raise MCPConnectionError(
                codigo="MCP_CONNECTION_ERROR",
                mensaje=f"Error al listar tools: {str(e)}",
                detalle=str(e)
            )

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        Lee un resource del servidor MCP.

        Args:
            uri: URI del resource (ej: "expediente://EXP-2024-001")

        Returns:
            Contenido del resource

        Raises:
            MCPConnectionError: Error de conexión
            MCPAuthError: Error de autenticación
        """
        try:
            response = await self.client.post(
                self.server_config.endpoint,
                json={
                    "jsonrpc": "2.0",
                    "id": self._next_request_id(),
                    "method": "resources/read",
                    "params": {"uri": uri}
                }
            )

            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise MCPToolError(
                    codigo="MCP_RESOURCE_ERROR",
                    mensaje=f"Error al leer resource '{uri}': {data['error']['message']}",
                    detalle=str(data['error'])
                )

            return data.get("result", {})

        except httpx.HTTPError as e:
            raise MCPConnectionError(
                codigo="MCP_CONNECTION_ERROR",
                mensaje=f"Error al leer resource: {str(e)}",
                detalle=str(e)
            )

    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()
