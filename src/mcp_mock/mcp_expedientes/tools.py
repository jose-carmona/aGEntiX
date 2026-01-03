"""
Implementación de Tools MCP para expedientes.

Las Tools exponen acciones que el agente puede ejecutar.
Pueden tener efectos secundarios (escribir, modificar).
"""

import json
import uuid
from datetime import datetime
from typing import List, Any, Dict
from mcp import types
from .models import Documento, EntradaHistorial
from .resources import load_expediente, save_expediente
from .auth import AuthError


def generate_id(prefix: str) -> str:
    """
    Genera un ID único con un prefijo.

    Args:
        prefix: Prefijo para el ID (ej: "DOC", "HIST")

    Returns:
        ID único en formato {prefix}-{número}
    """
    # En un sistema real, esto sería más sofisticado
    # Por ahora, usamos un timestamp y contador
    timestamp = int(datetime.now().timestamp() * 1000)
    return f"{prefix}-{timestamp % 1000000:06d}"


def add_historial_entry(
    expediente_id: str,
    tipo: str,
    accion: str,
    detalles: str,
    usuario: str = "Automático"
) -> None:
    """
    Añade una entrada al historial de un expediente.

    Args:
        expediente_id: ID del expediente
        tipo: Tipo de entrada (SISTEMA, AGENTE, HUMANO, ANOTACION)
        accion: Acción realizada
        detalles: Detalles de la acción
        usuario: Usuario que realizó la acción (default: Automático)
    """
    expediente = load_expediente(expediente_id)

    entrada = EntradaHistorial(
        id=generate_id("HIST"),
        fecha=datetime.now(),
        usuario=usuario,
        tipo=tipo,
        accion=accion,
        detalles=detalles
    )

    expediente.historial.append(entrada)
    save_expediente(expediente)


