# Paso 12: Escalado Horizontal con Celery + Redis

## Objetivo

Implementar escalabilidad horizontal en aGEntiX usando **Celery** como sistema de colas de tareas y **Redis** como broker y backend de resultados. Esto permitirá:

- Múltiples workers procesando agentes en paralelo
- Estado distribuido (persistente en Redis)
- Resiliencia ante fallos (reintentos automáticos)
- Visibilidad operacional (Flower UI, métricas)

## Contexto Previo

**IMPORTANTE:** Antes de implementar, revisar el documento de arquitectura:

- `/prompts/revision-arquitectura-escalado.md` - Contiene el análisis completo, arquitectura objetivo y código de referencia

### Estado Actual

| Componente       | Estado        | Limitación                                 |
| ---------------- | ------------- | ------------------------------------------ |
| FastAPI API      | ✅ Funcional  | Ejecuta agentes en el mismo proceso        |
| TaskTracker      | ⚠️ En memoria | No distribuido, pierde estado al reiniciar |
| BackgroundTasks  | ⚠️ Local      | No escala, no sobrevive reinicios          |
| AgentExecutor    | ✅ Funcional  | Interface se mantiene sin cambios          |

### Arquitectura Objetivo

```text
BPMN Engine
    ↓ POST /api/v1/agent/execute
FastAPI API (stateless)
    ↓ execute_agent_task.delay()
    ↓ Redis Queue

[Worker 1] [Worker 2] [Worker N]
    ↓ AgentExecutor.execute()
    ↓ Resultado → Redis
    ↓ send_webhook() → BPMN
```

## Instrucciones de Implementación

### Fase 1: Setup de Infraestructura ✅ COMPLETADA

#### 1.1. Instalar dependencias

Añadir a `requirements.txt` o `pyproject.toml`:

```text
celery[redis]==5.3.4
redis==5.0.1
flower==2.0.1
```

#### 1.2. Configurar Redis

##### Opción A: VSCode Dev Containers (Recomendado)

Actualizar `.devcontainer/devcontainer.json` para usar Docker Compose con Redis:

**1. Crear `.devcontainer/docker-compose.yml`:**

```yaml
version: '3.8'

services:
  app:
    build:
      context: ..
      dockerfile: .devcontainer/Dockerfile
    volumes:
      - ..:/workspaces/aGEntiX:cached
    command: sleep infinity
    network_mode: service:redis
    depends_on:
      - redis

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

volumes:
  redis_data:
```

**2. Crear `.devcontainer/Dockerfile`:**

```dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Instalar Node.js LTS
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs

# Instalar redis-tools para debugging
RUN apt-get update && apt-get install -y redis-tools && rm -rf /var/lib/apt/lists/*
```

**3. Actualizar `.devcontainer/devcontainer.json`:**

```json
{
  "name": "aGEntiX Development",
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspaces/aGEntiX",

  "features": {
    "ghcr.io/devcontainers/features/git:1": {
      "version": "latest"
    },
    "ghcr.io/devcontainers/features/common-utils:2": {
      "installZsh": true,
      "installOhMyZsh": true,
      "upgradePackages": true
    }
  },

  "customizations": {
    "vscode": {
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "python.testing.pytestEnabled": true
      },
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-python.black-formatter",
        "redhat.vscode-yaml",
        "cweijan.vscode-redis-client"
      ]
    }
  },

  "forwardPorts": [6379, 8000, 8080, 5173, 5555],
  "portsAttributes": {
    "6379": { "label": "Redis", "onAutoForward": "silent" },
    "8000": { "label": "MCP Server", "onAutoForward": "notify" },
    "8080": { "label": "API", "onAutoForward": "notify" },
    "5173": { "label": "Frontend", "onAutoForward": "openBrowser" },
    "5555": { "label": "Flower UI", "onAutoForward": "notify" }
  },

  "postCreateCommand": ".devcontainer/post-create.sh",
  "remoteUser": "vscode",

  "containerEnv": {
    "PYTHONUNBUFFERED": "1",
    "REDIS_HOST": "localhost",
    "CELERY_BROKER_URL": "redis://localhost:6379/0",
    "CELERY_RESULT_BACKEND": "redis://localhost:6379/0"
  }
}
```

