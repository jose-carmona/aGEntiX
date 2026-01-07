"""
Módulo MCP para documentación de tipos de expediente.

Expone herramientas y recursos para acceder a normativa,
instrucciones de tramitación y plantillas de documentos
asociados a cada tipo de expediente.
"""

from .tools import list_tools, call_tool
from .resources import list_resources, get_resource

__all__ = [
    "list_tools",
    "call_tool",
    "list_resources",
    "get_resource",
]
