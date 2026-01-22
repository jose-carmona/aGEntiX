# api/services/task_tracker_redis.py

"""
Task Tracker con backend Redis para estado distribuido.

Este tracker permite que múltiples instancias de API compartan
el estado de las ejecuciones de agentes.

Claves Redis:
- agentix:task:{agent_run_id} -> JSON con estado de tarea

TTL: 7 días (604800 segundos) para auto-limpieza
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Any

from redis import Redis

from backoffice.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class TaskTrackerRedis:
    """
    Tracker distribuido usando Redis.

    Reemplaza TaskTrackerInMemory para permitir múltiples
    instancias de API compartiendo estado.

    Thread-safe y process-safe gracias a Redis.
    """

    KEY_PREFIX = "agentix:task:"
    TTL_SECONDS = 604800  # 7 días

    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Inicializa el tracker con cliente Redis.

        Args:
            redis_client: Cliente Redis opcional (para testing).
                         Si no se proporciona, usa el cliente global.
        """
        self._redis = redis_client or get_redis_client()

    def _task_key(self, agent_run_id: str) -> str:
        """Construye clave Redis para una tarea."""
        return f"{self.KEY_PREFIX}{agent_run_id}"

    def register(
        self,
        agent_run_id: str,
        expediente_id: str,
        tarea_id: str
    ) -> None:
        """
        Registra una nueva tarea.

        Args:
            agent_run_id: ID único de la ejecución
            expediente_id: ID del expediente
            tarea_id: ID de la tarea BPMN
        """
        task_data = {
            "agent_run_id": agent_run_id,
            "expediente_id": expediente_id,
            "tarea_id": tarea_id,
            "status": "pending",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "elapsed_seconds": 0,
            "success": None,
            "resultado": None,
            "error": None
        }

        key = self._task_key(agent_run_id)
        self._redis.setex(
            key,
            self.TTL_SECONDS,
            json.dumps(task_data)
        )

        logger.debug(f"TaskTracker[Redis]: Tarea registrada {agent_run_id}")

    def mark_running(self, agent_run_id: str) -> None:
        """
        Marca tarea como en ejecución.

        Args:
            agent_run_id: ID de la ejecución
        """
        key = self._task_key(agent_run_id)
        data_str = self._redis.get(key)

        if data_str:
            task_data = json.loads(data_str)
            task_data["status"] = "running"
            self._redis.setex(key, self.TTL_SECONDS, json.dumps(task_data))
            logger.debug(f"TaskTracker[Redis]: Tarea running {agent_run_id}")
        else:
            logger.warning(f"TaskTracker[Redis]: Tarea no encontrada {agent_run_id}")

    def mark_completed(self, agent_run_id: str, result: Any) -> None:
        """
        Marca tarea como completada.

        Args:
            agent_run_id: ID de la ejecución
            result: AgentExecutionResult del backoffice
        """
        key = self._task_key(agent_run_id)
        data_str = self._redis.get(key)

        if data_str:
            task_data = json.loads(data_str)
            task_data["status"] = "completed"
            task_data["completed_at"] = datetime.now(timezone.utc).isoformat()
            task_data["success"] = result.success
            task_data["resultado"] = result.resultado

            if result.success:
                task_data["error"] = None
            else:
                task_data["error"] = {
                    "codigo": result.error.codigo if result.error else "UNKNOWN",
                    "mensaje": result.error.mensaje if result.error else "Error desconocido",
                    "detalle": result.error.detalle if result.error else ""
                }

            # Calcular elapsed_seconds
            started = datetime.fromisoformat(task_data["started_at"])
            completed = datetime.fromisoformat(task_data["completed_at"])
            task_data["elapsed_seconds"] = int((completed - started).total_seconds())

            self._redis.setex(key, self.TTL_SECONDS, json.dumps(task_data))
            logger.debug(
                f"TaskTracker[Redis]: Tarea completada {agent_run_id}, "
                f"success={result.success}"
            )
        else:
            logger.warning(f"TaskTracker[Redis]: Tarea no encontrada {agent_run_id}")

    def mark_failed(self, agent_run_id: str, error: Dict[str, str]) -> None:
        """
        Marca tarea como fallida.

        Args:
            agent_run_id: ID de la ejecución
            error: Dict con codigo, mensaje, detalle
        """
        key = self._task_key(agent_run_id)
        data_str = self._redis.get(key)

        if data_str:
            task_data = json.loads(data_str)
            task_data["status"] = "failed"
            task_data["completed_at"] = datetime.now(timezone.utc).isoformat()
            task_data["success"] = False
            task_data["error"] = error

            # Calcular elapsed_seconds
            started = datetime.fromisoformat(task_data["started_at"])
            completed = datetime.fromisoformat(task_data["completed_at"])
            task_data["elapsed_seconds"] = int((completed - started).total_seconds())

            self._redis.setex(key, self.TTL_SECONDS, json.dumps(task_data))
            logger.debug(
                f"TaskTracker[Redis]: Tarea fallida {agent_run_id}, "
                f"error={error.get('codigo')}"
            )
        else:
            logger.warning(f"TaskTracker[Redis]: Tarea no encontrada {agent_run_id}")

    def get_status(self, agent_run_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene estado de una tarea.

        Args:
            agent_run_id: ID de la ejecución

        Returns:
            Dict con estado completo o None si no existe
        """
        key = self._task_key(agent_run_id)
        data_str = self._redis.get(key)

        if not data_str:
            return None

        task_data = json.loads(data_str)

        # Si está running, calcular elapsed_seconds actual
        if task_data["status"] == "running":
            started = datetime.fromisoformat(task_data["started_at"])
            now = datetime.now(timezone.utc)
            task_data["elapsed_seconds"] = int((now - started).total_seconds())

        return task_data

    def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """
        Limpia tareas antiguas.

        Nota: Con Redis y TTL, la limpieza es automática.
        Este método está para compatibilidad con la interfaz.

        Args:
            max_age_hours: Edad máxima en horas (ignorado, usa TTL de Redis)

        Returns:
            Número de tareas eliminadas (siempre 0, Redis limpia automáticamente)
        """
        # Redis maneja la expiración automáticamente via TTL
        logger.debug("TaskTracker[Redis]: cleanup_old_tasks no es necesario (TTL)")
        return 0

    def exists(self, agent_run_id: str) -> bool:
        """
        Verifica si una tarea existe.

        Args:
            agent_run_id: ID de la ejecución

        Returns:
            True si la tarea existe
        """
        key = self._task_key(agent_run_id)
        return self._redis.exists(key) > 0

    def get_ttl(self, agent_run_id: str) -> int:
        """
        Obtiene TTL restante de una tarea.

        Args:
            agent_run_id: ID de la ejecución

        Returns:
            Segundos restantes de TTL, -1 si no existe TTL, -2 si no existe la clave
        """
        key = self._task_key(agent_run_id)
        return self._redis.ttl(key)
