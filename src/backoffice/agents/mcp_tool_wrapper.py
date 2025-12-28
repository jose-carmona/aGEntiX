# backoffice/agents/mcp_tool_wrapper.py

"""
Wrapper para exponer herramientas MCP como Tools de CrewAI.

Permite que los agentes CrewAI usen las herramientas del MCPClientRegistry
de forma transparente, convirtiendo llamadas síncronas a asíncronas.
"""

import json
import asyncio
from typing import Any, Callable, List, Optional
from pydantic import Field

from ..mcp.registry import MCPClientRegistry
from ..logging.audit_logger import AuditLogger

# Importación condicional de CrewAI
try:
    from crewai.tools import BaseTool
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Crear clase dummy para que el módulo cargue sin CrewAI
    class BaseTool:
        """Clase dummy cuando CrewAI no está instalado."""
        pass


class MCPTool(BaseTool):
    """
    Tool de CrewAI que ejecuta una herramienta MCP.

    Convierte la interfaz síncrona de CrewAI en llamadas asíncronas
    al MCPClientRegistry.
    """
    name: str = Field(description="Nombre de la herramienta MCP")
    description: str = Field(description="Descripción de la herramienta")

    # Campos excluidos del schema de Pydantic
    mcp_registry: Any = Field(default=None, exclude=True)
    logger: Any = Field(default=None, exclude=True)
    tool_tracker: Any = Field(default=None, exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, **kwargs) -> str:
        """
        Ejecuta la herramienta MCP de forma síncrona.

        CrewAI es síncrono, así que envolvemos la llamada async.

        Args:
            **kwargs: Argumentos para la herramienta MCP

        Returns:
            Resultado de la herramienta como string JSON
        """
        if not CREWAI_AVAILABLE:
            return json.dumps({"error": "CrewAI no está instalado"})

        try:
            # Obtener o crear event loop
            try:
                loop = asyncio.get_running_loop()
                # Si hay un loop corriendo, usamos run_in_executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self._async_call_tool(kwargs)
                    )
                    result = future.result()
            except RuntimeError:
                # No hay loop corriendo, podemos usar asyncio.run
                result = asyncio.run(self._async_call_tool(kwargs))

            # Registrar uso de herramienta
            if self.tool_tracker:
                self.tool_tracker(self.name)

            # Loguear resultado
            if self.logger:
                self.logger.log(f"MCP Tool '{self.name}' ejecutada correctamente")

            # Extraer contenido del resultado MCP
            content = result.get("content", [{}])
            if content and isinstance(content, list):
                text = content[0].get("text", "{}")
                return text

            return json.dumps(result)

        except Exception as e:
            error_msg = f"Error en MCP Tool '{self.name}': {str(e)}"
            if self.logger:
                self.logger.error(error_msg)
            return json.dumps({"error": str(e)})

    async def _async_call_tool(self, kwargs: dict) -> dict:
        """Ejecuta la llamada asíncrona al MCP."""
        return await self.mcp_registry.call_tool(self.name, kwargs)


class MCPToolFactory:
    """
    Factory para crear Tools de CrewAI desde el MCPClientRegistry.

    Uso:
        tools = MCPToolFactory.create_tools(
            tool_names=["consultar_expediente"],
            mcp_registry=registry,
            logger=logger,
            tool_tracker=agent._track_tool_use
        )
    """

    # Descripciones de herramientas MCP conocidas
    TOOL_DESCRIPTIONS = {
        "consultar_expediente": (
            "Consulta los datos completos de un expediente administrativo. "
            "Requiere el parámetro 'expediente_id' (string) con el ID del expediente. "
            "Retorna un JSON con todos los datos del expediente incluyendo: "
            "id, tipo, estado, fechas, documentos adjuntos y metadatos."
        ),
        "actualizar_datos": (
            "Actualiza un campo específico del expediente. "
            "Requiere los parámetros: 'expediente_id' (string), "
            "'campo' (string con la ruta del campo, ej: 'datos.validado'), "
            "'valor' (el nuevo valor a asignar). "
            "Retorna confirmación de la actualización."
        ),
        "añadir_anotacion": (
            "Añade una anotación al historial del expediente. "
            "Requiere los parámetros: 'expediente_id' (string), "
            "'texto' (string con el contenido de la anotación). "
            "Retorna confirmación con timestamp de la anotación."
        ),
        "calcular_puntuacion": (
            "Calcula la puntuación de una solicitud según criterios. "
            "Requiere 'expediente_id' y opcionalmente 'criterios'. "
            "Retorna puntuación numérica y desglose."
        ),
        "generar_informe": (
            "Genera un informe estructurado del expediente. "
            "Requiere 'expediente_id' y 'tipo_informe'. "
            "Retorna el informe generado."
        ),
        "generar_documento": (
            "Genera un documento a partir de plantilla. "
            "Requiere 'expediente_id', 'plantilla_id' y 'datos'. "
            "Retorna el documento generado."
        ),
    }

    @classmethod
    def create_tools(
        cls,
        tool_names: List[str],
        mcp_registry: MCPClientRegistry,
        logger: AuditLogger,
        tool_tracker: Optional[Callable[[str], None]] = None
    ) -> List[MCPTool]:
        """
        Crea lista de Tools de CrewAI para las herramientas MCP especificadas.

        Args:
            tool_names: Lista de nombres de herramientas MCP a exponer
            mcp_registry: Registry de clientes MCP
            logger: Logger de auditoría
            tool_tracker: Callback para registrar uso de herramientas

        Returns:
            Lista de MCPTool configuradas

        Raises:
            ImportError: Si CrewAI no está instalado
        """
        if not CREWAI_AVAILABLE:
            raise ImportError(
                "CrewAI no está instalado. "
                "Ejecuta: pip install crewai"
            )

        tools = []

        for name in tool_names:
            description = cls.TOOL_DESCRIPTIONS.get(
                name,
                f"Herramienta MCP: {name}. Consulta la documentación para más detalles."
            )

            tool = MCPTool(
                name=name,
                description=description,
                mcp_registry=mcp_registry,
                logger=logger,
                tool_tracker=tool_tracker
            )
            tools.append(tool)

        return tools

    @classmethod
    def get_tool_description(cls, tool_name: str) -> str:
        """
        Obtiene la descripción de una herramienta.

        Args:
            tool_name: Nombre de la herramienta

        Returns:
            Descripción de la herramienta
        """
        return cls.TOOL_DESCRIPTIONS.get(
            tool_name,
            f"Herramienta MCP: {tool_name}"
        )
