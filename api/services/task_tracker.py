# api/services/task_tracker.py

"""
Task Tracker para seguimiento de ejecuciones de agentes.

Mantiene en memoria el estado de las ejecuciones asíncronas.
En producción (Paso 5) esto será reemplazado por Redis.
"""

from datetime import datetime, timezone
from typing import Dict, Optional, Any
from threading import Lock


class TaskTracker:
    """
    Tracker simple en memoria para estado de tareas asíncronas.

    Thread-safe mediante Lock.
    """

    def __init__(self):
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

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
        with self._lock:
            self._tasks[agent_run_id] = {
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

    def mark_running(self, agent_run_id: str) -> None:
        """Marca tarea como en ejecución"""
        with self._lock:
            if agent_run_id in self._tasks:
                self._tasks[agent_run_id]["status"] = "running"

    def mark_completed(self, agent_run_id: str, result: Any) -> None:
        """
        Marca tarea como completada.

        Args:
            agent_run_id: ID de la ejecución
            result: AgentExecutionResult del backoffice
        """
        with self._lock:
            if agent_run_id in self._tasks:
                task = self._tasks[agent_run_id]
                task["status"] = "completed"
                task["completed_at"] = datetime.now(timezone.utc).isoformat()
                task["success"] = result.success
                task["resultado"] = result.resultado
                task["error"] = None if result.success else {
                    "codigo": result.error.codigo if result.error else "UNKNOWN",
                    "mensaje": result.error.mensaje if result.error else "Error desconocido",
                    "detalle": result.error.detalle if result.error else ""
                }

                # Calcular elapsed_seconds
                started = datetime.fromisoformat(task["started_at"])
                completed = datetime.fromisoformat(task["completed_at"])
                task["elapsed_seconds"] = int((completed - started).total_seconds())

    def mark_failed(self, agent_run_id: str, error: Dict[str, str]) -> None:
        """
        Marca tarea como fallida.

        Args:
            agent_run_id: ID de la ejecución
            error: Dict con codigo, mensaje, detalle
        """
        with self._lock:
            if agent_run_id in self._tasks:
                task = self._tasks[agent_run_id]
                task["status"] = "failed"
                task["completed_at"] = datetime.now(timezone.utc).isoformat()
                task["success"] = False
                task["error"] = error

                # Calcular elapsed_seconds
                started = datetime.fromisoformat(task["started_at"])
                completed = datetime.fromisoformat(task["completed_at"])
                task["elapsed_seconds"] = int((completed - started).total_seconds())

    def get_status(self, agent_run_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene estado de una tarea.

        Args:
            agent_run_id: ID de la ejecución

        Returns:
            Dict con estado completo o None si no existe
        """
        with self._lock:
            task = self._tasks.get(agent_run_id)
            if not task:
                return None

            # Si está running, calcular elapsed_seconds actual
            if task["status"] == "running":
                started = datetime.fromisoformat(task["started_at"])
                now = datetime.now(timezone.utc)
                task["elapsed_seconds"] = int((now - started).total_seconds())

            return task.copy()

    def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """
        Limpia tareas antiguas.

        Args:
            max_age_hours: Edad máxima en horas

        Returns:
            Número de tareas eliminadas
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            to_delete = []

            for run_id, task in self._tasks.items():
                started = datetime.fromisoformat(task["started_at"])
                age_hours = (now - started).total_seconds() / 3600

                if age_hours > max_age_hours:
                    to_delete.append(run_id)

            for run_id in to_delete:
                del self._tasks[run_id]

            return len(to_delete)


# Instancia global
_task_tracker = TaskTracker()


def get_task_tracker() -> TaskTracker:
    """
    Dependency injection para FastAPI.

    Returns:
        Instancia global del TaskTracker
    """
    return _task_tracker
