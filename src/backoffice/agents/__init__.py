# backoffice/agents/__init__.py

"""
Módulo de agentes del backoffice.

Exporta las clases base y el registro de agentes CrewAI y LangGraph.
"""

from .registry import (
    AGENT_REGISTRY,
    get_agent_class,
    list_available_agents,
    list_crewai_agents,
    list_langgraph_agents,
    is_crewai_available,
    is_langgraph_available,
)

# Agentes reales con CrewAI
# Puede fallar si CrewAI no está instalado o hay problemas de dependencias
try:
    from .base_real import AgentCrewAI
    from .clasificador_expediente import ClasificadorExpediente
    from .redactor_situacion import RedactorSituacion
    from .mcp_tool_wrapper import MCPTool, MCPToolFactory
except (ImportError, RuntimeError):
    # RuntimeError captura problemas como SQLite incompatible
    AgentCrewAI = None
    ClasificadorExpediente = None
    RedactorSituacion = None
    MCPTool = None
    MCPToolFactory = None

# Agentes reales con LangGraph (Paso 11)
try:
    from .base_langgraph import AgentLangGraph
    from .redactor_resolucion import RedactorResolucion
except (ImportError, RuntimeError):
    AgentLangGraph = None
    RedactorResolucion = None


__all__ = [
    # Base classes
    "AgentCrewAI",
    "AgentLangGraph",
    # Registry
    "AGENT_REGISTRY",
    "get_agent_class",
    "list_available_agents",
    "list_crewai_agents",
    "list_langgraph_agents",
    "is_crewai_available",
    "is_langgraph_available",
    # CrewAI agents
    "ClasificadorExpediente",
    "RedactorSituacion",
    # LangGraph agents
    "RedactorResolucion",
    # Tool wrapper
    "MCPTool",
    "MCPToolFactory",
]
