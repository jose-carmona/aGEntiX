# Plan de Mejoras - Commit 64fda4d

**Fecha:** 2025-12-10
**Commit:** 64fda4d93a2b680f5113dc32e38957aa7c7e5596
**Título:** Implementar Paso 2: API REST con FastAPI

---

## Índice de Mejoras

| ID | Título | Prioridad | Esfuerzo | Estado |
|----|--------|-----------|----------|--------|
| P1.1 | Migrar on_event → lifespan | Alta | 15 min | ✅ Completado |
| P1.2 | Webhook retry con backoff exponencial | Alta | 45 min | ⬜ Pendiente |
| P1.3 | Prevenir colisión run_id | Alta | 30 min | ⬜ Pendiente |
| P2.1 | Validar webhook_url (SSRF) | Media | 30 min | ⬜ Pendiente |
| P2.2 | Cleanup automático TaskTracker | Media | 1h | ⬜ Pendiente |
| P2.3 | Health check → MCP connectivity | Media | 45 min | ⬜ Pendiente |
| P2.4 | CORS hardening producción | Media | 15 min | ⬜ Pendiente |
| P2.5 | Test timeout real | Media | 30 min | ⬜ Pendiente |
| P2.6 | Test webhook failure | Media | 30 min | ⬜ Pendiente |
| P3.1 | Logs estructurados JSON | Baja | 1h | ⬜ Pendiente |
| P3.2 | Rate limiting | Baja | 2h | ⬜ Pendiente |

**Total:** 11 mejoras, ~8h esfuerzo

---

## Prioridad 1 (Alta) - 1.5h

### P1.1 - Migrar on_event → lifespan

**Severidad:** Media
**Esfuerzo:** 15 min
**Ubicación:** `api/main.py:68, 80`

#### Problema

FastAPI deprecó `@app.on_event("startup")` y `@app.on_event("shutdown")` en favor de `lifespan`.

**Warnings actuales:**
```
DeprecationWarning: on_event is deprecated, use lifespan event handlers instead.
  Ubicación: api/main.py:68, 80
  Ocurrencias: 29 (múltiples por tests)
```

#### Solución

**Antes:**
```python
@app.on_event("startup")
async def startup_event():
    logger.info("aGEntiX API iniciando...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("aGEntiX API cerrando...")
```

**Después:**
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("=" * 60)
    logger.info("aGEntiX API iniciando...")
    logger.info(f"Versión: 1.0.0")
    logger.info(f"MCP Config: {settings.MCP_CONFIG_PATH}")
    logger.info(f"Log Level: {settings.LOG_LEVEL}")
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("aGEntiX API cerrando...")

