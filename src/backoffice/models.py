# backoffice/models.py

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class AgentConfig:
    """Configuración de un agente"""
    nombre: str  # "ValidadorDocumental"
    system_prompt: str  # "Eres un validador..."
    modelo: str  # "claude-3-5-sonnet-20241022"
    herramientas: List[str]  # ["consultar_expediente", "actualizar_datos", ...]
    additional_goal: Optional[str] = None  # "Priorizar validación del NIF" (opcional, se añade al goal)


@dataclass
class AgentError:
    """Error de ejecución de agente"""
    codigo: str  # "AUTH_INVALID_TOKEN"
    mensaje: str  # "Token JWT inválido o expirado"
    detalle: Optional[str] = None


@dataclass
class AgentExecutionResult:
    """Resultado de ejecución de agente"""
    success: bool
    agent_run_id: str
    resultado: Dict[str, Any]  # {"completado": True, "mensaje": "...", "datos_actualizados": {...}}
    log_auditoria: List[str]  # ["Iniciando validación...", "Consultando expediente..."]
    herramientas_usadas: List[str]  # ["consultar_expediente", "actualizar_datos"]
    error: Optional[AgentError] = None


# Catálogo de códigos de error
ERROR_CODES = {
    # Errores de autenticación y autorización
    "AUTH_INVALID_TOKEN": "Token JWT inválido o mal formado",
    "AUTH_TOKEN_EXPIRED": "Token JWT expirado",
    "AUTH_TOKEN_NOT_YET_VALID": "Token JWT aún no válido (nbf)",
    "AUTH_PERMISSION_DENIED": "Permisos insuficientes",
    "AUTH_EXPEDIENTE_MISMATCH": "Token no autorizado para este expediente",
    "AUTH_INSUFFICIENT_PERMISSIONS": "Permisos insuficientes para la operación solicitada",

    # Errores de recursos
    "EXPEDIENTE_NOT_FOUND": "Expediente no encontrado",
    "DOCUMENTO_NOT_FOUND": "Documento no encontrado",

    # Errores de configuración
    "AGENT_NOT_CONFIGURED": "Tipo de agente no configurado",
    "AGENT_CONFIG_INVALID": "Configuración de agente inválida",

    # Errores de MCP
    "MCP_CONNECTION_ERROR": "Error al conectar con servidor MCP",
    "MCP_TIMEOUT": "Timeout en llamada a servidor MCP",
    "MCP_TOOL_ERROR": "Error al ejecutar tool MCP",
    "MCP_TOOL_NOT_FOUND": "Tool no encontrada en servidor MCP",
    "MCP_AUTH_ERROR": "Error de autenticación con servidor MCP",
    "MCP_SERVER_UNAVAILABLE": "Servidor MCP no disponible",
    "MCP_CONFLICT": "Conflicto de modificación concurrente",
    "MCP_UNEXPECTED_ERROR": "Error inesperado en cliente MCP",

    # Errores de validación
    "OUTPUT_VALIDATION_ERROR": "Output del agente no válido",
    "INPUT_VALIDATION_ERROR": "Parámetros de entrada inválidos",

    # Errores internos
    "INTERNAL_ERROR": "Error interno del sistema"
}