async def list_tools() -> List[types.Tool]:
    """
    Lista todas las tools disponibles.

    Returns:
        Lista de tools MCP con sus definiciones
    """
    return [
        # ========== TOOLS DE LECTURA ==========

        types.Tool(
            name="consultar_expediente",
            description="Obtiene toda la información de un expediente",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_id": {
                        "type": "string",
                        "description": "ID del expediente a consultar (ej: EXP-2024-001)"
                    }
                },
                "required": ["expediente_id"]
            }
        ),

        types.Tool(
            name="listar_documentos",
            description="Lista todos los documentos de un expediente",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_id": {
                        "type": "string",
                        "description": "ID del expediente"
                    }
                },
                "required": ["expediente_id"]
            }
        ),

        types.Tool(
            name="obtener_documento",
            description="Obtiene un documento específico de un expediente",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_id": {
                        "type": "string",
                        "description": "ID del expediente"
                    },
                    "documento_id": {
                        "type": "string",
                        "description": "ID del documento (ej: DOC-001)"
                    }
                },
                "required": ["expediente_id", "documento_id"]
            }
        ),

        types.Tool(
            name="obtener_texto_documento",
            description="Obtiene el texto markdown del contenido de un documento",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_id": {
                        "type": "string",
                        "description": "ID del expediente (ej: EXP-2024-001)"
                    },
                    "documento_id": {
                        "type": "string",
                        "description": "ID del documento (ej: DOC-001)"
                    }
                },
                "required": ["expediente_id", "documento_id"]
            }
        ),

        types.Tool(
            name="obtener_metadatos_documento",
            description="Obtiene los metadatos extraídos de un documento (NIF, fechas, importes, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_id": {
                        "type": "string",
                        "description": "ID del expediente"
                    },
                    "documento_id": {
                        "type": "string",
                        "description": "ID del documento"
                    }
                },
                "required": ["expediente_id", "documento_id"]
            }
        ),

        # ========== TOOLS DE ESCRITURA ==========

        types.Tool(
            name="añadir_documento",
            description="Añade un nuevo documento al expediente",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_id": {
                        "type": "string",
                        "description": "ID del expediente"
                    },
                    "nombre": {
                        "type": "string",
                        "description": "Nombre del documento (ej: informe_validacion.pdf)"
                    },
                    "tipo": {
                        "type": "string",
                        "description": "Tipo de documento (ej: INFORME, RESOLUCION, NOTIFICACION)"
                    },
                    "contenido": {
                        "type": "string",
                        "description": "Contenido del documento (puede ser base64 para binarios)"
                    },
                    "ruta": {
                        "type": "string",
                        "description": "Ruta donde se guardará el documento (opcional)"
                    }
                },
                "required": ["expediente_id", "nombre", "tipo", "contenido"]
            }
        ),

        types.Tool(
            name="actualizar_datos",
            description="Actualiza un campo de datos del expediente",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_id": {
                        "type": "string",
                        "description": "ID del expediente"
                    },
                    "campo": {
                        "type": "string",
                        "description": "Ruta del campo a actualizar (ej: 'datos.documentacion_valida', 'estado')"
                    },
                    "valor": {
                        "description": "Nuevo valor para el campo (puede ser string, number, boolean, etc.)"
                    }
                },
                "required": ["expediente_id", "campo", "valor"]
            }
        ),

        types.Tool(
            name="añadir_anotacion",
            description="Añade una anotación al historial del expediente",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_id": {
                        "type": "string",
                        "description": "ID del expediente"
                    },
                    "texto": {
                        "type": "string",
                        "description": "Texto de la anotación"
                    }
                },
                "required": ["expediente_id", "texto"]
            }
        ),

        types.Tool(
            name="actualizar_metadatos_documento",
            description="Actualiza los metadatos extraídos de un documento",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_id": {
                        "type": "string",
                        "description": "ID del expediente"
                    },
                    "documento_id": {
                        "type": "string",
                        "description": "ID del documento"
                    },
                    "metadatos": {
                        "type": "object",
                        "description": "Metadatos a establecer o actualizar (se mezclan con los existentes)"
                    },
                    "reemplazar": {
                        "type": "boolean",
                        "description": "Si true, reemplaza todos los metadatos. Si false, los mezcla (default: false)"
                    }
                },
                "required": ["expediente_id", "documento_id", "metadatos"]
            }
        ),

        types.Tool(
            name="crear_documento_desde_markdown",
            description="Crea un nuevo documento a partir de contenido markdown generado por el agente",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_id": {
                        "type": "string",
                        "description": "ID del expediente"
                    },
                    "nombre": {
                        "type": "string",
                        "description": "Nombre del documento (ej: informe_validacion.md)"
                    },
                    "tipo": {
                        "type": "string",
                        "description": "Tipo de documento (INFORME, RESOLUCION, NOTIFICACION, etc.)"
                    },
                    "texto_markdown": {
                        "type": "string",
                        "description": "Contenido del documento en formato markdown"
                    },
                    "metadatos": {
                        "type": "object",
                        "description": "Metadatos del documento (opcional)"
                    }
                },
                "required": ["expediente_id", "nombre", "tipo", "texto_markdown"]
            }
        )
    ]


async def call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """
    Ejecuta una tool con los argumentos proporcionados.

    Args:
        name: Nombre de la tool a ejecutar
        arguments: Argumentos para la tool

    Returns:
        Lista de contenido de texto con el resultado

    Raises:
        AuthError: Si hay error al ejecutar la tool
    """
    try:
        if name == "consultar_expediente":
            return await tool_consultar_expediente(**arguments)

        elif name == "listar_documentos":
            return await tool_listar_documentos(**arguments)

        elif name == "obtener_documento":
            return await tool_obtener_documento(**arguments)

        elif name == "añadir_documento":
            return await tool_añadir_documento(**arguments)

        elif name == "actualizar_datos":
            return await tool_actualizar_datos(**arguments)

        elif name == "añadir_anotacion":
            return await tool_añadir_anotacion(**arguments)

        elif name == "obtener_texto_documento":
            return await tool_obtener_texto_documento(**arguments)

        elif name == "obtener_metadatos_documento":
            return await tool_obtener_metadatos_documento(**arguments)

        elif name == "actualizar_metadatos_documento":
            return await tool_actualizar_metadatos_documento(**arguments)

        elif name == "crear_documento_desde_markdown":
            return await tool_crear_documento_desde_markdown(**arguments)

        else:
            raise AuthError(f"Tool desconocida: {name}", 404)

    except AuthError:
        raise
    except Exception as e:
        raise AuthError(f"Error al ejecutar tool '{name}': {str(e)}", 500)