app = FastAPI(
    title="aGEntiX API",
    description="API REST para ejecución de agentes IA en GEX",
    version="1.0.0",
    lifespan=lifespan,  # <-- Añadir aquí
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)
```

#### Checklist

- [x] Importar `asynccontextmanager` de `contextlib`
- [x] Definir función `lifespan` con decorador `@asynccontextmanager`
- [x] Mover lógica startup antes del `yield`
- [x] Mover lógica shutdown después del `yield`
- [x] Añadir parámetro `lifespan=lifespan` a `FastAPI()`
- [x] Eliminar `@app.on_event("startup")` y `@app.on_event("shutdown")`
- [x] Ejecutar tests → verificar 0 warnings (0 on_event warnings, 96/96 tests PASS)
- [x] Commit: "Implementar P1.1: Migrar on_event → lifespan (FastAPI best practice)"

---

### P1.2 - Webhook retry con backoff exponencial

**Severidad:** Alta
**Esfuerzo:** 45 min
**Ubicación:** `api/services/webhook.py`, `api/routers/agent.py`

#### Problema

Si el webhook falla (BPMN caído temporalmente), no se reintenta el envío. El BPMN nunca recibe notificación y la tarea queda en estado inconsistente.

**Impacto:** Alto - pérdida de notificaciones críticas

#### Solución

Implementar retry con backoff exponencial (3 intentos: 1s, 5s, 15s).

**Opción 1: Librería `tenacity`**

```bash
# requirements.txt
tenacity>=8.2.0
```

```python
# api/services/webhook.py

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=15),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
    reraise=False
)
async def send_webhook_with_retry(
    webhook_url: str,
    agent_run_id: str,
    result=None,
    error: Optional[Dict[str, str]] = None
) -> bool:
    """
    Envía webhook con retry automático.

    Retry strategy:
    - Intento 1: inmediato
    - Intento 2: 1s después
    - Intento 3: 5s después
    - Si falla 3 veces: retorna False
    """
    async with httpx.AsyncClient() as client:
        try:
            # ... (mismo código payload) ...

            logger.info(f"Enviando webhook a {webhook_url} para {agent_run_id}")
            response = await client.post(
                webhook_url,
                json=payload,
                timeout=10.0,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            logger.info(
                f"Webhook enviado exitosamente: {agent_run_id} -> "
                f"{webhook_url} (status={response.status_code})"
            )
            return True

        except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
            logger.warning(
                f"Intento fallido webhook: {agent_run_id} -> {webhook_url} "
                f"({type(e).__name__})"
            )
            raise  # Re-raise para que tenacity reintente

        except Exception as e:
            # Errores no recuperables → no reintentar
            logger.error(
                f"Error no recuperable webhook: {agent_run_id} -> {webhook_url} "
                f"({type(e).__name__}: {str(e)})"
            )
            return False


# Wrapper sin retry para compatibilidad
async def send_webhook(
    webhook_url: str,
    agent_run_id: str,
    result=None,
    error: Optional[Dict[str, str]] = None
) -> bool:
    """Wrapper para send_webhook_with_retry (compatibilidad)"""
    try:
        return await send_webhook_with_retry(webhook_url, agent_run_id, result, error)
    except Exception:
        # Todos los intentos fallaron
        logger.error(
            f"Webhook fallido después de 3 intentos: {agent_run_id} -> {webhook_url}"
        )
        return False
```

**Opción 2: Implementación manual (sin dependencia)**

```python
# api/services/webhook.py

async def send_webhook(
    webhook_url: str,
    agent_run_id: str,
    result=None,
    error: Optional[Dict[str, str]] = None,
    max_retries: int = 3
) -> bool:
    """
    Envía webhook con retry manual.

    Args:
        max_retries: Número máximo de intentos (default: 3)

    Returns:
        True si envío exitoso, False si falló después de todos los reintentos
    """

    # ... (construir payload igual que antes) ...

    retry_delays = [0, 1, 5]  # 0s, 1s, 5s

    for attempt in range(max_retries):
        if attempt > 0:
            delay = retry_delays[attempt]
            logger.info(
                f"Reintentando webhook en {delay}s "
                f"(intento {attempt + 1}/{max_retries}): {agent_run_id}"
            )
            await asyncio.sleep(delay)

        async with httpx.AsyncClient() as client:
            try:
                logger.info(
                    f"Enviando webhook (intento {attempt + 1}/{max_retries}): "
                    f"{agent_run_id} -> {webhook_url}"
                )

                response = await client.post(
                    webhook_url,
                    json=payload,
                    timeout=10.0,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()

                logger.info(
                    f"Webhook enviado exitosamente (intento {attempt + 1}): "
                    f"{agent_run_id} -> {webhook_url} (status={response.status_code})"
                )
                return True

            except httpx.TimeoutException:
                logger.warning(
                    f"Timeout webhook (intento {attempt + 1}): "
                    f"{agent_run_id} -> {webhook_url}"
                )
                if attempt == max_retries - 1:
                    logger.error(
                        f"Webhook fallido por timeout después de {max_retries} intentos: "
                        f"{agent_run_id} -> {webhook_url}"
                    )
                    return False
                # Continuar al siguiente intento

            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"Error HTTP webhook (intento {attempt + 1}): "
                    f"{agent_run_id} -> {webhook_url} (status={e.response.status_code})"
                )

                # 4xx → no reintentar (error cliente)
                if 400 <= e.response.status_code < 500:
                    logger.error(
                        f"Webhook fallido con error 4xx (no reintentar): "
                        f"{agent_run_id} -> {webhook_url}"
                    )
                    return False

                # 5xx → reintentar
                if attempt == max_retries - 1:
                    logger.error(
                        f"Webhook fallido por error 5xx después de {max_retries} intentos: "
                        f"{agent_run_id} -> {webhook_url}"
                    )
                    return False
                # Continuar al siguiente intento

            except Exception as e:
                logger.error(
                    f"Error inesperado webhook (no reintentar): "
                    f"{agent_run_id} -> {webhook_url} ({type(e).__name__}: {str(e)})"
                )
                return False

    return False
```

#### Test

```python
# tests/api/test_webhook_retry.py

import pytest
from unittest.mock import AsyncMock, patch
import httpx

from api.services.webhook import send_webhook

@pytest.mark.asyncio
async def test_webhook_retry_on_timeout():
    """Test: Webhook reintenta en caso de timeout"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_post = AsyncMock()
        # Primer intento: timeout
        # Segundo intento: timeout
        # Tercer intento: éxito
        mock_post.side_effect = [
            httpx.TimeoutException("Timeout 1"),
            httpx.TimeoutException("Timeout 2"),
            Mock(status_code=200)  # Éxito en 3er intento
        ]
        mock_client.return_value.__aenter__.return_value.post = mock_post

        success = await send_webhook(
            "http://example.com/callback",
            "RUN-TEST",
            result=Mock(success=True, resultado={}, herramientas_usadas=[])
        )

        assert success
        assert mock_post.call_count == 3

@pytest.mark.asyncio
async def test_webhook_no_retry_on_4xx():
    """Test: Webhook NO reintenta en error 4xx"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_post = AsyncMock()
        error_response = Mock(status_code=404)
        mock_post.side_effect = httpx.HTTPStatusError(
            "Not found",
            request=Mock(),
            response=error_response
        )
        mock_client.return_value.__aenter__.return_value.post = mock_post

        success = await send_webhook(
            "http://example.com/callback",
            "RUN-TEST",
            result=Mock(success=True, resultado={}, herramientas_usadas=[])
        )

        assert not success
        assert mock_post.call_count == 1  # No retry en 4xx
```

#### Checklist

- [ ] Implementar retry (elegir Opción 1 o 2)
- [ ] Actualizar tests (añadir tests retry)
- [ ] Ejecutar tests → verificar PASS
- [ ] Probar manualmente con webhook que falla
- [ ] Verificar logs muestran reintentos
- [ ] Commit: "Implementar webhook retry con backoff exponencial"

---

### P1.3 - Prevenir colisión run_id

**Severidad:** Baja (improbable pero mejor prevenir)
**Esfuerzo:** 30 min
**Ubicación:** `api/services/task_tracker.py:41`

#### Problema

Si 2 requests llegan exactamente en el mismo microsegundo, pueden generar el mismo `run_id`:

```python
agent_run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}"
```

Aunque extremadamente improbable, el segundo request sobrescribiría el primero en el `TaskTracker`.

#### Solución

Añadir check en `TaskTracker.register()`:

```python
# api/services/task_tracker.py

