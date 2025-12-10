# Paso 2: API REST con FastAPI para Ejecución de Agentes

## Objetivo

Crear una **API REST con FastAPI** que exponga el back-office de agentes (implementado en Paso 1) mediante endpoints HTTP seguros, permitiendo la ejecución asíncrona de agentes desde el motor BPMN de GEX.

Este paso permitirá:

- **Interfaz HTTP** para que BPMN invoque agentes de forma programática
- **Ejecución asíncrona** de agentes sin bloquear el flujo BPMN
- **Seguridad JWT** con validación de tokens en cada request
- **Métricas Prometheus** para observabilidad del sistema
- **Documentación OpenAPI** automática para integración
- **Manejo robusto de errores** con códigos HTTP semánticos

## Contexto del Sistema

### Estado Actual (Post-Paso 1)

Ya disponemos de:

- ✅ **AgentExecutor** (`backoffice/executor.py`): Orquestador principal con DI
- ✅ **Validación JWT** (`backoffice/auth/jwt_validator.py`): 10 claims validados
- ✅ **Multi-MCP Registry** (`backoffice/mcp/registry.py`): Routing automático
- ✅ **Audit Logging** (`backoffice/logging/audit_logger.py`): Logs con PII redaction
- ✅ **3 Agentes Mock** (ValidadorDocumental, AnalizadorSubvencion, GeneradorInforme)
- ✅ **86 tests** (100% PASS): 40 unitarios + 46 integración
- ✅ **Dependency Injection**: AgentExecutor 100% testeable

### Arquitectura Objetivo (Post-Paso 2)

