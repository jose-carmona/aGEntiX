# backoffice/config/agent_config_loader.py

"""
Cargador de configuración de agentes desde YAML.

Proporciona acceso centralizado a las definiciones de agentes,
permitiendo que el BPMN solo necesite especificar el nombre del agente.
"""

from pathlib import Path
from typing import Dict, List, Optional
import yaml
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class AgentDefinition(BaseModel):
    """Definición completa de un agente desde YAML"""

    name: str = Field(..., description="Nombre del agente")
    description: str = Field(..., description="Descripción del agente")
    model: str = Field(..., description="Modelo de LLM a utilizar")
    system_prompt: str = Field(..., description="Prompt del sistema")
    tools: List[str] = Field(default_factory=list, description="Herramientas disponibles")
    required_permissions: List[str] = Field(
        default_factory=list,
        description="Permisos requeridos en el JWT"
    )
    timeout_seconds: int = Field(300, description="Timeout de ejecución")


class AgentCatalog(BaseModel):
    """Catálogo completo de agentes"""

    agents: Dict[str, AgentDefinition] = Field(
        default_factory=dict,
        description="Mapa de nombre -> definición de agente"
    )


class AgentConfigLoader:
    """
    Carga y gestiona configuración de agentes desde YAML.

    Uso:
        loader = AgentConfigLoader("path/to/agents.yaml")
        agent_def = loader.get("ValidadorDocumental")
        all_agents = loader.list_agents()
    """

    def __init__(self, config_path: str):
        """
        Inicializa el loader con la ruta al archivo YAML.

        Args:
            config_path: Ruta al archivo agents.yaml
        """
        self._config_path = Path(config_path)
        self._catalog: Optional[AgentCatalog] = None
        self._load()

    def _load(self) -> None:
        """Carga el archivo YAML y parsea las definiciones"""
        if not self._config_path.exists():
            logger.warning(f"Archivo de configuración no encontrado: {self._config_path}")
            self._catalog = AgentCatalog()
            return

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "agents" not in data:
                logger.warning(f"Archivo YAML sin sección 'agents': {self._config_path}")
                self._catalog = AgentCatalog()
                return

            agents: Dict[str, AgentDefinition] = {}
            for name, config in data["agents"].items():
                agents[name] = AgentDefinition(
                    name=name,
                    description=config.get("description", ""),
                    model=config.get("model", "claude-3-5-sonnet-20241022"),
                    system_prompt=config.get("system_prompt", ""),
                    tools=config.get("tools", []),
                    required_permissions=config.get("required_permissions", []),
                    timeout_seconds=config.get("timeout_seconds", 300)
                )

            self._catalog = AgentCatalog(agents=agents)
            logger.info(f"Cargados {len(agents)} agentes desde {self._config_path}")

        except yaml.YAMLError as e:
            logger.error(f"Error parseando YAML: {e}")
            raise ValueError(f"Error en archivo de configuración: {e}")
        except Exception as e:
            logger.error(f"Error cargando configuración de agentes: {e}")
            raise

    def get(self, agent_name: str) -> AgentDefinition:
        """
        Obtiene la definición de un agente por nombre.

        Args:
            agent_name: Nombre del agente (ej: "ValidadorDocumental")

        Returns:
            AgentDefinition con la configuración completa

        Raises:
            KeyError: Si el agente no existe
        """
        if not self._catalog or agent_name not in self._catalog.agents:
            available = self.list_agent_names()
            raise KeyError(
                f"Agente '{agent_name}' no encontrado. "
                f"Agentes disponibles: {available}"
            )

        return self._catalog.agents[agent_name]

    def list_agents(self) -> List[AgentDefinition]:
        """
        Lista todas las definiciones de agentes disponibles.

        Returns:
            Lista de AgentDefinition
        """
        if not self._catalog:
            return []
        return list(self._catalog.agents.values())

    def list_agent_names(self) -> List[str]:
        """
        Lista los nombres de agentes disponibles.

        Returns:
            Lista de nombres de agentes
        """
        if not self._catalog:
            return []
        return list(self._catalog.agents.keys())

    def exists(self, agent_name: str) -> bool:
        """
        Verifica si un agente existe.

        Args:
            agent_name: Nombre del agente

        Returns:
            True si existe, False si no
        """
        if not self._catalog:
            return False
        return agent_name in self._catalog.agents

    def reload(self) -> None:
        """Recarga la configuración desde el archivo"""
        self._load()


# Instancia global (singleton) para uso en la aplicación
_agent_loader: Optional[AgentConfigLoader] = None


def get_agent_loader(config_path: Optional[str] = None) -> AgentConfigLoader:
    """
    Obtiene el loader de agentes (singleton).

    Args:
        config_path: Ruta al archivo YAML (solo necesario en primera llamada)

    Returns:
        AgentConfigLoader configurado
    """
    global _agent_loader

    if _agent_loader is None:
        if config_path is None:
            # Ruta por defecto
            default_path = Path(__file__).parent / "agents.yaml"
            config_path = str(default_path)
        _agent_loader = AgentConfigLoader(config_path)

    return _agent_loader


def reset_agent_loader() -> None:
    """Reinicia el loader (útil para tests)"""
    global _agent_loader
    _agent_loader = None
