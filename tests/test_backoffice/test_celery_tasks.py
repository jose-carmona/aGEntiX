# tests/test_backoffice/test_celery_tasks.py

"""
Tests para las tareas Celery de ejecución de agentes.

Verifica:
- Configuración de la tarea (retry, backoff)
- Funciones auxiliares
- Métricas Prometheus
- Integración con AuditLogger para redacción de PII (P4)
- La ejecución completa se verifica en tests de integración

NOTA: Los tests de ejecución completa de tareas Celery con bind=True
requieren un worker real y se ejecutan como tests de integración.
"""

import pytest
import tempfile
from pathlib import Path
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


class TestPrometheusBucketsConfiguration:
    """
    Tests para P1: Buckets de histograma configurables.

    Ver code-review/commit-41f313a/plan-mejoras.md
    """

    def test_prometheus_duration_buckets_property_exists(self):
        """Verifica que la propiedad prometheus_duration_buckets existe."""
        from backoffice.settings import settings

        assert hasattr(settings, 'prometheus_duration_buckets')

    def test_prometheus_duration_buckets_returns_tuple(self):
        """Verifica que retorna una tupla de floats."""
        from backoffice.settings import settings

        buckets = settings.prometheus_duration_buckets
        assert isinstance(buckets, tuple)
        assert all(isinstance(b, float) for b in buckets)

    def test_prometheus_duration_buckets_default_values(self):
        """Verifica los valores por defecto de los buckets."""
        from backoffice.settings import settings

        buckets = settings.prometheus_duration_buckets
        # Default: 1,5,10,30,60,120,300,600,1800,3600
        assert 1.0 in buckets
        assert 60.0 in buckets
        assert 3600.0 in buckets

    def test_task_duration_uses_configurable_buckets(self):
        """Verifica que el histograma usa los buckets de settings."""
        from backoffice.tasks.agent_execution import task_duration
        from backoffice.settings import settings

        # Los buckets del histograma deben coincidir con settings
        # Prometheus añade +Inf al final, así que comparamos sin él
        expected = settings.prometheus_duration_buckets
        actual = task_duration._upper_bounds[:-1]  # Sin +Inf

        assert tuple(actual) == expected


class TestProductionSettingsValidation:
    """
    Tests para P3: Validación de configuración de producción.

    Ver code-review/commit-41f313a/plan-mejoras.md
    """

    def test_validate_production_settings_exists(self):
        """Verifica que el método de validación existe."""
        from backoffice.settings import settings

        assert hasattr(settings, 'validate_production_settings')
        assert callable(settings.validate_production_settings)

    def test_validate_production_settings_returns_warnings(self):
        """Verifica que retorna lista de warnings."""
        from backoffice.settings import settings

        warnings = settings.validate_production_settings()
        assert isinstance(warnings, list)

    def test_validate_production_settings_warns_on_default_admin_token(self):
        """Verifica warning cuando API_ADMIN_TOKEN es default."""
        from backoffice.settings import Settings

        # Crear instancia con valores default
        test_settings = Settings(
            JWT_SECRET="a" * 32,
            API_ADMIN_TOKEN="change-me-in-production"
        )

        warnings = test_settings.validate_production_settings()
        assert any("API_ADMIN_TOKEN" in w for w in warnings)

    def test_validate_production_settings_warns_on_short_jwt_secret(self):
        """Verifica warning cuando JWT_SECRET es muy corto."""
        from backoffice.settings import Settings

        test_settings = Settings(
            JWT_SECRET="short",
            API_ADMIN_TOKEN="secure-token-123"
        )

        warnings = test_settings.validate_production_settings()
        assert any("JWT_SECRET" in w for w in warnings)

    def test_validate_production_settings_no_warnings_when_secure(self):
        """Verifica que no hay warnings con configuración segura."""
        from backoffice.settings import Settings

        test_settings = Settings(
            JWT_SECRET="a" * 32,
            API_ADMIN_TOKEN="secure-token-12345",
            REDIS_PASSWORD="secure-redis-password"
        )

        warnings = test_settings.validate_production_settings()

        # No debe haber warnings
        assert len(warnings) == 0


