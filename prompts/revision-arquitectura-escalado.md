# Revisión de Arquitectura para Escalado Horizontal con Celery

**Fecha:** 2026-01-18
**Objetivo:** Preparar el sistema aGEntiX para el Paso 12 - Escalado horizontal con Celery + Redis

---

## 1. Análisis de la Arquitectura Actual

### 1.1. Flujo de Ejecución Actual

```
BPMN Engine
    ↓ POST /api/v1/agent/execute (JWT + context)
FastAPI API (/api/main.py)
    ↓ BackgroundTasks.add_task()
execute_and_callback() [in-process background]
    ↓
AgentExecutor.execute()
    ↓ Validación JWT
    ↓ Carga MCP config
    ↓ Crea MCPClientRegistry
    ↓ Ejecuta agente (CrewAI/LangGraph)
    ↓ Cierra recursos MCP
    ↑ AgentExecutionResult
    ↓
send_webhook() → BPMN Engine
```

### 1.2. Componentes Clave

| Componente | Ubicación | Función | Estado |
|------------|-----------|---------|--------|
| **FastAPI API** | `src/api/main.py` | Punto de entrada HTTP | ✅ Funcional |
| **agent.router** | `src/api/routers/agent.py` | Endpoints ejecución/status | ✅ Funcional |
| **AgentExecutor** | `src/backoffice/executor.py` | Orquestador principal | ✅ Funcional |
| **TaskTracker** | `src/api/services/task_tracker.py` | Estado en memoria | ⚠️ No distribuido |
| **BackgroundTasks** | FastAPI nativo | Async local | ⚠️ No escalable |
| **Webhook Service** | `src/api/services/webhook.py` | Callback BPMN | ✅ Funcional |
| **MCPClientRegistry** | `src/backoffice/mcp/registry.py` | Gestión MCP clients | ✅ Funcional |

### 1.3. Limitaciones Actuales

#### ❌ No hay separación entre API y Workers
- FastAPI ejecuta los agentes **en el mismo proceso** usando `BackgroundTasks`
- Si un agente tarda 5 minutos, bloquea un worker de Uvicorn
- No hay forma de escalar workers independientemente

#### ❌ Estado en memoria no distribuido
- `TaskTracker` usa un diccionario Python local (`self._tasks`)
- Si reiniciamos la API, **perdemos el estado de todas las ejecuciones en curso**
- No hay forma de consultar estado desde múltiples instancias de API

#### ❌ No hay cola de trabajos persistente
- `BackgroundTasks` es efímero, no sobrevive reinicios
- Si la API crashea, **perdemos todas las ejecuciones pendientes**
- No hay priorización ni control de concurrencia

#### ❌ Recursos MCP se crean/destruyen por ejecución
- Cada ejecución de agente crea `MCPClientRegistry` desde cero
- Conexiones HTTP a servidores MCP no se reutilizan
- Overhead de conexión en cada invocación

#### ❌ No hay reintentos automáticos
- Si un agente falla por error transitorio (red, timeout MCP), se pierde
- El BPMN debe volver a invocar manualmente

---

## 2. Arquitectura Objetivo con Celery

### 2.1. Flujo Propuesto

```
BPMN Engine
    ↓ POST /api/v1/agent/execute (JWT + context)
FastAPI API (stateless)
    ↓ task_id = execute_agent_task.delay()
    ↓ Redis Queue (persistente)
    ↑ 202 Accepted {task_id}

[Celery Worker 1] [Celery Worker 2] [Celery Worker N]
    ↓ Consume tarea de Redis
    ↓ AgentExecutor.execute()
    ↓ Guarda resultado en Redis
    ↓ send_webhook() → BPMN Engine
```

### 2.2. Componentes Nuevos/Modificados

| Componente | Cambio | Justificación |
|------------|--------|---------------|
| **Redis** | Nuevo | Cola de trabajos + Estado distribuido |
| **Celery Worker** | Nuevo | Procesos separados ejecutando agentes |
| **Celery Beat** | Nuevo (opcional) | Tareas periódicas (cleanup, health checks) |
| **TaskTracker** | Redis backend | Estado persistente y distribuido |
| **AgentExecutor** | Sin cambios | Mantiene interface actual |
| **API Router** | Cambia a Celery | `BackgroundTasks` → `task.delay()` |

