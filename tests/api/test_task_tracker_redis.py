# tests/api/test_task_tracker_redis.py

"""
Tests para TaskTrackerRedis.

Verifica:
- Operaciones CRUD
- TTL de claves
- Cálculo de elapsed_seconds
- Compatibilidad con interfaz TaskTracker
"""

import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass


@dataclass
class MockAgentError:
    """Mock de AgentError"""
    codigo: str
    mensaje: str
    detalle: str = ""


@dataclass
class MockAgentResult:
    """Mock de AgentExecutionResult"""
    success: bool
    resultado: dict
    error: MockAgentError = None


class TestTaskTrackerRedisBasic:
    """Tests básicos para TaskTrackerRedis."""

    @pytest.fixture
    def mock_redis(self):
        """Mock de cliente Redis."""
        return MagicMock()

    @pytest.fixture
    def tracker(self, mock_redis):
        """Instancia de TaskTrackerRedis con mock."""
        from api.services.task_tracker_redis import TaskTrackerRedis
        return TaskTrackerRedis(redis_client=mock_redis)

    def test_register_creates_task(self, tracker, mock_redis):
        """Verifica que register crea una tarea en Redis."""
        tracker.register(
            agent_run_id="RUN-123",
            expediente_id="EXP-001",
            tarea_id="TASK-001"
        )

        # Verificar que se llamó setex
        mock_redis.setex.assert_called_once()

        # Verificar los argumentos
        call_args = mock_redis.setex.call_args
        key = call_args[0][0]
        ttl = call_args[0][1]
        value = call_args[0][2]

        assert key == "agentix:task:RUN-123"
        assert ttl == 604800  # 7 días
        assert "RUN-123" in value

    def test_register_task_data_structure(self, tracker, mock_redis):
        """Verifica la estructura de datos de la tarea registrada."""
        tracker.register(
            agent_run_id="RUN-123",
            expediente_id="EXP-001",
            tarea_id="TASK-001"
        )

        call_args = mock_redis.setex.call_args
        value_json = call_args[0][2]
        task_data = json.loads(value_json)

        assert task_data["agent_run_id"] == "RUN-123"
        assert task_data["expediente_id"] == "EXP-001"
        assert task_data["tarea_id"] == "TASK-001"
        assert task_data["status"] == "pending"
        assert task_data["started_at"] is not None
        assert task_data["completed_at"] is None
        assert task_data["success"] is None

    def test_mark_running_updates_status(self, tracker, mock_redis):
        """Verifica que mark_running actualiza el estado."""
        # Configurar mock para retornar tarea existente
        existing_task = {
            "agent_run_id": "RUN-123",
            "expediente_id": "EXP-001",
            "tarea_id": "TASK-001",
            "status": "pending",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "success": None
        }
        mock_redis.get.return_value = json.dumps(existing_task)

        tracker.mark_running("RUN-123")

        # Verificar que se actualizó
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        value_json = call_args[0][2]
        updated_task = json.loads(value_json)

        assert updated_task["status"] == "running"

    def test_mark_completed_success(self, tracker, mock_redis):
        """Verifica mark_completed con resultado exitoso."""
        start_time = datetime.now(timezone.utc) - timedelta(seconds=10)
        existing_task = {
            "agent_run_id": "RUN-123",
            "expediente_id": "EXP-001",
            "tarea_id": "TASK-001",
            "status": "running",
            "started_at": start_time.isoformat(),
            "completed_at": None,
            "success": None
        }
        mock_redis.get.return_value = json.dumps(existing_task)

        result = MockAgentResult(
            success=True,
            resultado={"output": "success"}
        )

        tracker.mark_completed("RUN-123", result)

        call_args = mock_redis.setex.call_args
        value_json = call_args[0][2]
        updated_task = json.loads(value_json)

        assert updated_task["status"] == "completed"
        assert updated_task["success"] is True
        assert updated_task["resultado"]["output"] == "success"
        assert updated_task["completed_at"] is not None
        assert updated_task["elapsed_seconds"] >= 10

    def test_mark_completed_failure(self, tracker, mock_redis):
        """Verifica mark_completed con resultado fallido."""
        start_time = datetime.now(timezone.utc) - timedelta(seconds=5)
        existing_task = {
            "agent_run_id": "RUN-123",
            "expediente_id": "EXP-001",
            "tarea_id": "TASK-001",
            "status": "running",
            "started_at": start_time.isoformat(),
            "completed_at": None,
            "success": None
        }
        mock_redis.get.return_value = json.dumps(existing_task)

        error = MockAgentError(
            codigo="TEST_ERROR",
            mensaje="Test error",
            detalle="Details"
        )
        result = MockAgentResult(
            success=False,
            resultado={},
            error=error
        )

        tracker.mark_completed("RUN-123", result)

        call_args = mock_redis.setex.call_args
        value_json = call_args[0][2]
        updated_task = json.loads(value_json)

        assert updated_task["status"] == "completed"
        assert updated_task["success"] is False
        assert updated_task["error"]["codigo"] == "TEST_ERROR"

    def test_mark_failed(self, tracker, mock_redis):
        """Verifica mark_failed."""
        start_time = datetime.now(timezone.utc) - timedelta(seconds=5)
        existing_task = {
            "agent_run_id": "RUN-123",
            "expediente_id": "EXP-001",
            "tarea_id": "TASK-001",
            "status": "running",
            "started_at": start_time.isoformat(),
            "completed_at": None,
            "success": None
        }
        mock_redis.get.return_value = json.dumps(existing_task)

        error = {
            "codigo": "TIMEOUT",
            "mensaje": "Timeout error",
            "detalle": ""
        }

        tracker.mark_failed("RUN-123", error)

        call_args = mock_redis.setex.call_args
        value_json = call_args[0][2]
        updated_task = json.loads(value_json)

        assert updated_task["status"] == "failed"
        assert updated_task["success"] is False
        assert updated_task["error"]["codigo"] == "TIMEOUT"