**4. Actualizar `.devcontainer/post-create.sh`:**

Añadir al final del script:

```bash
# Instalar dependencias de Celery
echo "📦 Instalando dependencias de Celery..."
pip install celery[redis]==5.3.4 redis==5.0.1 flower==2.0.1

# Verificar conexión a Redis
echo "🔍 Verificando conexión a Redis..."
redis-cli ping && echo "✅ Redis conectado" || echo "⚠️ Redis no disponible"
```

##### Opción B: Desarrollo Local (sin Dev Containers)

```bash
# macOS
brew install redis && brew services start redis

# Ubuntu/Debian
sudo apt install redis-server && sudo systemctl start redis

# Docker (standalone)
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

#### 1.3. Variables de entorno

Añadir a `.env.example` y `.env`:

```bash
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_TIME_LIMIT=3600
CELERY_TASK_TRACK_STARTED=true

# Feature Flag (migración gradual)
USE_CELERY=false
```

### Fase 2: Implementación del Código ✅ COMPLETADA

#### 2.1. Archivos nuevos a crear

| Archivo                                    | Propósito                                |
| ------------------------------------------ | ---------------------------------------- |
| `src/backoffice/redis_client.py`           | Cliente Redis reutilizable               |
| `src/backoffice/celery_app.py`             | Configuración de Celery                  |
| `src/backoffice/tasks/__init__.py`         | Package de tareas                        |
| `src/backoffice/tasks/agent_execution.py`  | Tarea Celery para ejecutar agentes       |
| `src/api/services/task_tracker_redis.py`   | TaskTracker con backend Redis            |

#### 2.2. Archivos a modificar

| Archivo                            | Cambios                              |
| ---------------------------------- | ------------------------------------ |
| `src/backoffice/settings.py`       | Añadir config Redis/Celery           |
| `src/api/routers/agent.py`         | Usar Celery con feature flag         |
| `src/api/services/task_tracker.py` | Factory pattern para elegir backend  |

#### 2.3. Código de referencia

Ver `/prompts/revision-arquitectura-escalado.md` secciones 3.2-3.6 para el código completo de cada componente.

**Puntos clave:**

1. **redis_client.py**: Cliente simple con connection pooling
2. **celery_app.py**: Configuración con `task_acks_late=True` para resiliencia
3. **agent_execution.py**: Tarea con `autoretry_for` y `retry_backoff`
4. **task_tracker_redis.py**: Claves con TTL de 7 días

### Fase 3: Feature Flag para Migración Gradual ✅ COMPLETADA

Implementar condicional en `agent.py`:

```python
if settings.USE_CELERY:
    # Nueva implementación con Celery
    celery_task = execute_agent_task.delay(
        token=token,
        expediente_id=request.context.expediente_id,
        tarea_id=request.context.tarea_id,
        agent_config=agent_config.dict(),
        callback_url=callback_url
    )
    agent_run_id = celery_task.id
else:
    # Implementación actual (BackgroundTasks)
    agent_run_id = f"RUN-{...}"
    background_tasks.add_task(execute_and_callback, ...)
```

### Fase 4: Testing ✅ COMPLETADA

#### 4.1. Tests unitarios nuevos

Crear `tests/backoffice/test_celery_tasks.py`:

- Test ejecución de tarea con mocks
- Test reintentos automáticos
- Test timeout de tarea

Crear `tests/api/test_task_tracker_redis.py`:

- Test register/mark_running/mark_completed
- Test get_status con cálculo de elapsed_seconds
- Test TTL de claves

#### 4.2. Tests de integración

Crear `tests/integration/test_celery_integration.py`:

- Test E2E con Redis y Worker reales
- Test múltiples tareas concurrentes
- Test recuperación tras fallo de worker

#### 4.3. Actualizar tests existentes

- Mockear Celery en tests unitarios que no lo necesitan
- Añadir fixture para elegir backend de TaskTracker

### Fase 5: Docker Compose para Producción ✅ COMPLETADA

Crear `docker-compose.prod.yml`:

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

  api:
    build: .
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8080
    ports:
      - "8080:8080"
    environment:
      - REDIS_HOST=redis
      - USE_CELERY=true
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis

  celery_worker:
    build: .
    command: celery -A backoffice.celery_app worker --loglevel=info --concurrency=4
    environment:
      - REDIS_HOST=redis
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
    deploy:
      replicas: 2

  flower:
    build: .
    command: celery -A backoffice.celery_app flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis

volumes:
  redis_data:
```