# ========== IMPLEMENTACIÓN DE TOOLS DE LECTURA ==========

async def tool_consultar_expediente(expediente_id: str) -> List[types.TextContent]:
    """Implementación de consultar_expediente"""
    expediente = load_expediente(expediente_id)

    return [
        types.TextContent(
            type="text",
            text=json.dumps(
                expediente.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2
            )
        )
    ]


async def tool_listar_documentos(expediente_id: str) -> List[types.TextContent]:
    """Implementación de listar_documentos"""
    expediente = load_expediente(expediente_id)

    return [
        types.TextContent(
            type="text",
            text=json.dumps(
                [doc.model_dump(mode="json") for doc in expediente.documentos],
                ensure_ascii=False,
                indent=2
            )
        )
    ]


async def tool_obtener_documento(
    expediente_id: str,
    documento_id: str
) -> List[types.TextContent]:
    """Implementación de obtener_documento"""
    expediente = load_expediente(expediente_id)

    # Buscar documento
    documento = next(
        (doc for doc in expediente.documentos if doc.id == documento_id),
        None
    )

    if not documento:
        raise AuthError(
            f"Documento {documento_id} no encontrado en expediente {expediente_id}",
            404
        )

    return [
        types.TextContent(
            type="text",
            text=json.dumps(
                documento.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2
            )
        )
    ]


# ========== IMPLEMENTACIÓN DE TOOLS DE ESCRITURA ==========

async def tool_añadir_documento(
    expediente_id: str,
    nombre: str,
    tipo: str,
    contenido: str,
    ruta: str = None
) -> List[types.TextContent]:
    """Implementación de añadir_documento"""
    expediente = load_expediente(expediente_id)

    # Generar ID para el documento
    doc_id = generate_id("DOC")

    # Generar ruta si no se proporciona
    if not ruta:
        ruta = f"data/documentos/{expediente_id}/{nombre}"

    # Crear documento
    documento = Documento(
        id=doc_id,
        nombre=nombre,
        fecha=datetime.now(),
        tipo=tipo,
        ruta=ruta,
        hash_sha256="",  # En un sistema real, se calcularía el hash del contenido
        tamano_bytes=len(contenido.encode('utf-8')),
        validado=None
    )

    # Añadir a la lista de documentos
    expediente.documentos.append(documento)

    # Registrar en historial
    entrada = EntradaHistorial(
        id=generate_id("HIST"),
        fecha=datetime.now(),
        usuario="Automático",
        tipo="AGENTE",
        accion="AÑADIR_DOCUMENTO",
        detalles=f"Añadido documento {doc_id}: {nombre} (tipo: {tipo})"
    )
    expediente.historial.append(entrada)

    # Guardar
    save_expediente(expediente)

    result = {
        "success": True,
        "documento_id": doc_id,
        "mensaje": f"Documento {doc_id} añadido correctamente"
    }

    return [
        types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )
    ]


async def tool_actualizar_datos(
    expediente_id: str,
    campo: str,
    valor: Any
) -> List[types.TextContent]:
    """Implementación de actualizar_datos"""
    expediente = load_expediente(expediente_id)

    # Obtener valor anterior
    valor_anterior = get_nested_value(expediente.model_dump(), campo)

    # Actualizar valor
    set_nested_value(expediente, campo, valor)

    # Registrar en historial
    entrada = EntradaHistorial(
        id=generate_id("HIST"),
        fecha=datetime.now(),
        usuario="Automático",
        tipo="AGENTE",
        accion="ACTUALIZAR_DATOS",
        detalles=f"Campo '{campo}' actualizado de '{valor_anterior}' a '{valor}'"
    )
    expediente.historial.append(entrada)

    # Guardar
    save_expediente(expediente)

    result = {
        "success": True,
        "campo": campo,
        "valor_anterior": valor_anterior,
        "valor_nuevo": valor,
        "mensaje": f"Campo '{campo}' actualizado correctamente"
    }

    return [
        types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )
    ]


