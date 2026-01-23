# Plan de Mejoras - Commit 41f313a

## Estado de Implementación

| ID | Mejora | Estado | Prioridad |
|----|--------|--------|-----------|
| **P4** | **Integrar AuditLogger en logs de tarea Celery** | ✅ COMPLETADO | **CRÍTICA** |
| P1 | Mover buckets histograma a configuración | ✅ COMPLETADO | Baja |
| P2 | Extraer mapeo de estados Celery | ✅ COMPLETADO | Baja |
| P3 | Documentar cambio de passwords por defecto | ✅ COMPLETADO | Alta |

---

## P4: Integrar PIIRedactor en Logs de Tarea Celery (CRÍTICO)

### Problema Actual

```python
# agent_execution.py:27 - Logger estándar SIN redacción de PII
logger = logging.getLogger(__name__)

# Línea 231-236 - RIESGO: str(e) puede contener datos personales
logger.error(
    f"[Celery] Error: task_id={agent_run_id}, "
    f"error={type(e).__name__}: {str(e)}, "  # ⚠️ PII EXPUESTO
    f"duration={duration:.2f}s",
    exc_info=True  # ⚠️ Traceback puede contener PII
)
```

### Impacto

| Aspecto | Riesgo |
|---------|--------|
| GDPR | Violación Art. 5 (minimización de datos) |
| LOPD | Violación principio de confidencialidad |
| ENS | No cumple medidas de seguridad nivel medio/alto |
| Auditoría | Logs no trazables por expediente |

### Datos que Podrían Exponerse

Cuando una excepción contiene datos del expediente:
```python
# Ejemplo de excepción que expone PII
raise ValueError(f"DNI inválido: 12345678A para expediente EXP-2024-001")
# str(e) = "DNI inválido: 12345678A para expediente EXP-2024-001"
# Este mensaje se logea SIN REDACTAR
```

### Solución Propuesta

**Opción A: Mínimo impacto (PIIRedactor en mensajes)**

```python
# agent_execution.py
from backoffice.logging.pii_redactor import PIIRedactor

# Crear wrapper para logging seguro
def _safe_log(level: str, message: str, **kwargs):
    """Logea mensaje con PII redactado."""
    redacted = PIIRedactor.redact(message)
    getattr(logger, level)(redacted, **kwargs)

# Uso en execute_agent_task:
_safe_log('info', f"[Celery] Iniciando: expediente={expediente_id}")
_safe_log('error', f"[Celery] Error: {str(e)}")
```

**Opción B: Integración completa con AuditLogger (Recomendada)**

```python
# agent_execution.py
from backoffice.logging.audit_logger import AuditLogger
from backoffice.settings import settings

@celery_app.task(...)
def execute_agent_task(self, token, expediente_id, tarea_id, ...):
    agent_run_id = self.request.id

    # Crear AuditLogger para esta tarea
    task_logger = AuditLogger(
        expediente_id=expediente_id,
        agent_run_id=agent_run_id,
        log_dir=settings.LOG_DIR
    )

    try:
        task_logger.log(f"[Celery] Iniciando ejecución")
        # ... código existente ...
        task_logger.log(f"[Celery] Completado exitosamente")

    except Exception as e:
        task_logger.error(f"[Celery] Error: {type(e).__name__}: {str(e)}")
        raise
```

### Beneficios de Opción B

1. **Logs unificados**: Tarea Celery y executor en mismo archivo
2. **PII siempre redactado**: Automático via AuditLogger
3. **Trazabilidad completa**: Por expediente y agent_run_id
4. **Formato consistente**: JSON lines como el resto del sistema

### Implementación Detallada

```python
# agent_execution.py - Cambios necesarios

# Añadir imports
from backoffice.logging.audit_logger import AuditLogger
from backoffice.settings import settings

# En execute_agent_task, después de obtener agent_run_id:
task_logger = AuditLogger(
    expediente_id=expediente_id,
    agent_run_id=agent_run_id,
    log_dir=settings.LOG_DIR
)

# Reemplazar todos los logger.info/error/warning por:
task_logger.log(mensaje)      # INFO
task_logger.error(mensaje)    # ERROR
task_logger.warning(mensaje)  # WARNING

# El logging estándar puede mantenerse para mensajes sin PII:
logger.debug(f"Task {agent_run_id} started")  # OK, no contiene PII
```

### Tests Requeridos

