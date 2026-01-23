# backoffice/tasks/agent_execution.py

"""
Tarea Celery para ejecución de agentes.

Esta tarea se ejecuta en workers Celery distribuidos, permitiendo:
- Escalado horizontal (múltiples workers)
- Reintentos automáticos con backoff exponencial
- Persistencia de estado en Redis
- Monitoreo vía Flower

IMPORTANTE: Todos los logs usan AuditLogger para redacción automática de PII
(GDPR/LOPD/ENS compliance). Ver P4 en code-review/commit-41f313a.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from prometheus_client import Counter, Histogram

from backoffice.celery_app import celery_app
from backoffice.executor_factory import create_default_executor
from backoffice.logging.audit_logger import AuditLogger
from backoffice.models import AgentConfig
from backoffice.settings import settings

# Logger estándar solo para mensajes de debug sin PII
logger = logging.getLogger(__name__)

# Métricas Prometheus
task_counter = Counter(
    'agentix_celery_tasks_total',
    'Total tareas Celery procesadas',
    ['agent_name', 'status']
)

# P1: Buckets configurables via PROMETHEUS_DURATION_BUCKETS
# Ver code-review/commit-41f313a/plan-mejoras.md
task_duration = Histogram(
    'agentix_celery_task_duration_seconds',
    'Duración ejecución agente en Celery',
    ['agent_name'],
    buckets=settings.prometheus_duration_buckets
)


class AgentExecutionTask(Task):
    """
    Clase base para tareas de ejecución de agentes.

    Añade retry automático con backoff exponencial y logging mejorado.
    """

    # Reintentar en caso de excepciones transitorias
    autoretry_for = (ConnectionError, TimeoutError, OSError)

    # Configuración de reintentos
    retry_kwargs = {
        'max_retries': 3,
        'countdown': 5  # Segundos antes del primer reintento
    }

    # Backoff exponencial y jitter para evitar thundering herd
    retry_backoff = True
    retry_backoff_max = 300  # Máximo 5 minutos entre reintentos
    retry_jitter = True


def _run_async(coro):
    """
    Ejecuta una corutina desde contexto síncrono (Celery).

    Crea un nuevo event loop si es necesario, ya que Celery
    ejecuta las tareas en threads sin event loop.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Si ya hay un loop, crear uno nuevo
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        # No hay event loop, crear uno nuevo
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(coro)
    finally:
        # No cerrar el loop para reutilización
        pass