async def tool_añadir_anotacion(
    expediente_id: str,
    texto: str
) -> List[types.TextContent]:
    """Implementación de añadir_anotacion"""
    expediente = load_expediente(expediente_id)

    # Añadir anotación al historial
    entrada = EntradaHistorial(
        id=generate_id("HIST"),
        fecha=datetime.now(),
        usuario="Automático",
        tipo="ANOTACION",
        accion="ANOTACION",
        detalles=texto
    )
    expediente.historial.append(entrada)

    # Guardar
    save_expediente(expediente)

    result = {
        "success": True,
        "historial_id": entrada.id,
        "mensaje": "Anotación añadida correctamente"
    }

    return [
        types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )
    ]


# ========== UTILIDADES ==========

def get_nested_value(obj: dict, path: str) -> Any:
    """
    Obtiene un valor anidado de un diccionario usando notación de punto.

    Args:
        obj: Diccionario fuente
        path: Ruta al valor (ej: "datos.solicitante.nombre")

    Returns:
        Valor encontrado o None
    """
    parts = path.split(".")
    current = obj

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None

    return current


def set_nested_value(obj: Any, path: str, value: Any) -> None:
    """
    Establece un valor anidado en un objeto usando notación de punto.

    Args:
        obj: Objeto destino (debe tener los atributos necesarios)
        path: Ruta al valor (ej: "datos.documentacion_valida")
        value: Valor a establecer

    Raises:
        AuthError: Si el campo no existe
    """
    parts = path.split(".")

    # Si solo hay un nivel, actualizar directamente
    if len(parts) == 1:
        if hasattr(obj, parts[0]):
            setattr(obj, parts[0], value)
        else:
            raise AuthError(f"Campo '{parts[0]}' no existe", 400)
        return

    # Navegar hasta el penúltimo nivel
    current = obj
    for part in parts[:-1]:
        if hasattr(current, part):
            current = getattr(current, part)
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise AuthError(f"Ruta '{path}' no válida", 400)

    # Establecer el valor final
    final_key = parts[-1]
    if isinstance(current, dict):
        current[final_key] = value
    elif hasattr(current, final_key):
        setattr(current, final_key, value)
    else:
        raise AuthError(f"Campo '{final_key}' no existe", 400)


# ========== TOOLS DE DOCUMENTOS (NUEVAS) ==========

async def tool_obtener_texto_documento(
    expediente_id: str,
    documento_id: str
) -> List[types.TextContent]:
    """
    Obtiene el texto markdown del contenido de un documento.

    Args:
        expediente_id: ID del expediente
        documento_id: ID del documento

    Returns:
        Texto markdown del documento

    Raises:
        AuthError: Si el documento no existe o no tiene texto_markdown
    """
    expediente = load_expediente(expediente_id)

    # Buscar documento
    documento = next(
        (doc for doc in expediente.documentos if doc.id == documento_id),
        None
    )

    if not documento:
        raise AuthError(
            f"Documento {documento_id} no encontrado en expediente {expediente_id}",
            404
        )

    if not documento.texto_markdown:
        raise AuthError(
            f"Documento {documento_id} no tiene texto markdown disponible",
            422
        )

    result = {
        "success": True,
        "documento_id": documento.id,
        "nombre": documento.nombre,
        "tipo": documento.tipo,
        "texto_markdown": documento.texto_markdown
    }

    return [
        types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )
    ]


async def tool_obtener_metadatos_documento(
    expediente_id: str,
    documento_id: str
) -> List[types.TextContent]:
    """
    Obtiene los metadatos extraídos de un documento.

    Args:
        expediente_id: ID del expediente
        documento_id: ID del documento

    Returns:
        Metadatos extraídos del documento (NIF, fechas, importes, etc.)

    Raises:
        AuthError: Si el documento no existe o no tiene metadatos
    """
    expediente = load_expediente(expediente_id)

    # Buscar documento
    documento = next(
        (doc for doc in expediente.documentos if doc.id == documento_id),
        None
    )

    if not documento:
        raise AuthError(
            f"Documento {documento_id} no encontrado en expediente {expediente_id}",
            404
        )

    if not documento.metadatos_extraidos:
        raise AuthError(
            f"Documento {documento_id} no tiene metadatos extraídos",
            422
        )

    result = {
        "success": True,
        "documento_id": documento.id,
        "nombre": documento.nombre,
        "tipo": documento.tipo,
        "metadatos_extraidos": documento.metadatos_extraidos
    }

    return [
        types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )
    ]


