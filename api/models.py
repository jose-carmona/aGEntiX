# api/models.py

"""
Modelos Pydantic para la API REST.

Define los schemas de request/response para todos los endpoints,
con validación automática y documentación OpenAPI.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class AgentConfigRequest(BaseModel):
    """Configuración de agente para ejecución"""

    nombre: str = Field(
        ...,
        example="ValidadorDocumental",
        description="Nombre del agente a ejecutar"
    )
    system_prompt: str = Field(
        ...,
        example="Eres un validador de documentación administrativa",
        description="Prompt del sistema para el agente"
    )
    modelo: str = Field(
        ...,
        example="claude-3-5-sonnet-20241022",
        description="Modelo de LLM a utilizar"
    )
    prompt_tarea: str = Field(
        ...,
        example="Valida que todos los documentos estén presentes y sean válidos",
        description="Prompt específico de la tarea"
    )
    herramientas: List[str] = Field(
        ...,
        example=["consultar_expediente", "actualizar_datos"],
        description="Lista de herramientas MCP que puede usar el agente"
    )


class ExecuteAgentRequest(BaseModel):
    """Request para ejecutar un agente"""

    expediente_id: str = Field(
        ...,
        example="EXP-2024-001",
        description="ID del expediente a procesar"
    )
    tarea_id: str = Field(
        ...,
        example="TAREA-VALIDAR-DOC",
        description="ID de la tarea BPMN"
    )
    agent_config: AgentConfigRequest = Field(
        ...,
        description="Configuración del agente"
    )
    webhook_url: str = Field(
        ...,
        example="https://bpmn.example.com/api/v1/tasks/callback",
        description="URL donde enviar el resultado cuando termine"
    )
    timeout_seconds: int = Field(
        300,
        ge=10,
        le=600,
        description="Timeout máximo de ejecución en segundos (10-600)"
    )


class ExecuteAgentResponse(BaseModel):
    """Response al iniciar ejecución de agente"""

    status: str = Field(
        "accepted",
        description="Estado de la solicitud (accepted)"
    )
    agent_run_id: str = Field(
        ...,
        example="RUN-20241208-143022-123456",
        description="ID único de esta ejecución"
    )
    message: str = Field(
        ...,
        example="Ejecución de agente iniciada",
        description="Mensaje informativo"
    )
    webhook_url: str = Field(
        ...,
        example="https://bpmn.example.com/api/v1/tasks/callback",
        description="URL donde se enviará el resultado"
    )


class AgentStatusResponse(BaseModel):
    """Response al consultar estado de ejecución"""

    agent_run_id: str = Field(
        ...,
        example="RUN-20241208-143022-123456",
        description="ID de la ejecución"
    )
    status: str = Field(
        ...,
        example="running",
        description="Estado: running, completed, failed"
    )
    expediente_id: str = Field(
        ...,
        example="EXP-2024-001",
        description="ID del expediente"
    )
    tarea_id: str = Field(
        ...,
        example="TAREA-VALIDAR-DOC",
        description="ID de la tarea BPMN"
    )
    started_at: str = Field(
        ...,
        example="2024-12-08T14:30:22Z",
        description="Timestamp de inicio (ISO 8601)"
    )
    completed_at: Optional[str] = Field(
        None,
        example="2024-12-08T14:35:22Z",
        description="Timestamp de finalización (si completado)"
    )
    elapsed_seconds: int = Field(
        ...,
        example=45,
        description="Segundos transcurridos"
    )
    success: Optional[bool] = Field(
        None,
        description="True si completó exitosamente (si completado)"
    )
    resultado: Optional[Dict[str, Any]] = Field(
        None,
        description="Resultado del agente (si completado exitosamente)"
    )
    error: Optional[Dict[str, str]] = Field(
        None,
        description="Detalle del error (si falló)"
    )


class HealthResponse(BaseModel):
    """Response del health check"""

    status: str = Field(
        ...,
        example="healthy",
        description="Estado general: healthy, unhealthy"
    )
    timestamp: str = Field(
        ...,
        example="2024-12-08T14:30:22Z",
        description="Timestamp del check (ISO 8601)"
    )
    version: str = Field(
        ...,
        example="1.0.0",
        description="Versión de la API"
    )
    dependencies: Dict[str, str] = Field(
        ...,
        example={"mcp_expedientes": "healthy"},
        description="Estado de dependencias externas"
    )


class WebhookPayload(BaseModel):
    """Payload enviado al webhook del BPMN"""

    agent_run_id: str = Field(..., description="ID de la ejecución")
    status: str = Field(..., description="completed o failed")
    success: bool = Field(..., description="True si éxito, False si error")
    timestamp: str = Field(..., description="Timestamp ISO 8601")
    resultado: Optional[Dict[str, Any]] = Field(None, description="Resultado si éxito")
    herramientas_usadas: Optional[List[str]] = Field(None, description="Tools usados")
    error: Optional[Dict[str, str]] = Field(None, description="Error si falló")


class ErrorResponse(BaseModel):
    """Response de error estándar"""

    detail: str = Field(
        ...,
        example="Token JWT ausente",
        description="Descripción del error"
    )
    status_code: int = Field(
        ...,
        example=401,
        description="Código HTTP del error"
    )