```text
┌─────────────────────────────────────────────────────────────────────┐
│ BPMN Engine (GEX)                                                   │
│   ├─ Activiti/Camunda                                               │
│   └─ Service Task: POST /api/v1/agent/execute                       │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ HTTP + JWT
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│ API REST (FastAPI) - NUEVO en Paso 2                                │
│   ├─ Endpoint: POST /api/v1/agent/execute                           │
│   ├─ Validación JWT (extrae claims)                                 │
│   ├─ Background Task (AsyncTask)                                    │
│   ├─ Métricas Prometheus                                            │
│   └─ OpenAPI docs                                                   │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ Async call
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Back-Office (Paso 1)                                                │
│   ├─ AgentExecutor (DI)                                             │
│   ├─ JWT Validator (10 claims)                                      │
│   ├─ MCP Client Registry                                            │
│   ├─ Audit Logger (PII redacted)                                    │
│   └─ Agent Mock (ValidadorDocumental, etc.)                         │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ MCP JSON-RPC 2.0
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│ MCP Servers                                                         │
│   ├─ mcp-expedientes (HTTP + SSE)                                   │
│   └─ (Futuros: mcp-firma, mcp-notificaciones, ...)                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Requisitos Funcionales

### 1. Endpoint Principal: Ejecutar Agente

**Ruta:** `POST /api/v1/agent/execute`

**Descripción:** Ejecuta un agente de forma asíncrona para una tarea BPMN.

**Autenticación:** Bearer token JWT (mismo token que se pasa al AgentExecutor)

**Request Body:**

```json
{
  "expediente_id": "EXP-2024-001",
  "tarea_id": "TAREA-VALIDAR-DOC",
  "agent_config": {
    "nombre": "ValidadorDocumental",
    "system_prompt": "Eres un validador de documentación administrativa",
    "modelo": "claude-3-5-sonnet-20241022",
    "prompt_tarea": "Valida que todos los documentos estén presentes y sean válidos",
    "herramientas": ["consultar_expediente", "actualizar_datos", "añadir_anotacion"]
  },
  "webhook_url": "https://bpmn.example.com/api/v1/tasks/TAREA-VALIDAR-DOC/callback",
  "timeout_seconds": 300
}
```

**Response 202 Accepted (Ejecución asíncrona iniciada):**

```json
{
  "status": "accepted",
  "agent_run_id": "RUN-20241208-143022-123456",
  "message": "Ejecución de agente iniciada",
  "webhook_url": "https://bpmn.example.com/api/v1/tasks/TAREA-VALIDAR-DOC/callback"
}
```

**Webhook Callback (cuando agente termina):**

POST al `webhook_url` con resultado:

```json
{
  "agent_run_id": "RUN-20241208-143022-123456",
  "status": "completed",
  "success": true,
  "resultado": {
    "completado": true,
    "mensaje": "Validación completada. Todos los documentos están presentes.",
    "documentos_validados": ["DNI", "Certificado", "Solicitud"]
  },
  "herramientas_usadas": ["consultar_expediente", "actualizar_datos"],
  "timestamp": "2024-12-08T14:35:22Z"
}
```

**Webhook Callback (en caso de error):**

```json
{
  "agent_run_id": "RUN-20241208-143022-123456",
  "status": "failed",
  "success": false,
  "error": {
    "codigo": "AUTH_TOKEN_EXPIRED",
    "mensaje": "Token JWT expirado",
    "detalle": "exp=1234567890"
  },
  "timestamp": "2024-12-08T14:35:22Z"
}
```

**Códigos de Estado HTTP:**

- `202 Accepted`: Ejecución asíncrona iniciada correctamente
- `400 Bad Request`: Request inválido (campos faltantes, formato incorrecto)
- `401 Unauthorized`: Token JWT ausente o inválido
- `403 Forbidden`: Token válido pero sin permisos para expediente/herramientas
- `500 Internal Server Error`: Error inesperado del servidor

### 2. Endpoint de Estado: Consultar Ejecución

**Ruta:** `GET /api/v1/agent/status/{agent_run_id}`

**Descripción:** Consulta el estado de una ejecución de agente.

**Autenticación:** Bearer token JWT

**Response 200 OK (En progreso):**

```json
{
  "agent_run_id": "RUN-20241208-143022-123456",
  "status": "running",
  "expediente_id": "EXP-2024-001",
  "tarea_id": "TAREA-VALIDAR-DOC",
  "started_at": "2024-12-08T14:30:22Z",
  "elapsed_seconds": 45
}
```

**Response 200 OK (Completado):**

```json
{
  "agent_run_id": "RUN-20241208-143022-123456",
  "status": "completed",
  "success": true,
  "expediente_id": "EXP-2024-001",
  "tarea_id": "TAREA-VALIDAR-DOC",
  "started_at": "2024-12-08T14:30:22Z",
  "completed_at": "2024-12-08T14:35:22Z",
  "elapsed_seconds": 300,
  "resultado": {
    "completado": true,
    "mensaje": "Validación completada"
  }
}
```

**Códigos de Estado:**

- `200 OK`: Estado encontrado
- `404 Not Found`: agent_run_id no existe
- `401 Unauthorized`: Token inválido

### 3. Endpoint de Salud: Health Check

**Ruta:** `GET /health`

**Descripción:** Verifica que la API y sus dependencias estén operativas.

**Autenticación:** No requiere

**Response 200 OK:**

```json
{
  "status": "healthy",
  "timestamp": "2024-12-08T14:30:22Z",
  "version": "1.0.0",
  "dependencies": {
    "mcp_expedientes": "healthy",
    "database": "not_applicable"
  }
}
```

**Response 503 Service Unavailable:**

```json
{
  "status": "unhealthy",
  "timestamp": "2024-12-08T14:30:22Z",
  "dependencies": {
    "mcp_expedientes": "unreachable"
  }
}
```

### 4. Endpoint de Métricas: Prometheus

**Ruta:** `GET /metrics`

**Descripción:** Expone métricas en formato Prometheus.

**Autenticación:** No requiere (protegido por red interna)

**Response 200 OK (formato texto Prometheus):**

```text
# HELP agentix_agent_executions_total Total de ejecuciones de agentes
# TYPE agentix_agent_executions_total counter
agentix_agent_executions_total{agent="ValidadorDocumental",status="success"} 42
agentix_agent_executions_total{agent="ValidadorDocumental",status="error"} 3

# HELP agentix_agent_duration_seconds Duración de ejecuciones de agentes
# TYPE agentix_agent_duration_seconds histogram
agentix_agent_duration_seconds_bucket{agent="ValidadorDocumental",le="1"} 5
agentix_agent_duration_seconds_bucket{agent="ValidadorDocumental",le="5"} 25
agentix_agent_duration_seconds_bucket{agent="ValidadorDocumental",le="10"} 40

# HELP agentix_mcp_tool_calls_total Total de llamadas a tools MCP
# TYPE agentix_mcp_tool_calls_total counter
agentix_mcp_tool_calls_total{tool="consultar_expediente",status="success"} 120
agentix_mcp_tool_calls_total{tool="actualizar_datos",status="success"} 45

