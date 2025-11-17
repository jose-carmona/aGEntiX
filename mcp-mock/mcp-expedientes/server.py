"""
Servidor MCP core - Lógica agnóstica del transporte.

Este módulo implementa el servidor MCP que puede usarse con cualquier
transporte (stdio, HTTP/SSE, etc.). Toda la lógica de negocio está aquí,
independiente de cómo se comunique el servidor.
"""

import os
import logging
from typing import Optional
from mcp.server import Server
from mcp import types

# Importar handlers
from auth import validate_jwt, AuthError
from resources import list_resources, get_resource
from tools import list_tools, call_tool

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPContext:
    """
    Contexto compartido para el servidor MCP.
    Almacena información sobre la petición actual, incluyendo el token JWT.
    """
    def __init__(self):
        self.token: Optional[str] = None
        self.server_id: str = "agentix-mcp-expedientes"

    def set_token(self, token: str):
        """Establece el token JWT para la petición actual"""
        self.token = token

    def get_token(self) -> Optional[str]:
        """Obtiene el token JWT de la petición actual"""
        # Prioridad: contexto > variable de entorno
        if self.token:
            return self.token
        return os.environ.get("MCP_JWT_TOKEN")


def create_server(name: str = "gex-expedientes-mock") -> tuple[Server, MCPContext]:
    """
    Crea el servidor MCP core que puede usarse con cualquier transporte.

    Esta función encapsula toda la lógica del servidor independientemente
    de cómo se comunique (stdio, HTTP, etc.)

    Args:
        name: Nombre del servidor MCP

    Returns:
        Tupla con (servidor MCP, contexto)
    """
    app = Server(name)
    context = MCPContext()

    logger.info(f"Creando servidor MCP: {name}")

    @app.list_resources()
    async def handle_list_resources() -> list[types.Resource]:
        """
        Handler para listar resources disponibles.

        Valida el token JWT antes de listar los resources.
        """
        logger.info("Petición: list_resources")

        try:
            token = context.get_token()
            await validate_jwt(token, server_id=context.server_id)

            resources = await list_resources()
            logger.info(f"Resources listados: {len(resources)}")

            return resources

        except AuthError as e:
            logger.error(f"Error de autenticación en list_resources: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado en list_resources: {str(e)}")
            raise

    @app.read_resource()
    async def handle_read_resource(uri: str) -> str:
        """
        Handler para leer un resource específico.

        Valida el token JWT y verifica permisos antes de leer.
        """
        logger.info(f"Petición: read_resource - URI: {uri}")

        try:
            token = context.get_token()
            await validate_jwt(
                token,
                resource_uri=uri,
                server_id=context.server_id
            )

            content = await get_resource(uri)
            logger.info(f"Resource leído: {uri}")

            return content

        except AuthError as e:
            logger.error(f"Error de autenticación en read_resource: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado en read_resource: {str(e)}")
            raise

    @app.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """
        Handler para listar tools disponibles.

        Valida el token JWT antes de listar las tools.
        """
        logger.info("Petición: list_tools")

        try:
            token = context.get_token()
            await validate_jwt(token, server_id=context.server_id)

            tools = await list_tools()
            logger.info(f"Tools listadas: {len(tools)}")

            return tools

        except AuthError as e:
            logger.error(f"Error de autenticación en list_tools: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado en list_tools: {str(e)}")
            raise

    @app.call_tool()
    async def handle_call_tool(
        name: str,
        arguments: dict
    ) -> list[types.TextContent]:
        """
        Handler para ejecutar una tool.

        Valida el token JWT y verifica permisos antes de ejecutar.
        """
        logger.info(f"Petición: call_tool - Tool: {name}, Args: {arguments}")

        try:
            token = context.get_token()
            await validate_jwt(
                token,
                tool_name=name,
                tool_args=arguments,
                server_id=context.server_id
            )

            result = await call_tool(name, arguments)
            logger.info(f"Tool ejecutada: {name}")

            return result

        except AuthError as e:
            logger.error(f"Error de autenticación en call_tool: {e.message}")
            # Convertir AuthError a un formato que MCP pueda manejar
            return [
                types.TextContent(
                    type="text",
                    text=f"ERROR {e.status_code}: {e.message}"
                )
            ]
        except Exception as e:
            logger.error(f"Error inesperado en call_tool: {str(e)}")
            return [
                types.TextContent(
                    type="text",
                    text=f"ERROR 500: {str(e)}"
                )
            ]

    return app, context


def get_server_info() -> dict:
    """
    Obtiene información sobre el servidor.

    Returns:
        Diccionario con información del servidor
    """
    return {
        "name": "gex-expedientes-mock",
        "version": "1.0.0",
        "description": "Servidor MCP Mock para expedientes de GEX",
        "protocol_version": "1.0",
        "capabilities": {
            "resources": True,
            "tools": True,
            "prompts": False
        },
        "transport": {
            "stdio": True,
            "http_sse": True
        }
    }