def register(
    self,
    agent_run_id: str,
    expediente_id: str,
    tarea_id: str
) -> None:
    """
    Registra una nueva tarea.

    Args:
        agent_run_id: ID único de la ejecución
        expediente_id: ID del expediente
        tarea_id: ID de la tarea BPMN

    Raises:
        ValueError: Si agent_run_id ya existe (colisión)
    """
    with self._lock:
        # Check colisión
        if agent_run_id in self._tasks:
            logger.error(
                f"Colisión detectada: run_id ya existe: {agent_run_id}"
            )
            raise ValueError(
                f"run_id ya existe: {agent_run_id}. "
                "Esto es extremadamente raro y sugiere un error del sistema."
            )

        self._tasks[agent_run_id] = {
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

        logger.debug(f"Tarea registrada: {agent_run_id}")
```

**Manejar excepción en `execute_agent`:**

```python
# api/routers/agent.py

@router.post("/execute", ...)
async def execute_agent(...):
    # ... (código anterior) ...

    # Generar run_id
    agent_run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}"

    task_tracker = get_task_tracker()

    try:
        task_tracker.register(
            agent_run_id=agent_run_id,
            expediente_id=request.expediente_id,
            tarea_id=request.tarea_id
        )
    except ValueError:
        # Colisión (extremadamente raro)
        # Regenerar run_id con uuid4 como suffix
        import uuid
        agent_run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"

        # Intentar de nuevo (no debería fallar)
        task_tracker.register(
            agent_run_id=agent_run_id,
            expediente_id=request.expediente_id,
            tarea_id=request.tarea_id
        )

    # ... (resto del código) ...
```

#### Test

```python
# tests/api/test_task_tracker.py

def test_task_tracker_raises_on_duplicate_run_id():
    """Test: TaskTracker lanza ValueError si run_id ya existe"""
    tracker = TaskTracker()

    tracker.register("RUN-TEST", "EXP-001", "TAREA-001")

    with pytest.raises(ValueError, match="run_id ya existe"):
        tracker.register("RUN-TEST", "EXP-002", "TAREA-002")
```

#### Checklist

- [ ] Añadir check colisión en `TaskTracker.register()`
- [ ] Manejar `ValueError` en `execute_agent` (regenerar con uuid)
- [ ] Añadir test colisión
- [ ] Ejecutar tests → verificar PASS
- [ ] Commit: "Prevenir colisión run_id en TaskTracker"

---

## Prioridad 2 (Media) - 3.5h

### P2.1 - Validar webhook_url (prevenir SSRF)

**Severidad:** Media
**Esfuerzo:** 30 min
**Ubicación:** `api/services/webhook.py`, `api/models.py`

#### Problema

No se valida el `webhook_url` proporcionado por el cliente. Esto abre vector de ataque SSRF (Server-Side Request Forgery):

```json
{
  "webhook_url": "http://localhost:6379/CONFIG SET dir /var/www/"
}
```

El servidor haría request a servicios internos (Redis, DB, etc.).

#### Solución

**Opción 1: Validación Pydantic (recomendado)**

```python
# api/models.py

from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import List, Dict, Any, Optional

