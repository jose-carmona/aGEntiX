# backoffice/config/agent_config_loader.py

"""
Cargador de configuración de agentes desde YAML.

Proporciona acceso centralizado a las definiciones de agentes,
soportando tanto agentes mock (Paso 1) como agentes reales CrewAI (Paso 6).
"""

from pathlib import Path
from typing import Dict, List, Optional
import yaml
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Modelos de configuración para CrewAI (Paso 6)
# =============================================================================

class LLMConfig(BaseModel):
    """Configuración del modelo LLM para agentes CrewAI."""
    provider: str = Field("anthropic", description="Proveedor del LLM")
    model: str = Field("claude-3-5-sonnet-20241022", description="Modelo a usar")
    max_tokens: int = Field(4096, description="Máximo de tokens")
    temperature: float = Field(0.1, description="Temperatura del modelo")


class CrewAIAgentConfig(BaseModel):
    """Configuración específica del agente CrewAI."""
    role: str = Field(..., description="Rol del agente")
    goal: str = Field(..., description="Objetivo del agente")
    backstory: str = Field(..., description="Historia/contexto del agente")
    verbose: bool = Field(True, description="Modo verbose")
    allow_delegation: bool = Field(False, description="Permitir delegación")


class CrewAITaskConfig(BaseModel):
    """Configuración de la tarea CrewAI."""
    description: str = Field(..., description="Descripción de la tarea")
    expected_output: str = Field(..., description="Output esperado")


# =============================================================================
# Modelo principal de definición de agente
# =============================================================================

class AgentDefinition(BaseModel):
    """
    Definición completa de un agente desde YAML.

    Soporta tanto agentes mock como agentes CrewAI.
    """
    name: str = Field(..., description="Nombre del agente")
    type: str = Field("mock", description="Tipo: mock | crewai | langgraph")
    enabled: bool = Field(True, description="Si el agente está habilitado")
    description: str = Field("", description="Descripción del agente")
    model: str = Field("claude-3-5-sonnet-20241022", description="Modelo de LLM")
    system_prompt: str = Field("", description="Prompt del sistema (mock)")
    tools: List[str] = Field(default_factory=list, description="Herramientas MCP")
    required_permissions: List[str] = Field(
        default_factory=list,
        description="Permisos requeridos en el JWT"
    )
    timeout_seconds: int = Field(300, description="Timeout de ejecución")

    # Campos específicos de CrewAI (Paso 6)
    llm: Optional[LLMConfig] = Field(None, description="Configuración LLM")
    crewai_agent: Optional[CrewAIAgentConfig] = Field(
        None,
        description="Configuración del agente CrewAI"
    )
    crewai_task: Optional[CrewAITaskConfig] = Field(
        None,
        description="Configuración de la tarea CrewAI"
    )

    @property
    def is_crewai(self) -> bool:
        """Indica si es un agente CrewAI."""
        return self.type == "crewai"

    @property
    def is_mock(self) -> bool:
        """Indica si es un agente mock."""
        return self.type == "mock"

    @property
    def mcp_tools(self) -> List[str]:
        """Alias para tools (compatibilidad con plan)."""
        return self.tools


class AgentCatalog(BaseModel):
    """Catálogo completo de agentes."""
    agents: Dict[str, AgentDefinition] = Field(
        default_factory=dict,
        description="Mapa de nombre -> definición de agente"
    )


# =============================================================================
# Loader principal
# =============================================================================