# HELP agentix_jwt_validations_total Total de validaciones JWT
# TYPE agentix_jwt_validations_total counter
agentix_jwt_validations_total{status="valid"} 150
agentix_jwt_validations_total{status="expired"} 5
agentix_jwt_validations_total{status="invalid"} 2
```

## Requisitos No Funcionales

### 1. Seguridad

**JWT en Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Validación:**
- Extraer token del header `Authorization`
- Pasar token sin modificar al `AgentExecutor`
- Retornar 401 si token ausente
- Retornar 403 si token válido pero sin permisos

**CORS:**
- Configurar CORS para permitir requests desde BPMN
- Restringir orígenes permitidos (no usar `*` en producción)

### 2. Ejecución Asíncrona

**Background Tasks:**
- Usar `BackgroundTasks` de FastAPI o similar
- Retornar `202 Accepted` inmediatamente
- Ejecutar `AgentExecutor.execute()` en background
- Al terminar, enviar resultado al webhook

**Timeout:**
- Respetar `timeout_seconds` del request
- Cancelar ejecución si excede timeout
- Enviar error al webhook si timeout

### 3. Logging y Auditoría

**Logging de API:**
- Loggear cada request (método, ruta, status code)
- Loggear duración de cada request
- Loggear errores con stacktrace
- **NO loggear tokens JWT completos** (solo últimos 8 caracteres)

**Integración con Audit Logger:**
- El `AuditLogger` del back-office ya maneja PII redaction
- La API solo debe loggear eventos HTTP, no lógica de negocio

### 4. Métricas Prometheus

**Métricas a implementar:**

1. **agentix_agent_executions_total** (Counter)
   - Labels: `agent`, `status` (success/error)
   - Incrementar al finalizar ejecución

2. **agentix_agent_duration_seconds** (Histogram)
   - Labels: `agent`
   - Buckets: [0.5, 1, 5, 10, 30, 60, 300]

3. **agentix_mcp_tool_calls_total** (Counter)
   - Labels: `tool`, `status` (success/error)

4. **agentix_jwt_validations_total** (Counter)
   - Labels: `status` (valid/expired/invalid/missing)

5. **agentix_http_requests_total** (Counter)
   - Labels: `method`, `endpoint`, `status_code`

6. **agentix_http_request_duration_seconds** (Histogram)
   - Labels: `method`, `endpoint`

**Librerías:**
- Usar `prometheus-client` o `prometheus-fastapi-instrumentator`

### 5. Documentación OpenAPI

**Automática con FastAPI:**
- Disponible en `/docs` (Swagger UI)
- Disponible en `/redoc` (ReDoc)

**Incluir:**
- Descripción de cada endpoint
- Schemas de request/response
- Ejemplos de uso
- Códigos de error posibles

### 6. Configuración

**Variables de entorno (.env):**

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8080
API_WORKERS=4
API_RELOAD=false

# CORS
CORS_ORIGINS=https://bpmn.gex.cordoba.es

# JWT (heredado de Paso 1)
JWT_SECRET=tu-secreto-super-seguro
JWT_ALGORITHM=HS256
JWT_EXPECTED_ISSUER=agentix-bpmn
JWT_EXPECTED_SUBJECT=Automático
JWT_REQUIRED_AUDIENCE=agentix-mcp-expedientes

# MCP (heredado de Paso 1)
MCP_CONFIG_PATH=backoffice/config/mcp_servers.yaml

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs
```

## Estructura del Código

### Estructura de Directorios

```
/workspaces/aGEntiX/
├── api/                              # NUEVO - API REST
│   ├── __init__.py
│   ├── main.py                       # App FastAPI principal
│   ├── dependencies.py               # Dependency injection para FastAPI
│   ├── models.py                     # Pydantic models (request/response)
│   ├── middleware.py                 # Middlewares (CORS, logging, métricas)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── agent.py                  # Endpoints /api/v1/agent/*
│   │   └── health.py                 # Endpoints /health, /metrics
│   └── services/
│       ├── __init__.py
│       ├── webhook.py                # Envío de webhooks
│       └── task_tracker.py           # Tracking de tareas async
│
├── backoffice/                       # Existente del Paso 1
│   ├── executor.py
│   ├── executor_factory.py
│   ├── protocols.py
│   ├── models.py
│   ├── auth/
│   ├── mcp/
│   ├── logging/
│   └── agents/
│
├── tests/
│   ├── api/                          # NUEVO - Tests de API
│   │   ├── test_agent_endpoints.py
│   │   ├── test_health_endpoints.py
│   │   └── test_integration.py
│   └── backoffice/                   # Existente (86 tests)
│
├── .env                              # Variables de entorno
├── requirements.txt                  # Actualizar con FastAPI
└── run-api.sh                        # NUEVO - Script para lanzar API
```