```python
# tests/test_backoffice/test_celery_tasks.py

def test_task_logs_are_pii_redacted():
    """Verifica que logs de tarea redactan PII."""
    # Simular error con PII
    error_with_pii = ValueError("DNI 12345678A no válido")

    # Verificar que el log redacta
    with patch('backoffice.tasks.agent_execution.AuditLogger') as mock:
        # ... ejecutar tarea que falla ...
        call_args = mock.return_value.error.call_args[0][0]
        assert "12345678A" not in call_args
        assert "[DNI-REDACTED]" in call_args
```

### Esfuerzo Estimado

| Tarea | Tiempo |
|-------|--------|
| Implementar Opción A (mínimo) | 30 min |
| Implementar Opción B (completa) | 1-2 horas |
| Añadir tests | 1 hora |
| **Total (Opción B recomendada)** | **2-3 horas** |

---

## P1: Mover Buckets del Histograma a Configuración

**Problema actual:**
```python
# agent_execution.py:36-41
task_duration = Histogram(
    'agentix_celery_task_duration_seconds',
    'Duración ejecución agente en Celery',
    ['agent_name'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600]  # Hardcoded
)
```

**Solución propuesta:**
```python
# settings.py
class Settings(BaseSettings):
    # ... existing settings ...

    PROMETHEUS_DURATION_BUCKETS: str = "1,5,10,30,60,120,300,600,1800,3600"

    @property
    def prometheus_duration_buckets(self) -> tuple:
        return tuple(int(x) for x in self.PROMETHEUS_DURATION_BUCKETS.split(","))

# agent_execution.py
from backoffice.settings import settings

task_duration = Histogram(
    'agentix_celery_task_duration_seconds',
    'Duración ejecución agente en Celery',
    ['agent_name'],
    buckets=settings.prometheus_duration_buckets
)
```

**Beneficios:**
- Configurable sin cambiar código
- Ajustable según patrones de uso reales
- Consistencia con otras métricas

**Esfuerzo:** Bajo (30 min)

---

## P2: Extraer Mapeo de Estados Celery

**Problema actual:**
```python
# agent.py:462-468
def _get_celery_task_status(agent_run_id: str) -> Optional[dict]:
    # ...
    status_map = {
        'PENDING': 'pending',
        'STARTED': 'running',
        'RETRY': 'running',
        'SUCCESS': 'completed',
        'FAILURE': 'failed'
    }
    # ...
```

**Solución propuesta:**
```python
# Constante a nivel de módulo o clase
CELERY_STATE_MAP = {
    'PENDING': 'pending',
    'STARTED': 'running',
    'RETRY': 'running',
    'SUCCESS': 'completed',
    'FAILURE': 'failed',
    'REVOKED': 'cancelled',  # Añadir estado adicional
}

def _get_celery_task_status(agent_run_id: str) -> Optional[dict]:
    # ...
    status = CELERY_STATE_MAP.get(celery_result.state, 'unknown')
    # ...
```

**Beneficios:**
- Documentación implícita de mapeo
- Fácil de extender
- Reutilizable si se necesita en otros lugares

**Esfuerzo:** Bajo (15 min)

---

## P3: Documentar Cambio de Passwords por Defecto

**Problema actual:**
```yaml
# docker-compose.prod.yml
--requirepass ${REDIS_PASSWORD:-changeme}
--basic_auth=${FLOWER_USER:-admin}:${FLOWER_PASSWORD:-changeme}
```

**Solución propuesta:**

1. Añadir sección en `docker-compose.prod.yml`:
```yaml
# SEGURIDAD - ANTES DE PRODUCCIÓN:
# ==================================
# 1. Crear archivo .env.prod con las siguientes variables:
#    REDIS_PASSWORD=<password-seguro-generado>
#    FLOWER_PASSWORD=<password-seguro-generado>
#    JWT_SECRET=<secret-seguro-generado>
#    API_ADMIN_TOKEN=<token-seguro-generado>
#
# 2. Generar passwords seguros:
#    openssl rand -base64 32
#
# 3. Nunca usar valores por defecto (changeme) en producción
```

2. Añadir script `scripts/generate_secrets.sh`:
```bash
#!/bin/bash
echo "REDIS_PASSWORD=$(openssl rand -base64 32)"
echo "FLOWER_PASSWORD=$(openssl rand -base64 32)"
echo "JWT_SECRET=$(openssl rand -base64 32)"
echo "API_ADMIN_TOKEN=$(openssl rand -base64 32)"
```

3. Añadir validación en startup:
```python
# settings.py
def validate_production_settings(self):
    if os.getenv('ENVIRONMENT') == 'production':
        if self.REDIS_PASSWORD == 'changeme':
            raise ValueError("REDIS_PASSWORD must be changed in production!")
```

**Beneficios:**
- Previene despliegue inseguro
- Documentación clara para DevOps
- Script automatizado para generar secretos