class ExecuteAgentRequest(BaseModel):
    expediente_id: str = Field(...)
    tarea_id: str = Field(...)
    agent_config: AgentConfigRequest = Field(...)
    webhook_url: HttpUrl = Field(  # <-- Cambiar str a HttpUrl
        ...,
        example="https://bpmn.example.com/api/v1/tasks/callback",
        description="URL donde enviar el resultado cuando termine"
    )
    timeout_seconds: int = Field(...)

    @field_validator('webhook_url')
    @classmethod
    def validate_webhook_url(cls, v: HttpUrl) -> HttpUrl:
        """
        Valida webhook_url para prevenir SSRF.

        Restricciones:
        - Solo HTTPS en producción (HTTP permitido en dev)
        - No localhost/127.0.0.1
        - No IPs privadas (10.x, 172.16.x, 192.168.x)
        """
        from backoffice.settings import settings

        # Convertir HttpUrl a str para validación
        url_str = str(v)
        hostname = v.host

        # 1. Validar scheme (HTTPS en prod)
        if settings.LOG_LEVEL == "INFO":  # Producción
            if v.scheme != "https":
                raise ValueError(
                    "webhook_url debe usar HTTPS en producción"
                )

        # 2. Prevenir localhost
        if hostname in ["localhost", "127.0.0.1", "::1"]:
            raise ValueError(
                "webhook_url no puede apuntar a localhost"
            )

        # 3. Prevenir IPs privadas
        import ipaddress
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private:
                raise ValueError(
                    f"webhook_url no puede apuntar a IP privada: {hostname}"
                )
        except ValueError:
            # No es IP, es hostname (OK)
            pass

        # 4. Validar puerto (opcional)
        if v.port and v.port not in [80, 443, 8080, 8443]:
            logger.warning(
                f"webhook_url usa puerto no estándar: {v.port}"
            )

        return v
```

**Opción 2: Allowlist de dominios**

```python
# backoffice/settings.py

class Settings(BaseSettings):
    # ... (existentes) ...

    WEBHOOK_ALLOWED_DOMAINS: str = Field(
        default="bpmn.gex.es,gex.dipucordoba.es",
        description="Dominios permitidos para webhooks (separados por coma)"
    )

# api/models.py

@field_validator('webhook_url')
@classmethod
def validate_webhook_url(cls, v: HttpUrl) -> HttpUrl:
    """Valida que webhook_url esté en allowlist"""
    from backoffice.settings import settings

    allowed_domains = settings.WEBHOOK_ALLOWED_DOMAINS.split(",")
    hostname = v.host

    # Check si hostname está en allowlist
    if not any(hostname.endswith(domain.strip()) for domain in allowed_domains):
        raise ValueError(
            f"webhook_url no permitido. Dominios permitidos: {allowed_domains}"
        )

    return v
```

#### Test

```python
# tests/api/test_webhook_validation.py

import pytest
from pydantic import ValidationError
from api.models import ExecuteAgentRequest

def test_webhook_url_rejects_localhost():
    """Test: webhook_url rechaza localhost"""
    with pytest.raises(ValidationError, match="localhost"):
        ExecuteAgentRequest(
            expediente_id="EXP-001",
            tarea_id="TAREA-001",
            agent_config={...},
            webhook_url="http://localhost:8080/callback",
            timeout_seconds=300
        )

def test_webhook_url_rejects_private_ip():
    """Test: webhook_url rechaza IPs privadas"""
    with pytest.raises(ValidationError, match="privada"):
        ExecuteAgentRequest(
            expediente_id="EXP-001",
            tarea_id="TAREA-001",
            agent_config={...},
            webhook_url="http://192.168.1.100/callback",
            timeout_seconds=300
        )

def test_webhook_url_accepts_valid_https():
    """Test: webhook_url acepta HTTPS válido"""
    req = ExecuteAgentRequest(
        expediente_id="EXP-001",
        tarea_id="TAREA-001",
        agent_config={...},
        webhook_url="https://bpmn.example.com/callback",
        timeout_seconds=300
    )
    assert str(req.webhook_url) == "https://bpmn.example.com/callback"
```

#### Checklist

- [ ] Cambiar `webhook_url: str` → `webhook_url: HttpUrl`
- [ ] Implementar `@field_validator` (elegir Opción 1 o 2)
- [ ] Añadir tests validación
- [ ] Ejecutar tests → verificar PASS
- [ ] Verificar error 422 en request inválido
- [ ] Commit: "Validar webhook_url para prevenir SSRF"

---

### P2.2 - Cleanup automático TaskTracker

**Severidad:** Media
**Esfuerzo:** 1h
**Ubicación:** `api/services/task_tracker.py`, `api/main.py`

#### Problema

`TaskTracker.cleanup_old_tasks()` está implementado pero nunca se ejecuta. En long-running processes, esto causa memory leak.

#### Solución

Añadir tarea periódica con APScheduler.

**Dependencia:**

```bash
# requirements.txt
apscheduler>=3.10.0
```

**Implementación:**

```python
# api/main.py

