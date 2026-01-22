# tests/api/test_task_tracker_factory.py

"""
Tests para el factory pattern de TaskTracker.

Verifica:
- Selección correcta de backend según USE_CELERY
- Singleton pattern
- Reset para testing
"""

import pytest
from unittest.mock import patch, MagicMock


class TestTaskTrackerFactory:
    """Tests para la factory de TaskTracker."""

    def setup_method(self):
        """Reset del tracker antes de cada test."""
        from api.services.task_tracker import reset_task_tracker
        reset_task_tracker()

    def test_get_task_tracker_returns_in_memory_when_use_celery_false(self):
        """Verifica que retorna InMemory cuando USE_CELERY=false."""
        with patch('api.services.task_tracker.settings') as mock_settings:
            mock_settings.USE_CELERY = False

            from api.services.task_tracker import get_task_tracker, TaskTrackerInMemory, reset_task_tracker
            reset_task_tracker()

            tracker = get_task_tracker()

            assert isinstance(tracker, TaskTrackerInMemory)

    def test_get_task_tracker_returns_redis_when_use_celery_true(self):
        """Verifica que retorna Redis cuando USE_CELERY=true."""
        with patch('api.services.task_tracker.settings') as mock_settings:
            mock_settings.USE_CELERY = True

            # Mock el import de TaskTrackerRedis
            with patch('api.services.task_tracker_redis.get_redis_client') as mock_redis:
                mock_redis.return_value = MagicMock()

                from api.services.task_tracker import get_task_tracker, reset_task_tracker
                from api.services.task_tracker_redis import TaskTrackerRedis
                reset_task_tracker()

                tracker = get_task_tracker()

                assert isinstance(tracker, TaskTrackerRedis)

    def test_get_task_tracker_singleton_in_memory(self):
        """Verifica singleton pattern para InMemory."""
        with patch('api.services.task_tracker.settings') as mock_settings:
            mock_settings.USE_CELERY = False

            from api.services.task_tracker import get_task_tracker, reset_task_tracker
            reset_task_tracker()

            tracker1 = get_task_tracker()
            tracker2 = get_task_tracker()

            assert tracker1 is tracker2

    def test_get_task_tracker_singleton_redis(self):
        """Verifica singleton pattern para Redis."""
        with patch('api.services.task_tracker.settings') as mock_settings:
            mock_settings.USE_CELERY = True

            with patch('api.services.task_tracker_redis.get_redis_client') as mock_redis:
                mock_redis.return_value = MagicMock()

                from api.services.task_tracker import get_task_tracker, reset_task_tracker
                reset_task_tracker()

                tracker1 = get_task_tracker()
                tracker2 = get_task_tracker()

                assert tracker1 is tracker2

    def test_reset_task_tracker_clears_instances(self):
        """Verifica que reset limpia las instancias."""
        with patch('api.services.task_tracker.settings') as mock_settings:
            mock_settings.USE_CELERY = False

            from api.services import task_tracker
            from api.services.task_tracker import get_task_tracker, reset_task_tracker
            reset_task_tracker()

            # Crear instancia
            tracker1 = get_task_tracker()
            assert task_tracker._task_tracker_in_memory is not None

            # Reset
            reset_task_tracker()
            assert task_tracker._task_tracker_in_memory is None
            assert task_tracker._task_tracker_redis is None

            # Nueva instancia debe ser diferente
            tracker2 = get_task_tracker()
            assert tracker1 is not tracker2


class TestTaskTrackerInMemoryBackwardCompatibility:
    """Tests de compatibilidad hacia atrás."""

    def setup_method(self):
        from api.services.task_tracker import reset_task_tracker
        reset_task_tracker()

    def test_tasktracker_alias_exists(self):
        """Verifica que TaskTracker es alias de TaskTrackerInMemory."""
        from api.services.task_tracker import TaskTracker, TaskTrackerInMemory
        assert TaskTracker is TaskTrackerInMemory

    def test_in_memory_tracker_has_all_methods(self):
        """Verifica que InMemory tiene todos los métodos requeridos."""
        from api.services.task_tracker import TaskTrackerInMemory

        tracker = TaskTrackerInMemory()

        assert hasattr(tracker, 'register')
        assert hasattr(tracker, 'mark_running')
        assert hasattr(tracker, 'mark_completed')
        assert hasattr(tracker, 'mark_failed')
        assert hasattr(tracker, 'get_status')
        assert hasattr(tracker, 'cleanup_old_tasks')


class TestTaskTrackerInterfaceCompatibility:
    """Tests de compatibilidad de interfaz entre backends."""

    def setup_method(self):
        from api.services.task_tracker import reset_task_tracker
        reset_task_tracker()

    def test_both_backends_have_same_interface(self):
        """Verifica que ambos backends tienen la misma interfaz."""
        from api.services.task_tracker import TaskTrackerInMemory
        from api.services.task_tracker_redis import TaskTrackerRedis

        in_memory_methods = set(dir(TaskTrackerInMemory()))
        # Filtrar métodos privados
        in_memory_public = {m for m in in_memory_methods if not m.startswith('_')}

        # TaskTrackerRedis necesita mock de Redis
        with patch('api.services.task_tracker_redis.get_redis_client') as mock:
            mock.return_value = MagicMock()
            redis_methods = set(dir(TaskTrackerRedis()))
            redis_public = {m for m in redis_methods if not m.startswith('_')}

        # Los métodos principales deben estar en ambos
        required_methods = {'register', 'mark_running', 'mark_completed', 'mark_failed', 'get_status', 'cleanup_old_tasks'}
        assert required_methods.issubset(in_memory_public)
        assert required_methods.issubset(redis_public)