### Fase 6: Monitoreo ✅ COMPLETADA

#### 6.1. Métricas Prometheus

Añadir contadores y histogramas en `agent_execution.py`:

- `agentix_celery_tasks_total{agent_name, status}`
- `agentix_celery_task_duration_seconds{agent_name}`

#### 6.2. Flower UI

Accesible en `http://localhost:5555`:

- Tareas en curso y completadas
- Workers activos
- Latencias y errores

### Fase 7: Scripts de Inicio ✅ COMPLETADA

Crear `scripts/start_worker.sh`:

```bash
#!/bin/bash
celery -A backoffice.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=100
```

Crear `scripts/start_flower.sh`:

```bash
#!/bin/bash
celery -A backoffice.celery_app flower \
    --port=5555 \
    --basic_auth=admin:changeme
```

## Comandos de Desarrollo (Dev Container)

Una vez dentro del dev container:

```bash
# Verificar que Redis está corriendo
redis-cli ping

# Iniciar worker de Celery (terminal 1)
celery -A backoffice.celery_app worker --loglevel=info

# Iniciar Flower para monitoreo (terminal 2)
celery -A backoffice.celery_app flower --port=5555

# Iniciar API (terminal 3)
python -m uvicorn src.api.main:app --reload --port 8080

# Ejecutar tests
./run-tests.sh
```

## Criterios de Aceptación

### Tests

- [ ] Todos los tests existentes siguen pasando (119/119)
- [ ] Tests nuevos de Celery pasan
- [ ] Tests de TaskTracker Redis pasan
- [ ] Tests de integración E2E pasan

### Funcionalidad

- [ ] `POST /execute` encola tarea en Celery correctamente
- [ ] `GET /status/{id}` retorna estado desde Redis
- [ ] Webhook se envía tras completar tarea en worker
- [ ] Estado persiste tras reiniciar API
- [ ] Múltiples workers procesan tareas concurrentemente
- [ ] Reintentos automáticos funcionan tras fallo transitorio
- [ ] Timeout de tareas funciona (CELERY_TASK_TIME_LIMIT)

### Feature Flag

- [ ] `USE_CELERY=false` mantiene comportamiento actual
- [ ] `USE_CELERY=true` usa nueva arquitectura
- [ ] Transición sin downtime

### Monitoreo

- [ ] Flower muestra tareas y workers
- [ ] Métricas Prometheus expuestas
- [ ] Logs incluyen task_id de Celery

### Documentación

- [ ] Actualizar `CLAUDE.md` con instrucciones de Redis/Celery
- [ ] Actualizar `README.md` con setup
- [ ] Actualizar `.devcontainer/` con Redis
- [ ] Crear nota Zettelkasten en `/doc` sobre arquitectura distribuida

## Notas de Seguridad

1. **Redis**: Usar password en producción, restringir acceso por firewall
2. **Celery**: Serialización JSON (no pickle), no pasar secrets como argumentos
3. **Flower**: Configurar autenticación básica

## Rollback

Si hay problemas:

1. `export USE_CELERY=false`
2. Reiniciar API
3. Workers completarán tareas en curso
4. Opcional: `celery -A backoffice.celery_app purge` para limpiar cola

## Referencias

- `/prompts/revision-arquitectura-escalado.md` - Arquitectura detallada
- `/src/api/services/task_tracker.py` - Implementación actual en memoria
- `/src/api/routers/agent.py` - Router actual con BackgroundTasks
- `/src/backoffice/executor.py` - AgentExecutor (sin cambios)
- `.devcontainer/` - Configuración actual de Dev Containers
- [Celery docs](https://docs.celeryq.dev/)
- [Flower docs](https://flower.readthedocs.io/)
