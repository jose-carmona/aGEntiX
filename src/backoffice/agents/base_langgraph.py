# backoffice/agents/base_langgraph.py

"""
Clase base para agentes reales usando LangChain/LangGraph.

Los agentes acceden a datos del expediente mediante herramientas MCP.
"""

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

# Importación condicional de LangChain/LangGraph
try:
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_core.tools import StructuredTool
    from langgraph.prebuilt import create_react_agent
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    ChatAnthropic = None
    HumanMessage = None
    SystemMessage = None
    StructuredTool = None
    create_react_agent = None


class AgentLangGraph(ABC):
    """
    Clase base para agentes reales con LangGraph.

    Implementa la misma interfaz que AgentReal para compatibilidad.

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
        Inicializa el agente LangGraph.

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

        # Verificar que es un agente LangGraph
        if not config.is_langgraph:
            raise ValueError(
                f"Agente '{config.name}' no es de tipo 'langgraph'. "
                f"Tipo actual: {config.type}"
            )

        # Verificar que LangGraph está disponible
        if not LANGGRAPH_AVAILABLE:
            raise ImportError(
                "LangChain/LangGraph no está instalado. "
                "Ejecuta: pip install langchain langchain-anthropic langgraph"
            )

        # Configurar LLM
        settings = get_settings()
        self.llm = self._create_llm(settings)

        # Crear tools MCP para LangChain
        self.tools = self._create_langchain_tools()

    def _create_llm(self, settings) -> "ChatAnthropic":
        """
        Crea instancia del LLM Anthropic para LangChain.

        Args:
            settings: Configuración de la aplicación

        Returns:
            Instancia de ChatAnthropic configurada
        """
        llm_config = self.config.llm

        if llm_config is None:
            raise ValueError(
                f"Agente '{self.config.name}' no tiene configuración LLM"
            )

        return ChatAnthropic(
            model=llm_config.model,
            api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=llm_config.max_tokens,
            temperature=llm_config.temperature,
            timeout=float(llm_config.request_timeout),
            max_retries=llm_config.num_retries
        )

    def _create_langchain_tools(self) -> List["StructuredTool"]:
        """
        Crea herramientas LangChain desde las tools MCP configuradas.

        Returns:
            Lista de StructuredTool para LangChain
        """
        tools = []
        for tool_name in self.config.mcp_tools:
            tool = self._create_single_tool(tool_name)
            if tool:
                tools.append(tool)

        self.logger.log(f"Creadas {len(tools)} herramientas LangChain")
        return tools

    def _sanitize_tool_name(self, name: str) -> str:
        """
        Sanitiza el nombre de una herramienta para cumplir con el patrón
        de Anthropic: ^[a-zA-Z0-9_-]{1,128}$

        Args:
            name: Nombre original del tool

        Returns:
            Nombre sanitizado
        """
        # Reemplazar caracteres especiales comunes en español
        replacements = {
            'ñ': 'n',
            'Ñ': 'N',
            'á': 'a',
            'é': 'e',
            'í': 'i',
            'ó': 'o',
            'ú': 'u',
            'Á': 'A',
            'É': 'E',
            'Í': 'I',
            'Ó': 'O',
            'Ú': 'U',
            'ü': 'u',
            'Ü': 'U',
        }
        sanitized = name
        for original, replacement in replacements.items():
            sanitized = sanitized.replace(original, replacement)

        # Eliminar cualquier caracter que no sea alfanumérico, guión o guión bajo
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', sanitized)

        # Truncar a 128 caracteres
        return sanitized[:128]

    def _create_single_tool(self, tool_name: str) -> Optional["StructuredTool"]:
        """
        Crea una herramienta LangChain para un tool MCP.

        Args:
            tool_name: Nombre del tool MCP

        Returns:
            StructuredTool o None si no se pudo crear
        """
        # Obtener descripción del tool desde el registry
        description = self._get_tool_description(tool_name)

        # Sanitizar nombre para cumplir con patrón de Anthropic
        sanitized_name = self._sanitize_tool_name(tool_name)

        # Crear closure para capturar tool_name original (para llamar al MCP)
        def make_tool_func(mcp_name: str):
            """Crea función de ejecución para el tool."""
            def tool_func(**kwargs) -> str:
                # Extraer argumentos si vienen envueltos en 'kwargs'
                # (LangChain a veces envuelve los args así)
                if 'kwargs' in kwargs and len(kwargs) == 1:
                    actual_args = kwargs['kwargs']
                else:
                    actual_args = kwargs

                self._track_tool_use(mcp_name)
                self.logger.log(
                    f"[LangGraph] Ejecutando tool MCP: {mcp_name}",
                    metadata={"tool": mcp_name, "args": actual_args}
                )

                try:
                    # Llamar al MCP con el nombre original
                    result = self.mcp_registry.call_tool_sync(mcp_name, actual_args)
                    return json.dumps(result, ensure_ascii=False, default=str)
                except Exception as e:
                    error_msg = f"Error en tool {mcp_name}: {str(e)}"
                    self.logger.error(error_msg)
                    return json.dumps({"error": error_msg})

            return tool_func

        return StructuredTool.from_function(
            func=make_tool_func(tool_name),
            name=sanitized_name,
            description=description
        )

    def _get_tool_description(self, tool_name: str) -> str:
        """
        Obtiene la descripción de una herramienta MCP.

        Args:
            tool_name: Nombre del tool

        Returns:
            Descripción del tool
        """
        # Descripciones conocidas
        descriptions = {
            "consultar_expediente": "Consulta los datos completos de un expediente. Parámetro: expediente_id (string)",
            "listar_documentos": "Lista todos los documentos de un expediente. Parámetro: expediente_id (string)",
            "obtener_texto_documento": "Obtiene el texto de un documento. Parámetros: expediente_id (string), documento_id (string)",
            "crear_documento_desde_markdown": "Crea un documento desde Markdown. Parámetros: expediente_id, nombre, tipo, texto_markdown, metadatos (opcional)",
            "añadir_anotacion": "Añade una anotación al expediente. Parámetros: expediente_id (string), texto (string)",
            "actualizar_datos": "Actualiza un campo del expediente. Parámetros: expediente_id, campo, valor",
            "obtener_doc_documentacion": "Obtiene documentación de un tipo de expediente. Parámetros: tipo_expediente, tipo_documento",
            "listar_documentacion": "Lista la documentación disponible para un tipo de expediente. Parámetro: tipo_expediente",
        }

        return descriptions.get(
            tool_name,
            f"Herramienta MCP: {tool_name}"
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

    async def execute(self) -> Dict[str, Any]:
        """
        Ejecuta el agente usando LangGraph.

        El agente usará las herramientas MCP configuradas para
        acceder a los datos del expediente.

        Returns:
            Dict con 'completado', 'mensaje', 'datos_actualizados'
        """
        self.logger.log(
            f"Iniciando agente LangGraph '{self.config.name}' "
            f"para expediente {self.expediente_id}"
        )
        self.logger.log(f"Herramientas MCP disponibles: {self.config.mcp_tools}")

        # Crear archivo temporal para logs
        log_file = create_crewai_log_file(self.run_id)

        try:
            # Verificar configuración LangGraph
            if not self.config.langgraph_config:
                raise ValueError("Configuración 'langgraph_config' no encontrada")

            lg_cfg = self.config.langgraph_config

            # Crear el agente ReAct de LangGraph
            agent = create_react_agent(
                model=self.llm,
                tools=self.tools
            )

            # Preparar mensajes
            system_content = lg_cfg.system_prompt
            task_content = self._format_template(lg_cfg.task_prompt)

            # Ejecutar agente
            self.logger.log("Ejecutando agente LangGraph...")

            # LangGraph puede ser síncrono, envolver en executor
            loop = asyncio.get_event_loop()

            def run_agent():
                return agent.invoke({
                    "messages": [
                        ("system", system_content),
                        ("human", task_content)
                    ]
                })

            result = await loop.run_in_executor(None, run_agent)

            self.logger.log("Agente LangGraph completado exitosamente")

            # Extraer respuesta final
            messages = result.get("messages", [])
            final_message = ""
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, 'content'):
                    final_message = last_msg.content
                elif isinstance(last_msg, tuple):
                    final_message = last_msg[1] if len(last_msg) > 1 else str(last_msg)
                else:
                    final_message = str(last_msg)

            # Procesar logs
            entries = process_crewai_logs(log_file, self.logger, delete_after=False)
            self.logger.log(f"Procesadas {entries} entradas de logs")

            # Parsear resultado
            resultado_parseado = self._parse_result(final_message)

            return {
                "completado": True,
                "mensaje": final_message,
                "datos_actualizados": resultado_parseado
            }

        except Exception as e:
            process_crewai_logs(log_file, self.logger, delete_after=False)
            error_msg = f"Error en agente LangGraph: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e

        finally:
            if log_file.exists():
                try:
                    log_file.unlink()
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
            # Buscar el JSON más completo (con anidamiento)
            json_pattern = r'\{(?:[^{}]|\{[^{}]*\})*\}'
            json_match = re.search(json_pattern, result, re.DOTALL)
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
