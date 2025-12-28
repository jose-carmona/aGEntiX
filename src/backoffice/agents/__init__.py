# backoffice/agents/__init__.py

"""
Módulo de agentes del backoffice.

Exporta las clases base y el registro de agentes.
"""

from .base import AgentMock
from .registry import (
    AGENT_REGISTRY,
    get_agent_class,
    list_available_agents,
    list_mock_agents,
    list_crewai_agents,
    is_crewai_available,
)

# Agentes mock
from .validador_documental import ValidadorDocumental
from .analizador_subvencion import AnalizadorSubvencion
from .generador_informe import GeneradorInforme

# Agentes reales (importación condicional)
# Puede fallar si CrewAI no está instalado o hay problemas de dependencias
try:
    from .base_real import AgentReal
    from .clasificador_expediente import ClasificadorExpediente
    from .mcp_tool_wrapper import MCPTool, MCPToolFactory
except (ImportError, RuntimeError):
    # RuntimeError captura problemas como SQLite incompatible
    AgentReal = None
    ClasificadorExpediente = None
    MCPTool = None
    MCPToolFactory = None


__all__ = [
    # Base classes
    "AgentMock",
    "AgentReal",
    # Registry
    "AGENT_REGISTRY",
    "get_agent_class",
    "list_available_agents",
    "list_mock_agents",
    "list_crewai_agents",
    "is_crewai_available",
    # Mock agents
    "ValidadorDocumental",
    "AnalizadorSubvencion",
    "GeneradorInforme",
    # CrewAI agents
    "ClasificadorExpediente",
    # Tool wrapper
    "MCPTool",
    "MCPToolFactory",
]