### 2.3. Ventajas Clave

✅ **Escalabilidad horizontal**: Añadir más workers sin tocar código
✅ **Resiliencia**: Reintentos automáticos, tareas sobreviven reinicios
✅ **Separación de responsabilidades**: API responde rápido, workers procesan
✅ **Visibilidad**: Flower UI para monitoreo en tiempo real
✅ **Control de concurrencia**: Rate limiting, prioridades, timeouts
✅ **Estado distribuido**: Múltiples instancias de API comparten estado en Redis

---

## 3. Cambios Específicos por Componente

### 3.1. Nuevas Dependencias

```toml
# pyproject.toml o requirements.txt
celery[redis]==5.3.4
redis==5.0.1
flower==2.0.1  # UI opcional para monitoreo
```

### 3.2. Configuración de Redis

**Nuevo archivo: `src/backoffice/redis_client.py`**

```python
from redis import Redis
from backoffice.settings import settings

def get_redis_client() -> Redis:
    """
    Cliente Redis reutilizable.

    Usado por:
    - Celery como broker y backend
    - TaskTracker para estado distribuido
    """
    return Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        decode_responses=True
    )
```

**Actualizar `src/backoffice/settings.py`:**

```python
class Settings(BaseSettings):
    # ... campos existentes ...

    # Redis Configuration (Paso 12 - Escalado Horizontal)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 3600  # 1 hora max por tarea
```

### 3.3. Celery App

**Nuevo archivo: `src/backoffice/celery_app.py`**

```python
from celery import Celery
from backoffice.settings import settings

# Crear app Celery
celery_app = Celery(
    "agentix",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configuración
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_acks_late=True,  # Reintento si worker muere
    worker_prefetch_multiplier=1,  # Un task a la vez
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['backoffice.tasks'])
```

### 3.4. Tarea Celery para Ejecución de Agentes

**Nuevo archivo: `src/backoffice/tasks/agent_execution.py`**

```python
import asyncio
from celery import Task
from typing import Dict, Any, Optional

from backoffice.celery_app import celery_app
from backoffice.executor_factory import create_default_executor
from backoffice.models import AgentConfig
from backoffice.settings import settings
from api.services.webhook import send_webhook_with_retry


class AgentExecutionTask(Task):
    """
    Clase base para tareas de ejecución de agentes.

    Añade retry automático y logging mejorado.
    """
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 5}
    retry_backoff = True
    retry_jitter = True


@celery_app.task(
    bind=True,
    base=AgentExecutionTask,
    name='backoffice.execute_agent'
)
def execute_agent_task(
    self,
    token: str,
    expediente_id: str,
    tarea_id: str,
    agent_config: Dict[str, Any],
    callback_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tarea Celery para ejecutar un agente.

    Args:
        token: JWT token completo
        expediente_id: ID del expediente
        tarea_id: ID de la tarea BPMN
        agent_config: Dict serializable con config del agente
        callback_url: URL para webhook (opcional)

    Returns:
        Dict con resultado serializable

    Raises:
        Propaga excepciones para retry automático
    """

    # El task_id de Celery es nuestro agent_run_id
    agent_run_id = self.request.id

    # Convertir dict a AgentConfig
    config = AgentConfig(**agent_config)

    # Crear executor
    executor = create_default_executor(
        mcp_config_path=settings.MCP_CONFIG_PATH,
        jwt_secret=settings.JWT_SECRET,
        jwt_algorithm=settings.JWT_ALGORITHM
    )

    # Ejecutar agente (async)
    # Necesitamos correr el código async desde Celery (sync)
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        executor.execute(token, expediente_id, tarea_id, config)
    )

    # Enviar webhook si hay callback_url
    if callback_url:
        loop.run_until_complete(
            send_webhook_with_retry(
                callback_url,
                agent_run_id,
                result=result if result.success else None,
                error=result.error.dict() if result.error else None
            )
        )

    # Retornar resultado serializable
    return {
        "success": result.success,
        "agent_run_id": agent_run_id,
        "resultado": result.resultado,
        "herramientas_usadas": result.herramientas_usadas,
        "error": result.error.dict() if result.error else None,
        "log_auditoria": result.log_auditoria
    }
```

### 3.5. TaskTracker con Redis Backend

**Actualizar `src/api/services/task_tracker.py`:**

