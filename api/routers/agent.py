# api/routers/agent.py

"""
Endpoints para ejecución y gestión de agentes.

- POST /execute: Ejecuta un agente de forma asíncrona
- GET /status/{agent_run_id}: Consulta estado de ejecución
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, BackgroundTasks

from ..models import (
    ExecuteAgentRequest,
    ExecuteAgentResponse,
    AgentStatusResponse
)
from ..services.webhook import send_webhook
from ..services.task_tracker import get_task_tracker
from backoffice.executor_factory import create_default_executor
from backoffice.models import AgentConfig
from backoffice.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/execute",
    response_model=ExecuteAgentResponse,
    status_code=202,
    tags=["Agent"],
    summary="Ejecutar agente de forma asíncrona",
    description="Inicia la ejecución de un agente y retorna inmediatamente. "
                "El resultado se enviará al webhook_url cuando termine."
)
async def execute_agent(
    request: ExecuteAgentRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None)
):
    """
    Ejecuta un agente de forma asíncrona.

    **Flujo:**
    1. Valida JWT presente
    2. Crea executor con DI
    3. Registra tarea en tracker
    4. Inicia ejecución en background
    5. Retorna 202 Accepted inmediatamente

    **Callback:**
    Cuando el agente termine (éxito o error), se enviará un POST
    al webhook_url con el resultado completo.

    **Errores:**
    - 401: Token JWT ausente
    - 400: Request inválido (validación Pydantic)
    """

    # 1. Validar JWT presente
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Request sin token JWT")
        raise HTTPException(
            status_code=401,
            detail="Token JWT ausente. Header requerido: Authorization: Bearer <token>"
        )

    token = authorization.replace("Bearer ", "")

    # 2. Crear executor con implementaciones por defecto
    executor = create_default_executor(
        mcp_config_path=settings.MCP_CONFIG_PATH,
        jwt_secret=settings.JWT_SECRET,
        jwt_algorithm=settings.JWT_ALGORITHM
    )

    # 3. Convertir request a AgentConfig del backoffice
    agent_config = AgentConfig(
        nombre=request.agent_config.nombre,
        system_prompt=request.agent_config.system_prompt,
        modelo=request.agent_config.modelo,
        prompt_tarea=request.agent_config.prompt_tarea,
        herramientas=request.agent_config.herramientas
    )

    # 4. Generar run_id y registrar tarea
    agent_run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}"

    task_tracker = get_task_tracker()
    task_tracker.register(
        agent_run_id=agent_run_id,
        expediente_id=request.expediente_id,
        tarea_id=request.tarea_id
    )

    logger.info(
        f"Agente registrado: {agent_run_id} "
        f"(expediente={request.expediente_id}, tarea={request.tarea_id}, "
        f"agente={request.agent_config.nombre})"
    )

    # 5. Ejecutar en background
    background_tasks.add_task(
        execute_and_callback,
        executor=executor,
        token=token,
        expediente_id=request.expediente_id,
        tarea_id=request.tarea_id,
        agent_config=agent_config,
        agent_run_id=agent_run_id,
        webhook_url=request.webhook_url,
        timeout_seconds=request.timeout_seconds
    )

    # 6. Retornar 202 Accepted inmediatamente
    return ExecuteAgentResponse(
        agent_run_id=agent_run_id,
        message="Ejecución de agente iniciada",
        webhook_url=request.webhook_url
    )


async def execute_and_callback(
    executor,
    token: str,
    expediente_id: str,
    tarea_id: str,
    agent_config: AgentConfig,
    agent_run_id: str,
    webhook_url: str,
    timeout_seconds: int
):
    """
    Función auxiliar para ejecutar agente y enviar callback.

    Se ejecuta en background. No lanza excepciones al caller.

    Args:
        executor: AgentExecutor configurado
        token: JWT token
        expediente_id: ID del expediente
        tarea_id: ID de la tarea BPMN
        agent_config: Configuración del agente
        agent_run_id: ID único de esta ejecución
        webhook_url: URL para callback
        timeout_seconds: Timeout máximo
    """
    task_tracker = get_task_tracker()

    try:
        # Marcar como running
        task_tracker.mark_running(agent_run_id)
        logger.info(f"Ejecutando agente: {agent_run_id}")

        # Ejecutar con timeout
        result = await asyncio.wait_for(
            executor.execute(token, expediente_id, tarea_id, agent_config),
            timeout=timeout_seconds
        )

        # Marcar como completado
        task_tracker.mark_completed(agent_run_id, result)

        logger.info(
            f"Agente completado: {agent_run_id} "
            f"(success={result.success})"
        )

        # Enviar webhook
        webhook_sent = await send_webhook(webhook_url, agent_run_id, result=result)

        if not webhook_sent:
            logger.warning(
                f"Webhook NO enviado (pero agente completó): {agent_run_id}"
            )

    except asyncio.TimeoutError:
        # Timeout
        logger.error(
            f"Timeout ejecutando agente: {agent_run_id} "
            f"(timeout={timeout_seconds}s)"
        )

        error = {
            "codigo": "TIMEOUT",
            "mensaje": f"Ejecución excedió {timeout_seconds} segundos",
            "detalle": f"El agente no completó en el tiempo máximo permitido"
        }

        task_tracker.mark_failed(agent_run_id, error)
        await send_webhook(webhook_url, agent_run_id, error=error)

    except Exception as e:
        # Error inesperado
        logger.error(
            f"Error inesperado ejecutando agente: {agent_run_id} "
            f"({type(e).__name__}: {str(e)})",
            exc_info=True
        )

        error = {
            "codigo": "INTERNAL_ERROR",
            "mensaje": f"Error interno del sistema: {type(e).__name__}",
            "detalle": str(e)
        }

        task_tracker.mark_failed(agent_run_id, error)
        await send_webhook(webhook_url, agent_run_id, error=error)


@router.get(
    "/status/{agent_run_id}",
    response_model=AgentStatusResponse,
    tags=["Agent"],
    summary="Consultar estado de ejecución",
    description="Obtiene el estado actual de una ejecución de agente"
)
async def get_agent_status(agent_run_id: str):
    """
    Consulta el estado de una ejecución de agente.

    **Estados posibles:**
    - `pending`: Registrado pero aún no iniciado
    - `running`: En ejecución
    - `completed`: Completado (verificar campo `success`)
    - `failed`: Falló con error

    **Errores:**
    - 404: agent_run_id no encontrado
    """

    task_tracker = get_task_tracker()
    status = task_tracker.get_status(agent_run_id)

    if not status:
        logger.warning(f"Status no encontrado: {agent_run_id}")
        raise HTTPException(
            status_code=404,
            detail=f"agent_run_id no encontrado: {agent_run_id}"
        )

    return AgentStatusResponse(**status)
