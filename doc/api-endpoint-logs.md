# API Endpoint: GET /api/v1/logs

## Descripción

Endpoint para consultar logs del sistema aGEntiX con filtros avanzados y paginación. Lee los archivos de log generados por el `AuditLogger` durante las ejecuciones de agentes.

**Estado:** ✅ Implementado (2024-12-22)

## Autenticación

**Requerido:** Sí - Token de administrador

**Header:**
```
Authorization: Bearer <API_ADMIN_TOKEN>
```

**Token:** Configurado en variable de entorno `API_ADMIN_TOKEN` (`.env`)

**Ejemplo:**
```bash
Authorization: Bearer agentix-admin-dev-token-2024
```

**Respuestas de error:**
- `401 Unauthorized`: Token inválido o faltante

## Endpoint

```
GET /api/v1/logs
```

## Parámetros Query

Todos los parámetros son opcionales. Si no se proporcionan, se devuelven todos los logs disponibles.

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `page` | integer | `1` | Número de página (≥ 1) |
| `page_size` | integer | `50` | Tamaño de página (1-500) |
| `level` | string | - | Niveles de log separados por comas |
| `component` | string | - | Componentes separados por comas |
| `agent` | string | - | Tipos de agente separados por comas |
| `expediente_id` | string | - | ID de expediente (búsqueda parcial) |
| `date_from` | datetime | - | Fecha desde (ISO 8601) |
| `date_to` | datetime | - | Fecha hasta (ISO 8601) |
| `search` | string | - | Búsqueda de texto completo |

### Detalles de Parámetros

#### `level`
Filtra por niveles de log. Valores separados por comas.

**Valores válidos:** `INFO`, `WARNING`, `ERROR`, `CRITICAL`, `DEBUG`

**Ejemplo:**
```
level=ERROR,CRITICAL
```

#### `component`
Filtra por componentes del sistema. Valores separados por comas.

**Valores válidos:** `AgentExecutor`, `MCPClient`, `PIIRedactor`, `AuditLogger`, `JWTValidator`, `APIServer`, `WebhookService`, `TaskTracker`

**Ejemplo:**
```
component=AgentExecutor,MCPClient
```

#### `agent`
Filtra por tipos de agente. Valores separados por comas.

**Valores válidos:** `ValidadorDocumental`, `AnalizadorSubvencion`, `GeneradorInforme`

**Ejemplo:**
```
agent=ValidadorDocumental
```

#### `expediente_id`
Búsqueda parcial case-insensitive en el ID del expediente.

**Ejemplo:**
```
expediente_id=EXP-2024-001
```

#### `date_from` y `date_to`
Rango de fechas en formato ISO 8601.

**Formato:** `YYYY-MM-DDTHH:MM:SS.sssZ`

**Ejemplo:**
```
date_from=2024-12-22T00:00:00.000Z&date_to=2024-12-22T23:59:59.999Z
```

#### `search`
Búsqueda de texto completo (case-insensitive) en:
- Mensaje del log
- Contexto (metadata) serializado a JSON
- Información de errores

**Ejemplo:**
```
search=validación
```

## Respuesta

### Estructura

```typescript
{
  logs: LogEntry[],
  total: number,
  page: number,
  page_size: number,
  has_more: boolean
}
```

### Modelo `LogEntry`

```typescript
{
  id: string,                    // ID único del log
  timestamp: string,             // ISO 8601 timestamp
  level: string,                 // INFO | WARNING | ERROR | CRITICAL | DEBUG
  component: string,             // Componente del sistema
  agent?: string,                // Tipo de agente (opcional)
  expediente_id?: string,        // ID del expediente (opcional)
  message: string,               // Mensaje del log (con PII redactado)
  context?: object,              // Metadata adicional (opcional)
  user_id?: string,              // ID del usuario (opcional)
  agent_run_id?: string,         // ID de ejecución del agente (opcional)
  duration_ms?: number,          // Duración en ms (opcional)
  error?: {                      // Información de error (opcional)
    type: string,
    message: string,
    stacktrace?: string
  }
}
```

### Ejemplo de Respuesta