class TestTaskTrackerRedisGetStatus:
    """Tests para get_status."""

    @pytest.fixture
    def mock_redis(self):
        return MagicMock()

    @pytest.fixture
    def tracker(self, mock_redis):
        from api.services.task_tracker_redis import TaskTrackerRedis
        return TaskTrackerRedis(redis_client=mock_redis)

    def test_get_status_returns_task(self, tracker, mock_redis):
        """Verifica que get_status retorna la tarea."""
        task_data = {
            "agent_run_id": "RUN-123",
            "expediente_id": "EXP-001",
            "tarea_id": "TASK-001",
            "status": "completed",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": 10,
            "success": True,
            "resultado": {"output": "success"},
            "error": None
        }
        mock_redis.get.return_value = json.dumps(task_data)

        result = tracker.get_status("RUN-123")

        assert result is not None
        assert result["agent_run_id"] == "RUN-123"
        assert result["success"] is True

    def test_get_status_returns_none_for_missing(self, tracker, mock_redis):
        """Verifica que get_status retorna None si no existe."""
        mock_redis.get.return_value = None

        result = tracker.get_status("RUN-NONEXISTENT")

        assert result is None

    def test_get_status_calculates_elapsed_for_running(self, tracker, mock_redis):
        """Verifica cálculo de elapsed_seconds para tareas running."""
        start_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        task_data = {
            "agent_run_id": "RUN-123",
            "expediente_id": "EXP-001",
            "tarea_id": "TASK-001",
            "status": "running",
            "started_at": start_time.isoformat(),
            "completed_at": None,
            "elapsed_seconds": 0,
            "success": None,
            "resultado": None,
            "error": None
        }
        mock_redis.get.return_value = json.dumps(task_data)

        result = tracker.get_status("RUN-123")

        # elapsed_seconds debe ser aproximadamente 30
        assert result["elapsed_seconds"] >= 29


class TestTaskTrackerRedisKeyManagement:
    """Tests para gestión de claves."""

    @pytest.fixture
    def mock_redis(self):
        return MagicMock()

    @pytest.fixture
    def tracker(self, mock_redis):
        from api.services.task_tracker_redis import TaskTrackerRedis
        return TaskTrackerRedis(redis_client=mock_redis)

    def test_task_key_format(self, tracker):
        """Verifica el formato de las claves."""
        key = tracker._task_key("RUN-123")
        assert key == "agentix:task:RUN-123"

    def test_exists_returns_true(self, tracker, mock_redis):
        """Verifica exists cuando la tarea existe."""
        mock_redis.exists.return_value = 1

        assert tracker.exists("RUN-123") is True
        mock_redis.exists.assert_called_with("agentix:task:RUN-123")

    def test_exists_returns_false(self, tracker, mock_redis):
        """Verifica exists cuando la tarea no existe."""
        mock_redis.exists.return_value = 0

        assert tracker.exists("RUN-123") is False

    def test_get_ttl(self, tracker, mock_redis):
        """Verifica get_ttl."""
        mock_redis.ttl.return_value = 86400

        ttl = tracker.get_ttl("RUN-123")

        assert ttl == 86400
        mock_redis.ttl.assert_called_with("agentix:task:RUN-123")

    def test_cleanup_old_tasks_noop(self, tracker):
        """Verifica que cleanup_old_tasks retorna 0 (Redis usa TTL)."""
        result = tracker.cleanup_old_tasks(max_age_hours=24)
        assert result == 0


class TestTaskTrackerRedisConstants:
    """Tests para constantes."""

    def test_key_prefix(self):
        """Verifica el prefijo de claves."""
        from api.services.task_tracker_redis import TaskTrackerRedis
        assert TaskTrackerRedis.KEY_PREFIX == "agentix:task:"

    def test_ttl_seconds(self):
        """Verifica TTL de 7 días."""
        from api.services.task_tracker_redis import TaskTrackerRedis
        assert TaskTrackerRedis.TTL_SECONDS == 604800