@celery_app.task(
    bind=True,
    base=AgentExecutionTask,
    name='backoffice.execute_agent',
    soft_time_limit=settings.CELERY_TASK_TIME_LIMIT - 60,  # Soft limit 1 min antes
    time_limit=settings.CELERY_TASK_TIME_LIMIT
)
def execute_agent_task(
    self,
    token: str,
    expediente_id: str,
    tarea_id: str,
    agent_config_dict: Dict[str, Any],
    callback_url: Optional[str] = None,
    timeout_seconds: Optional[int] = None
) -> Dict[str, Any]:
    """
    Tarea Celery para ejecutar un agente.

    Args:
        token: JWT token completo
        expediente_id: ID del expediente
        tarea_id: ID de la tarea BPMN
        agent_config_dict: Dict serializable con config del agente
        callback_url: URL para webhook (opcional)
        timeout_seconds: Timeout específico para este agente (opcional)

    Returns:
        Dict con resultado serializable:
        {
            "success": bool,
            "agent_run_id": str,
            "resultado": Dict,
            "herramientas_usadas": List[str],
            "error": Optional[Dict],
            "log_auditoria": List[str]
        }

    Raises:
        Propaga excepciones para retry automático en fallos transitorios.
    """
    # El task_id de Celery es nuestro agent_run_id
    agent_run_id = self.request.id
    agent_name = agent_config_dict.get('nombre', 'unknown')
    start_time = time.time()

    # Crear AuditLogger para redacción automática de PII (GDPR/LOPD/ENS)
    # Los logs se guardan en /logs/{expediente_id}/{agent_run_id}.log
    task_logger = AuditLogger(
        expediente_id=expediente_id,
        agent_run_id=agent_run_id,
        log_dir=settings.LOG_DIR
    )

    task_logger.log(
        f"[Celery] Iniciando ejecución: task_id={agent_run_id}, "
        f"expediente={expediente_id}, agente={agent_name}"
    )

    try:
        # Actualizar estado en TaskTracker a "running"
        _update_task_status(agent_run_id, 'running', task_logger)

        # Convertir dict a AgentConfig
        config = AgentConfig(
            nombre=agent_config_dict['nombre'],
            system_prompt=agent_config_dict['system_prompt'],
            modelo=agent_config_dict['modelo'],
            herramientas=agent_config_dict['herramientas'],
            additional_goal=agent_config_dict.get('additional_goal')
        )

        # Crear executor
        executor = create_default_executor(
            mcp_config_path=settings.MCP_CONFIG_PATH,
            jwt_secret=settings.JWT_SECRET,
            jwt_algorithm=settings.JWT_ALGORITHM
        )

        # Ejecutar agente (async to sync)
        result = _run_async(
            executor.execute(token, expediente_id, tarea_id, config)
        )

        # Registrar métricas de éxito
        duration = time.time() - start_time
        task_counter.labels(agent_name=agent_name, status='success').inc()
        task_duration.labels(agent_name=agent_name).observe(duration)

        task_logger.log(
            f"[Celery] Completado: task_id={agent_run_id}, "
            f"success={result.success}, duration={duration:.2f}s"
        )

        # Preparar resultado serializable
        result_dict = {
            "success": result.success,
            "agent_run_id": agent_run_id,
            "resultado": result.resultado,
            "herramientas_usadas": result.herramientas_usadas,
            "error": _error_to_dict(result.error) if result.error else None,
            "log_auditoria": result.log_auditoria
        }

        # Actualizar estado final en TaskTracker
        _update_task_completed(agent_run_id, result, task_logger)

        # Enviar webhook si hay callback_url
        if callback_url:
            _send_webhook_async(callback_url, agent_run_id, result, task_logger)

        return result_dict

    except SoftTimeLimitExceeded:
        # Soft timeout - intentar limpiar antes del hard timeout
        duration = time.time() - start_time
        task_counter.labels(agent_name=agent_name, status='timeout').inc()

        task_logger.error(
            f"[Celery] Soft timeout: task_id={agent_run_id}, "
            f"duration={duration:.2f}s"
        )

        error_dict = {
            "codigo": "TIMEOUT",
            "mensaje": f"Ejecución excedió el tiempo límite ({timeout_seconds or settings.CELERY_TASK_TIME_LIMIT}s)",
            "detalle": f"task_id={agent_run_id}"
        }

        _update_task_failed(agent_run_id, error_dict, task_logger)

        if callback_url:
            _send_webhook_error(callback_url, agent_run_id, error_dict, task_logger)

        return {
            "success": False,
            "agent_run_id": agent_run_id,
            "resultado": {},
            "herramientas_usadas": [],
            "error": error_dict,
            "log_auditoria": task_logger.get_log_entries()
        }

    except Exception as e:
        # Error inesperado
        duration = time.time() - start_time
        task_counter.labels(agent_name=agent_name, status='failed').inc()

        # Usar AuditLogger para redactar PII en str(e)
        # str(e) puede contener datos personales del expediente
        task_logger.error(
            f"[Celery] Error: task_id={agent_run_id}, "
            f"error={type(e).__name__}: {str(e)}, "
            f"duration={duration:.2f}s"
        )

        # También log a debug para traceback completo (sin PII en el tipo de excepción)
        logger.debug(f"Traceback for task {agent_run_id}", exc_info=True)

        error_dict = {
            "codigo": "INTERNAL_ERROR",
            "mensaje": f"Error interno: {type(e).__name__}",
            "detalle": str(e)  # Se redactará cuando se devuelva en log_auditoria
        }

        _update_task_failed(agent_run_id, error_dict, task_logger)

        if callback_url:
            _send_webhook_error(callback_url, agent_run_id, error_dict, task_logger)

        # Propagar excepción para retry automático si es transitoria
        raise