**Esfuerzo:** Medio (1 hora)

---

## Priorización Recomendada

### Fase 0 (BLOQUEANTE - Antes de Producción) ✅ COMPLETADO
- [x] **P4: Integrar AuditLogger en logs de tarea Celery** (CRÍTICO - Compliance GDPR/LOPD/ENS)

### Fase 1 (Antes del primer deploy a producción) ✅ COMPLETADO
- [x] P3: Documentar y validar passwords

### Fase 2 (Próximo sprint) ✅ COMPLETADO
- [x] P1: Buckets configurables
- [x] P2: Constante para mapeo de estados

---

## Mejoras No Prioritarias (Backlog)

### Observabilidad Avanzada

1. **Tracing distribuido con OpenTelemetry**
   ```python
   # Añadir spans para trazar ejecución completa
   with tracer.start_span("execute_agent") as span:
       span.set_attribute("agent_name", agent_name)
       span.set_attribute("expediente_id", expediente_id)
       result = await executor.execute(...)
   ```
   - Esfuerzo: Alto
   - Impacto: Alto para debugging

2. **Dead Letter Queue (DLQ)**
   ```python
   # Mover tareas fallidas a cola especial para análisis
   celery_app.conf.task_routes = {
       'backoffice.execute_agent': {'queue': 'agents'},
   }
   celery_app.conf.task_reject_on_worker_lost = True
   ```
   - Esfuerzo: Medio
   - Impacto: Alto para debugging

### Rendimiento

3. **Prefork pool con optimizaciones**
   ```python
   celery_app.conf.update(
       worker_pool='prefork',
       worker_concurrency=4,
       worker_max_memory_per_child=200_000,  # 200MB
   )
   ```
   - Esfuerzo: Bajo
   - Impacto: Medio

4. **Task routing por tipo de agente**
   ```python
   # Agentes rápidos a cola 'fast', lentos a 'slow'
   celery_app.conf.task_routes = {
       'backoffice.execute_agent': {
           'queue': lambda args: 'slow' if args[2].get('modelo') == 'claude-opus-4-20250514' else 'fast'
       }
   }
   ```
   - Esfuerzo: Medio
   - Impacto: Medio

### Resiliencia

5. **Circuit breaker para MCP**
   ```python
   from circuitbreaker import circuit

   @circuit(failure_threshold=5, recovery_timeout=30)
   async def call_mcp_tool(tool_name, args):
       # ...
   ```
   - Esfuerzo: Medio
   - Impacto: Alto

6. **Retry con jitter personalizado**
   ```python
   # Jitter más agresivo para evitar thundering herd
   import random

   def custom_backoff(retries):
       base = 5 * (2 ** retries)
       jitter = random.uniform(0, base * 0.5)
       return min(base + jitter, 300)
   ```
   - Esfuerzo: Bajo
   - Impacto: Medio

---

## Deuda Técnica Aceptable

*(Todas las deudas técnicas identificadas han sido resueltas)*

## Deuda Técnica Resuelta

1. **P4 - Logs sin PIIRedactor**: ✅ RESUELTO - AuditLogger integrado en `agent_execution.py`
2. **P1 - Buckets hardcodeados**: ✅ RESUELTO - Configurable via `PROMETHEUS_DURATION_BUCKETS`
3. **P2 - Mapeo de estados inline**: ✅ RESUELTO - Extraído a constante `CELERY_STATE_MAP`
4. **P3 - Passwords por defecto**: ✅ RESUELTO - Script `generate_secrets.sh` + validación en `Settings`

---

## Notas para el Próximo Sprint

### Antes de Producción (Código Implementado)

- [x] **P4: Integrar AuditLogger en `agent_execution.py`** (COMPLETADO)
- [x] **P1: Buckets configurables via `PROMETHEUS_DURATION_BUCKETS`** (COMPLETADO)
- [x] **P2: Constante `CELERY_STATE_MAP` extraída** (COMPLETADO)
- [x] **P3: Script `generate_secrets.sh` + validación en Settings** (COMPLETADO)

### Antes de Deploy (Tareas DevOps)

- [ ] Ejecutar `scripts/generate_secrets.sh` y configurar `.env.prod`
- [ ] Verificar healthchecks funcionan correctamente
- [ ] Configurar alertas Prometheus
- [ ] Documentar proceso de rollback (USE_CELERY=false)

### Monitoreo Post-Deploy

- [ ] Verificar métricas Prometheus aparecen en Grafana
- [ ] Confirmar Flower accesible y mostrando workers
- [ ] Ejecutar agente de prueba y verificar flujo completo
- [ ] Medir latencia real vs BackgroundTasks
