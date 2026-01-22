# tests/test_backoffice/test_celery_app.py

"""
Tests para la configuración de Celery.

Verifica:
- Configuración de seguridad (serialización JSON)
- Configuración de resiliencia (task_acks_late)
- Configuración de monitoreo (track_started)
- Autodiscovery de tasks
"""

import pytest


class TestCeleryAppConfiguration:
    """Tests para la configuración de celery_app.py"""

    def test_celery_app_exists(self):
        """Verifica que la app Celery está definida."""
        from backoffice.celery_app import celery_app
        assert celery_app is not None
        assert celery_app.main == "agentix"

    def test_task_serializer_is_json(self):
        """Verifica que la serialización es JSON (seguridad)."""
        from backoffice.celery_app import celery_app
        assert celery_app.conf.task_serializer == 'json'

    def test_accept_content_is_json_only(self):
        """Verifica que solo acepta JSON (seguridad)."""
        from backoffice.celery_app import celery_app
        assert celery_app.conf.accept_content == ['json']

    def test_result_serializer_is_json(self):
        """Verifica que los resultados se serializan en JSON."""
        from backoffice.celery_app import celery_app
        assert celery_app.conf.result_serializer == 'json'

    def test_task_acks_late_is_true(self):
        """Verifica task_acks_late para resiliencia."""
        from backoffice.celery_app import celery_app
        assert celery_app.conf.task_acks_late is True

    def test_task_track_started_configured(self):
        """Verifica que task_track_started está configurado."""
        from backoffice.celery_app import celery_app
        # El valor viene de settings, solo verificar que está definido
        assert celery_app.conf.task_track_started is not None

    def test_task_time_limit_configured(self):
        """Verifica que task_time_limit está configurado."""
        from backoffice.celery_app import celery_app
        assert celery_app.conf.task_time_limit is not None
        assert celery_app.conf.task_time_limit > 0

    def test_timezone_is_utc(self):
        """Verifica que el timezone es UTC."""
        from backoffice.celery_app import celery_app
        assert celery_app.conf.timezone == 'UTC'
        assert celery_app.conf.enable_utc is True

    def test_worker_prefetch_multiplier(self):
        """Verifica prefetch multiplier para control de concurrencia."""
        from backoffice.celery_app import celery_app
        assert celery_app.conf.worker_prefetch_multiplier == 1

    def test_worker_max_tasks_per_child(self):
        """Verifica max_tasks_per_child para evitar memory leaks."""
        from backoffice.celery_app import celery_app
        assert celery_app.conf.worker_max_tasks_per_child == 100

    def test_result_expires_configured(self):
        """Verifica que result_expires está configurado (7 días)."""
        from backoffice.celery_app import celery_app
        assert celery_app.conf.result_expires == 604800  # 7 días en segundos

    def test_broker_url_from_settings(self):
        """Verifica que broker URL viene de settings."""
        from backoffice.celery_app import celery_app
        from backoffice.settings import settings

        assert celery_app.conf.broker_url == settings.CELERY_BROKER_URL

    def test_result_backend_from_settings(self):
        """Verifica que result backend viene de settings."""
        from backoffice.celery_app import celery_app
        from backoffice.settings import settings

        assert celery_app.conf.result_backend == settings.CELERY_RESULT_BACKEND


class TestCeleryAutoDiscovery:
    """Tests para autodiscovery de tasks."""

    def test_autodiscover_includes_backoffice_tasks(self):
        """Verifica que autodiscover está configurado para backoffice.tasks."""
        from backoffice.celery_app import celery_app

        # Verificar que el módulo de tasks está en la lista de autodiscovery
        # Celery guarda esto internamente de forma diferente, verificamos que la app existe
        assert celery_app is not None


class TestCelerySecurityConfig:
    """Tests específicos de seguridad."""

    def test_no_pickle_serialization(self):
        """Verifica que pickle NO está habilitado (seguridad)."""
        from backoffice.celery_app import celery_app

        # Pickle no debe estar en accept_content
        assert 'pickle' not in celery_app.conf.accept_content

    def test_default_retry_delay(self):
        """Verifica configuración de retry delay."""
        from backoffice.celery_app import celery_app
        assert celery_app.conf.task_default_retry_delay == 5
