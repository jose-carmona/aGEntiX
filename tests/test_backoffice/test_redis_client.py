# tests/test_backoffice/test_redis_client.py

"""
Tests para el cliente Redis.

Verifica:
- Conexión básica
- Connection pooling
- Configuración desde settings
"""

import pytest
from unittest.mock import patch, MagicMock


class TestRedisClient:
    """Tests para redis_client.py"""

    def test_get_redis_client_returns_redis_instance(self):
        """Verifica que get_redis_client retorna una instancia de Redis."""
        with patch('backoffice.redis_client.ConnectionPool') as mock_pool:
            mock_pool.return_value = MagicMock()

            # Resetear el pool global
            import backoffice.redis_client as rc
            rc._connection_pool = None

            with patch('backoffice.redis_client.Redis') as mock_redis:
                mock_redis.return_value = MagicMock()

                from backoffice.redis_client import get_redis_client
                client = get_redis_client()

                assert client is not None
                mock_redis.assert_called_once()

    def test_get_connection_pool_creates_once(self):
        """Verifica que el pool se crea solo una vez (singleton)."""
        with patch('backoffice.redis_client.ConnectionPool') as mock_pool:
            mock_pool.return_value = MagicMock()

            # Resetear el pool global
            import backoffice.redis_client as rc
            rc._connection_pool = None

            from backoffice.redis_client import get_connection_pool

            pool1 = get_connection_pool()
            pool2 = get_connection_pool()

            # Solo debe crear una vez
            mock_pool.assert_called_once()
            assert pool1 is pool2

    def test_connection_pool_uses_settings(self):
        """Verifica que usa la configuración de settings."""
        with patch('backoffice.redis_client.ConnectionPool') as mock_pool:
            mock_pool.return_value = MagicMock()

            # Resetear el pool global
            import backoffice.redis_client as rc
            rc._connection_pool = None

            with patch('backoffice.redis_client.settings') as mock_settings:
                mock_settings.REDIS_HOST = "test-host"
                mock_settings.REDIS_PORT = 6380
                mock_settings.REDIS_DB = 1
                mock_settings.REDIS_PASSWORD = "test-password"

                from backoffice.redis_client import get_connection_pool
                get_connection_pool()

                mock_pool.assert_called_once()
                call_kwargs = mock_pool.call_args[1]
                assert call_kwargs['host'] == "test-host"
                assert call_kwargs['port'] == 6380
                assert call_kwargs['db'] == 1
                assert call_kwargs['password'] == "test-password"

    def test_close_redis_pool_disconnects(self):
        """Verifica que close_redis_pool desconecta el pool."""
        mock_pool = MagicMock()

        import backoffice.redis_client as rc
        rc._connection_pool = mock_pool

        from backoffice.redis_client import close_redis_pool
        close_redis_pool()

        mock_pool.disconnect.assert_called_once()
        assert rc._connection_pool is None

    def test_close_redis_pool_handles_none(self):
        """Verifica que close_redis_pool maneja pool None sin error."""
        import backoffice.redis_client as rc
        rc._connection_pool = None

        from backoffice.redis_client import close_redis_pool

        # No debe lanzar excepción
        close_redis_pool()
        assert rc._connection_pool is None

    def test_pool_config_decode_responses(self):
        """Verifica que decode_responses está configurado."""
        with patch('backoffice.redis_client.ConnectionPool') as mock_pool:
            mock_pool.return_value = MagicMock()

            # Resetear el pool global
            import backoffice.redis_client as rc
            rc._connection_pool = None

            from backoffice.redis_client import get_connection_pool
            get_connection_pool()

            call_kwargs = mock_pool.call_args[1]
            assert call_kwargs['decode_responses'] is True

    def test_pool_config_max_connections(self):
        """Verifica que max_connections está configurado."""
        with patch('backoffice.redis_client.ConnectionPool') as mock_pool:
            mock_pool.return_value = MagicMock()

            # Resetear el pool global
            import backoffice.redis_client as rc
            rc._connection_pool = None

            from backoffice.redis_client import get_connection_pool
            get_connection_pool()

            call_kwargs = mock_pool.call_args[1]
            assert call_kwargs['max_connections'] == 20

    def test_pool_config_timeouts(self):
        """Verifica que los timeouts están configurados."""
        with patch('backoffice.redis_client.ConnectionPool') as mock_pool:
            mock_pool.return_value = MagicMock()

            # Resetear el pool global
            import backoffice.redis_client as rc
            rc._connection_pool = None

            from backoffice.redis_client import get_connection_pool
            get_connection_pool()

            call_kwargs = mock_pool.call_args[1]
            assert call_kwargs['socket_connect_timeout'] == 5
            assert call_kwargs['socket_timeout'] == 5