### Archivos a Crear

#### 1. `api/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from .routers import agent, health
from .middleware import logging_middleware, metrics_middleware
from backoffice.config import settings

app = FastAPI(
    title="aGEntiX API",
    description="API REST para ejecución de agentes IA en GEX",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middlewares
app.middleware("http")(logging_middleware)
app.middleware("http")(metrics_middleware)

# Routers
app.include_router(agent.router, prefix="/api/v1/agent", tags=["Agent"])
app.include_router(health.router, tags=["Health"])

# Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

@app.get("/")
async def root():
    return {
        "name": "aGEntiX API",
        "version": "1.0.0",
        "docs": "/docs"
    }
```

#### 2. `api/models.py`

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class AgentConfigRequest(BaseModel):
    nombre: str = Field(..., example="ValidadorDocumental")
    system_prompt: str = Field(..., example="Eres un validador...")
    modelo: str = Field(..., example="claude-3-5-sonnet-20241022")
    prompt_tarea: str = Field(..., example="Valida documentos...")
    herramientas: List[str] = Field(..., example=["consultar_expediente"])

class ExecuteAgentRequest(BaseModel):
    expediente_id: str = Field(..., example="EXP-2024-001")
    tarea_id: str = Field(..., example="TAREA-VALIDAR-DOC")
    agent_config: AgentConfigRequest
    webhook_url: str = Field(..., example="https://bpmn.example.com/callback")
    timeout_seconds: int = Field(300, ge=10, le=600)

class ExecuteAgentResponse(BaseModel):
    status: str = Field("accepted")
    agent_run_id: str
    message: str
    webhook_url: str

class AgentStatusResponse(BaseModel):
    agent_run_id: str
    status: str  # "running", "completed", "failed"
    expediente_id: str
    tarea_id: str
    started_at: str
    completed_at: Optional[str] = None
    elapsed_seconds: int
    success: Optional[bool] = None
    resultado: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, str]] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    dependencies: Dict[str, str]
```

#### 3. `api/routers/agent.py`

```python
from fastapi import APIRouter, Header, HTTPException, BackgroundTasks
from typing import Optional

from ..models import ExecuteAgentRequest, ExecuteAgentResponse, AgentStatusResponse
from ..services.webhook import send_webhook
from ..services.task_tracker import TaskTracker
from backoffice.executor_factory import create_default_executor
from backoffice.models import AgentConfig
from backoffice.config import settings

router = APIRouter()
task_tracker = TaskTracker()

@router.post("/execute", response_model=ExecuteAgentResponse, status_code=202)
async def execute_agent(
    request: ExecuteAgentRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None)
):
    """Ejecuta un agente de forma asíncrona."""

    # 1. Validar JWT presente
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token JWT ausente")

    token = authorization.replace("Bearer ", "")

    # 2. Crear executor
    executor = create_default_executor(
        mcp_config_path=settings.MCP_CONFIG_PATH,
        jwt_secret=settings.JWT_SECRET,
        jwt_algorithm=settings.JWT_ALGORITHM
    )

    # 3. Convertir request a AgentConfig
    agent_config = AgentConfig(
        nombre=request.agent_config.nombre,
        system_prompt=request.agent_config.system_prompt,
        modelo=request.agent_config.modelo,
        prompt_tarea=request.agent_config.prompt_tarea,
        herramientas=request.agent_config.herramientas
    )

    # 4. Registrar tarea
    agent_run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}"
    task_tracker.register(
        agent_run_id=agent_run_id,
        expediente_id=request.expediente_id,
        tarea_id=request.tarea_id
    )

    # 5. Ejecutar en background
    background_tasks.add_task(
        execute_and_callback,
        executor=executor,
        token=token,
        expediente_id=request.expediente_id,
        tarea_id=request.tarea_id,
        agent_config=agent_config,
        agent_run_id=agent_run_id,
        webhook_url=request.webhook_url,
        timeout_seconds=request.timeout_seconds
    )

    return ExecuteAgentResponse(
        agent_run_id=agent_run_id,
        message="Ejecución de agente iniciada",
        webhook_url=request.webhook_url
    )

async def execute_and_callback(
    executor,
    token: str,
    expediente_id: str,
    tarea_id: str,
    agent_config: AgentConfig,
    agent_run_id: str,
    webhook_url: str,
    timeout_seconds: int
):
    """Ejecuta agente y envía resultado al webhook."""
    try:
        # Marcar como running
        task_tracker.mark_running(agent_run_id)

        # Ejecutar con timeout
        result = await asyncio.wait_for(
            executor.execute(token, expediente_id, tarea_id, agent_config),
            timeout=timeout_seconds
        )

        # Marcar como completado
        task_tracker.mark_completed(agent_run_id, result)

        # Enviar webhook
        await send_webhook(webhook_url, agent_run_id, result)

    except asyncio.TimeoutError:
        # Timeout
        error = {"codigo": "TIMEOUT", "mensaje": f"Ejecución excedió {timeout_seconds}s"}
        task_tracker.mark_failed(agent_run_id, error)
        await send_webhook(webhook_url, agent_run_id, error=error)

    except Exception as e:
        # Error inesperado
        error = {"codigo": "INTERNAL_ERROR", "mensaje": str(e)}
        task_tracker.mark_failed(agent_run_id, error)
        await send_webhook(webhook_url, agent_run_id, error=error)

@router.get("/status/{agent_run_id}", response_model=AgentStatusResponse)
async def get_agent_status(agent_run_id: str):
    """Consulta estado de ejecución de agente."""
    status = task_tracker.get_status(agent_run_id)

    if not status:
        raise HTTPException(status_code=404, detail="agent_run_id no encontrado")

    return status
```

#### 4. `api/services/webhook.py`

```python
import httpx
from datetime import datetime, timezone

async def send_webhook(webhook_url: str, agent_run_id: str, result=None, error=None):
    """Envía resultado al webhook del BPMN."""

    payload = {
        "agent_run_id": agent_run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if error:
        payload["status"] = "failed"
        payload["success"] = False
        payload["error"] = error
    else:
        payload["status"] = "completed"
        payload["success"] = result.success
        payload["resultado"] = result.resultado
        payload["herramientas_usadas"] = result.herramientas_usadas

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                webhook_url,
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()
        except Exception as e:
            # Loggear error pero no propagar
            print(f"Error enviando webhook: {e}")
```

#### 5. `run-api.sh`

```bash
#!/bin/bash
# Script para lanzar la API de aGEntiX

# Cargar variables de entorno
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Valores por defecto
API_HOST=${API_HOST:-0.0.0.0}
API_PORT=${API_PORT:-8080}
API_WORKERS=${API_WORKERS:-4}
API_RELOAD=${API_RELOAD:-false}

echo "🚀 Iniciando aGEntiX API..."
echo "   Host: $API_HOST"
echo "   Port: $API_PORT"
echo "   Workers: $API_WORKERS"
echo "   Reload: $API_RELOAD"

if [ "$API_RELOAD" = "true" ]; then
    # Modo desarrollo (con auto-reload)
    uvicorn api.main:app --host $API_HOST --port $API_PORT --reload
else
    # Modo producción (con múltiples workers)
    uvicorn api.main:app --host $API_HOST --port $API_PORT --workers $API_WORKERS
fi
```

## Dependencias a Añadir

Actualizar `requirements.txt`:

```txt
# Existentes del Paso 1
pydantic>=2.0.0
pydantic-settings>=2.0.0
PyJWT>=2.8.0
httpx>=0.25.0
pyyaml>=6.0.1
pytest>=7.4.0
pytest-asyncio>=0.21.0

# NUEVAS para Paso 2
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
prometheus-client>=0.19.0
prometheus-fastapi-instrumentator>=6.1.0
```

## Tests a Implementar

### 1. Tests de Endpoints (Unitarios)

**Archivo:** `tests/api/test_agent_endpoints.py`

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from api.main import app

client = TestClient(app)

def test_execute_agent_without_token_returns_401():
    """Test: Request sin token retorna 401"""
    response = client.post("/api/v1/agent/execute", json={
        "expediente_id": "EXP-2024-001",
        "tarea_id": "TAREA-001",
        "agent_config": {...},
        "webhook_url": "http://example.com/callback"
    })
    assert response.status_code == 401

def test_execute_agent_with_valid_token_returns_202():
    """Test: Request válido retorna 202"""
    # Mock del executor para evitar ejecución real
    with patch('api.routers.agent.create_default_executor'):
        response = client.post(
            "/api/v1/agent/execute",
            json={...},
            headers={"Authorization": "Bearer valid-token"}
        )
        assert response.status_code == 202
        assert "agent_run_id" in response.json()

# ... más tests (20-30 tests)
```

### 2. Tests de Integración

**Archivo:** `tests/api/test_integration.py`

```python
@pytest.mark.asyncio
async def test_full_flow_execute_and_webhook():
    """Test: Flujo completo desde request hasta webhook"""
    # Mock del MCP server
    # Mock del webhook endpoint
    # Ejecutar request
    # Esperar callback
    # Verificar resultado
```

### 3. Criterios de Aceptación

- ✅ Todos los tests pasan (>95 tests totales)
- ✅ Endpoint `/api/v1/agent/execute` retorna 202
- ✅ Webhook recibe resultado correcto
- ✅ Métricas Prometheus se incrementan
- ✅ OpenAPI docs accesibles en `/docs`
- ✅ Health check retorna status correcto

## Plan de Implementación

### Fase 1: Setup Básico (2-3 horas)

1. Crear estructura `api/`
2. Instalar dependencias FastAPI
3. Crear `api/main.py` básico
4. Verificar que `/docs` funciona

### Fase 2: Endpoint Execute (4-6 horas)

1. Implementar `api/models.py`
2. Implementar `api/routers/agent.py`
3. Integrar con `AgentExecutor`
4. Implementar background tasks
5. Tests del endpoint

### Fase 3: Webhooks (2-3 horas)

1. Implementar `api/services/webhook.py`
2. Tests de webhook delivery
3. Manejo de errores en webhook

### Fase 4: Métricas (2-3 horas)

1. Configurar Prometheus
2. Implementar métricas custom
3. Verificar `/metrics` endpoint

### Fase 5: Health & Status (1-2 horas)

1. Implementar `/health` endpoint
2. Implementar `/status/{run_id}` endpoint
3. Implementar `TaskTracker`

### Fase 6: Testing (3-4 horas)

1. Tests de endpoints (20 tests)
2. Tests de integración (5 tests)
3. Verificar cobertura

**Tiempo Total Estimado:** 14-21 horas (2-3 días)

## Criterios de Calidad

- ✅ **100% tests PASS** (>95 tests totales)
- ✅ **OpenAPI docs completos** con ejemplos
- ✅ **Métricas Prometheus** funcionando
- ✅ **Manejo robusto de errores** (401, 403, 500)
- ✅ **Logging completo** (requests, errors, webhooks)
- ✅ **Configuración externalizada** (.env)
- ✅ **README actualizado** con instrucciones de uso

## Entregables

1. **Código:**
   - `api/` completo con todos los módulos
   - `tests/api/` con >25 tests
   - `run-api.sh` ejecutable

2. **Documentación:**
   - OpenAPI docs en `/docs`
   - README con instrucciones
   - Ejemplos de uso

3. **Tests:**
   - >95 tests totales (86 existentes + ~10 nuevos)
   - 100% PASS

4. **Demo:**
   - Script que demuestre flujo completo:
     1. POST /api/v1/agent/execute
     2. GET /api/v1/agent/status/{run_id}
     3. Webhook callback recibido
     4. GET /metrics muestra contadores

## Notas Importantes

- **NO implementar frontend** en este paso (se hará después)
- **NO implementar Celery** todavía (Paso 5)
- **Usar BackgroundTasks de FastAPI** (simple, suficiente para 1 worker)
- **Priorizar simplicidad** sobre optimización prematura
- **Reutilizar al máximo** el código del Paso 1
- **Mantener backward compatibility** con AgentExecutor

## Próximo Paso

Después de completar este paso, el sistema estará listo para:

- **Paso 3:** Frontend de monitorización (métricas, logs, test manual)
- **Paso 4:** Agentes reales con LangGraph/CrewAI
- **Paso 5:** Escalabilidad horizontal con Celery + Redis
