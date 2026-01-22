# backoffice/redis_client.py

"""
Cliente Redis centralizado para aGEntiX.

Usado por:
- Celery como broker y backend
- TaskTracker para estado distribuido

Proporciona connection pooling para eficiencia.
"""

from typing import Optional
from redis import Redis, ConnectionPool

from .settings import settings


# Connection pool global para reutilizar conexiones
_connection_pool: Optional[ConnectionPool] = None


def get_connection_pool() -> ConnectionPool:
    """
    Obtiene o crea el connection pool de Redis.

    El pool se crea una sola vez y se reutiliza.

    Returns:
        ConnectionPool configurado con los settings.
    """
    global _connection_pool

    if _connection_pool is None:
        _connection_pool = ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD or None,
            decode_responses=True,
            max_connections=20,
            socket_connect_timeout=5,
            socket_timeout=5
        )

    return _connection_pool


def get_redis_client() -> Redis:
    """
    Obtiene un cliente Redis reutilizable con connection pooling.

    Usado por:
    - Celery como broker y backend
    - TaskTracker para estado distribuido

    Returns:
        Redis client configurado.
    """
    return Redis(connection_pool=get_connection_pool())


def close_redis_pool() -> None:
    """
    Cierra el connection pool de Redis.

    Llamar al finalizar la aplicación para limpieza.
    """
    global _connection_pool

    if _connection_pool is not None:
        _connection_pool.disconnect()
        _connection_pool = None
