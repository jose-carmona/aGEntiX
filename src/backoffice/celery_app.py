# backoffice/celery_app.py

"""
Configuración de Celery para aGEntiX.

Celery se usa para ejecutar agentes de forma distribuida,
permitiendo escalado horizontal mediante múltiples workers.

Configuración de seguridad:
- Serialización JSON (no pickle) para evitar code injection
- task_acks_late=True para resiliencia ante fallos de workers
- task_track_started=True para monitoreo de estado "running"
"""

from celery import Celery

from .settings import settings


# Crear app Celery
celery_app = Celery(
    "agentix",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configuración de Celery
celery_app.conf.update(
    # Serialización segura (JSON, no pickle)
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',

    # Timezone
    timezone='UTC',
    enable_utc=True,

    # Tracking de tareas
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,

    # Límite de tiempo por tarea (default: 1 hora)
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,

    # Resiliencia: reintento si worker muere antes de completar
    task_acks_late=True,

    # Un task a la vez por worker para evitar contención de recursos
    worker_prefetch_multiplier=1,

    # Reutilizar workers tras N tareas (evita memory leaks)
    worker_max_tasks_per_child=100,

    # Retries con backoff exponencial
    task_default_retry_delay=5,

    # Result backend expiration (7 días)
    result_expires=604800,

    # No almacenar resultados de tareas exitosas para reducir uso de memoria
    # (El estado se guarda en TaskTracker con TTL propio)
    task_ignore_result=False,
)

# Auto-discover tasks en el paquete backoffice.tasks
celery_app.autodiscover_tasks(['backoffice.tasks'])
