# Análisis Detallado - Commit 41f313a

## 1. Arquitectura

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Feature Flag                               │
│                        USE_CELERY=true/false                        │
└─────────────────────────────────────────────────────────────────────┘
                                  │
          ┌───────────────────────┴───────────────────────┐
          ▼                                               ▼
┌─────────────────────────┐               ┌─────────────────────────┐
│   USE_CELERY=false      │               │   USE_CELERY=true       │
│   (Desarrollo)          │               │   (Producción)          │
├─────────────────────────┤               ├─────────────────────────┤
│ BackgroundTasks (uvicorn)│               │ Celery Workers          │
│ TaskTrackerInMemory     │               │ TaskTrackerRedis        │
│ Single process          │               │ Distributed             │
└─────────────────────────┘               └─────────────────────────┘
```

### Flujo de Ejecución (Modo Celery)

```
1. POST /execute (API FastAPI)
         │
         ▼
2. Validar JWT + Cargar config agente
         │
         ▼
3. _execute_with_celery()
         │
         ├── Serializar AgentConfig → dict (JSON)
         │
         ├── execute_agent_task.delay() → Encolar en Redis
         │
         └── task_tracker.register() en Redis
         │
         ▼
4. Return 202 Accepted (inmediato)

═══════════════ Worker Celery (proceso separado) ═══════════════

5. execute_agent_task() (worker recibe tarea)
         │
         ├── task_tracker.mark_running()
         │
         ├── create_default_executor()
         │
         └── _run_async(executor.execute(...))
                  │
                  ├── JWT validation
                  ├── MCP tool calls
                  └── Agent execution
         │
         ▼
6. task_tracker.mark_completed() / mark_failed()
         │
         ▼
7. send_webhook() si callback_url
```

### Factory Pattern para TaskTracker

```
                        get_task_tracker()
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
    settings.USE_CELERY   _singleton_        return
            │            inmemory/redis       tracker
            │                 │
            ▼                 ▼
   ┌────────────────┐  ┌────────────────┐
   │ USE_CELERY=    │  │ USE_CELERY=    │
   │    false       │  │    true        │
   ├────────────────┤  ├────────────────┤
   │TaskTrackerIn   │  │TaskTrackerRedis│
   │   Memory       │  │                │
   │ (dict + Lock)  │  │ (Redis + TTL)  │
   └────────────────┘  └────────────────┘
```

## 2. Código Clave

### Clase AgentExecutionTask

```python
class AgentExecutionTask(Task):
    """Base para tareas de ejecución de agentes."""

    # Errores transitorios que activan retry automático
    autoretry_for = (ConnectionError, TimeoutError, OSError)

    # Configuración de reintentos
    retry_kwargs = {
        'max_retries': 3,
        'countdown': 5  # Segundos antes del primer reintento
    }

    # Backoff exponencial: 5s → 10s → 20s → ... → max 300s
    retry_backoff = True
    retry_backoff_max = 300  # Máximo 5 minutos entre reintentos
    retry_jitter = True      # Añade aleatoriedad (evita thundering herd)
