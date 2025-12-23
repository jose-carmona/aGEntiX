# backoffice/config/__init__.py

"""
Módulo de configuración del backoffice.

Exporta los modelos y loaders de configuración.
"""

from .models import MCPAuthConfig, MCPServerConfig, MCPServersConfig
from .agent_config_loader import (
    AgentDefinition,
    AgentCatalog,
    AgentConfigLoader,
    get_agent_loader,
    reset_agent_loader
)

__all__ = [
    # MCP Config
    "MCPAuthConfig",
    "MCPServerConfig",
    "MCPServersConfig",
    # Agent Config
    "AgentDefinition",
    "AgentCatalog",
    "AgentConfigLoader",
    "get_agent_loader",
    "reset_agent_loader",
]