```python
from datetime import datetime, timezone
from typing import Dict, Optional, Any
import json
from redis import Redis

from backoffice.redis_client import get_redis_client


class TaskTracker:
    """
    Tracker distribuido usando Redis.

    Reemplaza implementación en memoria para permitir múltiples
    instancias de API compartiendo estado.

    Claves Redis:
    - agentix:task:{run_id} -> JSON con estado de tarea
    """

    def __init__(self, redis_client: Optional[Redis] = None):
        self._redis = redis_client or get_redis_client()
        self._key_prefix = "agentix:task:"
        self._ttl_seconds = 86400 * 7  # 7 días

    def _task_key(self, agent_run_id: str) -> str:
        """Construye clave Redis para una tarea"""
        return f"{self._key_prefix}{agent_run_id}"

    def register(
        self,
        agent_run_id: str,
        expediente_id: str,
        tarea_id: str
    ) -> None:
        """Registra una nueva tarea"""
        task_data = {
            "agent_run_id": agent_run_id,
            "expediente_id": expediente_id,
            "tarea_id": tarea_id,
            "status": "pending",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "elapsed_seconds": 0,
            "success": None,
            "resultado": None,
            "error": None
        }

        key = self._task_key(agent_run_id)
        self._redis.setex(
            key,
            self._ttl_seconds,
            json.dumps(task_data)
        )

    def mark_running(self, agent_run_id: str) -> None:
        """Marca tarea como en ejecución"""
        key = self._task_key(agent_run_id)
        data_str = self._redis.get(key)

        if data_str:
            task_data = json.loads(data_str)
            task_data["status"] = "running"
            self._redis.setex(key, self._ttl_seconds, json.dumps(task_data))

    def mark_completed(self, agent_run_id: str, result: Any) -> None:
        """Marca tarea como completada"""
        key = self._task_key(agent_run_id)
        data_str = self._redis.get(key)

        if data_str:
            task_data = json.loads(data_str)
            task_data["status"] = "completed"
            task_data["completed_at"] = datetime.now(timezone.utc).isoformat()
            task_data["success"] = result.success
            task_data["resultado"] = result.resultado
            task_data["error"] = None if result.success else {
                "codigo": result.error.codigo if result.error else "UNKNOWN",
                "mensaje": result.error.mensaje if result.error else "Error desconocido",
                "detalle": result.error.detalle if result.error else ""
            }

            # Calcular elapsed_seconds
            started = datetime.fromisoformat(task_data["started_at"])
            completed = datetime.fromisoformat(task_data["completed_at"])
            task_data["elapsed_seconds"] = int((completed - started).total_seconds())

            self._redis.setex(key, self._ttl_seconds, json.dumps(task_data))

    def get_status(self, agent_run_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene estado de una tarea"""
        key = self._task_key(agent_run_id)
        data_str = self._redis.get(key)

        if not data_str:
            return None

        task_data = json.loads(data_str)

        # Si está running, calcular elapsed_seconds actual
        if task_data["status"] == "running":
            started = datetime.fromisoformat(task_data["started_at"])
            now = datetime.now(timezone.utc)
            task_data["elapsed_seconds"] = int((now - started).total_seconds())

        return task_data


# Singleton global
_task_tracker = None

def get_task_tracker() -> TaskTracker:
    """Dependency injection para FastAPI"""
    global _task_tracker
    if _task_tracker is None:
        _task_tracker = TaskTracker()
    return _task_tracker
```

### 3.6. Router de Agent con Celery

**Actualizar `src/api/routers/agent.py`:**

