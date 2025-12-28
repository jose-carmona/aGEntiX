# backoffice/agents/registry.py

"""
Registro de agentes disponibles.

Proporciona acceso centralizado a todas las clases de agentes,
tanto mock (Paso 1) como reales con CrewAI (Paso 6).
"""

from typing import Dict, Type, Union

# Agentes mock (Paso 1)
from .base import AgentMock
from .validador_documental import ValidadorDocumental
from .analizador_subvencion import AnalizadorSubvencion
from .generador_informe import GeneradorInforme

# Agentes reales con CrewAI (Paso 6)
# Importación condicional para evitar errores si CrewAI no está instalado
# o si hay problemas con dependencias (SQLite, ChromaDB, etc.)
try:
    from .base_real import AgentReal
    from .clasificador_expediente import ClasificadorExpediente
    CREWAI_AGENTS_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    # RuntimeError captura problemas como SQLite incompatible
    AgentReal = None
    ClasificadorExpediente = None
    CREWAI_AGENTS_AVAILABLE = False


# Tipo unificado para agentes mock y reales
AgentType = Union[Type[AgentMock], Type["AgentReal"]] if AgentReal else Type[AgentMock]


# Registro de agentes disponibles
AGENT_REGISTRY: Dict[str, AgentType] = {
    # Agentes mock existentes (Paso 1)
    "ValidadorDocumental": ValidadorDocumental,
    "AnalizadorSubvencion": AnalizadorSubvencion,
    "GeneradorInforme": GeneradorInforme,
}

# Añadir agentes CrewAI si están disponibles
if CREWAI_AGENTS_AVAILABLE and ClasificadorExpediente is not None:
    AGENT_REGISTRY["ClasificadorExpediente"] = ClasificadorExpediente


def get_agent_class(agent_name: str) -> AgentType:
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


def list_mock_agents() -> list[str]:
    """
    Lista los nombres de agentes mock.

    Returns:
        Lista de nombres de agentes mock
    """
    return ["ValidadorDocumental", "AnalizadorSubvencion", "GeneradorInforme"]


def list_crewai_agents() -> list[str]:
    """
    Lista los nombres de agentes CrewAI.

    Returns:
        Lista de nombres de agentes CrewAI (vacía si CrewAI no está instalado)
    """
    if CREWAI_AGENTS_AVAILABLE:
        return ["ClasificadorExpediente"]
    return []


def is_crewai_available() -> bool:
    """
    Verifica si los agentes CrewAI están disponibles.

    Returns:
        True si CrewAI está instalado y los agentes disponibles
    """
    return CREWAI_AGENTS_AVAILABLE
