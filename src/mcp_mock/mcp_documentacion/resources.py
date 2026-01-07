"""
Implementación de Resources MCP para documentación de tipos de expediente.

Expone recursos que permiten acceder a la documentación de cada tipo.
"""

import json
from typing import List
from mcp import types

from .data_loader import (
    listar_documentos,
    obtener_tipos_expediente,
    DocumentacionError,
)


async def list_resources() -> List[types.Resource]:
    """
    Lista todos los resources de documentación disponibles.

    Retorna un resource por cada tipo de expediente.

    Returns:
        Lista de resources MCP
    """
    resources = []

    for tipo in obtener_tipos_expediente():
        # Formatear nombre legible
        nombre_legible = tipo.replace("_", " ").title()

        resources.append(
            types.Resource(
                uri=f"documentacion://{tipo}",
                name=f"Documentación de {nombre_legible}",
                description=f"Lista de documentos disponibles para expedientes de tipo {nombre_legible}: normativa, instrucciones y plantillas",
                mimeType="application/json"
            )
        )

    return resources


async def get_resource(uri: str) -> str:
    """
    Obtiene el contenido de un resource de documentación.

    Args:
        uri: URI del resource (documentacion://{tipo_expediente})

    Returns:
        Contenido del resource en formato JSON

    Raises:
        DocumentacionError: Si el resource no existe
    """
    if not uri.startswith("documentacion://"):
        raise DocumentacionError(f"URI no válida: {uri}", 400)

    # Extraer tipo de expediente de la URI
    tipo_expediente = uri.replace("documentacion://", "")

    # Obtener lista de documentos
    documentos = listar_documentos(tipo_expediente)

    # Formatear nombre legible
    nombre_legible = tipo_expediente.replace("_", " ").title()

    result = {
        "tipo_expediente": tipo_expediente,
        "nombre": nombre_legible,
        "documentos": documentos,
        "instrucciones": (
            f"Esta documentación contiene normativa, instrucciones de tramitación "
            f"y plantillas para expedientes de tipo '{nombre_legible}'. "
            f"Usa la tool 'obtener_doc_documentacion' para obtener el contenido "
            f"completo de cada documento."
        )
    }

    return json.dumps(result, ensure_ascii=False, indent=2)
