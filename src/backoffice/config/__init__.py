# backoffice/config/__init__.py

"""
Módulo de configuración del backoffice.

Exporta los modelos y loaders de configuración.
"""

from .models import MCPAuthConfig, MCPServerConfig, MCPServersConfig
from .agent_config_loader import (
    # Modelos de configuración
    LLMConfig,
    CrewAIAgentConfig,
    CrewAITaskConfig,
    AgentDefinition,
    AgentCatalog,
    # Loader
    AgentConfigLoader,
    get_agent_loader,
    reset_agent_loader,
)

__all__ = [
    # MCP Config
    "MCPAuthConfig",
    "MCPServerConfig",
    "MCPServersConfig",
    # Agent Config - Models
    "LLMConfig",
    "CrewAIAgentConfig",
    "CrewAITaskConfig",
    "AgentDefinition",
    "AgentCatalog",
    # Agent Config - Loader
    "AgentConfigLoader",
    "get_agent_loader",
    "reset_agent_loader",
]