def _error_to_dict(error) -> Dict[str, Any]:
    """Convierte AgentError a dict serializable."""
    if error is None:
        return None
    return {
        "codigo": error.codigo,
        "mensaje": error.mensaje,
        "detalle": error.detalle
    }


def _update_task_status(
    agent_run_id: str,
    status: str,
    task_logger: Optional[AuditLogger] = None
) -> None:
    """Actualiza estado de tarea en TaskTracker (Redis)."""
    try:
        from api.services.task_tracker import get_task_tracker
        tracker = get_task_tracker()
        if status == 'running':
            tracker.mark_running(agent_run_id)
    except Exception as e:
        # Usar AuditLogger si disponible, sino logger estándar
        if task_logger:
            task_logger.warning(f"No se pudo actualizar TaskTracker: {e}")
        else:
            logger.warning(f"No se pudo actualizar TaskTracker (sin contexto PII): {e}")


def _update_task_completed(
    agent_run_id: str,
    result,
    task_logger: Optional[AuditLogger] = None
) -> None:
    """Marca tarea como completada en TaskTracker."""
    try:
        from api.services.task_tracker import get_task_tracker
        tracker = get_task_tracker()
        tracker.mark_completed(agent_run_id, result)
    except Exception as e:
        if task_logger:
            task_logger.warning(f"No se pudo marcar completada en TaskTracker: {e}")
        else:
            logger.warning(f"No se pudo marcar completada en TaskTracker (sin contexto PII): {e}")


def _update_task_failed(
    agent_run_id: str,
    error_dict: Dict[str, str],
    task_logger: Optional[AuditLogger] = None
) -> None:
    """Marca tarea como fallida en TaskTracker."""
    try:
        from api.services.task_tracker import get_task_tracker
        tracker = get_task_tracker()
        tracker.mark_failed(agent_run_id, error_dict)
    except Exception as e:
        if task_logger:
            task_logger.warning(f"No se pudo marcar fallida en TaskTracker: {e}")
        else:
            logger.warning(f"No se pudo marcar fallida en TaskTracker (sin contexto PII): {e}")


def _send_webhook_async(
    callback_url: str,
    agent_run_id: str,
    result,
    task_logger: Optional[AuditLogger] = None
) -> None:
    """Envía webhook con resultado exitoso."""
    try:
        from api.services.webhook import send_webhook_with_retry

        _run_async(
            send_webhook_with_retry(
                callback_url,
                agent_run_id,
                result=result if result.success else None,
                error=_error_to_dict(result.error) if result.error else None
            )
        )
    except Exception as e:
        # Usar AuditLogger para redactar PII en mensajes de error
        if task_logger:
            task_logger.error(f"Error enviando webhook: {e}")
        else:
            logger.error(f"Error enviando webhook (sin contexto PII): {e}")


def _send_webhook_error(
    callback_url: str,
    agent_run_id: str,
    error_dict: Dict[str, str],
    task_logger: Optional[AuditLogger] = None
) -> None:
    """Envía webhook con error."""
    try:
        from api.services.webhook import send_webhook_with_retry

        _run_async(
            send_webhook_with_retry(
                callback_url,
                agent_run_id,
                error=error_dict
            )
        )
    except Exception as e:
        if task_logger:
            task_logger.error(f"Error enviando webhook de error: {e}")
        else:
            logger.error(f"Error enviando webhook de error (sin contexto PII): {e}")
