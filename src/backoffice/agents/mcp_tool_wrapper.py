# backoffice/agents/mcp_tool_wrapper.py

"""
Wrapper para exponer herramientas MCP como Tools de CrewAI.

Permite que los agentes CrewAI usen las herramientas del MCPClientRegistry
de forma transparente, usando la interfaz síncrona del cliente MCP.
"""

import json
from typing import Any, Callable, Dict, List, Optional, Type
from pydantic import BaseModel, Field

from ..mcp.registry import MCPClientRegistry
from ..mcp.exceptions import MCPError, MCPConnectionError, MCPAuthError, MCPToolError
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

    Usa la interfaz síncrona del MCPClientRegistry para ejecutar
    herramientas MCP desde el contexto síncrono de CrewAI.
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
            # Ejecutar llamada síncrona al MCP
            result = self._call_mcp_tool(all_args)

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

        except MCPConnectionError as e:
            # Errores de conexión (timeout, servidor caído, etc.)
            error_response = {
                "error": e.codigo,
                "message": e.mensaje,
                "type": "connection",
                "retriable": True  # El agente podría reintentar
            }
            if self.logger:
                self.logger.error(f"MCP Connection Error '{self.name}': [{e.codigo}] {e.mensaje}")
            return json.dumps(error_response)

        except MCPAuthError as e:
            # Errores de autenticación (token inválido, permisos insuficientes)
            error_response = {
                "error": e.codigo,
                "message": e.mensaje,
                "type": "auth",
                "retriable": False  # No reintentar, error definitivo
            }
            if self.logger:
                self.logger.error(f"MCP Auth Error '{self.name}': [{e.codigo}] {e.mensaje}")
            return json.dumps(error_response)

        except MCPToolError as e:
            # Errores de ejecución de la tool (tool no encontrada, error de negocio)
            error_response = {
                "error": e.codigo,
                "message": e.mensaje,
                "type": "tool",
                "retriable": e.codigo == "MCP_CONFLICT"  # Solo conflictos son retriables
            }
            if self.logger:
                self.logger.error(f"MCP Tool Error '{self.name}': [{e.codigo}] {e.mensaje}")
            return json.dumps(error_response)

        except MCPError as e:
            # Cualquier otro error MCP
            error_response = {
                "error": e.codigo,
                "message": e.mensaje,
                "type": "mcp",
                "retriable": False
            }
            if self.logger:
                self.logger.error(f"MCP Error '{self.name}': [{e.codigo}] {e.mensaje}")
            return json.dumps(error_response)

        except Exception as e:
            # Errores inesperados (bugs, etc.)
            error_response = {
                "error": "INTERNAL_ERROR",
                "message": str(e),
                "type": "internal",
                "retriable": False
            }
            if self.logger:
                self.logger.error(f"Unexpected Error in MCP Tool '{self.name}': {type(e).__name__}: {e}")
            return json.dumps(error_response)

    def _call_mcp_tool(self, args: dict) -> dict:
        """
        Ejecuta la llamada al servidor MCP usando la interfaz síncrona.

        Delega al MCPClientRegistry que maneja el routing y la conexión.

        Args:
            args: Argumentos para la tool

        Returns:
            Resultado de la tool

        Raises:
            MCPError: Errores de conexión, autenticación o ejecución
        """
        return self.mcp_registry.call_tool_sync(self.name, args)


class MCPToolFactory:
    """
    Factory para crear Tools de CrewAI desde el MCPClientRegistry.

    Soporta dos modos:
    1. Discovery dinámico: Obtiene schemas del servidor MCP (recomendado)
    2. Fallback estático: Usa schemas hardcodeados si el servidor no responde

    Uso:
        # Con discovery dinámico (recomendado)
        tools = MCPToolFactory.create_tools(
            tool_names=["consultar_expediente"],
            mcp_registry=registry,
            logger=logger,
            use_dynamic_schemas=True  # Default
        )

        # Con schemas estáticos (fallback)
        tools = MCPToolFactory.create_tools(
            tool_names=["consultar_expediente"],
            mcp_registry=registry,
            logger=logger,
            use_dynamic_schemas=False
        )
    """

    # Descripciones fallback cuando el servidor no responde
    FALLBACK_DESCRIPTIONS = {
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

    # Cache de schemas dinámicos (evita llamadas repetidas al servidor)
    _dynamic_schemas_cache: Optional[Dict[str, Dict[str, Any]]] = None

    @classmethod
    def create_tools(
        cls,
        tool_names: List[str],
        mcp_registry: MCPClientRegistry,
        logger: AuditLogger,
        tool_tracker: Optional[Callable[[str], None]] = None,
        use_dynamic_schemas: bool = True
    ) -> List[MCPTool]:
        """
        Crea lista de Tools de CrewAI para las herramientas MCP especificadas.

        Args:
            tool_names: Lista de nombres de herramientas MCP a exponer
            mcp_registry: Registry de clientes MCP
            logger: Logger de auditoría
            tool_tracker: Callback para registrar uso de herramientas
            use_dynamic_schemas: Si True, obtiene schemas del servidor MCP.
                                Si False, usa schemas hardcodeados.

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

        # Importar schema_builder aquí para evitar import circular
        from .schema_builder import build_pydantic_model, GenericMCPArgs

        # Obtener schemas dinámicos del servidor si está habilitado
        dynamic_schemas: Dict[str, Dict[str, Any]] = {}
        if use_dynamic_schemas:
            try:
                dynamic_schemas = mcp_registry.get_tools_with_schemas()
            except Exception as e:
                # Si falla, usamos schemas estáticos
                import logging
                logging.getLogger(__name__).warning(
                    f"No se pudieron obtener schemas dinámicos: {e}. "
                    "Usando schemas estáticos."
                )

        tools = []

        for name in tool_names:
            # 1. Obtener descripción (dinámica o fallback)
            if name in dynamic_schemas:
                description = dynamic_schemas[name].get("description", "")
                if not description:
                    description = cls.FALLBACK_DESCRIPTIONS.get(
                        name,
                        f"Herramienta MCP: {name}. Consulta la documentación."
                    )
            else:
                description = cls.FALLBACK_DESCRIPTIONS.get(
                    name,
                    f"Herramienta MCP: {name}. Consulta la documentación."
                )

            # 2. Obtener schema (dinámico o fallback)
            if name in dynamic_schemas:
                input_schema = dynamic_schemas[name].get("inputSchema", {})
                if input_schema:
                    # Construir modelo Pydantic dinámicamente
                    model_name = "".join(
                        word.capitalize()
                        for word in name.replace("_", " ").split()
                    ) + "Args"
                    args_schema = build_pydantic_model(model_name, input_schema)
                else:
                    args_schema = GenericMCPArgs
            else:
                # Fallback a schemas hardcodeados
                args_schema = TOOL_ARGS_SCHEMAS.get(name, GenericMCPArgs)

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
    def clear_schema_cache(cls) -> None:
        """Limpia el cache de schemas dinámicos."""
        cls._dynamic_schemas_cache = None

    @classmethod
    def get_tool_description(cls, tool_name: str) -> str:
        """
        Obtiene la descripción de una herramienta (fallback).

        Args:
            tool_name: Nombre de la herramienta

        Returns:
            Descripción de la herramienta
        """
        return cls.FALLBACK_DESCRIPTIONS.get(
            tool_name,
            f"Herramienta MCP: {tool_name}"
        )
