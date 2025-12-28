# backoffice/agents/base_real.py

"""
Clase base para agentes reales usando CrewAI.

Mantiene compatibilidad con AgentMock mientras usa CrewAI internamente.
Los agentes acceden a datos del expediente mediante herramientas MCP.
"""

# Workaround para ChromaDB que requiere SQLite >= 3.35.0
# pysqlite3-binary incluye una versión compatible
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass  # Si no está instalado, usa el sqlite3 del sistema

import asyncio
import json
import re
from abc import ABC
from typing import Dict, Any, List, Optional

from ..mcp.registry import MCPClientRegistry
from ..logging.audit_logger import AuditLogger
from ..settings import get_settings
from ..config.agent_config_loader import AgentConfigLoader, AgentDefinition

# Importación condicional de CrewAI
try:
    from crewai import Agent, Task, Crew, LLM
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = None
    Task = None
    Crew = None
    LLM = None


class AgentReal(ABC):
    """
    Clase base para agentes reales con CrewAI.

    Implementa la misma interfaz que AgentMock para mantener
    compatibilidad con AgentExecutor.

    IMPORTANTE: Accede a datos del expediente mediante MCP tools,
    NO directamente. El LLM razona sobre los datos obtenidos.

    Atributos:
        expediente_id: ID del expediente a procesar
        tarea_id: ID de la tarea BPMN
        run_id: ID único de esta ejecución
        mcp_registry: Registry para acceso a herramientas MCP
        logger: Logger de auditoría
        config: Configuración del agente desde YAML
    """

    def __init__(
        self,
        expediente_id: str,
        tarea_id: str,
        run_id: str,
        mcp_registry: MCPClientRegistry,
        logger: AuditLogger,
        config: Optional[AgentDefinition] = None
    ):
        """
        Inicializa el agente real.

        Args:
            expediente_id: ID del expediente a procesar
            tarea_id: ID de la tarea BPMN
            run_id: ID único de esta ejecución
            mcp_registry: Registry de clientes MCP para routing
            logger: Logger de auditoría
            config: Configuración del agente (opcional, se carga del YAML si no se proporciona)
        """
        self.expediente_id = expediente_id
        self.tarea_id = tarea_id
        self.run_id = run_id
        self.mcp_registry = mcp_registry
        self.logger = logger
        self._tools_used: List[str] = []

        # Cargar configuración si no se proporciona
        if config is None:
            loader = AgentConfigLoader()
            config = loader.get(self.__class__.__name__)
        self.config = config

        # Verificar que es un agente CrewAI
        if not config.is_crewai:
            raise ValueError(
                f"Agente '{config.name}' no es de tipo 'crewai'. "
                f"Tipo actual: {config.type}"
            )

        # Verificar que CrewAI está disponible
        if not CREWAI_AVAILABLE:
            raise ImportError(
                "CrewAI no está instalado. Ejecuta: pip install crewai"
            )

        # Configurar LLM
        settings = get_settings()
        self.llm = self._create_llm(settings)

        # Crear tools MCP para CrewAI
        from .mcp_tool_wrapper import MCPToolFactory
        self.mcp_tools = MCPToolFactory.create_tools(
            tool_names=config.mcp_tools,
            mcp_registry=mcp_registry,
            logger=logger,
            tool_tracker=self._track_tool_use
        )

    def _create_llm(self, settings) -> "LLM":
        """
        Crea instancia del LLM según configuración.

        Args:
            settings: Configuración de la aplicación

        Returns:
            Instancia de LLM configurada
        """
        llm_config = self.config.llm

        if llm_config is None:
            raise ValueError(
                f"Agente '{self.config.name}' no tiene configuración LLM"
            )

        # Construir model string en formato LiteLLM
        model = f"{llm_config.provider}/{llm_config.model}"

        return LLM(
            model=model,
            api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=llm_config.max_tokens,
            temperature=llm_config.temperature
        )

    def _format_template(self, template: str) -> str:
        """
        Formatea un template con las variables del contexto.

        Args:
            template: String con placeholders {variable}

        Returns:
            String formateado
        """
        return template.format(
            expediente_id=self.expediente_id,
            tarea_id=self.tarea_id,
            run_id=self.run_id
        )

    async def execute(self) -> Dict[str, Any]:
        """
        Ejecuta el agente usando CrewAI con acceso a MCP.

        El agente usará las herramientas MCP configuradas para
        acceder a los datos del expediente.

        Returns:
            Dict con 'completado', 'mensaje', 'datos_actualizados'
        """
        self.logger.log(
            f"Iniciando agente CrewAI '{self.config.name}' "
            f"para expediente {self.expediente_id}"
        )
        self.logger.log(f"Herramientas MCP disponibles: {self.config.mcp_tools}")

        try:
            # Verificar configuración CrewAI
            if not self.config.crewai_agent:
                raise ValueError("Configuración 'crewai_agent' no encontrada")
            if not self.config.crewai_task:
                raise ValueError("Configuración 'crewai_task' no encontrada")

            # Crear agente CrewAI con configuración YAML
            agent_cfg = self.config.crewai_agent
            agent = Agent(
                role=agent_cfg.role,
                goal=self._format_template(agent_cfg.goal),
                backstory=agent_cfg.backstory,
                llm=self.llm,
                tools=self.mcp_tools,
                verbose=agent_cfg.verbose,
                allow_delegation=agent_cfg.allow_delegation
            )

            # Crear tarea con descripción formateada
            task_cfg = self.config.crewai_task
            task = Task(
                description=self._format_template(task_cfg.description),
                expected_output=task_cfg.expected_output,
                agent=agent
            )

            # Crear y ejecutar crew
            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=True
            )

            # Ejecutar (CrewAI es síncrono, lo envolvemos)
            self.logger.log("Ejecutando crew...")

            # Usar run_in_executor para no bloquear el event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, crew.kickoff)

            self.logger.log("Agente completado exitosamente")

            # Intentar parsear resultado como JSON
            resultado_parseado = self._parse_result(str(result))

            return {
                "completado": True,
                "mensaje": str(result),
                "datos_actualizados": resultado_parseado
            }

        except Exception as e:
            error_msg = f"Error en agente CrewAI: {str(e)}"
            self.logger.error(error_msg)
            return {
                "completado": False,
                "mensaje": error_msg,
                "datos_actualizados": {}
            }

    def _parse_result(self, result: str) -> Dict[str, Any]:
        """
        Intenta extraer JSON del resultado del agente.

        Args:
            result: Resultado del agente como string

        Returns:
            Dict con los datos parseados, o {} si no se puede parsear
        """
        try:
            # Buscar JSON en el resultado (puede estar envuelto en texto)
            json_match = re.search(r'\{[^{}]*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())

            # Intentar parsear todo el resultado
            return json.loads(result)

        except (json.JSONDecodeError, AttributeError):
            return {}

    def _track_tool_use(self, tool_name: str):
        """
        Registra el uso de una herramienta.

        Args:
            tool_name: Nombre de la herramienta usada
        """
        if tool_name not in self._tools_used:
            self._tools_used.append(tool_name)
            self.logger.log(f"Herramienta MCP usada: {tool_name}")

    def get_tools_used(self) -> List[str]:
        """
        Retorna lista de herramientas usadas.

        Returns:
            Copia de la lista de herramientas usadas
        """
        return self._tools_used.copy()
