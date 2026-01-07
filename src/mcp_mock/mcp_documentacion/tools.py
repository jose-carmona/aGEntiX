"""
Implementación de Tools MCP para documentación de tipos de expediente.

Expone herramientas para acceder a normativa, instrucciones y plantillas.
"""

import json
from typing import List
from mcp import types

from .data_loader import (
    cargar_documento,
    listar_documentos,
    buscar_en_documentacion,
    DocumentacionError,
    TIPOS_EXPEDIENTE,
    TIPOS_DOCUMENTO,
)


# Nombres de las tools de este módulo
TOOL_NAMES = [
    "listar_documentacion",
    "obtener_doc_documentacion",
    "buscar_en_documentacion"
]


async def list_tools() -> List[types.Tool]:
    """
    Lista todas las tools de documentación disponibles.

    Returns:
        Lista de tools MCP con sus definiciones
    """
    return [
        types.Tool(
            name="listar_documentacion",
            description="Lista la documentación disponible para un tipo de expediente (normativa, instrucciones, plantillas)",
            inputSchema={
                "type": "object",
                "properties": {
                    "tipo_expediente": {
                        "type": "string",
                        "enum": TIPOS_EXPEDIENTE,
                        "description": "Tipo de expediente"
                    }
                },
                "required": ["tipo_expediente"]
            }
        ),

        types.Tool(
            name="obtener_doc_documentacion",
            description="Obtiene el contenido completo de un documento de la documentación (normativa, instrucciones o plantilla)",
            inputSchema={
                "type": "object",
                "properties": {
                    "tipo_expediente": {
                        "type": "string",
                        "enum": TIPOS_EXPEDIENTE,
                        "description": "Tipo de expediente"
                    },
                    "tipo_documento": {
                        "type": "string",
                        "enum": TIPOS_DOCUMENTO,
                        "description": "Tipo de documento a obtener"
                    }
                },
                "required": ["tipo_expediente", "tipo_documento"]
            }
        ),

        types.Tool(
            name="buscar_en_documentacion",
            description="Busca texto en la documentación de un tipo de expediente",
            inputSchema={
                "type": "object",
                "properties": {
                    "tipo_expediente": {
                        "type": "string",
                        "enum": TIPOS_EXPEDIENTE,
                        "description": "Tipo de expediente donde buscar"
                    },
                    "query": {
                        "type": "string",
                        "description": "Texto a buscar"
                    },
                    "tipo_documento": {
                        "type": "string",
                        "enum": TIPOS_DOCUMENTO,
                        "description": "Filtrar por tipo de documento (opcional)"
                    }
                },
                "required": ["tipo_expediente", "query"]
            }
        )
    ]


async def call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """
    Ejecuta una tool de documentación con los argumentos proporcionados.

    Args:
        name: Nombre de la tool a ejecutar
        arguments: Argumentos para la tool

    Returns:
        Lista de contenido de texto con el resultado

    Raises:
        DocumentacionError: Si hay error al ejecutar la tool
    """
    try:
        if name == "listar_documentacion":
            return await tool_listar_documentacion(**arguments)

        elif name == "obtener_doc_documentacion":
            return await tool_obtener_doc_documentacion(**arguments)

        elif name == "buscar_en_documentacion":
            return await tool_buscar_en_documentacion(**arguments)

        else:
            raise DocumentacionError(f"Tool desconocida: {name}", 404)

    except DocumentacionError:
        raise
    except Exception as e:
        raise DocumentacionError(f"Error al ejecutar tool '{name}': {str(e)}", 500)


async def tool_listar_documentacion(tipo_expediente: str) -> List[types.TextContent]:
    """
    Lista la documentación disponible para un tipo de expediente.

    Args:
        tipo_expediente: Tipo de expediente

    Returns:
        Lista de documentos con metadatos
    """
    documentos = listar_documentos(tipo_expediente)

    result = {
        "tipo_expediente": tipo_expediente,
        "documentos": documentos
    }

    return [
        types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )
    ]


async def tool_obtener_doc_documentacion(
    tipo_expediente: str,
    tipo_documento: str
) -> List[types.TextContent]:
    """
    Obtiene el contenido completo de un documento de documentación.

    Args:
        tipo_expediente: Tipo de expediente
        tipo_documento: Tipo de documento a obtener

    Returns:
        Documento completo con contenido
    """
    doc = cargar_documento(tipo_expediente, tipo_documento)

    result = {
        "id": doc.id,
        "tipo": doc.tipo,
        "tipo_expediente": doc.tipo_expediente,
        "descripcion": doc.descripcion,
        "instrucciones_agente": doc.instrucciones_agente,
        "contenido": doc.contenido
    }

    if doc.subtipo:
        result["subtipo"] = doc.subtipo

    return [
        types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )
    ]


async def tool_buscar_en_documentacion(
    tipo_expediente: str,
    query: str,
    tipo_documento: str = None
) -> List[types.TextContent]:
    """
    Busca texto en la documentación de un tipo de expediente.

    Args:
        tipo_expediente: Tipo de expediente donde buscar
        query: Texto a buscar
        tipo_documento: Filtrar por tipo de documento (opcional)

    Returns:
        Resultados de búsqueda con contexto
    """
    result = buscar_en_documentacion(tipo_expediente, query, tipo_documento)

    return [
        types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )
    ]
