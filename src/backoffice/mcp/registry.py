# backoffice/mcp/registry.py

"""
Registro de clientes MCP con routing automático.

Provee una API pública completa para evitar accesos a atributos privados:
- get_server_for_tool(): Obtiene el servidor para una tool
- get_tool_names(): Lista de tools disponibles
- is_tool_available(): Verifica si una tool existe
- is_initialized: Estado de inicialización
- list_tools_sync(): Discovery síncrono de tools
"""

from typing import Dict, List, Any, Optional
from .client import MCPClient
from .exceptions import MCPError, MCPToolError
from ..config.models import MCPServersConfig
import asyncio
import logging

logger = logging.getLogger(__name__)


class MCPClientRegistry:
    """
    Registro de clientes MCP con routing automático.

    Permite arquitectura plug-and-play: añadir MCPs mediante configuración.
    """

    def __init__(self, config: MCPServersConfig, token: str):
        """
        Inicializa el registro de clientes MCP.

        Args:
            config: Configuración de servidores MCP
            token: Token JWT con audiencias para los MCPs
        """
        self.config = config
        self.token = token

        # MCPClient por ID de servidor
        self._clients: Dict[str, MCPClient] = {}

        # Cache: tool_name → server_id
        self._tool_routing: Dict[str, str] = {}

        # Flag de inicialización
        self._initialized = False

    async def initialize(self):
        """
        Inicializa clientes MCP para servidores habilitados y descubre tools.

        En Paso 1: solo crea cliente para MCP Expedientes.
        En futuro: creará clientes para todos los MCPs con enabled=true.
        """
        if not self._initialized:
            # 1. Crear cliente solo para MCPs habilitados
            enabled_servers = self.config.get_enabled_servers()

            for server_config in enabled_servers:
                client = MCPClient(
                    server_config=server_config,
                    token=self.token
                )
                self._clients[server_config.id] = client

            # 2. Descubrir tools de cada MCP (en paralelo)
            tasks = [
                self._discover_tools(server_id)
                for server_id in self._clients.keys()
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

            self._initialized = True

    async def _discover_tools(self, server_id: str):
        """Descubre las tools disponibles en un servidor MCP."""
        client = self._clients[server_id]

        try:
            tools_response = await client.list_tools()
            tools = tools_response.get("tools", [])
            tool_names = [tool["name"] for tool in tools]

            # Actualizar routing: cada tool → su servidor
            for tool_name in tool_names:
                self._tool_routing[tool_name] = server_id

        except Exception as e:
            # No fallar si un MCP no responde en discovery
            # El sistema seguirá funcionando con los MCPs disponibles
            logger.warning(f"No se pudieron descubrir tools de MCP '{server_id}': {e}")

    def _get_client_for_tool(self, tool_name: str) -> "MCPClient":
        """
        Obtiene el cliente MCP para una tool específica.

        Args:
            tool_name: Nombre de la tool

        Returns:
            Cliente MCP correspondiente

        Raises:
            MCPToolError: Si la tool no se encuentra
        """
        server_id = self._tool_routing.get(tool_name)

        if not server_id:
            available_tools = list(self._tool_routing.keys())
            raise MCPToolError(
                codigo="MCP_TOOL_NOT_FOUND",
                mensaje=f"Tool '{tool_name}' no encontrada en ningún servidor MCP configurado",
                detalle=f"Tools disponibles: {available_tools}"
            )

        return self._clients[server_id]

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta una tool con routing automático al MCP correcto (async).

        Args:
            tool_name: Nombre de la tool
            arguments: Argumentos de la tool

        Returns:
            Resultado de la tool

        Raises:
            MCPToolError: Si la tool no se encuentra
        """
        if not self._initialized:
            await self.initialize()

        client = self._get_client_for_tool(tool_name)
        return await client.call_tool(tool_name, arguments)

    def call_tool_sync(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta una tool con routing automático (sync).

        Versión síncrona para uso desde CrewAI y otros contextos no-async.
        NOTA: Requiere que initialize() haya sido llamado previamente.

        Args:
            tool_name: Nombre de la tool
            arguments: Argumentos de la tool

        Returns:
            Resultado de la tool

        Raises:
            MCPToolError: Si la tool no se encuentra
            RuntimeError: Si el registry no ha sido inicializado
        """
        if not self._initialized:
            raise RuntimeError(
                "MCPClientRegistry no inicializado. "
                "Llama a 'await registry.initialize()' antes de usar call_tool_sync()."
            )

        client = self._get_client_for_tool(tool_name)
        return client.call_tool_sync(tool_name, arguments)

    def get_available_tools(self) -> Dict[str, str]:
        """
        Retorna mapping de tools disponibles por servidor.

        Returns:
            Diccionario {tool_name: server_id}
        """
        return self._tool_routing.copy()

    def get_enabled_server_ids(self) -> List[str]:
        """
        Retorna lista de IDs de servidores MCP habilitados.

        Returns:
            Lista de IDs de servidores
        """
        return list(self._clients.keys())

    # ========== FASE 2: MÉTODOS PÚBLICOS ADICIONALES ==========

    @property
    def is_initialized(self) -> bool:
        """
        Indica si el registry ha sido inicializado.

        Returns:
            True si initialize() fue llamado exitosamente
        """
        return self._initialized

    def get_server_for_tool(self, tool_name: str) -> Optional[str]:
        """
        Retorna el server_id para una tool específica.

        Args:
            tool_name: Nombre de la tool

        Returns:
            ID del servidor que provee la tool, o None si no existe
        """
        return self._tool_routing.get(tool_name)

    def get_tool_names(self) -> List[str]:
        """
        Retorna lista de nombres de tools disponibles.

        Returns:
            Lista de nombres de tools
        """
        return list(self._tool_routing.keys())

    def is_tool_available(self, tool_name: str) -> bool:
        """
        Verifica si una tool está disponible.

        Args:
            tool_name: Nombre de la tool

        Returns:
            True si la tool existe en algún servidor MCP
        """
        return tool_name in self._tool_routing

    def list_tools_sync(self, server_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Lista tools disponibles de forma síncrona.

        Útil para discovery en contextos no-async (CrewAI).
        NOTA: Requiere que initialize() haya sido llamado.

        Args:
            server_id: ID del servidor (opcional). Si no se especifica,
                      retorna tools de todos los servidores.

        Returns:
            Dict con lista de tools y sus metadatos

        Raises:
            RuntimeError: Si el registry no está inicializado
            MCPToolError: Si el servidor no existe
        """
        if not self._initialized:
            raise RuntimeError(
                "MCPClientRegistry no inicializado. "
                "Llama a 'await registry.initialize()' antes de usar list_tools_sync()."
            )

        if server_id:
            if server_id not in self._clients:
                raise MCPToolError(
                    codigo="MCP_SERVER_NOT_FOUND",
                    mensaje=f"Servidor MCP '{server_id}' no encontrado",
                    detalle=f"Servidores disponibles: {list(self._clients.keys())}"
                )
            return self._clients[server_id].list_tools_sync()

        # Agregar tools de todos los servidores
        all_tools = []
        for client in self._clients.values():
            try:
                result = client.list_tools_sync()
                tools = result.get("tools", [])
                all_tools.extend(tools)
            except Exception as e:
                logger.warning(f"Error listando tools: {e}")

        return {"tools": all_tools}

    def get_server_config(self, server_id: str) -> Optional[Any]:
        """
        Obtiene la configuración de un servidor MCP.

        Args:
            server_id: ID del servidor

        Returns:
            Configuración del servidor o None si no existe
        """
        client = self._clients.get(server_id)
        if client:
            return client.server_config
        return None

    async def close(self):
        """Cierra todos los clientes HTTP async."""
        tasks = [client.close() for client in self._clients.values()]
        await asyncio.gather(*tasks)

    def close_sync(self):
        """Cierra todos los clientes HTTP sync."""
        for client in self._clients.values():
            client.close_sync()
