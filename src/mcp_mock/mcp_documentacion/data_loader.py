"""
Carga de documentos de documentación desde JSON/MD.

Gestiona la lectura y búsqueda de documentación asociada
a cada tipo de expediente.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Directorio de datos de documentación
DATA_PATH = Path(__file__).parent.parent / "data" / "documentos"

# Tipos de expediente válidos
TIPOS_EXPEDIENTE = ["subvenciones", "licencias_obras", "certificado_empadronamiento"]

# Tipos de documento válidos
TIPOS_DOCUMENTO = [
    "normativa",
    "instrucciones_tramitacion",
    "plantilla_propuesta_resolucion",
    "plantilla_requerimiento_documentacion",
    "plantilla_certificado"
]


@dataclass
class DocumentoTipo:
    """Documento de documentación de tipo de expediente."""
    id: str
    tipo: str
    subtipo: Optional[str]
    tipo_expediente: str
    descripcion: str
    instrucciones_agente: str
    contenido: str


class DocumentacionError(Exception):
    """Error al acceder a documentación."""
    def __init__(self, message: str, status_code: int = 404):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def validar_tipo_expediente(tipo_expediente: str) -> None:
    """
    Valida que el tipo de expediente sea válido.

    Args:
        tipo_expediente: Tipo de expediente a validar

    Raises:
        DocumentacionError: Si el tipo no es válido
    """
    if tipo_expediente not in TIPOS_EXPEDIENTE:
        raise DocumentacionError(
            f"Tipo de expediente no válido: '{tipo_expediente}'. "
            f"Tipos válidos: {', '.join(TIPOS_EXPEDIENTE)}",
            400
        )


def validar_tipo_documento(tipo_documento: str, tipo_expediente: str) -> None:
    """
    Valida que el tipo de documento sea válido para el tipo de expediente.

    Args:
        tipo_documento: Tipo de documento a validar
        tipo_expediente: Tipo de expediente

    Raises:
        DocumentacionError: Si el tipo de documento no es válido
    """
    # plantilla_certificado solo existe para certificado_empadronamiento
    if tipo_documento == "plantilla_certificado" and tipo_expediente != "certificado_empadronamiento":
        raise DocumentacionError(
            f"El documento 'plantilla_certificado' solo existe para 'certificado_empadronamiento'",
            404
        )

    # plantilla_propuesta_resolucion no existe para certificado_empadronamiento
    if tipo_documento == "plantilla_propuesta_resolucion" and tipo_expediente == "certificado_empadronamiento":
        raise DocumentacionError(
            f"El documento 'plantilla_propuesta_resolucion' no existe para 'certificado_empadronamiento'",
            404
        )

    if tipo_documento not in TIPOS_DOCUMENTO:
        raise DocumentacionError(
            f"Tipo de documento no válido: '{tipo_documento}'. "
            f"Tipos válidos: {', '.join(TIPOS_DOCUMENTO)}",
            400
        )


def cargar_documento(tipo_expediente: str, tipo_documento: str) -> DocumentoTipo:
    """
    Carga un documento JSON y su contenido MD asociado.

    Args:
        tipo_expediente: Tipo de expediente (subvenciones, licencias_obras, etc.)
        tipo_documento: Tipo de documento (normativa, instrucciones_tramitacion, etc.)

    Returns:
        DocumentoTipo con todos los datos y contenido

    Raises:
        DocumentacionError: Si el documento no existe o hay error al cargarlo
    """
    validar_tipo_expediente(tipo_expediente)
    validar_tipo_documento(tipo_documento, tipo_expediente)

    json_path = DATA_PATH / tipo_expediente / f"{tipo_documento}.json"

    if not json_path.exists():
        raise DocumentacionError(
            f"Documento no encontrado: {tipo_documento} para {tipo_expediente}",
            404
        )

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            doc = json.load(f)

        # Cargar contenido markdown
        md_filename = doc.get("contenido", f"{tipo_documento}.md")
        md_path = DATA_PATH / tipo_expediente / md_filename

        if md_path.exists():
            with open(md_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
        else:
            contenido = ""

        return DocumentoTipo(
            id=doc.get("id", ""),
            tipo=doc.get("tipo", ""),
            subtipo=doc.get("subtipo"),
            tipo_expediente=doc.get("tipo_expediente", tipo_expediente),
            descripcion=doc.get("descripcion", ""),
            instrucciones_agente=doc.get("instrucciones_agente", ""),
            contenido=contenido
        )

    except json.JSONDecodeError as e:
        raise DocumentacionError(f"Error al parsear JSON: {str(e)}", 500)
    except Exception as e:
        raise DocumentacionError(f"Error al cargar documento: {str(e)}", 500)


def listar_documentos(tipo_expediente: str) -> List[Dict[str, Any]]:
    """
    Lista todos los documentos disponibles para un tipo de expediente.

    Args:
        tipo_expediente: Tipo de expediente

    Returns:
        Lista de documentos con metadatos básicos (sin contenido)

    Raises:
        DocumentacionError: Si el tipo de expediente no es válido
    """
    validar_tipo_expediente(tipo_expediente)

    dir_path = DATA_PATH / tipo_expediente
    documentos = []

    if not dir_path.exists():
        return documentos

    for json_file in sorted(dir_path.glob("*.json")):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                doc = json.load(f)
                documentos.append({
                    "id": doc.get("id", ""),
                    "tipo": doc.get("tipo", ""),
                    "subtipo": doc.get("subtipo"),
                    "descripcion": doc.get("descripcion", "")
                })
        except Exception:
            # Ignorar archivos con errores
            continue

    return documentos


def buscar_en_documentacion(
    tipo_expediente: str,
    query: str,
    tipo_documento: Optional[str] = None
) -> Dict[str, Any]:
    """
    Busca texto en la documentación de un tipo de expediente.

    Args:
        tipo_expediente: Tipo de expediente donde buscar
        query: Texto a buscar (case-insensitive)
        tipo_documento: Filtrar por tipo de documento (opcional)

    Returns:
        Diccionario con resultados de búsqueda

    Raises:
        DocumentacionError: Si hay error en la búsqueda
    """
    validar_tipo_expediente(tipo_expediente)

    if tipo_documento:
        validar_tipo_documento(tipo_documento, tipo_expediente)

    dir_path = DATA_PATH / tipo_expediente
    resultados = []
    total_coincidencias = 0

    if not dir_path.exists():
        return {"resultados": [], "total_coincidencias": 0}

    # Patrón de búsqueda (case-insensitive)
    pattern = re.compile(re.escape(query), re.IGNORECASE)

    for json_file in sorted(dir_path.glob("*.json")):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                doc = json.load(f)

            doc_tipo = json_file.stem  # Nombre sin extensión

            # Filtrar por tipo de documento si se especifica
            if tipo_documento and doc_tipo != tipo_documento:
                continue

            # Cargar contenido markdown
            md_filename = doc.get("contenido", f"{doc_tipo}.md")
            md_path = DATA_PATH / tipo_expediente / md_filename

            if not md_path.exists():
                continue

            with open(md_path, 'r', encoding='utf-8') as f:
                contenido = f.read()

            # Buscar coincidencias
            lineas = contenido.split('\n')
            coincidencias = []

            for num_linea, linea in enumerate(lineas, 1):
                if pattern.search(linea):
                    # Extraer contexto (línea completa, limitada a 200 chars)
                    contexto = linea.strip()[:200]
                    if len(linea.strip()) > 200:
                        contexto += "..."

                    coincidencias.append({
                        "linea": num_linea,
                        "contexto": contexto
                    })

            if coincidencias:
                resultados.append({
                    "documento_id": doc.get("id", ""),
                    "tipo": doc.get("tipo", ""),
                    "coincidencias": coincidencias
                })
                total_coincidencias += len(coincidencias)

        except Exception:
            # Ignorar archivos con errores
            continue

    return {
        "resultados": resultados,
        "total_coincidencias": total_coincidencias
    }


def obtener_tipos_expediente() -> List[str]:
    """
    Retorna la lista de tipos de expediente válidos.

    Returns:
        Lista de IDs de tipos de expediente
    """
    return TIPOS_EXPEDIENTE.copy()
