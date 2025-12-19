# backoffice/agents/registry.py

from typing import Dict, Type
from .base import AgentMock
from .validador_documental import ValidadorDocumental
from .analizador_subvencion import AnalizadorSubvencion
from .generador_informe import GeneradorInforme


# Registro de agentes disponibles
AGENT_REGISTRY: Dict[str, Type[AgentMock]] = {
    "ValidadorDocumental": ValidadorDocumental,
    "AnalizadorSubvencion": AnalizadorSubvencion,
    "GeneradorInforme": GeneradorInforme
}


def get_agent_class(agent_name: str) -> Type[AgentMock]:
    """
    Obtiene la clase de agente por nombre.

    Args:
        agent_name: Nombre del agente

    Returns:
        Clase del agente

    Raises:
        KeyError: Si el agente no está registrado
    """
    if agent_name not in AGENT_REGISTRY:
        available = list(AGENT_REGISTRY.keys())
        raise KeyError(
            f"Agente '{agent_name}' no encontrado. Agentes disponibles: {available}"
        )

    return AGENT_REGISTRY[agent_name]


def list_available_agents() -> list[str]:
    """
    Lista los nombres de todos los agentes disponibles.

    Returns:
        Lista de nombres de agentes
    """
    return list(AGENT_REGISTRY.keys())
