# tests/test_backoffice/test_celery_tasks.py

"""
Tests para las tareas Celery de ejecución de agentes.

Verifica:
- Configuración de la tarea (retry, backoff)
- Funciones auxiliares
- Métricas Prometheus
- La ejecución completa se verifica en tests de integración

NOTA: Los tests de ejecución completa de tareas Celery con bind=True
requieren un worker real y se ejecutan como tests de integración.
"""

import pytest
from unittest.mock import patch, MagicMock
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
    agent_run_id: str
    resultado: dict
    herramientas_usadas: list
    log_auditoria: list
    error: MockAgentError = None


class TestAgentExecutionTaskClass:
    """Tests para la clase AgentExecutionTask."""

    def test_autoretry_for_transient_errors(self):
        """Verifica que autoretry está configurado para errores transitorios."""
        from backoffice.tasks.agent_execution import AgentExecutionTask

        assert ConnectionError in AgentExecutionTask.autoretry_for
        assert TimeoutError in AgentExecutionTask.autoretry_for
        assert OSError in AgentExecutionTask.autoretry_for

    def test_retry_kwargs_configured(self):
        """Verifica configuración de retry."""
        from backoffice.tasks.agent_execution import AgentExecutionTask

        assert AgentExecutionTask.retry_kwargs['max_retries'] == 3
        assert AgentExecutionTask.retry_kwargs['countdown'] == 5

    def test_retry_backoff_enabled(self):
        """Verifica que backoff exponencial está habilitado."""
        from backoffice.tasks.agent_execution import AgentExecutionTask

        assert AgentExecutionTask.retry_backoff is True
        assert AgentExecutionTask.retry_jitter is True

    def test_retry_backoff_max(self):
        """Verifica el máximo backoff."""
        from backoffice.tasks.agent_execution import AgentExecutionTask

        assert AgentExecutionTask.retry_backoff_max == 300  # 5 minutos


class TestTaskRegistration:
    """Tests para verificar que la tarea está registrada correctamente."""

    def test_task_is_registered(self):
        """Verifica que la tarea está registrada en Celery."""
        from backoffice.celery_app import celery_app
        from backoffice.tasks.agent_execution import execute_agent_task

        assert execute_agent_task.name == 'backoffice.execute_agent'

    def test_task_has_correct_base(self):
        """Verifica que usa AgentExecutionTask como base."""
        from backoffice.tasks.agent_execution import execute_agent_task, AgentExecutionTask

        # La tarea hereda las propiedades de la base
        assert execute_agent_task.autoretry_for == AgentExecutionTask.autoretry_for

    def test_task_is_bound(self):
        """Verifica que la tarea está bound (tiene acceso a self)."""
        from backoffice.tasks.agent_execution import execute_agent_task

        # Las tareas bound tienen el método request como propiedad
        assert hasattr(execute_agent_task, 'request')


class TestHelperFunctions:
    """Tests para funciones auxiliares."""

    def test_error_to_dict_with_error(self):
        """Test conversión de AgentError a dict."""
        from backoffice.tasks.agent_execution import _error_to_dict

        error = MockAgentError(
            codigo="TEST_ERROR",
            mensaje="Test message",
            detalle="Test detail"
        )

        result = _error_to_dict(error)

        assert result["codigo"] == "TEST_ERROR"
        assert result["mensaje"] == "Test message"
        assert result["detalle"] == "Test detail"

    def test_error_to_dict_with_none(self):
        """Test conversión de None."""
        from backoffice.tasks.agent_execution import _error_to_dict

        result = _error_to_dict(None)
        assert result is None

    def test_run_async_helper_exists(self):
        """Verifica que el helper _run_async existe."""
        from backoffice.tasks.agent_execution import _run_async

        assert callable(_run_async)


class TestTaskTrackerIntegration:
    """Tests para funciones de integración con TaskTracker."""

    def test_update_task_status_handles_missing_tracker(self):
        """Verifica que _update_task_status maneja errores graciosamente."""
        from backoffice.tasks.agent_execution import _update_task_status

        # No debe lanzar excepción incluso si falla
        # Patch en el módulo api.services.task_tracker donde se importa
        with patch('api.services.task_tracker.get_task_tracker') as mock:
            mock.side_effect = Exception("Connection error")

            # No debe lanzar excepción
            _update_task_status("test-run", "running")

    def test_update_task_completed_handles_missing_tracker(self):
        """Verifica que _update_task_completed maneja errores graciosamente."""
        from backoffice.tasks.agent_execution import _update_task_completed

        mock_result = MockAgentResult(
            success=True,
            agent_run_id="test",
            resultado={},
            herramientas_usadas=[],
            log_auditoria=[]
        )

        with patch('api.services.task_tracker.get_task_tracker') as mock:
            mock.side_effect = Exception("Connection error")

            # No debe lanzar excepción
            _update_task_completed("test-run", mock_result)

    def test_update_task_failed_handles_missing_tracker(self):
        """Verifica que _update_task_failed maneja errores graciosamente."""
        from backoffice.tasks.agent_execution import _update_task_failed

        with patch('api.services.task_tracker.get_task_tracker') as mock:
            mock.side_effect = Exception("Connection error")

            # No debe lanzar excepción
            _update_task_failed("test-run", {"codigo": "ERROR"})


class TestPrometheusMetrics:
    """Tests para métricas Prometheus."""

    def test_task_counter_exists(self):
        """Verifica que el contador de tareas existe."""
        from backoffice.tasks.agent_execution import task_counter
        assert task_counter is not None

    def test_task_duration_histogram_exists(self):
        """Verifica que el histograma de duración existe."""
        from backoffice.tasks.agent_execution import task_duration
        assert task_duration is not None

    def test_task_counter_labels(self):
        """Verifica las labels del contador."""
        from backoffice.tasks.agent_execution import task_counter

        # Verificar que tiene las labels correctas
        assert 'agent_name' in task_counter._labelnames
        assert 'status' in task_counter._labelnames

    def test_task_duration_labels(self):
        """Verifica las labels del histograma."""
        from backoffice.tasks.agent_execution import task_duration

        assert 'agent_name' in task_duration._labelnames

    def test_task_duration_buckets(self):
        """Verifica los buckets del histograma."""
        from backoffice.tasks.agent_execution import task_duration

        # Debe tener buckets configurados para tiempos de ejecución de agentes
        # (desde 1 segundo hasta 1 hora)
        assert len(task_duration._upper_bounds) > 0


class TestTaskConfiguration:
    """Tests para configuración de la tarea."""

    def test_task_time_limit(self):
        """Verifica que task_time_limit está configurado."""
        from backoffice.tasks.agent_execution import execute_agent_task
        from backoffice.settings import settings

        # El time_limit debe venir de settings
        assert execute_agent_task.time_limit == settings.CELERY_TASK_TIME_LIMIT

    def test_task_soft_time_limit(self):
        """Verifica que soft_time_limit está configurado."""
        from backoffice.tasks.agent_execution import execute_agent_task
        from backoffice.settings import settings

        # Soft limit es 60 segundos antes del hard limit
        expected_soft = settings.CELERY_TASK_TIME_LIMIT - 60
        assert execute_agent_task.soft_time_limit == expected_soft
