# api/routers/agent.py

"""
Endpoints para ejecución y gestión de agentes.

- POST /execute: Ejecuta un agente de forma asíncrona
- GET /status/{agent_run_id}: Consulta estado de ejecución
- GET /agents: Lista agentes disponibles

Soporta dos modos de ejecución según USE_CELERY:
- false: BackgroundTasks (desarrollo, testing)
- true: Celery + Redis (producción, escalable)
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, BackgroundTasks

from ..models import (
    ExecuteAgentRequest,
    ExecuteAgentResponse,
    AgentStatusResponse,
    ListAgentsResponse,
    AgentInfo
)
from ..services.webhook import send_webhook
from ..services.task_tracker import get_task_tracker
from backoffice.executor_factory import create_default_executor
from backoffice.models import AgentConfig
from backoffice.settings import settings
from backoffice.config import get_agent_loader

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/agents",
    response_model=ListAgentsResponse,
    summary="Listar agentes disponibles",
    description="Obtiene la lista de agentes configurados y sus descripciones"
)
async def list_agents():
    """
    Lista los agentes disponibles para ejecución.

    **Uso:**
    Permite al BPMN descubrir qué agentes están configurados
    y qué permisos requieren antes de invocarlos.

    **Response:**
    Lista de agentes con nombre, descripción y permisos requeridos.
    """
    agent_loader = get_agent_loader()
    agents = agent_loader.list_agents()

    return ListAgentsResponse(
        agents=[
            AgentInfo(
                name=agent.name,
                description=agent.description,
                required_permissions=agent.required_permissions
            )
            for agent in agents
        ]
    )


@router.post(
    "/execute",
    response_model=ExecuteAgentResponse,
    status_code=202,
    summary="Ejecutar agente de forma asíncrona",
    description="Inicia la ejecución de un agente y retorna inmediatamente. "
                "El resultado se enviará al callback_url cuando termine (si se especifica)."
)
async def execute_agent(
    request: ExecuteAgentRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None)
):
    """
    Ejecuta un agente de forma asíncrona.

    **Request simplificado:**
    - `agent`: Nombre del agente (debe existir en agents.yaml)
    - `additional_goal`: Objetivo adicional opcional que se añade al goal del agente
    - `context`: expediente_id y tarea_id
    - `callback_url`: URL de callback (opcional)

    **Flujo:**
    1. Valida JWT presente
    2. Carga configuración del agente desde YAML
    3. Crea executor con DI
    4. Registra tarea en tracker
    5. Inicia ejecución en background (Celery o BackgroundTasks según USE_CELERY)
    6. Retorna 202 Accepted inmediatamente

    **Callback:**
    Si se especifica callback_url, cuando el agente termine (éxito o error),
    se enviará un POST con el resultado completo.

    **Errores:**
    - 401: Token JWT ausente
    - 404: Agente no encontrado
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

    logger.info(f"token JWT recibido para ejecución de agente {token[:50]}")

    # 2. Cargar configuración del agente desde YAML
    agent_loader = get_agent_loader()

    if not agent_loader.exists(request.agent):
        available_agents = agent_loader.list_agent_names()
        logger.warning(f"Agente no encontrado: {request.agent}")
        raise HTTPException(
            status_code=404,
            detail=f"Agente '{request.agent}' no encontrado. "
                   f"Agentes disponibles: {available_agents}"
        )

    agent_definition = agent_loader.get(request.agent)

    # 3. Construir AgentConfig combinando YAML + request
    # El additional_goal se añadirá al goal del agente definido en YAML
    # Para agentes CrewAI, el modelo está en llm.model
    modelo = agent_definition.model
    if agent_definition.is_crewai and agent_definition.llm:
        modelo = agent_definition.llm.model

    agent_config = AgentConfig(
        nombre=agent_definition.name,
        system_prompt=agent_definition.system_prompt,
        modelo=modelo,
        herramientas=agent_definition.tools,
        additional_goal=request.additional_goal  # Se interpola en {additional_goal} del goal
    )

    # 4. Determinar callback_url y timeout
    callback_url = str(request.callback_url) if request.callback_url else None
    timeout_seconds = agent_definition.timeout_seconds

    # 5. Elegir modo de ejecución según USE_CELERY
    if settings.USE_CELERY:
        # Modo Celery: encolar tarea en Redis
        agent_run_id = _execute_with_celery(
            token=token,
            expediente_id=request.context.expediente_id,
            tarea_id=request.context.tarea_id,
            agent_config=agent_config,
            callback_url=callback_url,
            timeout_seconds=timeout_seconds
        )
        message = "Ejecución de agente encolada en Celery"
    else:
        # Modo BackgroundTasks: ejecución en proceso
        agent_run_id = _execute_with_background_tasks(
            background_tasks=background_tasks,
            token=token,
            expediente_id=request.context.expediente_id,
            tarea_id=request.context.tarea_id,
            agent_config=agent_config,
            callback_url=callback_url,
            timeout_seconds=timeout_seconds
        )
        message = "Ejecución de agente iniciada"

    logger.info(
        f"Agente registrado: {agent_run_id} "
        f"(expediente={request.context.expediente_id}, "
        f"tarea={request.context.tarea_id}, "
        f"agente={request.agent}, "
        f"mode={'celery' if settings.USE_CELERY else 'background'})"
    )

    # 6. Retornar 202 Accepted inmediatamente
    return ExecuteAgentResponse(
        agent_run_id=agent_run_id,
        message=message,
        callback_url=callback_url
    )


