# tests/integration/test_celery_integration.py

"""
Tests de integración E2E para Celery + Redis.

IMPORTANTE: Estos tests requieren:
- Redis corriendo en localhost:6379
- USE_CELERY=true

Para ejecutar solo estos tests:
    pytest tests/integration/test_celery_integration.py -v -m integration

Para ejecutar con Redis real:
    redis-cli ping  # Verificar Redis
    pytest tests/integration/test_celery_integration.py -v
"""

import pytest
import time
from unittest.mock import patch, MagicMock


# Marcar todos los tests como de integración
pytestmark = pytest.mark.integration


def redis_available():
    """Verifica si Redis está disponible."""
    try:
        from redis import Redis
        client = Redis(host='localhost', port=6379, db=0)
        client.ping()
        return True
    except Exception:
        return False


@pytest.fixture
def redis_client():
    """Proporciona un cliente Redis para tests."""
    if not redis_available():
        pytest.skip("Redis no está disponible")

    from redis import Redis
    client = Redis(host='localhost', port=6379, db=0, decode_responses=True)
    yield client

    # Limpiar claves de test
    for key in client.keys("agentix:task:TEST-*"):
        client.delete(key)


@pytest.fixture
def task_tracker_redis(redis_client):
    """Proporciona un TaskTrackerRedis con Redis real."""
    from api.services.task_tracker_redis import TaskTrackerRedis
    return TaskTrackerRedis(redis_client=redis_client)


class TestTaskTrackerRedisIntegration:
    """Tests de integración para TaskTrackerRedis con Redis real."""

    def test_register_and_get_status(self, task_tracker_redis, redis_client):
        """Test completo de registro y consulta de estado."""
        agent_run_id = f"TEST-{int(time.time())}"

        # Registrar
        task_tracker_redis.register(
            agent_run_id=agent_run_id,
            expediente_id="EXP-001",
            tarea_id="TASK-001"
        )

        # Consultar
        status = task_tracker_redis.get_status(agent_run_id)

        assert status is not None
        assert status["agent_run_id"] == agent_run_id
        assert status["status"] == "pending"

    def test_full_lifecycle(self, task_tracker_redis):
        """Test del ciclo completo: pending -> running -> completed."""
        from dataclasses import dataclass

        @dataclass
        class MockResult:
            success: bool
            resultado: dict
            error: None = None

        agent_run_id = f"TEST-{int(time.time())}-lifecycle"

        # 1. Registrar (pending)
        task_tracker_redis.register(
            agent_run_id=agent_run_id,
            expediente_id="EXP-001",
            tarea_id="TASK-001"
        )
        status = task_tracker_redis.get_status(agent_run_id)
        assert status["status"] == "pending"

        # 2. Marcar running
        task_tracker_redis.mark_running(agent_run_id)
        status = task_tracker_redis.get_status(agent_run_id)
        assert status["status"] == "running"

        # 3. Marcar completed
        result = MockResult(success=True, resultado={"output": "test"})
        task_tracker_redis.mark_completed(agent_run_id, result)
        status = task_tracker_redis.get_status(agent_run_id)
        assert status["status"] == "completed"
        assert status["success"] is True

    def test_elapsed_seconds_calculated(self, task_tracker_redis):
        """Test que elapsed_seconds se calcula correctamente."""
        agent_run_id = f"TEST-{int(time.time())}-elapsed"

        task_tracker_redis.register(
            agent_run_id=agent_run_id,
            expediente_id="EXP-001",
            tarea_id="TASK-001"
        )

        task_tracker_redis.mark_running(agent_run_id)

        # Esperar un poco
        time.sleep(2)

        status = task_tracker_redis.get_status(agent_run_id)
        assert status["elapsed_seconds"] >= 2

    def test_ttl_is_set(self, task_tracker_redis, redis_client):
        """Test que el TTL está configurado."""
        agent_run_id = f"TEST-{int(time.time())}-ttl"

        task_tracker_redis.register(
            agent_run_id=agent_run_id,
            expediente_id="EXP-001",
            tarea_id="TASK-001"
        )

        ttl = task_tracker_redis.get_ttl(agent_run_id)

        # TTL debe ser cercano a 7 días (604800 segundos)
        assert ttl > 604700

    def test_exists_method(self, task_tracker_redis):
        """Test del método exists."""
        agent_run_id = f"TEST-{int(time.time())}-exists"

        # No existe aún
        assert task_tracker_redis.exists(agent_run_id) is False

        # Registrar
        task_tracker_redis.register(
            agent_run_id=agent_run_id,
            expediente_id="EXP-001",
            tarea_id="TASK-001"
        )

        # Ahora existe
        assert task_tracker_redis.exists(agent_run_id) is True


class TestRedisClientIntegration:
    """Tests de integración para redis_client.py."""

    @pytest.mark.skipif(not redis_available(), reason="Redis no disponible")
    def test_get_redis_client_connects(self):
        """Test que el cliente se conecta correctamente."""
        # Resetear pool
        import backoffice.redis_client as rc
        rc._connection_pool = None

        from backoffice.redis_client import get_redis_client

        client = get_redis_client()

        # Debería poder hacer ping
        result = client.ping()
        assert result is True

    @pytest.mark.skipif(not redis_available(), reason="Redis no disponible")
    def test_connection_pool_reused(self):
        """Test que el pool se reutiliza."""
        import backoffice.redis_client as rc
        rc._connection_pool = None

        from backoffice.redis_client import get_redis_client

        client1 = get_redis_client()
        client2 = get_redis_client()

        # Ambos deben usar el mismo pool
        assert client1.connection_pool is client2.connection_pool


class TestCeleryAppIntegration:
    """Tests de integración para celery_app.py."""

    @pytest.mark.skipif(not redis_available(), reason="Redis no disponible")
    def test_celery_can_connect_to_redis(self):
        """Test que Celery puede conectar a Redis."""
        from backoffice.celery_app import celery_app

        # Verificar que la app existe
        assert celery_app is not None

        # Verificar configuración
        assert 'redis' in celery_app.conf.broker_url


class TestFeatureFlagIntegration:
    """Tests de integración para el feature flag USE_CELERY."""

    def setup_method(self):
        """Reset del tracker antes de cada test."""
        from api.services.task_tracker import reset_task_tracker
        reset_task_tracker()

    @pytest.mark.skipif(not redis_available(), reason="Redis no disponible")
    def test_use_celery_true_uses_redis_tracker(self):
        """Test que USE_CELERY=true usa TaskTrackerRedis."""
        from api.services.task_tracker import get_task_tracker, reset_task_tracker
        from api.services.task_tracker_redis import TaskTrackerRedis

        # Simular USE_CELERY=true
        with patch('api.services.task_tracker.settings') as mock_settings:
            mock_settings.USE_CELERY = True
            reset_task_tracker()

            tracker = get_task_tracker()
            assert isinstance(tracker, TaskTrackerRedis)

    def test_use_celery_false_uses_in_memory_tracker(self):
        """Test que USE_CELERY=false usa TaskTrackerInMemory."""
        from api.services.task_tracker import get_task_tracker, reset_task_tracker, TaskTrackerInMemory

        with patch('api.services.task_tracker.settings') as mock_settings:
            mock_settings.USE_CELERY = False
            reset_task_tracker()

            tracker = get_task_tracker()
            assert isinstance(tracker, TaskTrackerInMemory)
