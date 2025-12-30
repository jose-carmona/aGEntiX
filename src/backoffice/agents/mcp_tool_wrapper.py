# backoffice/agents/mcp_tool_wrapper.py

"""
Wrapper para exponer herramientas MCP como Tools de CrewAI.

Permite que los agentes CrewAI usen las herramientas del MCPClientRegistry
de forma transparente, convirtiendo llamadas síncronas a asíncronas.
"""

import json
from typing import Any, Callable, List, Optional, Type
from pydantic import BaseModel, Field

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


# ========== SCHEMAS DE ARGUMENTOS PARA HERRAMIENTAS MCP ==========

class ConsultarExpedienteArgs(BaseModel):
    """Argumentos para consultar_expediente."""
    expediente_id: str = Field(description="ID del expediente a consultar")


class ActualizarDatosArgs(BaseModel):
    """Argumentos para actualizar_datos."""
    expediente_id: str = Field(description="ID del expediente")
    campo: str = Field(description="Ruta del campo a actualizar (ej: 'datos.validado')")
    valor: Any = Field(description="Nuevo valor a asignar")


class AñadirAnotacionArgs(BaseModel):
    """Argumentos para añadir_anotacion."""
    expediente_id: str = Field(description="ID del expediente")
    texto: str = Field(description="Texto de la anotación")


class CalcularPuntuacionArgs(BaseModel):
    """Argumentos para calcular_puntuacion."""
    expediente_id: str = Field(description="ID del expediente")
    criterios: Optional[dict] = Field(default=None, description="Criterios opcionales")


class GenerarInformeArgs(BaseModel):
    """Argumentos para generar_informe."""
    expediente_id: str = Field(description="ID del expediente")
    tipo_informe: str = Field(description="Tipo de informe a generar")


class GenerarDocumentoArgs(BaseModel):
    """Argumentos para generar_documento."""
    expediente_id: str = Field(description="ID del expediente")
    plantilla_id: str = Field(description="ID de la plantilla")
    datos: dict = Field(description="Datos para la plantilla")


class ListarDocumentosArgs(BaseModel):
    """Argumentos para listar_documentos."""
    expediente_id: str = Field(description="ID del expediente")


class ObtenerDocumentoArgs(BaseModel):
    """Argumentos para obtener_documento."""
    expediente_id: str = Field(description="ID del expediente")
    documento_id: str = Field(description="ID del documento")


class AñadirDocumentoArgs(BaseModel):
    """Argumentos para añadir_documento."""
    expediente_id: str = Field(description="ID del expediente")
    nombre: str = Field(description="Nombre del documento")
    tipo: str = Field(description="Tipo MIME del documento")
    contenido: str = Field(description="Contenido del documento (base64)")


# Mapping de nombre de herramienta a schema de argumentos
TOOL_ARGS_SCHEMAS: dict[str, Type[BaseModel]] = {
    "consultar_expediente": ConsultarExpedienteArgs,
    "actualizar_datos": ActualizarDatosArgs,
    "añadir_anotacion": AñadirAnotacionArgs,
    "calcular_puntuacion": CalcularPuntuacionArgs,
    "generar_informe": GenerarInformeArgs,
    "generar_documento": GenerarDocumentoArgs,
    "listar_documentos": ListarDocumentosArgs,
    "obtener_documento": ObtenerDocumentoArgs,
    "añadir_documento": AñadirDocumentoArgs,
}


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

    def _run(self, expediente_id: str = "", **kwargs) -> str:
        """
        Ejecuta la herramienta MCP de forma síncrona.

        CrewAI es síncrono, así que envolvemos la llamada async.

        Args:
            expediente_id: ID del expediente (parámetro común a todas las herramientas)
            **kwargs: Argumentos adicionales para la herramienta MCP

        Returns:
            Resultado de la herramienta como string JSON
        """
        if not CREWAI_AVAILABLE:
            return json.dumps({"error": "CrewAI no está instalado"})

        # Combinar expediente_id con kwargs
        all_args = {"expediente_id": expediente_id, **kwargs}

        try:
            # Ejecutar llamada async desde contexto síncrono
            result = self._run_async_safely(all_args)

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

            if self.logger:
                self.logger.warning(
                    f"MCP Tool '{self.name}' retornó resultado inesperado: {result}"
                )
            return json.dumps(result)

        except Exception as e:
            error_msg = f"Error en MCP Tool '{self.name}': {str(e)} {e.detalle if hasattr(e, 'detalle') else ''}"
            if self.logger:
                self.logger.error(error_msg)
            return json.dumps({"error": str(e)})

    def _run_async_safely(self, args: dict) -> dict:
        """
        Ejecuta la llamada HTTP de forma segura desde contexto síncrono.

        Usa httpx síncrono para evitar problemas de event loop cuando
        CrewAI ejecuta en un contexto async.
        """
        import httpx

        # Obtener configuración del servidor MCP desde el registry
        tool_name = self.name
        server_id = self.mcp_registry._tool_routing.get(tool_name)

        if not server_id:
            raise ValueError(f"Tool '{tool_name}' no encontrada en ningún servidor MCP")

        mcp_client = self.mcp_registry._clients.get(server_id)
        if not mcp_client:
            raise ValueError(f"Servidor MCP '{server_id}' no encontrado")

        # Usar la configuración del cliente existente
        server_config = mcp_client.server_config
        token = mcp_client.token

        # Hacer llamada HTTP síncrona
        with httpx.Client(
            base_url=str(server_config.url),
            timeout=float(server_config.timeout),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        ) as http_client:
            response = http_client.post(
                server_config.endpoint,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": args
                    }
                }
            )

            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise ValueError(f"Error MCP: {data['error'].get('message', data['error'])}")

            return data.get("result", {})


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

            # Obtener schema de argumentos para esta herramienta
            args_schema = TOOL_ARGS_SCHEMAS.get(name, ConsultarExpedienteArgs)

            tool = MCPTool(
                name=name,
                description=description,
                args_schema=args_schema,
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