```python
# Reemplazar import de BackgroundTasks
from backoffice.tasks.agent_execution import execute_agent_task

@router.post(
    "/execute",
    response_model=ExecuteAgentResponse,
    status_code=202,
    summary="Ejecutar agente de forma asíncrona",
    description="Inicia la ejecución de un agente en Celery y retorna inmediatamente."
)
async def execute_agent(
    request: ExecuteAgentRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Ejecuta un agente usando Celery.

    **Cambios vs. versión anterior:**
    - Ya no usa BackgroundTasks (local)
    - Envía tarea a Redis/Celery (distribuido)
    - Workers separados procesan las ejecuciones
    """

    # 1-4. [Igual que antes: validación JWT, carga config, crear executor, etc.]
    # ...

    # 5. Enviar tarea a Celery
    celery_task = execute_agent_task.delay(
        token=token,
        expediente_id=request.context.expediente_id,
        tarea_id=request.context.tarea_id,
        agent_config=agent_config.dict(),  # Serializable
        callback_url=callback_url
    )

    # El task_id de Celery ES nuestro agent_run_id
    agent_run_id = celery_task.id

    # 6. Registrar en TaskTracker (Redis)
    task_tracker = get_task_tracker()
    task_tracker.register(
        agent_run_id=agent_run_id,
        expediente_id=request.context.expediente_id,
        tarea_id=request.context.tarea_id
    )

    logger.info(
        f"Tarea Celery encolada: {agent_run_id} "
        f"(expediente={request.context.expediente_id}, agente={request.agent})"
    )

    # 7. Retornar 202 Accepted inmediatamente
    return ExecuteAgentResponse(
        agent_run_id=agent_run_id,
        message="Ejecución de agente encolada en Celery",
        callback_url=callback_url
    )
```

**ELIMINAR:** La función `execute_and_callback()` ya no es necesaria (ahora es `execute_agent_task` en Celery).

### 3.7. Endpoint de Status con Celery

**Actualizar `src/api/routers/agent.py`:**

```python
from celery.result import AsyncResult
from backoffice.celery_app import celery_app

@router.get(
    "/status/{agent_run_id}",
    response_model=AgentStatusResponse,
    summary="Consultar estado de ejecución"
)
async def get_agent_status(agent_run_id: str):
    """
    Consulta el estado desde Celery + Redis.

    **Prioridad:**
    1. Consultar TaskTracker (Redis) si existe
    2. Fallback a Celery task state
    """

    # Primero intentar TaskTracker (más completo)
    task_tracker = get_task_tracker()
    status = task_tracker.get_status(agent_run_id)

    if status:
        return AgentStatusResponse(**status)

    # Fallback: consultar Celery directamente
    celery_result = AsyncResult(agent_run_id, app=celery_app)

    if celery_result.state == 'PENDING':
        # Tarea no existe o aún no empezó
        raise HTTPException(
            status_code=404,
            detail=f"agent_run_id no encontrado: {agent_run_id}"
        )

    # Mapear estados Celery a nuestro formato
    status_map = {
        'PENDING': 'pending',
        'STARTED': 'running',
        'RETRY': 'running',
        'SUCCESS': 'completed',
        'FAILURE': 'failed'
    }

    return AgentStatusResponse(
        agent_run_id=agent_run_id,
        status=status_map.get(celery_result.state, 'unknown'),
        success=celery_result.successful() if celery_result.ready() else None,
        resultado=celery_result.result if celery_result.successful() else None,
        error=str(celery_result.result) if celery_result.failed() else None
    )
```

---

## 4. Infraestructura y Despliegue

### 4.1. Docker Compose (Desarrollo)

**Actualizar `docker-compose.yml` (si existe) o crear uno nuevo:**

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  api:
    build: .
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8080
    ports:
      - "8080:8080"
    environment:
      - REDIS_HOST=redis
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
    volumes:
      - .:/app

  celery_worker:
    build: .
    command: celery -A backoffice.celery_app worker --loglevel=info --concurrency=4
    environment:
      - REDIS_HOST=redis
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
    volumes:
      - .:/app
    deploy:
      replicas: 2  # 2 workers para HA

  flower:
    build: .
    command: celery -A backoffice.celery_app flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis

volumes:
  redis_data:
```

### 4.2. Scripts de Inicio

**Nuevo script: `scripts/start_worker.sh`**

```bash
#!/bin/bash
# Inicia un worker de Celery

celery -A backoffice.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=100 \
    --time-limit=3600
```

**Nuevo script: `scripts/start_flower.sh`**

```bash
#!/bin/bash
# Inicia Flower (UI de monitoreo)

celery -A backoffice.celery_app flower \
    --port=5555 \
    --basic_auth=admin:changeme
```

### 4.3. Configuración de Producción

**Variables de entorno adicionales (`.env`):**

```bash
# Redis
REDIS_HOST=redis.production.internal
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=secure_password_here