class AgentConfigLoader:
    """
    Carga y gestiona configuración de agentes desde YAML.

    Uso:
        loader = AgentConfigLoader("path/to/agents.yaml")
        agent_def = loader.get("ValidadorDocumental")
        all_agents = loader.list_agents()

        # Filtrar por tipo
        crewai_agents = loader.list_by_type("crewai")
        mock_agents = loader.list_by_type("mock")
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa el loader con la ruta al archivo YAML.

        Args:
            config_path: Ruta al archivo agents.yaml.
                        Si es None, usa el path por defecto.
        """
        if config_path is None:
            config_path = str(Path(__file__).parent / "agents.yaml")

        self._config_path = Path(config_path)
        self._catalog: Optional[AgentCatalog] = None
        self._load()

    def _load(self) -> None:
        """Carga el archivo YAML y parsea las definiciones."""
        if not self._config_path.exists():
            logger.warning(
                f"Archivo de configuración no encontrado: {self._config_path}"
            )
            self._catalog = AgentCatalog()
            return

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "agents" not in data:
                logger.warning(
                    f"Archivo YAML sin sección 'agents': {self._config_path}"
                )
                self._catalog = AgentCatalog()
                return

            agents: Dict[str, AgentDefinition] = {}
            for name, config in data["agents"].items():
                agents[name] = self._parse_agent(name, config)

            self._catalog = AgentCatalog(agents=agents)
            logger.info(
                f"Cargados {len(agents)} agentes desde {self._config_path}"
            )

        except yaml.YAMLError as e:
            logger.error(f"Error parseando YAML: {e}")
            raise ValueError(f"Error en archivo de configuración: {e}")
        except Exception as e:
            logger.error(f"Error cargando configuración de agentes: {e}")
            raise

    def _parse_agent(self, name: str, config: Dict) -> AgentDefinition:
        """
        Parsea la configuración de un agente.

        Soporta tanto formato mock como CrewAI.
        """
        # Parsear configuración LLM si existe
        llm_config = None
        if "llm" in config:
            llm_config = LLMConfig(**config["llm"])

        # Parsear configuración CrewAI agent si existe
        crewai_agent_config = None
        if "crewai_agent" in config:
            crewai_agent_config = CrewAIAgentConfig(**config["crewai_agent"])

        # Parsear configuración CrewAI task si existe
        crewai_task_config = None
        if "crewai_task" in config:
            crewai_task_config = CrewAITaskConfig(**config["crewai_task"])

        return AgentDefinition(
            name=name,
            type=config.get("type", "mock"),
            enabled=config.get("enabled", True),
            description=config.get("description", ""),
            model=config.get("model", "claude-3-5-sonnet-20241022"),
            system_prompt=config.get("system_prompt", ""),
            tools=config.get("tools", []),
            required_permissions=config.get("required_permissions", []),
            timeout_seconds=config.get("timeout_seconds", 300),
            llm=llm_config,
            crewai_agent=crewai_agent_config,
            crewai_task=crewai_task_config,
        )

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

    def get_agent(self, agent_name: str) -> AgentDefinition:
        """Alias para get() - compatibilidad con plan."""
        return self.get(agent_name)

    def list_agents(self, only_enabled: bool = False) -> List[AgentDefinition]:
        """
        Lista todas las definiciones de agentes disponibles.

        Args:
            only_enabled: Si True, solo retorna agentes habilitados

        Returns:
            Lista de AgentDefinition
        """
        if not self._catalog:
            return []
        agents = list(self._catalog.agents.values())
        if only_enabled:
            agents = [a for a in agents if a.enabled]
        return agents

    def list_agent_names(self, only_enabled: bool = False) -> List[str]:
        """
        Lista los nombres de agentes disponibles.

        Args:
            only_enabled: Si True, solo retorna agentes habilitados

        Returns:
            Lista de nombres de agentes
        """
        if not self._catalog:
            return []
        if only_enabled:
            return [
                name for name, agent in self._catalog.agents.items()
                if agent.enabled
            ]
        return list(self._catalog.agents.keys())

    def list_by_type(self, agent_type: str, only_enabled: bool = True) -> List[str]:
        """
        Lista agentes de un tipo específico.

        Args:
            agent_type: Tipo de agente (mock, crewai, langgraph)
            only_enabled: Si True, solo retorna agentes habilitados

        Returns:
            Lista de nombres de agentes del tipo especificado
        """
        if not self._catalog:
            return []
        return [
            name for name, agent in self._catalog.agents.items()
            if agent.type == agent_type and (not only_enabled or agent.enabled)
        ]

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
        """Recarga la configuración desde el archivo."""
        self._catalog = None
        self._load()


# =============================================================================
# Singleton y funciones de utilidad
# =============================================================================

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
            default_path = Path(__file__).parent / "agents.yaml"
            config_path = str(default_path)
        _agent_loader = AgentConfigLoader(config_path)

    return _agent_loader


def reset_agent_loader() -> None:
    """Reinicia el loader (útil para tests)."""
    global _agent_loader
    _agent_loader = None