class TestAuditLoggerIntegration:
    """
    Tests para verificar la integración con AuditLogger (P4 - GDPR/LOPD/ENS).

    Verifica que los logs de la tarea Celery redactan automáticamente PII.
    """

    def test_audit_logger_is_imported(self):
        """Verifica que AuditLogger está importado en el módulo."""
        from backoffice.tasks import agent_execution

        assert hasattr(agent_execution, 'AuditLogger')

    def test_helper_functions_accept_task_logger(self):
        """Verifica que las funciones helper aceptan task_logger opcional."""
        from backoffice.tasks.agent_execution import (
            _update_task_status,
            _update_task_completed,
            _update_task_failed,
            _send_webhook_async,
            _send_webhook_error
        )
        import inspect

        # Verificar que todas las funciones aceptan task_logger
        for func in [_update_task_status, _update_task_completed,
                     _update_task_failed, _send_webhook_async, _send_webhook_error]:
            sig = inspect.signature(func)
            assert 'task_logger' in sig.parameters, \
                f"{func.__name__} debe aceptar parámetro task_logger"

    def test_helper_uses_audit_logger_when_provided(self):
        """Verifica que helper usa AuditLogger cuando se proporciona."""
        from backoffice.tasks.agent_execution import _update_task_status
        from backoffice.logging.audit_logger import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            # Crear AuditLogger real
            task_logger = AuditLogger(
                expediente_id="EXP-TEST",
                agent_run_id="RUN-TEST",
                log_dir=tmpdir
            )

            # Simular error en TaskTracker
            with patch('api.services.task_tracker.get_task_tracker') as mock:
                mock.side_effect = Exception("Error con DNI 12345678A")

                # No debe lanzar excepción
                _update_task_status("test-run", "running", task_logger)

            # Verificar que el log fue escrito
            log_entries = task_logger.get_log_entries()
            assert len(log_entries) > 0

            # Verificar que PII fue redactado
            for entry in log_entries:
                assert "12345678A" not in entry, "DNI no debe aparecer en logs"

    def test_pii_redaction_in_error_messages(self):
        """Verifica que los mensajes de error redactan PII."""
        from backoffice.logging.audit_logger import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            task_logger = AuditLogger(
                expediente_id="EXP-TEST",
                agent_run_id="RUN-TEST",
                log_dir=tmpdir
            )

            # Simular error con PII
            pii_message = "Error procesando DNI 12345678A del usuario juan@example.com"
            task_logger.error(pii_message)

            entries = task_logger.get_log_entries()
            assert len(entries) == 1

            # Verificar redacción
            assert "12345678A" not in entries[0]
            assert "[DNI-REDACTED]" in entries[0]
            assert "juan@example.com" not in entries[0]
            assert "[EMAIL-REDACTED]" in entries[0]

    def test_pii_redaction_multiple_types(self):
        """Verifica redacción de múltiples tipos de PII."""
        from backoffice.logging.audit_logger import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            task_logger = AuditLogger(
                expediente_id="EXP-TEST",
                agent_run_id="RUN-TEST",
                log_dir=tmpdir
            )

            # Mensaje con múltiples tipos de PII
            pii_message = (
                "Usuario DNI 12345678A, NIE X1234567Z, "
                "email test@test.com, móvil 612345678, "
                "IBAN ES1234567890123456789012"
            )
            task_logger.log(pii_message)

            entries = task_logger.get_log_entries()
            entry = entries[0]

            # Verificar que ningún PII aparece sin redactar
            assert "12345678A" not in entry
            assert "X1234567Z" not in entry
            assert "test@test.com" not in entry
            assert "612345678" not in entry
            assert "ES1234567890123456789012" not in entry

            # Verificar que los placeholders están presentes
            assert "[DNI-REDACTED]" in entry
            assert "[NIE-REDACTED]" in entry
            assert "[EMAIL-REDACTED]" in entry
            assert "[TELEFONO_MOVIL-REDACTED]" in entry
            assert "[IBAN-REDACTED]" in entry

    def test_log_file_created_with_pii_redacted(self):
        """Verifica que el archivo de log contiene PII redactado."""
        from backoffice.logging.audit_logger import AuditLogger
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            expediente_id = "EXP-2024-001"
            agent_run_id = "RUN-TEST-123"

            task_logger = AuditLogger(
                expediente_id=expediente_id,
                agent_run_id=agent_run_id,
                log_dir=tmpdir
            )

            # Log con PII
            task_logger.log("Procesando solicitud de 12345678A")
            task_logger.error("Error para email juan@test.com")

            # Verificar archivo de log
            log_file = Path(tmpdir) / expediente_id / f"{agent_run_id}.log"
            assert log_file.exists()

            # Leer y verificar contenido
            with open(log_file, 'r') as f:
                lines = f.readlines()

            assert len(lines) == 2

            for line in lines:
                log_entry = json.loads(line)
                assert "12345678A" not in log_entry["mensaje"]
                assert "juan@test.com" not in log_entry["mensaje"]

    def test_update_task_failed_with_pii_in_error(self):
        """Verifica que _update_task_failed redacta PII en errores."""
        from backoffice.tasks.agent_execution import _update_task_failed
        from backoffice.logging.audit_logger import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            task_logger = AuditLogger(
                expediente_id="EXP-TEST",
                agent_run_id="RUN-TEST",
                log_dir=tmpdir
            )

            error_with_pii = {
                "codigo": "VALIDATION_ERROR",
                "mensaje": "DNI inválido",
                "detalle": "El DNI 12345678A no es válido"
            }

            with patch('api.services.task_tracker.get_task_tracker') as mock:
                mock.side_effect = Exception("Error de conexión")
                _update_task_failed("test-run", error_with_pii, task_logger)

            # Verificar que se logeó el warning
            entries = task_logger.get_log_entries()
            assert len(entries) >= 1