# Celery
CELERY_BROKER_URL=redis://:secure_password_here@redis.production.internal:6379/0
CELERY_RESULT_BACKEND=redis://:secure_password_here@redis.production.internal:6379/0
CELERY_TASK_TIME_LIMIT=3600

# Workers
CELERY_WORKER_CONCURRENCY=8
CELERY_WORKER_MAX_TASKS_PER_CHILD=100
```

---

## 5. Plan de Migración (Paso a Paso)

### Fase 1: Preparación (Sin Downtime)

**Objetivo:** Instalar dependencias y configuración sin afectar funcionamiento actual.

1. **Instalar Redis**
   ```bash
   # macOS
   brew install redis
   brew services start redis

   # Ubuntu/Debian
   sudo apt install redis-server
   sudo systemctl start redis
   ```

2. **Instalar dependencias Python**
   ```bash
   pip install celery[redis]==5.3.4 redis==5.0.1 flower==2.0.1
   ```

3. **Añadir configuración a `.env`**
   ```bash
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   REDIS_PASSWORD=
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```

4. **Crear archivos nuevos** (sin modificar existentes)
   - `src/backoffice/redis_client.py`
   - `src/backoffice/celery_app.py`
   - `src/backoffice/tasks/__init__.py`
   - `src/backoffice/tasks/agent_execution.py`

5. **Verificar que tests actuales siguen pasando**
   ```bash
   ./run-tests.sh
   ```

### Fase 2: Implementación Paralela (Feature Flag)

**Objetivo:** Implementar Celery con flag de activación, mantener código anterior.

6. **Añadir feature flag a settings**
   ```python
   # src/backoffice/settings.py
   USE_CELERY: bool = False  # Default: mantener comportamiento actual
   ```

7. **Modificar `agent.py` con condicional**
   ```python
   if settings.USE_CELERY:
       # Nueva implementación con Celery
       celery_task = execute_agent_task.delay(...)
   else:
       # Implementación actual con BackgroundTasks
       background_tasks.add_task(execute_and_callback, ...)
   ```

8. **Implementar TaskTracker dual**
   ```python
   # src/api/services/task_tracker.py
   class TaskTrackerFactory:
       @staticmethod
       def create():
           if settings.USE_CELERY:
               return RedisTaskTracker()
           else:
               return InMemoryTaskTracker()  # Actual
   ```

9. **Tests para nueva implementación**
   ```bash
   # Crear tests/api/test_celery_integration.py
   pytest tests/api/test_celery_integration.py -v
   ```

### Fase 3: Testing en Desarrollo

**Objetivo:** Validar nueva arquitectura con flag activado.

10. **Activar flag en `.env`**
    ```bash
    USE_CELERY=true
    ```

11. **Iniciar workers en terminal separada**
    ```bash
    celery -A backoffice.celery_app worker --loglevel=info
    ```

12. **Iniciar API**
    ```bash
    uvicorn src.api.main:app --reload --port 8080
    ```

13. **Ejecutar suite de tests**
    ```bash
    ./run-tests.sh
    pytest tests/api/test_celery_integration.py -v
    ```

14. **Test manual desde frontend**
    - Ejecutar agente desde Dashboard
    - Verificar logs en worker
    - Comprobar webhook callback

15. **Monitoreo con Flower**
    ```bash
    celery -A backoffice.celery_app flower --port=5555
    # Abrir http://localhost:5555
    ```

### Fase 4: Migración Completa

**Objetivo:** Hacer Celery el modo por defecto, deprecar código antiguo.

16. **Cambiar default del flag**
    ```python
    USE_CELERY: bool = True  # Nuevo default
    ```

17. **Actualizar documentación**
    - `CLAUDE.md`: Sección "Running the Application"
    - `README.md`: Setup de Redis + Celery
    - `/doc`: Nuevo Zettelkasten sobre arquitectura distribuida

18. **Deprecation warnings en código antiguo**
    ```python
    if not settings.USE_CELERY:
        logger.warning(
            "DEPRECATION: BackgroundTasks mode is deprecated. "
            "Set USE_CELERY=true in .env"
        )
    ```

### Fase 5: Limpieza (Post-Validación)

**Objetivo:** Eliminar código legacy tras validación en producción.

19. **Eliminar código de BackgroundTasks** (tras 1-2 semanas en prod)
    - Función `execute_and_callback()` en `agent.py`
    - Clase `InMemoryTaskTracker`
    - Feature flag `USE_CELERY`

20. **Optimizaciones**
    - Connection pooling para Redis
    - Celery Beat para tareas periódicas (cleanup logs, etc.)
    - Monitoring con Prometheus + Grafana

---

## 6. Testing

### 6.1. Tests Unitarios Nuevos

**Archivo: `tests/backoffice/test_celery_tasks.py`**

```python
import pytest
from unittest.mock import patch, MagicMock
from backoffice.tasks.agent_execution import execute_agent_task
from backoffice.models import AgentConfig