from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Scheduler global
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("=" * 60)
    logger.info("aGEntiX API iniciando...")
    # ... (logging existente) ...

    # Iniciar scheduler
    logger.info("Iniciando scheduler de tareas periódicas")
    scheduler.start()

    # Añadir job de cleanup (cada 1 hora)
    from api.services.task_tracker import get_task_tracker

    def cleanup_task_tracker():
        """Job periódico: limpia tareas antiguas"""
        tracker = get_task_tracker()
        deleted = tracker.cleanup_old_tasks(max_age_hours=24)
        if deleted > 0:
            logger.info(f"Cleanup TaskTracker: {deleted} tareas eliminadas")

    scheduler.add_job(
        cleanup_task_tracker,
        'interval',
        hours=1,
        id='cleanup_task_tracker',
        name='Cleanup old tasks from TaskTracker'
    )

    logger.info("Scheduler iniciado con jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name} (trigger: {job.trigger})")

    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("Deteniendo scheduler...")
    scheduler.shutdown(wait=True)
    logger.info("aGEntiX API cerrando...")

app = FastAPI(lifespan=lifespan, ...)
```

**Configuración:**

```python
# backoffice/settings.py

class Settings(BaseSettings):
    # ... (existentes) ...

    TASK_TRACKER_CLEANUP_INTERVAL_HOURS: int = Field(
        default=1,
        description="Intervalo de cleanup de TaskTracker (horas)"
    )

    TASK_TRACKER_MAX_AGE_HOURS: int = Field(
        default=24,
        description="Edad máxima de tareas en TaskTracker (horas)"
    )
```

**Uso en lifespan:**

```python
scheduler.add_job(
    cleanup_task_tracker,
    'interval',
    hours=settings.TASK_TRACKER_CLEANUP_INTERVAL_HOURS,
    id='cleanup_task_tracker'
)

def cleanup_task_tracker():
    tracker = get_task_tracker()
    deleted = tracker.cleanup_old_tasks(
        max_age_hours=settings.TASK_TRACKER_MAX_AGE_HOURS
    )
    if deleted > 0:
        logger.info(f"Cleanup: {deleted} tareas eliminadas")
```

#### Test

```python
# tests/api/test_task_tracker_cleanup.py

import pytest
from datetime import datetime, timedelta, timezone
from api.services.task_tracker import TaskTracker

def test_cleanup_removes_old_tasks():
    """Test: cleanup elimina tareas antiguas"""
    tracker = TaskTracker()

    # Registrar tarea "antigua" (simular)
    tracker._tasks["RUN-OLD"] = {
        "agent_run_id": "RUN-OLD",
        "expediente_id": "EXP-001",
        "tarea_id": "TAREA-001",
        "status": "completed",
        "started_at": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(),
        "completed_at": (datetime.now(timezone.utc) - timedelta(hours=24, minutes=30)).isoformat(),
        "elapsed_seconds": 1800,
        "success": True,
        "resultado": {},
        "error": None
    }

    # Registrar tarea reciente
    tracker.register("RUN-NEW", "EXP-002", "TAREA-002")

    assert len(tracker._tasks) == 2

    # Cleanup (max_age=24h)
    deleted = tracker.cleanup_old_tasks(max_age_hours=24)

    assert deleted == 1
    assert "RUN-OLD" not in tracker._tasks
    assert "RUN-NEW" in tracker._tasks
```

#### Checklist

- [ ] Añadir dependencia `apscheduler`
- [ ] Migrar a `lifespan` (prereq: P1.1)
- [ ] Implementar scheduler en `lifespan`
- [ ] Añadir configuración `TASK_TRACKER_CLEANUP_INTERVAL_HOURS`
- [ ] Añadir test cleanup automático
- [ ] Ejecutar tests → verificar PASS
- [ ] Verificar en logs que cleanup se ejecuta
- [ ] Commit: "Añadir cleanup automático de TaskTracker"

---

### P2.3 - Health check → MCP connectivity

**Severidad:** Media
**Esfuerzo:** 45 min
**Ubicación:** `api/routers/health.py`

#### Problema

Health check actualmente retorna `"not_checked"` para dependencias. No detecta si MCP servers están caídos.

```python
dependencies = {
    "mcp_expedientes": "not_checked",
    "database": "not_applicable"
}
```

Útil para K8s readiness probes.

#### Solución

```python
# api/routers/health.py

import httpx
import yaml
from pathlib import Path

