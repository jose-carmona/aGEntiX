# backoffice/agents/schema_builder.py

"""
Constructor dinámico de modelos Pydantic desde JSON Schema.

Permite crear schemas de argumentos para tools MCP dinámicamente,
sin necesidad de definirlos manualmente en el código.

Uso:
    from backoffice.agents.schema_builder import build_pydantic_model

    json_schema = {
        "type": "object",
        "properties": {
            "expediente_id": {"type": "string", "description": "ID del expediente"},
            "campo": {"type": "string", "description": "Campo a actualizar"}
        },
        "required": ["expediente_id", "campo"]
    }

    ArgsModel = build_pydantic_model("ActualizarDatosArgs", json_schema)
    # ArgsModel es ahora una clase Pydantic válida
"""

from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel, Field, create_model
import logging

logger = logging.getLogger(__name__)


# Mapping de tipos JSON Schema a tipos Python
JSON_SCHEMA_TO_PYTHON: Dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _get_python_type(json_type: Optional[str], is_required: bool = True) -> type:
    """
    Convierte un tipo JSON Schema a tipo Python.

    Args:
        json_type: Tipo JSON Schema (string, integer, etc.)
        is_required: Si el campo es requerido

    Returns:
        Tipo Python correspondiente
    """
    if json_type is None:
        # Sin tipo especificado = Any
        base_type = Any
    else:
        base_type = JSON_SCHEMA_TO_PYTHON.get(json_type, Any)

    if not is_required:
        return Optional[base_type]

    return base_type


def _create_field_info(
    prop_schema: Dict[str, Any],
    is_required: bool
) -> tuple:
    """
    Crea la información de campo para Pydantic.

    Args:
        prop_schema: Schema JSON del campo
        is_required: Si el campo es requerido

    Returns:
        Tupla (tipo, Field) para create_model
    """
    json_type = prop_schema.get("type")
    description = prop_schema.get("description", "")
    default = prop_schema.get("default", ... if is_required else None)

    python_type = _get_python_type(json_type, is_required)

    # Crear Field con descripción y default
    if is_required:
        field = Field(description=description)
    else:
        field = Field(default=default, description=description)

    return (python_type, field)


def build_pydantic_model(
    model_name: str,
    json_schema: Dict[str, Any],
    base_class: Type[BaseModel] = BaseModel
) -> Type[BaseModel]:
    """
    Construye un modelo Pydantic dinámicamente desde un JSON Schema.

    Args:
        model_name: Nombre para la clase generada
        json_schema: JSON Schema del servidor MCP
        base_class: Clase base (default: BaseModel)

    Returns:
        Clase Pydantic generada dinámicamente

    Example:
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "expediente_id": {"type": "string", "description": "ID"}
        ...     },
        ...     "required": ["expediente_id"]
        ... }
        >>> Model = build_pydantic_model("MyArgs", schema)
        >>> instance = Model(expediente_id="EXP-001")
    """
    if not json_schema:
        # Schema vacío = modelo sin campos específicos
        logger.debug(f"Schema vacío para {model_name}, usando modelo genérico")
        return create_model(model_name, __base__=base_class)

    properties = json_schema.get("properties", {})
    required = set(json_schema.get("required", []))

    if not properties:
        # Sin propiedades = modelo genérico con kwargs
        logger.debug(f"Sin propiedades para {model_name}, usando modelo genérico")
        return create_model(model_name, __base__=base_class)

    # Construir campos para create_model
    fields: Dict[str, Any] = {}

    for prop_name, prop_schema in properties.items():
        is_required = prop_name in required
        field_type, field_info = _create_field_info(prop_schema, is_required)
        fields[prop_name] = (field_type, field_info)

    # Crear modelo dinámicamente
    try:
        model = create_model(
            model_name,
            __base__=base_class,
            **fields
        )
        logger.debug(f"Modelo {model_name} creado con campos: {list(fields.keys())}")
        return model

    except Exception as e:
        logger.warning(f"Error creando modelo {model_name}: {e}. Usando modelo genérico.")
        return create_model(model_name, __base__=base_class)


def build_models_from_tools(
    tools_with_schemas: Dict[str, Dict[str, Any]]
) -> Dict[str, Type[BaseModel]]:
    """
    Construye modelos Pydantic para múltiples tools.

    Args:
        tools_with_schemas: Dict de tools con sus schemas
            {tool_name: {name, description, inputSchema, server_id}}

    Returns:
        Dict[tool_name, ModelClass]
    """
    models: Dict[str, Type[BaseModel]] = {}

    for tool_name, tool_info in tools_with_schemas.items():
        input_schema = tool_info.get("inputSchema", {})

        # Nombre del modelo: CamelCase del nombre de la tool + "Args"
        model_name = "".join(
            word.capitalize()
            for word in tool_name.replace("_", " ").split()
        ) + "Args"

        models[tool_name] = build_pydantic_model(model_name, input_schema)

    return models


class GenericMCPArgs(BaseModel):
    """
    Schema genérico para tools MCP sin schema definido.

    Acepta cualquier argumento como kwargs.
    """

    class Config:
        extra = "allow"  # Permitir campos adicionales