def test_execute_agent_task_success():
    """Test que tarea Celery ejecuta agente correctamente"""
    # Mock del executor
    with patch('backoffice.tasks.agent_execution.create_default_executor') as mock_factory:
        mock_executor = MagicMock()
        mock_result = MagicMock(
            success=True,
            agent_run_id="test-run-123",
            resultado={"output": "success"},
            herramientas_usadas=["tool1"],
            error=None
        )
        mock_executor.execute.return_value = mock_result
        mock_factory.return_value = mock_executor

        # Ejecutar tarea
        result = execute_agent_task(
            token="fake-jwt",
            expediente_id="EXP-001",
            tarea_id="TASK-001",
            agent_config={"nombre": "test", "sistema": "mock"},
            callback_url=None
        )

        # Validar
        assert result["success"] is True
        assert result["resultado"]["output"] == "success"
```

**Archivo: `tests/api/test_celery_integration.py`**

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

def test_execute_agent_enqueues_celery_task(client: TestClient):
    """Test que POST /execute envía tarea a Celery"""
    with patch('api.routers.agent.execute_agent_task.delay') as mock_delay:
        mock_delay.return_value.id = "celery-task-123"

        response = client.post(
            "/api/v1/agent/execute",
            json={
                "agent": "test",
                "context": {
                    "expediente_id": "EXP-001",
                    "tarea_id": "TASK-001"
                }
            },
            headers={"Authorization": "Bearer fake-jwt"}
        )

        assert response.status_code == 202
        assert response.json()["agent_run_id"] == "celery-task-123"
        mock_delay.assert_called_once()
```

### 6.2. Tests de Integración

**Archivo: `tests/integration/test_end_to_end_celery.py`**

```python
import pytest
import time
from celery.result import AsyncResult

@pytest.mark.integration
def test_full_agent_execution_flow():
    """
    Test E2E con Celery real:
    1. POST /execute
    2. Esperar tarea en worker
    3. GET /status hasta completed
    4. Verificar resultado
    """
    # Requiere Redis + Worker corriendo
    pass  # Implementar con pytest-celery
```

### 6.3. Actualizar Tests Existentes

- **Mockear Celery en tests que no lo necesitan:**
  ```python
  @pytest.fixture(autouse=True)
  def mock_celery_for_unit_tests():
      with patch('api.routers.agent.execute_agent_task.delay'):
          yield
  ```

---

## 7. Monitoreo y Observabilidad

### 7.1. Métricas Nuevas

**Añadir a Prometheus:**

- `celery_tasks_total{status="success|failed|retry"}`
- `celery_task_duration_seconds{agent_name}`
- `celery_queue_length`
- `celery_workers_active`
- `redis_connection_pool_usage`

**Implementación:**

```python
# src/backoffice/tasks/agent_execution.py
from prometheus_client import Counter, Histogram

task_counter = Counter(
    'agentix_celery_tasks_total',
    'Total tareas Celery procesadas',
    ['agent_name', 'status']
)

task_duration = Histogram(
    'agentix_celery_task_duration_seconds',
    'Duración ejecución agente',
    ['agent_name']
)

@celery_app.task(...)
def execute_agent_task(...):
    with task_duration.labels(agent_name=agent_config['nombre']).time():
        try:
            result = ...
            task_counter.labels(agent_name=..., status='success').inc()
        except Exception:
            task_counter.labels(agent_name=..., status='failed').inc()
            raise
```

### 7.2. Flower UI

- URL: `http://localhost:5555`
- Muestra: tareas en curso, historial, workers activos, latencias
- Autenticación: `--basic_auth=admin:password`

### 7.3. Logging Estructurado

**Añadir contexto Celery a logs:**

