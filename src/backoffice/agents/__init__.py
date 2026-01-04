# backoffice/agents/__init__.py

"""
Módulo de agentes del backoffice.

Exporta las clases base y el registro de agentes CrewAI.
"""

from .registry import (
    AGENT_REGISTRY,
    get_agent_class,
    list_available_agents,
    list_crewai_agents,
    is_crewai_available,
)

# Agentes reales con CrewAI
# Puede fallar si CrewAI no está instalado o hay problemas de dependencias
try:
    from .base_real import AgentReal
    from .clasificador_expediente import ClasificadorExpediente
    from .redactor_situacion import RedactorSituacion
    from .mcp_tool_wrapper import MCPTool, MCPToolFactory
except (ImportError, RuntimeError):
    # RuntimeError captura problemas como SQLite incompatible
    AgentReal = None
    ClasificadorExpediente = None
    RedactorSituacion = None
    MCPTool = None
    MCPToolFactory = None


__all__ = [
    # Base classes
    "AgentReal",
    # Registry
    "AGENT_REGISTRY",
    "get_agent_class",
    "list_available_agents",
    "list_crewai_agents",
    "is_crewai_available",
    # CrewAI agents
    "ClasificadorExpediente",
    "RedactorSituacion",
    # Tool wrapper
    "MCPTool",
    "MCPToolFactory",
]
