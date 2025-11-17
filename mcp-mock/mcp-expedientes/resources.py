"""
Implementación de Resources MCP para expedientes.

Los Resources exponen información que el agente puede leer pasivamente.
Son operaciones idempotentes sin efectos secundarios.
"""

import json
import os
from pathlib import Path
from typing import List, Optional
from mcp import types
from models import Expediente
from auth import AuthError


# Directorio de datos
DATA_DIR = Path(__file__).parent / "data" / "expedientes"


def load_expediente(exp_id: str) -> Expediente:
    """
    Carga un expediente desde el almacenamiento JSON.

    Args:
        exp_id: ID del expediente a cargar

    Returns:
        Expediente cargado

    Raises:
        AuthError: Si el expediente no existe (404)
    """
    exp_file = DATA_DIR / f"{exp_id}.json"

    if not exp_file.exists():
        raise AuthError(f"Expediente {exp_id} no encontrado", 404)

    try:
        with open(exp_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return Expediente(**data)
    except Exception as e:
        raise AuthError(f"Error al cargar expediente: {str(e)}", 500)


def save_expediente(expediente: Expediente) -> None:
    """
    Guarda un expediente en el almacenamiento JSON.

    Args:
        expediente: Expediente a guardar

    Raises:
        AuthError: Si hay error al guardar (500)
    """
    exp_file = DATA_DIR / f"{expediente.id}.json"

    try:
        # Asegurar que el directorio existe
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Serializar y guardar
        with open(exp_file, "w", encoding="utf-8") as f:
            json.dump(
                expediente.model_dump(mode="json"),
                f,
                ensure_ascii=False,
                indent=2
            )
    except Exception as e:
        raise AuthError(f"Error al guardar expediente: {str(e)}", 500)


def list_expedientes() -> List[str]:
    """
    Lista todos los IDs de expedientes disponibles.

    Returns:
        Lista de IDs de expedientes
    """
    if not DATA_DIR.exists():
        return []

    return [
        f.stem for f in DATA_DIR.glob("*.json")
    ]


async def list_resources() -> List[types.Resource]:
    """
    Lista todos los resources disponibles.

    Esta función lista resources para todos los expedientes disponibles.
    En un sistema real, esto podría filtrarse por permisos del usuario.

    Returns:
        Lista de resources MCP
    """
    resources = []

    # Listar todos los expedientes
    expedientes = list_expedientes()

    for exp_id in expedientes:
        # Resource principal del expediente
        resources.append(
            types.Resource(
                uri=f"expediente://{exp_id}",
                name=f"Expediente {exp_id}",
                description=f"Información completa del expediente {exp_id}",
                mimeType="application/json"
            )
        )

        # Resource de documentos
        resources.append(
            types.Resource(
                uri=f"expediente://{exp_id}/documentos",
                name=f"Documentos de {exp_id}",
                description=f"Lista de documentos del expediente {exp_id}",
                mimeType="application/json"
            )
        )

        # Resource de historial
        resources.append(
            types.Resource(
                uri=f"expediente://{exp_id}/historial",
                name=f"Historial de {exp_id}",
                description=f"Historial de acciones del expediente {exp_id}",
                mimeType="application/json"
            )
        )

    return resources


async def get_resource(uri: str) -> str:
    """
    Obtiene el contenido de un resource específico.

    Args:
        uri: URI del resource a obtener

    Returns:
        Contenido del resource en formato JSON

    Raises:
        AuthError: Si el resource no existe o hay error al obtenerlo
    """
    if not uri.startswith("expediente://"):
        raise AuthError(f"URI no válida: {uri}", 400)

    # Parsear la URI
    path = uri.replace("expediente://", "")
    parts = path.split("/")

    if len(parts) == 0:
        raise AuthError("URI inválida: falta ID de expediente", 400)

    exp_id = parts[0]

    # Cargar expediente
    expediente = load_expediente(exp_id)

    # Determinar qué retornar según la URI
    if len(parts) == 1:
        # expediente://{id} - Expediente completo
        return json.dumps(
            expediente.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2
        )

    elif len(parts) == 2:
        sub_resource = parts[1]

        if sub_resource == "documentos":
            # expediente://{id}/documentos - Lista de documentos
            return json.dumps(
                [doc.model_dump(mode="json") for doc in expediente.documentos],
                ensure_ascii=False,
                indent=2
            )

        elif sub_resource == "historial":
            # expediente://{id}/historial - Historial
            return json.dumps(
                [entry.model_dump(mode="json") for entry in expediente.historial],
                ensure_ascii=False,
                indent=2
            )

        else:
            raise AuthError(f"Sub-resource no válido: {sub_resource}", 404)

    elif len(parts) == 3 and parts[1] == "documento":
        # expediente://{id}/documento/{doc_id} - Documento específico
        doc_id = parts[2]

        # Buscar documento
        documento = next(
            (doc for doc in expediente.documentos if doc.id == doc_id),
            None
        )

        if not documento:
            raise AuthError(f"Documento {doc_id} no encontrado", 404)

        return json.dumps(
            documento.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2
        )

    else:
        raise AuthError(f"URI no válida: {uri}", 400)