def _execute_with_celery(
    token: str,
    expediente_id: str,
    tarea_id: str,
    agent_config: AgentConfig,
    callback_url: Optional[str],
    timeout_seconds: int
) -> str:
    """
    Ejecuta agente usando Celery (modo distribuido).

    Args:
        token: JWT token
        expediente_id: ID del expediente
        tarea_id: ID de la tarea BPMN
        agent_config: Configuración del agente
        callback_url: URL para callback (puede ser None)
        timeout_seconds: Timeout máximo

    Returns:
        agent_run_id (= Celery task ID)
    """
    from backoffice.tasks import execute_agent_task

    # Serializar AgentConfig a dict para Celery (JSON serializable)
    agent_config_dict = {
        "nombre": agent_config.nombre,
        "system_prompt": agent_config.system_prompt,
        "modelo": agent_config.modelo,
        "herramientas": agent_config.herramientas,
        "additional_goal": agent_config.additional_goal
    }

    # Encolar tarea en Celery
    celery_task = execute_agent_task.delay(
        token=token,
        expediente_id=expediente_id,
        tarea_id=tarea_id,
        agent_config_dict=agent_config_dict,
        callback_url=callback_url,
        timeout_seconds=timeout_seconds
    )

    # El task_id de Celery es nuestro agent_run_id
    agent_run_id = celery_task.id

    # Registrar en TaskTracker (Redis)
    task_tracker = get_task_tracker()
    task_tracker.register(
        agent_run_id=agent_run_id,
        expediente_id=expediente_id,
        tarea_id=tarea_id
    )

    logger.info(f"[Celery] Tarea encolada: {agent_run_id}")

    return agent_run_id


def _execute_with_background_tasks(
    background_tasks: BackgroundTasks,
    token: str,
    expediente_id: str,
    tarea_id: str,
    agent_config: AgentConfig,
    callback_url: Optional[str],
    timeout_seconds: int
) -> str:
    """
    Ejecuta agente usando BackgroundTasks (modo local).

    Args:
        background_tasks: FastAPI BackgroundTasks
        token: JWT token
        expediente_id: ID del expediente
        tarea_id: ID de la tarea BPMN
        agent_config: Configuración del agente
        callback_url: URL para callback (puede ser None)
        timeout_seconds: Timeout máximo

    Returns:
        agent_run_id generado localmente
    """
    # Crear executor
    executor = create_default_executor(
        mcp_config_path=settings.MCP_CONFIG_PATH,
        jwt_secret=settings.JWT_SECRET,
        jwt_algorithm=settings.JWT_ALGORITHM
    )

    # Generar run_id y registrar tarea
    agent_run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}"

    task_tracker = get_task_tracker()
    task_tracker.register(
        agent_run_id=agent_run_id,
        expediente_id=expediente_id,
        tarea_id=tarea_id
    )

    # Ejecutar en background
    background_tasks.add_task(
        execute_and_callback,
        executor=executor,
        token=token,
        expediente_id=expediente_id,
        tarea_id=tarea_id,
        agent_config=agent_config,
        agent_run_id=agent_run_id,
        callback_url=callback_url,
        timeout_seconds=timeout_seconds
    )

    return agent_run_id


async def execute_and_callback(
    executor,
    token: str,
    expediente_id: str,
    tarea_id: str,
    agent_config: AgentConfig,
    agent_run_id: str,
    callback_url: Optional[str],
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
        callback_url: URL para callback (puede ser None)
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

        # Enviar webhook solo si hay callback_url
        if callback_url:
            webhook_sent = await send_webhook(callback_url, agent_run_id, result=result)

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

        if callback_url:
            await send_webhook(callback_url, agent_run_id, error=error)

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

        if callback_url:
            await send_webhook(callback_url, agent_run_id, error=error)


@router.get(
    "/status/{agent_run_id}",
    response_model=AgentStatusResponse,
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
        # Si usamos Celery, intentar fallback a estado de Celery
        if settings.USE_CELERY:
            status = _get_celery_task_status(agent_run_id)

    if not status:
        logger.warning(f"Status no encontrado: {agent_run_id}")
        raise HTTPException(
            status_code=404,
            detail=f"agent_run_id no encontrado: {agent_run_id}"
        )

    return AgentStatusResponse(**status)


def _get_celery_task_status(agent_run_id: str) -> Optional[dict]:
    """
    Fallback: obtiene estado desde Celery directamente.

    Útil si el TaskTracker no tiene la información pero
    Celery sí la tiene.
    """
    try:
        from celery.result import AsyncResult
        from backoffice.celery_app import celery_app

        celery_result = AsyncResult(agent_run_id, app=celery_app)

        if celery_result.state == 'PENDING':
            # PENDING puede significar que no existe o que está en cola
            return None

        # Mapear estados Celery a nuestro formato
        status_map = {
            'PENDING': 'pending',
            'STARTED': 'running',
            'RETRY': 'running',
            'SUCCESS': 'completed',
            'FAILURE': 'failed'
        }

        status = status_map.get(celery_result.state, 'unknown')
        success = celery_result.successful() if celery_result.ready() else None

        result_dict = {
            "agent_run_id": agent_run_id,
            "expediente_id": "unknown",  # No disponible desde Celery directamente
            "tarea_id": "unknown",
            "status": status,
            "started_at": None,
            "completed_at": None,
            "elapsed_seconds": 0,
            "success": success,
            "resultado": celery_result.result if celery_result.successful() else None,
            "error": {"mensaje": str(celery_result.result)} if celery_result.failed() else None
        }

        return result_dict

    except Exception as e:
        logger.debug(f"No se pudo obtener estado de Celery: {e}")
        return None
