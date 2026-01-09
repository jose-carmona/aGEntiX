# backoffice/agents/registry.py

"""
Registro de agentes disponibles.

Proporciona acceso centralizado a todas las clases de agentes CrewAI.
"""

from typing import Dict, Type

# Agentes reales con CrewAI (Paso 6)
# Importación condicional para evitar errores si CrewAI no está instalado
# o si hay problemas con dependencias (SQLite, ChromaDB, etc.)
try:
    from .base_real import AgentReal
    from .clasificador_expediente import ClasificadorExpediente
    from .redactor_situacion import RedactorSituacion
    from .redactor_propuesta_resolucion import RedactorPropuestaResolucion
    CREWAI_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    # RuntimeError captura problemas como SQLite incompatible
    AgentReal = None
    ClasificadorExpediente = None
    RedactorSituacion = None
    RedactorPropuestaResolucion = None
    CREWAI_AVAILABLE = False


# Tipo para agentes CrewAI
AgentType = Type["AgentReal"] if AgentReal else type


# Registro de agentes disponibles
AGENT_REGISTRY: Dict[str, AgentType] = {}

# Añadir agentes CrewAI si están disponibles
if CREWAI_AVAILABLE:
    if ClasificadorExpediente is not None:
        AGENT_REGISTRY["ClasificadorExpediente"] = ClasificadorExpediente
    if RedactorSituacion is not None:
        AGENT_REGISTRY["RedactorSituacion"] = RedactorSituacion
    if RedactorPropuestaResolucion is not None:
        AGENT_REGISTRY["RedactorPropuestaResolucion"] = RedactorPropuestaResolucion


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


def list_crewai_agents() -> list[str]:
    """
    Lista los nombres de agentes CrewAI.

    Returns:
        Lista de nombres de agentes CrewAI (vacía si CrewAI no está instalado)
    """
    if CREWAI_AVAILABLE:
        return [
            "ClasificadorExpediente",
            "RedactorSituacion",
            "RedactorPropuestaResolucion"
        ]
    return []


def is_crewai_available() -> bool:
    """
    Verifica si los agentes CrewAI están disponibles.

    Returns:
        True si CrewAI está instalado y los agentes disponibles
    """
    return CREWAI_AVAILABLE