```json
{
  "logs": [
    {
      "id": "run-test-001-5",
      "timestamp": "2025-12-22T10:16:17.315007+00:00",
      "level": "INFO",
      "component": "AgentExecutor",
      "agent": "ValidadorDocumental",
      "expediente_id": "EXP-2024-001",
      "message": "Ejecución completada",
      "context": {
        "agent": "ValidadorDocumental",
        "duration_ms": 45000
      },
      "user_id": null,
      "agent_run_id": "run-test-001",
      "duration_ms": 45000,
      "error": null
    },
    {
      "id": "run-test-001-4",
      "timestamp": "2025-12-22T10:15:17.315001+00:00",
      "level": "ERROR",
      "component": "AgentExecutor",
      "agent": "ValidadorDocumental",
      "expediente_id": "EXP-2024-001",
      "message": "Error al validar documento",
      "context": {
        "agent": "ValidadorDocumental",
        "error": {
          "type": "ValidationError",
          "message": "Documento incompleto",
          "stacktrace": "File \"validator.py\", line 45, in validate"
        }
      },
      "user_id": null,
      "agent_run_id": "run-test-001",
      "duration_ms": null,
      "error": {
        "type": "ValidationError",
        "message": "Documento incompleto",
        "stacktrace": "File \"validator.py\", line 45, in validate"
      }
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 10,
  "has_more": false
}
```

## Ejemplos de Uso

### 1. Obtener todos los logs (primera página)

```bash
curl -X GET "http://localhost:8080/api/v1/logs?page=1&page_size=50" \
  -H "Authorization: Bearer agentix-admin-dev-token-2024"
```

### 2. Filtrar solo errores críticos

```bash
curl -X GET "http://localhost:8080/api/v1/logs?level=ERROR,CRITICAL&page=1&page_size=50" \
  -H "Authorization: Bearer agentix-admin-dev-token-2024"
```

### 3. Logs de un expediente específico

```bash
curl -X GET "http://localhost:8080/api/v1/logs?expediente_id=EXP-2024-001&page=1&page_size=50" \
  -H "Authorization: Bearer agentix-admin-dev-token-2024"
```

### 4. Logs de ValidadorDocumental en las últimas 24 horas

```bash
curl -X GET "http://localhost:8080/api/v1/logs?agent=ValidadorDocumental&date_from=2024-12-21T00:00:00Z&page=1&page_size=50" \
  -H "Authorization: Bearer agentix-admin-dev-token-2024"
```

### 5. Búsqueda de texto completo

```bash
curl -X GET "http://localhost:8080/api/v1/logs?search=validación&page=1&page_size=50" \
  -H "Authorization: Bearer agentix-admin-dev-token-2024"
```

### 6. Filtros combinados

```bash
curl -X GET "http://localhost:8080/api/v1/logs?level=ERROR&agent=ValidadorDocumental&expediente_id=EXP-2024&page=1&page_size=50" \
  -H "Authorization: Bearer agentix-admin-dev-token-2024"
```

## Implementación Backend

### Archivos

**Router:** `src/api/routers/logs.py` (305 líneas)
- Endpoint GET `/api/v1/logs`
- Funciones de lectura y filtrado de logs
- Mapeo de formato interno a API

**Dependency:** `src/api/routers/auth.py`
- Función `verify_admin_token()` para proteger endpoints
- Valida header `Authorization: Bearer <token>`

**Registro:** `src/api/main.py`
- Router registrado en la aplicación FastAPI

### Lectura de Logs

Los logs se leen desde el sistema de archivos:

**Directorio base:** `logs/agent_runs/` (configurado en `settings.LOG_DIR`)

**Estructura:**
```
logs/agent_runs/
├── EXP-2024-001/
│   ├── run-abc123.log
│   └── run-xyz789.log
├── EXP-2024-002/
│   └── run-def456.log
...
```

**Formato de archivo:** JSON Lines (`.log`)

Cada línea es un objeto JSON:
```json
{
  "timestamp": "2024-12-22T10:00:00.000Z",
  "level": "INFO",
  "agent_run_id": "run-abc123",
  "expediente_id": "EXP-2024-001",
  "mensaje": "Mensaje con PII redactado",
  "metadata": {...}
}
```

### Proceso de Lectura

1. **Recorrer directorios:** Itera sobre todos los subdirectorios en `logs/agent_runs/`
2. **Leer archivos `.log`:** Parsea cada línea como JSON
3. **Generar ID único:** Combina nombre de archivo y número de línea
4. **Recopilar todos los logs:** Agrega a lista en memoria
5. **Aplicar filtros:** Filtra según parámetros query
6. **Ordenar:** Por timestamp descendente (más reciente primero)
7. **Paginar:** Retorna página solicitada
8. **Mapear formato:** Convierte de formato interno a formato API

### Mapeo de Formato

El `AuditLogger` escribe logs con el campo `mensaje` (español), pero la API lo expone como `message` (inglés) para consistencia con el frontend.

**Mapeo de campos:**
- `mensaje` → `message`
- `metadata.agent` → `agent`
- `metadata.duration_ms` → `duration_ms`
- `metadata.error` → `error`