```python
import logging
from celery.signals import task_prerun, task_postrun

@task_prerun.connect
def task_prerun_handler(sender, task_id, task, args, kwargs, **extra):
    logger = logging.getLogger('agentix.celery')
    logger.info(
        "Tarea iniciando",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "expediente_id": kwargs.get('expediente_id')
        }
    )
```

---

## 8. Consideraciones de Seguridad

### 8.1. Redis

- **Autenticación:** Usar `REDIS_PASSWORD` en producción
- **Firewall:** Restringir acceso a Redis a IPs internas
- **TLS:** Considerar `rediss://` para conexiones cifradas

### 8.2. Celery

- **Serialización:** Usar JSON (no pickle) para evitar code injection
- **Rate limiting:** Limitar tareas por IP/usuario para evitar DoS
- **Task signatures:** Verificar integridad de argumentos

### 8.3. Secrets Management

- No pasar API keys como argumentos de tarea (quedan en logs)
- Cargar secrets desde env vars dentro del worker

---

## 9. Rollback Plan

### En caso de problemas en producción:

1. **Desactivar feature flag:**
   ```bash
   export USE_CELERY=false
   ```

2. **Reiniciar API:**
   ```bash
   systemctl restart agentix-api
   ```

3. **Mantener workers corriendo** (para completar tareas en curso)

4. **Drenar cola de Redis:**
   ```bash
   celery -A backoffice.celery_app purge
   ```

---

## 10. Checklist de Validación

Antes de considerar la migración completa:

- [ ] Redis instalado y accesible
- [ ] Celery workers inician sin errores
- [ ] Tests unitarios pasan (119/119)
- [ ] Tests de integración Celery pasan
- [ ] POST /execute encola tarea correctamente
- [ ] GET /status retorna estado desde Redis
- [ ] Webhook se envía tras completar tarea
- [ ] Flower muestra tareas en UI
- [ ] Métricas Prometheus funcionan
- [ ] Logs estructurados capturan task_id
- [ ] Timeout de tareas funciona (CELERY_TASK_TIME_LIMIT)
- [ ] Retry automático funciona tras fallo transitorio
- [ ] Múltiples workers procesan tareas concurrentemente
- [ ] Estado persiste tras reiniciar API
- [ ] Documentación actualizada (CLAUDE.md, README)

---

## 11. Impacto en Otros Componentes

### ✅ Sin Cambios Necesarios

- **AgentExecutor**: Interface se mantiene igual
- **MCPClientRegistry**: Sin cambios
- **JWT Validator**: Sin cambios
- **PII Redactor**: Sin cambios
- **Agents (CrewAI/LangGraph)**: Sin cambios
- **Frontend Dashboard**: Usa mismos endpoints

### ⚠️ Cambios Menores

- **Webhook Service**: Mover a `backoffice/tasks` para ser accesible desde workers
- **Settings**: Añadir config de Redis/Celery
- **Logs**: Añadir `task_id` al contexto

---

## 12. Próximos Pasos Post-Migración

Una vez completado el escalado horizontal:

1. **Auto-scaling:** Escalar workers según carga (Kubernetes HPA)
2. **Task routing:** Colas separadas por tipo de agente (CPU-bound vs I/O-bound)
3. **Priorización:** Alta prioridad para tareas críticas
4. **Scheduled tasks:** Celery Beat para cleanup, health checks periódicos
5. **Dead letter queue:** Manejo de tareas que fallan repetidamente

---

## Conclusión

La migración a Celery es **evolutiva y sin riesgo** gracias al uso de feature flags. La arquitectura actual está bien diseñada con inyección de dependencias, lo que facilita la transición.

**Esfuerzo estimado:**
- Fase 1-2 (Setup + Feature flag): 2-3 días
- Fase 3 (Testing): 1-2 días
- Fase 4-5 (Deploy + Cleanup): 1 día

**Beneficios clave:**
- ✅ Escalabilidad horizontal real (añadir workers sin código)
- ✅ Resiliencia ante fallos (reintentos, persistencia)
- ✅ Visibilidad operacional (Flower, métricas)
- ✅ Mejor utilización de recursos (workers dedicados)

**Sin comprometer:**
- ✅ Tests actuales (119/119 pasan)
- ✅ Seguridad JWT/PII
- ✅ Interface del AgentExecutor
- ✅ Compatibilidad con frontend