```

**¿Por qué es importante?**
- `autoretry_for`: Solo reintenta errores de red, no errores de lógica
- `retry_backoff`: Evita sobrecargar servicios caídos
- `retry_jitter`: Previene que múltiples workers reintenten simultáneamente

### Helper _run_async()

```python
def _run_async(coro):
    """
    Ejecuta una corutina desde contexto síncrono (Celery).
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(coro)
    finally:
        pass  # No cerrar el loop para reutilización
```

**¿Por qué es necesario?**
- Celery ejecuta tareas en threads sin event loop
- El executor de agentes es async
- Este helper crea un event loop bajo demanda

### Serialización para Celery

```python
# En agent.py: _execute_with_celery()
agent_config_dict = {
    "nombre": agent_config.nombre,
    "system_prompt": agent_config.system_prompt,
    "modelo": agent_config.modelo,
    "herramientas": agent_config.herramientas,
    "additional_goal": agent_config.additional_goal
}

# Celery usa JSON, no pickle (seguridad)
celery_task = execute_agent_task.delay(
    token=token,
    expediente_id=expediente_id,
    tarea_id=tarea_id,
    agent_config_dict=agent_config_dict,  # Dict, no dataclass
    ...
)
```

**¿Por qué dict y no dataclass?**
- Celery con JSON serializer no puede serializar dataclasses directamente
- JSON es más seguro que pickle (no permite code execution)
- El dict se reconstruye en el worker

### Redis Connection Pooling

```python
def get_connection_pool() -> ConnectionPool:
    global _connection_pool

    if _connection_pool is None:
        _connection_pool = ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD or None,
            decode_responses=True,
            max_connections=20,       # Pool de 20 conexiones
            socket_connect_timeout=5,
            socket_timeout=5
        )

    return _connection_pool
```

**Beneficios:**
- Reutilización de conexiones TCP
- Evita overhead de handshake por cada operación
- Timeouts previenen bloqueos indefinidos

## 3. Configuración Celery

```python
celery_app.conf.update(
    # Serialización segura
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',

    # Resiliencia
    task_acks_late=True,              # Ack después de completar
    worker_prefetch_multiplier=1,      # Un task a la vez
    worker_max_tasks_per_child=100,    # Prevenir memory leaks

    # Límites
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,  # 1 hora default

    # Limpieza
    result_expires=604800,  # 7 días
)
```

**task_acks_late=True:**
- El mensaje NO se elimina de Redis hasta que el task complete
- Si el worker muere, otro worker puede tomar el task
- Garantiza at-least-once delivery

**worker_prefetch_multiplier=1:**
- Cada worker toma solo 1 tarea a la vez
- Evita que un worker "acapare" muchas tareas
- Mejor distribución en múltiples workers

## 4. TaskTracker Redis

### Estructura de Claves

```
Clave: agentix:task:{agent_run_id}
TTL:   604800 segundos (7 días)

Valor (JSON):
{
    "agent_run_id": "abc-123-def",
    "expediente_id": "EXP-2024-001",
    "tarea_id": "TASK-001",
    "status": "running" | "pending" | "completed" | "failed",
    "started_at": "2026-01-22T10:30:00Z",
    "completed_at": null | "2026-01-22T10:35:00Z",
    "elapsed_seconds": 300,
    "success": null | true | false,
    "resultado": {...} | null,
    "error": null | {"codigo": "...", "mensaje": "...", "detalle": "..."}
}
```

### Operaciones Atómicas

```python
def mark_completed(self, agent_run_id: str, result: Any) -> None:
    key = self._task_key(agent_run_id)
    data_str = self._redis.get(key)

    if data_str:
        task_data = json.loads(data_str)
        task_data["status"] = "completed"
        task_data["completed_at"] = datetime.now(timezone.utc).isoformat()
        task_data["success"] = result.success
        task_data["resultado"] = result.resultado
        # ...

        # setex: SET + EXPIRE atómico, renueva TTL
        self._redis.setex(key, self.TTL_SECONDS, json.dumps(task_data))
```

## 5. Docker Compose Producción

### Servicios

```yaml
services:
  redis:
    # Broker + Result backend
    image: redis:7-alpine
    command: redis-server --requirepass ... --appendonly yes

  api:
    # FastAPI stateless (N instancias posibles)
    environment:
      USE_CELERY: "true"
    depends_on:
      redis: { condition: service_healthy }

  celery_worker:
    # Workers distribuidos
    command: celery ... --concurrency=4
    deploy:
      replicas: 2  # Configurable
      resources:
        limits: { cpus: '2', memory: 2G }

  flower:
    # UI monitoreo
    command: celery ... flower --basic_auth=admin:changeme
```

### Healthchecks

```yaml
redis:
  healthcheck:
    test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5

api:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
    interval: 30s
    timeout: 10s

flower:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:5555/flower/healthcheck"]
```

## 6. Métricas Prometheus

```python
# Counter de tareas
task_counter = Counter(
    'agentix_celery_tasks_total',
    'Total tareas Celery procesadas',
    ['agent_name', 'status']  # Labels
)

# Histograma de duración
task_duration = Histogram(
    'agentix_celery_task_duration_seconds',
    'Duración ejecución agente en Celery',
    ['agent_name'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600]
)
```

**Uso en tarea:**
```python
# Éxito
task_counter.labels(agent_name=agent_name, status='success').inc()
task_duration.labels(agent_name=agent_name).observe(duration)

# Timeout
task_counter.labels(agent_name=agent_name, status='timeout').inc()

# Error
task_counter.labels(agent_name=agent_name, status='failed').inc()
```

## 7. Comparación: BackgroundTasks vs Celery

| Característica | BackgroundTasks | Celery |
|----------------|-----------------|--------|
| Escalabilidad | Single process | N workers |
| Persistencia estado | Memoria (pierde en restart) | Redis (persiste) |
| Retry automático | Manual | Automático con backoff |
| Monitoreo | Logs | Flower UI + Prometheus |
| Distribución | Misma máquina | Cualquier máquina |
| Complejidad | Baja | Media |
| Dependencias | Ninguna | Redis + Celery + Flower |

## 8. Tests Implementados

### Tests Unitarios (68 nuevos)

| Suite | Tests | Cobertura |
|-------|-------|-----------|
| test_celery_app.py | 8 | Configuración Celery |
| test_celery_tasks.py | 16 | AgentExecutionTask |
| test_redis_client.py | 10 | Connection pool |
| test_task_tracker_factory.py | 12 | Factory pattern |
| test_task_tracker_redis.py | 16 | Redis backend |
| test_celery_integration.py | 6 | Integración E2E |

### Ejemplos de Tests

```python
# Test retry configuration
def test_autoretry_for_transient_errors(self):
    from backoffice.tasks.agent_execution import AgentExecutionTask

    assert ConnectionError in AgentExecutionTask.autoretry_for
    assert TimeoutError in AgentExecutionTask.autoretry_for
    assert OSError in AgentExecutionTask.autoretry_for

# Test factory pattern
def test_get_task_tracker_returns_redis_when_celery_enabled(self):
    with patch.object(settings, 'USE_CELERY', True):
        reset_task_tracker()
        tracker = get_task_tracker()
        assert isinstance(tracker, TaskTrackerRedis)

# Test TaskTracker Redis
def test_register_and_get_status(self, mock_redis):
    tracker = TaskTrackerRedis(redis_client=mock_redis)
    tracker.register("run-123", "EXP-001", "TASK-001")

    status = tracker.get_status("run-123")
    assert status["status"] == "pending"
    assert status["expediente_id"] == "EXP-001"
```

## 9. Compatibilidad

### ✅ Backward Compatible

- No modifica comportamiento de modo BackgroundTasks
- USE_CELERY=false mantiene funcionamiento original
- Mismo formato de respuesta API

### ✅ Migración Gradual

1. Deploy con USE_CELERY=false (sin cambios)
2. Agregar Redis + Workers
3. Cambiar USE_CELERY=true
4. Si hay problemas, rollback a false

### ✅ Graceful Degradation

- Si Redis no está disponible, error claro al iniciar
- Fallback a estado Celery si TaskTracker Redis falla
- Webhooks se envían aunque TaskTracker falle
