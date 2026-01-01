# backoffice/mcp/client.py

"""
Cliente MCP HTTP con soporte dual sync/async.

Permite usar el cliente tanto en contextos asíncronos (AgentExecutor)
como síncronos (CrewAI tools).
"""

import httpx
from typing import Dict, Any, Optional
from ..config.models import MCPServerConfig
from .exceptions import MCPConnectionError, MCPToolError, MCPAuthError, MCPError


class MCPClient:
    """
    Cliente MCP HTTP con interfaz dual (sync + async).

    Soporta tanto llamadas asíncronas (para AgentExecutor) como
    síncronas (para CrewAI tools), reutilizando la lógica de
    manejo de errores.

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

        # Clientes HTTP (lazy initialization)
        self._async_client: Optional[httpx.AsyncClient] = None
        self._sync_client: Optional[httpx.Client] = None

    @property
    def _headers(self) -> Dict[str, str]:
        """Headers comunes para todas las peticiones."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    @property
    def _base_url(self) -> str:
        """URL base del servidor MCP."""
        return str(self.server_config.url)

    @property
    def _timeout(self) -> float:
        """Timeout en segundos."""
        return float(self.server_config.timeout)

    def _get_async_client(self) -> httpx.AsyncClient:
        """Obtiene cliente async (lazy init)."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                headers=self._headers
            )
        return self._async_client

    def _get_sync_client(self) -> httpx.Client:
        """Obtiene cliente sync (lazy init)."""
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                base_url=self._base_url,
                timeout=self._timeout,
                headers=self._headers
            )
        return self._sync_client

    def _next_request_id(self) -> int:
        """Genera ID único para request JSON-RPC."""
        self._request_id += 1
        return self._request_id

    def _build_jsonrpc_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Construye request JSON-RPC 2.0.

        Args:
            method: Método JSON-RPC (ej: "tools/call")
            params: Parámetros opcionales

        Returns:
            Dict con estructura JSON-RPC
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": method
        }
        if params:
            request["params"] = params
        return request

    def _handle_http_error(self, e: httpx.HTTPStatusError, context: str) -> None:
        """
        Maneja errores HTTP y lanza excepción MCP apropiada.

        Args:
            e: Excepción HTTP
            context: Contexto para el mensaje (ej: nombre de tool)

        Raises:
            MCPAuthError: Para errores 401/403
            MCPToolError: Para errores 404/409
            MCPConnectionError: Para errores 5xx
        """
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
                mensaje=f"Tool '{context}' no encontrada en servidor MCP",
                detalle=e.response.text
            )

        elif status == 409:
            raise MCPToolError(
                codigo="MCP_CONFLICT",
                mensaje=f"Conflicto de modificación concurrente en {self.server_config.name}",
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
                mensaje=f"Error en '{context}' (HTTP {status})",
                detalle=e.response.text
            )

    def _handle_connection_error(self, e: Exception, context: str) -> None:
        """
        Maneja errores de conexión.

        Args:
            e: Excepción de conexión
            context: Contexto para el mensaje

        Raises:
            MCPConnectionError: Siempre
        """
        if isinstance(e, httpx.TimeoutException):
            raise MCPConnectionError(
                codigo="MCP_TIMEOUT",
                mensaje=f"Timeout en '{context}' en MCP '{self.server_id}' (>{self.server_config.timeout}s)",
                detalle=str(e)
            )

        elif isinstance(e, httpx.ConnectError):
            raise MCPConnectionError(
                codigo="MCP_CONNECTION_ERROR",
                mensaje=f"No se puede conectar al servidor MCP '{self.server_id}': {self.server_config.url}",
                detalle=str(e)
            )

        else:
            raise MCPConnectionError(
                codigo="MCP_UNEXPECTED_ERROR",
                mensaje=f"Error inesperado en '{context}': {type(e).__name__}",
                detalle=str(e)
            )

    def _process_response(
        self,
        data: Dict[str, Any],
        context: str
    ) -> Dict[str, Any]:
        """
        Procesa respuesta JSON-RPC.

        Args:
            data: Respuesta parseada
            context: Contexto para mensajes de error

        Returns:
            Campo 'result' de la respuesta

        Raises:
            MCPToolError: Si hay error en la respuesta
        """
        if "error" in data:
            error = data["error"]
            raise MCPToolError(
                codigo="MCP_TOOL_ERROR",
                mensaje=f"Error en '{context}': {error.get('message', str(error))}",
                detalle=str(error)
            )
        return data.get("result", {})

    # ========== INTERFAZ ASÍNCRONA ==========

    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta una tool en el servidor MCP (async).

        Args:
            name: Nombre de la tool
            arguments: Argumentos de la tool

        Returns:
            Resultado de la tool

        Raises:
            MCPConnectionError: Error de conexión
            MCPAuthError: Error de autenticación
            MCPToolError: Error en la tool
        """
        try:
            client = self._get_async_client()
            response = await client.post(
                self.server_config.endpoint,
                json=self._build_jsonrpc_request(
                    method="tools/call",
                    params={"name": name, "arguments": arguments}
                )
            )
            response.raise_for_status()
            return self._process_response(response.json(), name)

        except httpx.HTTPStatusError as e:
            self._handle_http_error(e, name)

        except MCPError:
            raise

        except Exception as e:
            self._handle_connection_error(e, name)

    async def list_tools(self) -> Dict[str, Any]:
        """
        Lista tools disponibles (async).

        Returns:
            Dict con lista de tools

        Raises:
            MCPConnectionError: Error de conexión
        """
        try:
            client = self._get_async_client()
            response = await client.post(
                self.server_config.endpoint,
                json=self._build_jsonrpc_request(method="tools/list")
            )
            response.raise_for_status()
            return self._process_response(response.json(), "tools/list")

        except httpx.HTTPStatusError as e:
            self._handle_http_error(e, "tools/list")

        except MCPError:
            raise

        except Exception as e:
            self._handle_connection_error(e, "tools/list")

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        Lee un resource del servidor MCP (async).

        Args:
            uri: URI del resource

        Returns:
            Contenido del resource

        Raises:
            MCPConnectionError: Error de conexión
        """
        try:
            client = self._get_async_client()
            response = await client.post(
                self.server_config.endpoint,
                json=self._build_jsonrpc_request(
                    method="resources/read",
                    params={"uri": uri}
                )
            )
            response.raise_for_status()
            return self._process_response(response.json(), uri)

        except httpx.HTTPStatusError as e:
            self._handle_http_error(e, uri)

        except MCPError:
            raise

        except Exception as e:
            self._handle_connection_error(e, uri)

    # ========== INTERFAZ SÍNCRONA ==========

    def call_tool_sync(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta una tool en el servidor MCP (sync).

        Versión síncrona para uso desde CrewAI y otros contextos no-async.

        Args:
            name: Nombre de la tool
            arguments: Argumentos de la tool

        Returns:
            Resultado de la tool

        Raises:
            MCPConnectionError: Error de conexión
            MCPAuthError: Error de autenticación
            MCPToolError: Error en la tool
        """
        try:
            client = self._get_sync_client()
            response = client.post(
                self.server_config.endpoint,
                json=self._build_jsonrpc_request(
                    method="tools/call",
                    params={"name": name, "arguments": arguments}
                )
            )
            response.raise_for_status()
            return self._process_response(response.json(), name)

        except httpx.HTTPStatusError as e:
            self._handle_http_error(e, name)

        except MCPError:
            raise

        except Exception as e:
            self._handle_connection_error(e, name)

    def list_tools_sync(self) -> Dict[str, Any]:
        """
        Lista tools disponibles (sync).

        Returns:
            Dict con lista de tools

        Raises:
            MCPConnectionError: Error de conexión
        """
        try:
            client = self._get_sync_client()
            response = client.post(
                self.server_config.endpoint,
                json=self._build_jsonrpc_request(method="tools/list")
            )
            response.raise_for_status()
            return self._process_response(response.json(), "tools/list")

        except httpx.HTTPStatusError as e:
            self._handle_http_error(e, "tools/list")

        except MCPError:
            raise

        except Exception as e:
            self._handle_connection_error(e, "tools/list")

    # ========== GESTIÓN DE RECURSOS ==========

    async def close(self):
        """Cierra el cliente HTTP async."""
        if self._async_client is not None:
            await self._async_client.aclose()
            self._async_client = None

    def close_sync(self):
        """Cierra el cliente HTTP sync."""
        if self._sync_client is not None:
            self._sync_client.close()
            self._sync_client = None

    async def close_all(self):
        """Cierra ambos clientes HTTP."""
        await self.close()
        self.close_sync()