async def tool_actualizar_metadatos_documento(
    expediente_id: str,
    documento_id: str,
    metadatos: Dict[str, Any],
    reemplazar: bool = False
) -> List[types.TextContent]:
    """
    Actualiza los metadatos extraídos de un documento.

    Args:
        expediente_id: ID del expediente
        documento_id: ID del documento
        metadatos: Nuevos metadatos a establecer
        reemplazar: Si True, reemplaza todos los metadatos. Si False, los mezcla.

    Returns:
        Resultado de la operación con metadatos anteriores y nuevos

    Raises:
        AuthError: Si el documento no existe
    """
    expediente = load_expediente(expediente_id)

    # Buscar documento
    documento = None
    doc_index = None
    for i, doc in enumerate(expediente.documentos):
        if doc.id == documento_id:
            documento = doc
            doc_index = i
            break

    if not documento:
        raise AuthError(
            f"Documento {documento_id} no encontrado en expediente {expediente_id}",
            404
        )

    # Guardar metadatos anteriores
    metadatos_anteriores = documento.metadatos_extraidos.copy() if documento.metadatos_extraidos else {}

    # Actualizar metadatos
    if reemplazar or not documento.metadatos_extraidos:
        documento.metadatos_extraidos = metadatos
    else:
        documento.metadatos_extraidos.update(metadatos)

    # Actualizar documento en el expediente
    expediente.documentos[doc_index] = documento

    # Registrar en historial
    entrada = EntradaHistorial(
        id=generate_id("HIST"),
        fecha=datetime.now(),
        usuario="Automático",
        tipo="AGENTE",
        accion="ACTUALIZAR_METADATOS_DOCUMENTO",
        detalles=f"Metadatos del documento {documento_id} actualizados (reemplazar={reemplazar})"
    )
    expediente.historial.append(entrada)

    # Guardar
    save_expediente(expediente)

    result = {
        "success": True,
        "documento_id": documento_id,
        "metadatos_anteriores": metadatos_anteriores,
        "metadatos_nuevos": documento.metadatos_extraidos,
        "mensaje": "Metadatos actualizados correctamente"
    }

    return [
        types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )
    ]


async def tool_crear_documento_desde_markdown(
    expediente_id: str,
    nombre: str,
    tipo: str,
    texto_markdown: str,
    metadatos: Dict[str, Any] = None
) -> List[types.TextContent]:
    """
    Crea un nuevo documento a partir de contenido markdown.

    Args:
        expediente_id: ID del expediente
        nombre: Nombre del documento
        tipo: Tipo de documento (INFORME, RESOLUCION, etc.)
        texto_markdown: Contenido en formato markdown
        metadatos: Metadatos opcionales del documento

    Returns:
        Resultado con el ID del documento creado

    Raises:
        AuthError: Si hay error al crear el documento
    """
    expediente = load_expediente(expediente_id)

    # Generar ID para el documento
    doc_id = generate_id("DOC")

    # Generar ruta
    ruta = f"data/documentos/{expediente_id}/{nombre}"

    # Calcular tamaño
    tamano_bytes = len(texto_markdown.encode('utf-8'))

    # Crear documento
    documento = Documento(
        id=doc_id,
        nombre=nombre,
        fecha=datetime.now(),
        tipo=tipo,
        ruta=ruta,
        hash_sha256="",  # En un sistema real, se calcularía el hash
        tamano_bytes=tamano_bytes,
        validado=None,
        metadatos_extraidos=metadatos,
        texto_markdown=texto_markdown
    )

    # Añadir a la lista de documentos
    expediente.documentos.append(documento)

    # Registrar en historial
    entrada = EntradaHistorial(
        id=generate_id("HIST"),
        fecha=datetime.now(),
        usuario="Automático",
        tipo="AGENTE",
        accion="CREAR_DOCUMENTO_MARKDOWN",
        detalles=f"Documento {doc_id} creado desde markdown: {nombre} (tipo: {tipo})"
    )
    expediente.historial.append(entrada)

    # Guardar
    save_expediente(expediente)

    result = {
        "success": True,
        "documento_id": doc_id,
        "nombre": nombre,
        "tipo": tipo,
        "ruta": ruta,
        "mensaje": f"Documento {doc_id} creado correctamente"
    }

    return [
        types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )
    ]
