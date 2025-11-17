"""
Modelos de datos para el MCP Mock de Expedientes.

Define la estructura de los expedientes, documentos, historial y metadatos BPMN
usando Pydantic para validación y serialización.
"""

from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field


class Solicitante(BaseModel):
    """Datos del solicitante de un expediente"""
    nombre: str
    nif: str
    direccion: str
    email: str
    telefono: str


class Documento(BaseModel):
    """Representa un documento adjunto a un expediente"""
    id: str
    nombre: str
    fecha: datetime
    tipo: str
    ruta: str
    hash_sha256: str
    tamano_bytes: int
    validado: Optional[bool] = None


class EntradaHistorial(BaseModel):
    """Entrada en el historial de acciones de un expediente"""
    id: str
    fecha: datetime
    usuario: str
    tipo: str  # SISTEMA, AGENTE, HUMANO, ANOTACION
    accion: str
    detalles: str


class FlujoBPMN(BaseModel):
    """Información del flujo BPMN asociado al expediente"""
    id: str
    nombre: str
    version: str
    fecha_inicio_flujo: datetime


class TareaActual(BaseModel):
    """Tarea BPMN actualmente en ejecución"""
    id: str
    nombre: str
    tipo: str  # agent, human, system
    fecha_inicio: datetime
    fecha_limite: datetime
    estado: str  # EN_EJECUCION, COMPLETADA, FALLIDA, TIMEOUT
    intentos: int
    responsable: str


class TareaCompletada(BaseModel):
    """Tarea BPMN que ha sido completada"""
    id: str
    nombre: str
    fecha_inicio: datetime
    fecha_fin: datetime
    responsable: str
    resultado: str


class CandidatoSiguienteTarea(BaseModel):
    """Candidato para la siguiente tarea en el flujo BPMN"""
    id: str
    nombre: str
    condicion: str  # Expresión que determina si esta tarea se activa


class SiguienteTarea(BaseModel):
    """Información sobre posibles siguientes tareas"""
    candidatos: List[CandidatoSiguienteTarea]


class Metadatos(BaseModel):
    """Metadatos del expediente relacionados con BPMN"""
    flujo_bpmn: FlujoBPMN
    tarea_actual: TareaActual
    tareas_completadas: List[TareaCompletada]
    siguiente_tarea: SiguienteTarea


class Expediente(BaseModel):
    """
    Modelo completo de un expediente.

    Incluye todos los datos del expediente, documentos asociados,
    historial de acciones y metadatos del flujo BPMN.
    """
    id: str
    tipo: str
    estado: str
    fecha_inicio: datetime
    datos: Dict[str, Any]  # Estructura flexible para datos específicos del tipo
    documentos: List[Documento]
    historial: List[EntradaHistorial]
    metadatos: Metadatos

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class JWTClaims(BaseModel):
    """Claims esperados en el token JWT"""
    sub: str  # Debe ser "Automático"
    iat: int  # Timestamp de emisión
    exp: int  # Timestamp de expiración
    nbf: int  # Not before timestamp
    iss: str  # Emisor (debe ser "agentix-bpmn")
    aud: List[str] | str  # Audiencia (puede ser string o lista de strings)
    jti: str  # ID único del token
    exp_id: str  # ID del expediente autorizado
    exp_tipo: str  # Tipo de expediente
    tarea_id: str  # ID de la tarea BPMN
    tarea_nombre: str  # Nombre de la tarea
    permisos: List[str]  # ["consulta"] o ["consulta", "gestion"]
