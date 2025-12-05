# backoffice/mcp/exceptions.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class MCPError(Exception):
    """Error base del cliente MCP"""
    codigo: str
    mensaje: str
    detalle: Optional[str] = None

    def __str__(self):
        return f"[{self.codigo}] {self.mensaje}"


@dataclass
class MCPConnectionError(MCPError):
    """
    Error de conexión con servidor MCP.

    Errores incluidos:
    - MCP_TIMEOUT: Timeout en la request
    - MCP_CONNECTION_ERROR: No se puede conectar
    - MCP_SERVER_UNAVAILABLE: Servidor retorna 502/503/504
    """
    pass


@dataclass
class MCPToolError(MCPError):
    """
    Error al ejecutar una tool MCP.

    Errores incluidos:
    - MCP_TOOL_ERROR: Error genérico en tool
    - MCP_TOOL_NOT_FOUND: Tool no existe (404)
    - MCP_RESOURCE_ERROR: Error al leer resource
    """
    pass


@dataclass
class MCPAuthError(MCPError):
    """
    Error de autenticación/autorización con MCP.

    Errores incluidos:
    - AUTH_INVALID_TOKEN: Token inválido (401)
    - AUTH_PERMISSION_DENIED: Permisos insuficientes (403)
    """
    pass