## Integración Frontend

### Servicio TypeScript

**Archivo:** `frontend/src/services/logsService.ts`

**Cambio realizado:**
```typescript
// Antes
const USE_MOCK_DATA = true;

// Ahora
const USE_MOCK_DATA = false;
```

### Llamada a la API

```typescript
const response = await api.get<LogsResponse>('/api/v1/logs', {
  params: {
    page,
    page_size: pageSize,
    level: filters.level?.join(','),
    component: filters.component?.join(','),
    agent: filters.agent?.join(','),
    expediente_id: filters.expediente_id,
    date_from: filters.dateFrom?.toISOString(),
    date_to: filters.dateTo?.toISOString(),
    search: filters.searchText,
  },
});
```

**Nota:** El interceptor de Axios añade automáticamente el header `Authorization: Bearer <token>` desde `localStorage`.

## Performance

### Consideraciones

- **Lectura completa en memoria:** Todos los logs se leen en memoria antes de filtrar
- **Sin índices:** Búsqueda secuencial (O(n) por cada filtro)
- **Escalabilidad limitada:** Óptimo para ~10k logs, degradación gradual hasta ~100k

### Optimizaciones Futuras

Para producción con grandes volúmenes de logs (>100k):

1. **Base de datos:** Migrar a PostgreSQL/MongoDB
2. **Índices:** Indexar por `timestamp`, `level`, `expediente_id`, `agent`
3. **Full-text search:** Elasticsearch para búsqueda de texto
4. **Agregación:** Pre-calcular estadísticas
5. **Streaming:** SSE para logs en tiempo real (ya preparado en frontend)

## Seguridad

### Protección de Datos

- ✅ **PII ya redactado:** Los logs en disco ya tienen PII redactado por `PIIRedactor`
- ✅ **Autenticación requerida:** Solo usuarios con token de admin pueden acceder
- ✅ **Sin exposición de rutas:** No se exponen paths del sistema de archivos
- ✅ **Sin inyección:** Todos los parámetros se sanitizan antes de filtrar

### Headers de Seguridad

El endpoint hereda los headers de seguridad configurados en `main.py`:
- CORS configurado con orígenes permitidos
- Rate limiting (pendiente de implementar)

## Testing

### Datos de Prueba

Se pueden generar logs de prueba con:

```python
import json
from pathlib import Path
from datetime import datetime, timezone

log_dir = Path('logs/agent_runs/EXP-TEST-001')
log_dir.mkdir(parents=True, exist_ok=True)

log = {
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'level': 'INFO',
    'agent_run_id': 'run-test-001',
    'expediente_id': 'EXP-TEST-001',
    'mensaje': 'Log de prueba',
    'metadata': {'component': 'Test'}
}

with open(log_dir / 'run-test-001.log', 'a') as f:
    f.write(json.dumps(log) + '\n')
```

### Tests Manuales

Ver sección "Ejemplos de Uso" arriba.

### Tests Automatizados

Pendiente de implementar en `tests/api/test_logs.py`:
- Test de autenticación (401 sin token)
- Test de paginación
- Test de filtros individuales
- Test de filtros combinados
- Test de búsqueda de texto
- Test de ordenamiento
- Test con logs vacíos

## Documentación Relacionada

- [Paso 3 - Fase 3: Visor de Logs](paso-3-fase-3-visor-logs.md) - Documentación completa del frontend
- [AuditLogger](../src/backoffice/logging/audit_logger.py) - Sistema de logs del backend
- [PIIRedactor](../src/backoffice/logging/pii_redactor.py) - Redacción de PII

## Changelog

### 2024-12-22 - Implementación Inicial

- ✅ Endpoint GET `/api/v1/logs` implementado
- ✅ Lectura de logs desde `logs/agent_runs/`
- ✅ Filtrado por 8 parámetros diferentes
- ✅ Paginación completa
- ✅ Protección con token de admin
- ✅ Integración con frontend (USE_MOCK_DATA = false)
- ✅ Documentación completa

**Commit:** `b67ad24` - "Implementar Paso 3 - Fase 3: Visor de Logs en Tiempo Real"

## Pendiente

- [ ] Endpoint GET `/api/v1/logs/stream` para SSE (streaming en tiempo real)
- [ ] Tests automatizados
- [ ] Rate limiting específico para este endpoint
- [ ] Caché de logs leídos (invalidar cada N segundos)
- [ ] Compresión de respuestas grandes (gzip)
- [ ] Métricas Prometheus específicas (requests, filtros usados, etc.)
