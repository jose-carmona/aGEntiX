# backoffice/agents/base_real.py

"""
Clase base para agentes reales usando CrewAI.

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
from ..logging.crewai_log_processor import create_crewai_log_file, process_crewai_logs
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


class AgentCrewAI(ABC):
    """
    Clase base para agentes reales con CrewAI.

    Implementa la interfaz requerida por AgentExecutor.

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
        config: Optional[AgentDefinition] = None,
        additional_goal: Optional[str] = None
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
            additional_goal: Objetivo adicional opcional que se añade al goal del agente
        """
        self.expediente_id = expediente_id
        self.tarea_id = tarea_id
        self.run_id = run_id
        self.mcp_registry = mcp_registry
        self.logger = logger
        self.additional_goal = additional_goal or ""
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
            temperature=llm_config.temperature,
            # Rate limiting - reintentos automáticos para errores 429
            num_retries=llm_config.num_retries,
            timeout=llm_config.request_timeout
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
            run_id=self.run_id,
            additional_goal=self.additional_goal
        )

    def log(
        self,
        mensaje: str,
        nivel: str = "INFO",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Registra un mensaje en el log incluyendo automáticamente el nombre del agente.

        Args:
            mensaje: Mensaje a logear
            nivel: Nivel de log (INFO, WARNING, ERROR)
            metadata: Metadata adicional (se fusiona con agent)
        """
        # Crear metadata con el nombre del agente
        agent_metadata = {"agent": self.config.name}
        if metadata:
            agent_metadata.update(metadata)

        self.logger.log(mensaje, nivel=nivel, metadata=agent_metadata)

    def log_error(self, mensaje: str, metadata: Optional[Dict[str, Any]] = None):
        """Registra un mensaje de error con el nombre del agente."""
        self.log(mensaje, nivel="ERROR", metadata=metadata)

    def log_warning(self, mensaje: str, metadata: Optional[Dict[str, Any]] = None):
        """Registra un mensaje de advertencia con el nombre del agente."""
        self.log(mensaje, nivel="WARNING", metadata=metadata)

    async def execute(self) -> Dict[str, Any]:
        """
        Ejecuta el agente usando CrewAI con acceso a MCP.

        El agente usará las herramientas MCP configuradas para
        acceder a los datos del expediente.

        Returns:
            Dict con 'completado', 'mensaje', 'datos_actualizados'
        """
        self.log(
            f"Iniciando agente CrewAI '{self.config.name}' "
            f"para expediente {self.expediente_id}"
        )
        self.log(f"Herramientas MCP disponibles: {self.config.mcp_tools}")

        # Crear archivo temporal para capturar logs de CrewAI
        crewai_log_file = create_crewai_log_file(self.run_id)

        try:
            # Verificar configuración CrewAI
            if not self.config.crewai_agent:
                raise ValueError("Configuración 'crewai_agent' no encontrada")
            if not self.config.crewai_task:
                raise ValueError("Configuración 'crewai_task' no encontrada")

            # Crear agente CrewAI con configuración YAML
            agent_cfg = self.config.crewai_agent
            agent_kwargs = {
                "role": agent_cfg.role,
                "goal": self._format_template(agent_cfg.goal),
                "backstory": agent_cfg.backstory,
                "llm": self.llm,
                "tools": self.mcp_tools,
                "verbose": agent_cfg.verbose,
                "allow_delegation": agent_cfg.allow_delegation,
                # FAIL-FAST: No reintentar en caso de error
                "max_retry_limit": 0,
                # FAIL-FAST: Fallar si el contexto se excede (no truncar)
                "respect_context_window": False,
            }
            # Rate limiting - max requests por minuto
            if agent_cfg.max_rpm is not None:
                agent_kwargs["max_rpm"] = agent_cfg.max_rpm
            # Limitar iteraciones si está configurado
            if hasattr(agent_cfg, 'max_iter') and agent_cfg.max_iter is not None:
                agent_kwargs["max_iter"] = agent_cfg.max_iter

            agent = Agent(**agent_kwargs)

            # Crear tarea con descripción formateada
            task_cfg = self.config.crewai_task
            task = Task(
                description=self._format_template(task_cfg.description),
                expected_output=task_cfg.expected_output,
                agent=agent
            )

            # Crear y ejecutar crew con captura de logs
            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=True,
                output_log_file=str(crewai_log_file)
            )

            # Ejecutar (CrewAI es síncrono, lo envolvemos)
            self.log("Ejecutando crew...")

            # Usar run_in_executor para no bloquear el event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, crew.kickoff)

            self.log("Agente completado exitosamente")

            # Procesar logs de CrewAI (redacción PII automática)
            entries = process_crewai_logs(
                crewai_log_file, self.logger, delete_after=False
            )
            self.log(f"Procesadas {entries} entradas de logs de CrewAI")

            # Intentar parsear resultado como JSON
            resultado_parseado = self._parse_result(str(result))

            return {
                "completado": True,
                "mensaje": str(result),
                "datos_actualizados": resultado_parseado
            }

        except Exception as e:
            # Procesar logs incluso en caso de error
            process_crewai_logs(crewai_log_file, self.logger, delete_after=False)
            # FAIL-FAST: Loguear y propagar error para detener ejecución
            error_msg = f"Error en agente CrewAI: {str(e)}"
            self.log_error(error_msg)
            raise RuntimeError(error_msg) from e

        finally:
            # Asegurar limpieza del archivo temporal
            if crewai_log_file.exists():
                try:
                    crewai_log_file.unlink()
                except OSError:
                    pass

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
            self.log(f"Herramienta MCP usada: {tool_name}", metadata={"tool": tool_name})

    def get_tools_used(self) -> List[str]:
        """
        Retorna lista de herramientas usadas.

        Returns:
            Copia de la lista de herramientas usadas
        """
        return self._tools_used.copy()