async def check_mcp_servers() -> Dict[str, str]:
    """
    Verifica conectividad con MCP servers.

    Returns:
        Dict con estado de cada MCP server (healthy/unhealthy/unknown)
    """
    from backoffice.settings import settings

    # Leer config MCP
    config_path = Path(settings.MCP_CONFIG_PATH)
    if not config_path.exists():
        return {"mcp_config": "not_found"}

    with open(config_path) as f:
        config = yaml.safe_load(f)

    dependencies = {}

    for server in config.get("mcp_servers", []):
        server_id = server["id"]

        if not server.get("enabled", False):
            dependencies[server_id] = "disabled"
            continue

        server_url = server["url"]

        # Verificar conectividad (simple GET a root)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    server_url,
                    timeout=2.0  # Timeout corto para health check
                )

                if response.status_code < 500:
                    dependencies[server_id] = "healthy"
                else:
                    dependencies[server_id] = "unhealthy"

        except httpx.TimeoutException:
            dependencies[server_id] = "timeout"
        except httpx.ConnectError:
            dependencies[server_id] = "unreachable"
        except Exception as e:
            dependencies[server_id] = f"error:{type(e).__name__}"

    return dependencies


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint con verificación MCP"""
    version = "1.0.0"
    timestamp = datetime.now(timezone.utc).isoformat()

    # Check MCP servers
    mcp_status = await check_mcp_servers()

    # Determinar status general
    all_healthy = all(
        status in ["healthy", "disabled", "not_applicable"]
        for status in mcp_status.values()
    )

    overall_status = "healthy" if all_healthy else "degraded"

    return HealthResponse(
        status=overall_status,
        timestamp=timestamp,
        version=version,
        dependencies=mcp_status
    )
```

**Configuración:**

```python
# backoffice/settings.py

class Settings(BaseSettings):
    # ... (existentes) ...

    HEALTH_CHECK_MCP_ENABLED: bool = Field(
        default=True,
        description="Habilitar verificación MCP en health check"
    )
```

**Con toggle:**

```python
@router.get("/health", response_model=HealthResponse)
async def health_check():
    from backoffice.settings import settings

    if settings.HEALTH_CHECK_MCP_ENABLED:
        dependencies = await check_mcp_servers()
    else:
        dependencies = {"mcp": "not_checked"}

    # ... (resto igual) ...
```

#### Test

```python
# tests/api/test_health_check_mcp.py

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@patch('api.routers.health.check_mcp_servers')
@pytest.mark.asyncio
async def test_health_check_returns_degraded_if_mcp_down(mock_check):
    """Test: Health check retorna 'degraded' si MCP caído"""
    mock_check.return_value = {
        "mcp_expedientes": "unhealthy"
    }

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["dependencies"]["mcp_expedientes"] == "unhealthy"
```

#### Checklist

- [ ] Implementar `check_mcp_servers()`
- [ ] Integrar en `health_check()`
- [ ] Añadir configuración `HEALTH_CHECK_MCP_ENABLED`
- [ ] Actualizar modelo `HealthResponse` (permitir "degraded")
- [ ] Añadir tests
- [ ] Ejecutar tests → verificar PASS
- [ ] Probar con MCP caído
- [ ] Commit: "Health check: verificar conectividad MCP"

---

### P2.4 - CORS hardening producción

**Severidad:** Baja
**Esfuerzo:** 15 min
**Ubicación:** `api/main.py:47-48`

#### Problema

CORS usa wildcard en métodos/headers:

```python
allow_methods=["*"],
allow_headers=["*"],
```

En producción, mejor limitar a mínimo necesario.

#### Solución

```python
# api/main.py

from backoffice.settings import settings

# Determinar config CORS según ambiente
if settings.LOG_LEVEL == "DEBUG":
    # Desarrollo: relajado
    cors_methods = ["*"]
    cors_headers = ["*"]
else:
    # Producción: restrictivo
    cors_methods = ["GET", "POST", "OPTIONS"]
    cors_headers = ["Content-Type", "Authorization"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=cors_methods,
    allow_headers=cors_headers,
)

logger.info(f"CORS configurado:")
logger.info(f"  Origins: {cors_origins}")
logger.info(f"  Methods: {cors_methods}")
logger.info(f"  Headers: {cors_headers}")
```

**Configuración explícita:**

```python
# backoffice/settings.py

class Settings(BaseSettings):
    # ... (existentes) ...

    CORS_ALLOWED_METHODS: str = Field(
        default="GET,POST,OPTIONS",
        description="Métodos HTTP permitidos en CORS"
    )

    CORS_ALLOWED_HEADERS: str = Field(
        default="Content-Type,Authorization",
        description="Headers permitidos en CORS"
    )

# api/main.py

cors_methods = settings.CORS_ALLOWED_METHODS.split(",")
cors_headers = settings.CORS_ALLOWED_HEADERS.split(",")
```

#### Checklist

- [ ] Añadir configuración `CORS_ALLOWED_METHODS`, `CORS_ALLOWED_HEADERS`
- [ ] Aplicar en `CORSMiddleware`
- [ ] Actualizar `.env.example`
- [ ] Verificar API funciona (OPTIONS, POST)
- [ ] Commit: "CORS: limitar métodos/headers en producción"

---

### P2.5 - Test timeout real

**Severidad:** Baja
**Esfuerzo:** 30 min
**Ubicación:** `tests/api/`

#### Problema

No hay test que verifique el manejo de `asyncio.TimeoutError` cuando el agente excede el timeout.

#### Solución

```python
# tests/api/test_agent_timeout.py

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@patch('api.routers.agent.create_default_executor')
def test_execute_agent_timeout_marks_failed(mock_executor):
    """
    Test: Si agente excede timeout, se marca como failed
    con código TIMEOUT y se envía webhook.
    """
    # Mock executor que tarda más que timeout
    mock_instance = Mock()

    async def slow_execute(*args, **kwargs):
        await asyncio.sleep(3)  # Más que timeout
        return Mock()

    mock_instance.execute = slow_execute
    mock_executor.return_value = mock_instance

    # Mock webhook
    with patch('api.routers.agent.send_webhook') as mock_webhook:
        mock_webhook.return_value = AsyncMock(return_value=True)

        # Ejecutar con timeout corto
        response = client.post(
            "/api/v1/agent/execute",
            json={
                "expediente_id": "EXP-2024-001",
                "tarea_id": "TAREA-001",
                "agent_config": {
                    "nombre": "TestAgent",
                    "system_prompt": "Test",
                    "modelo": "test-model",
                    "prompt_tarea": "Test task",
                    "herramientas": ["tool1"]
                },
                "webhook_url": "http://example.com/callback",
                "timeout_seconds": 1  # Muy corto
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 202
        agent_run_id = response.json()["agent_run_id"]

        # Esperar background task (con margin)
        import time
        time.sleep(2)

        # Verificar que se marcó como failed
        status_response = client.get(f"/api/v1/agent/status/{agent_run_id}")
        assert status_response.status_code == 200

        status_data = status_response.json()
        assert status_data["status"] == "failed"
        assert status_data["success"] == False
        assert status_data["error"]["codigo"] == "TIMEOUT"

        # Verificar que se llamó webhook con error
        assert mock_webhook.called
        webhook_call_args = mock_webhook.call_args
        assert webhook_call_args.kwargs["error"]["codigo"] == "TIMEOUT"
```

#### Checklist

- [ ] Crear `tests/api/test_agent_timeout.py`
- [ ] Implementar test con sleep > timeout
- [ ] Ejecutar test → verificar PASS
- [ ] Commit: "Test: verificar manejo de timeout real"

---

### P2.6 - Test webhook failure

**Severidad:** Baja
**Esfuerzo:** 30 min
**Ubicación:** `tests/api/`

#### Problema

No hay test que verifique qué pasa si `send_webhook` falla.

#### Solución

```python
# tests/api/test_webhook_failure.py

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@patch('api.routers.agent.create_default_executor')
@patch('api.routers.agent.send_webhook')
def test_execute_agent_continues_if_webhook_fails(mock_webhook, mock_executor):
    """
    Test: Si webhook falla, agente se marca como completado
    pero se logea warning.
    """
    # Mock executor exitoso
    from backoffice.models import AgentExecutionResult
    mock_instance = Mock()
    mock_instance.execute = AsyncMock(return_value=AgentExecutionResult(
        success=True,
        agent_run_id="RUN-TEST",
        resultado={"message": "OK"},
        log_auditoria=[],
        herramientas_usadas=[]
    ))
    mock_executor.return_value = mock_instance

    # Mock webhook que falla
    mock_webhook.return_value = AsyncMock(return_value=False)

    response = client.post(
        "/api/v1/agent/execute",
        json={
            "expediente_id": "EXP-2024-001",
            "tarea_id": "TAREA-001",
            "agent_config": {
                "nombre": "TestAgent",
                "system_prompt": "Test",
                "modelo": "test-model",
                "prompt_tarea": "Test task",
                "herramientas": ["tool1"]
            },
            "webhook_url": "http://example.com/callback",
            "timeout_seconds": 300
        },
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 202
    agent_run_id = response.json()["agent_run_id"]

    # Esperar background task
    import time
    time.sleep(0.5)

    # Verificar que agente completó exitosamente
    status_response = client.get(f"/api/v1/agent/status/{agent_run_id}")
    status_data = status_response.json()

    assert status_data["status"] == "completed"
    assert status_data["success"] == True

    # Verificar que webhook se intentó
    assert mock_webhook.called
```

#### Checklist

- [ ] Crear `tests/api/test_webhook_failure.py`
- [ ] Implementar test con `send_webhook` returning False
- [ ] Ejecutar test → verificar PASS
- [ ] Commit: "Test: verificar comportamiento si webhook falla"

---

## Prioridad 3 (Baja) - 3h

### P3.1 - Logs estructurados JSON

**Severidad:** Baja
**Esfuerzo:** 1h
**Ubicación:** `api/main.py:22-24`

#### Problema

Logs en formato texto plano:

```
2024-12-10 14:30:22 - api.main - INFO - aGEntiX API iniciando...
```

Dificulta parseo en Elasticsearch/Loki.

#### Solución

Usar `python-json-logger`:

```bash
# requirements.txt
python-json-logger>=2.0.0
```

```python
# api/main.py

import logging
from pythonjsonlogger import jsonlogger

# Configurar logging estructurado
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    "%(timestamp)s %(level)s %(name)s %(message)s",
    rename_fields={"levelname": "level", "asctime": "timestamp"}
)
logHandler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))
```

**Output:**

```json
{
  "timestamp": "2024-12-10T14:30:22Z",
  "level": "INFO",
  "name": "api.main",
  "message": "aGEntiX API iniciando...",
  "version": "1.0.0",
  "mcp_config": "backoffice/config/mcp_servers.yaml"
}
```

**Con contexto adicional:**

```python
logger.info(
    "Agente completado",
    extra={
        "agent_run_id": agent_run_id,
        "success": result.success,
        "elapsed_seconds": elapsed
    }
)
```

#### Checklist

- [ ] Añadir dependencia `python-json-logger`
- [ ] Configurar `JsonFormatter`
- [ ] Actualizar logs con `extra={...}`
- [ ] Verificar output JSON válido
- [ ] Commit: "Logs: formato JSON estructurado"

---

### P3.2 - Rate limiting

**Severidad:** Baja (pero importante para producción)
**Esfuerzo:** 2h
**Ubicación:** `api/main.py`

#### Problema

No hay protección contra abuso de API (DoS).

#### Solución

Usar `slowapi`:

```bash
# requirements.txt
slowapi>=0.1.9
```

```python
# api/main.py

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Crear limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(...)

# Registrar error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# api/routers/agent.py

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/execute", ...)
@limiter.limit("10/minute")  # Max 10 requests por minuto
async def execute_agent(...):
    # ... (código existente) ...
```

**Configuración:**

```python
# backoffice/settings.py

class Settings(BaseSettings):
    # ... (existentes) ...

    RATE_LIMIT_EXECUTE: str = Field(
        default="10/minute",
        description="Rate limit para POST /execute"
    )

    RATE_LIMIT_STATUS: str = Field(
        default="100/minute",
        description="Rate limit para GET /status"
    )

# api/routers/agent.py

from backoffice.settings import settings

@router.post("/execute", ...)
@limiter.limit(settings.RATE_LIMIT_EXECUTE)
async def execute_agent(...):
    ...

@router.get("/status/{agent_run_id}", ...)
@limiter.limit(settings.RATE_LIMIT_STATUS)
async def get_agent_status(...):
    ...
```

**Error response:**

```json
{
  "error": "Rate limit exceeded",
  "detail": "10 per 1 minute"
}
```

#### Checklist

- [ ] Añadir dependencia `slowapi`
- [ ] Configurar `Limiter`
- [ ] Aplicar `@limiter.limit()` en endpoints
- [ ] Añadir configuración `RATE_LIMIT_*`
- [ ] Test rate limiting
- [ ] Commit: "Rate limiting con slowapi"

---

## Orden de Implementación Recomendado

1. **P1.1** - Migrar lifespan (15 min)
   - Prerequisito para P2.2
   - Elimina warnings

2. **P1.3** - Colisión run_id (30 min)
   - Rápido y defensivo

3. **P1.2** - Webhook retry (45 min)
   - Crítico para robustez

4. **P2.1** - Validar webhook (30 min)
   - Seguridad

5. **P2.2** - Cleanup automático (1h)
   - Requiere P1.1

6. **P2.4** - CORS hardening (15 min)
   - Rápido

7. **P2.5, P2.6** - Tests adicionales (1h total)
   - Completar coverage

8. **P2.3** - Health check MCP (45 min)
   - Nice to have

9. **P3.1, P3.2** - Logs JSON + Rate limiting (3h)
   - Opcional, según necesidad

---

## Checklist General

### Antes de Merge

- [ ] Todos los tests PASS (96/96)
- [ ] Sin regresiones
- [ ] README actualizado (si aplica)

### Antes de Producción (P1)

- [ ] P1.1 - lifespan
- [ ] P1.2 - webhook retry
- [ ] P1.3 - colisión run_id

### Antes de Producción (P2 recomendado)

- [ ] P2.1 - SSRF validation
- [ ] P2.2 - cleanup automático
- [ ] P2.4 - CORS hardening

### Opcional (P3)

- [ ] P3.1 - Logs JSON
- [ ] P3.2 - Rate limiting

---

**Fecha:** 2025-12-10
**Autor plan:** Claude Code (Sonnet 4.5)
**Basado en:** Code review commit 64fda4d
