# Plan de Mejoras - Commit c039abe

## Objetivo

Este documento detalla las mejoras recomendadas tras la revisión del commit c039abe, priorizadas por urgencia y esfuerzo.

---

## Resumen Ejecutivo

- **Total de mejoras:** 10
- **Críticas:** 0
- **Altas:** 3 (3h 2min)
- **Medias:** 4 (54min)
- **Bajas:** 3 (7h)
- **Esfuerzo total:** ~11h

**Recomendación:** Implementar al menos las mejoras P1 (3) y P2 rápidas (3) antes de pasar al Paso 2.

---

## P1 - Prioridad Alta (3h 2min)

### 1. Añadir timezone UTC a run_id ⚡

**Archivo:** `backoffice/executor.py:59`

**Problema:**
```python
agent_run_id = f"RUN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
```

Usa `datetime.now()` sin timezone, lo que puede causar ambigüedad en logs.

**Solución:**
```python
from datetime import datetime, timezone

agent_run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')[:21]}"
```

**Cambios adicionales:**
- Añadir microsegundos para evitar colisiones
- Truncar a 6 dígitos de microsegundos

**Esfuerzo:** 2 minutos
**Impacto:** Evita ambigüedad en logs distribuidos
**Archivos:** 1

---

### 2. Añadir tests de integración MCP

**Archivos:** Nuevo archivo `backoffice/tests/test_mcp_integration.py`

**Tests requeridos:**

1. **test_mcp_client_connection_success**
   - Mock de httpx
   - Verificar llamada correcta a `/sse`
   - Verificar headers JWT

2. **test_mcp_client_timeout**
   - Mock de timeout
   - Verificar MCPConnectionError
   - Verificar código `MCP_TIMEOUT`

3. **test_mcp_client_auth_error_401**
   - Mock de respuesta 401
   - Verificar MCPAuthError
   - Verificar código `AUTH_INVALID_TOKEN`

4. **test_mcp_client_tool_not_found_404**
   - Mock de respuesta 404
   - Verificar MCPToolError
   - Verificar código `MCP_TOOL_NOT_FOUND`

5. **test_mcp_registry_routing**
   - Mock de múltiples MCPs
   - Verificar routing correcto
   - Verificar discovery de tools

6. **test_mcp_registry_tool_not_found**
   - Intentar llamar tool inexistente
   - Verificar error con lista de tools disponibles

**Esfuerzo:** 2 horas
**Impacto:** Confianza en integración MCP
**Archivos:** 1 nuevo

**Template de inicio:**
```python
# backoffice/tests/test_mcp_integration.py
import pytest
from unittest.mock import AsyncMock, patch
from backoffice.mcp.client import MCPClient
from backoffice.mcp.registry import MCPClientRegistry
from backoffice.mcp.exceptions import MCPConnectionError, MCPAuthError, MCPToolError
from backoffice.config.models import MCPServerConfig, MCPAuthConfig

@pytest.fixture
def mock_server_config():
    return MCPServerConfig(
        id="test-mcp",
        name="Test MCP",
        description="Test server",
        url="http://localhost:8000",
        type="http",
        auth=MCPAuthConfig(type="jwt", audience="test-audience"),
        timeout=30
    )

@pytest.mark.asyncio
async def test_mcp_client_connection_success(mock_server_config):
    # TODO: Implementar
    pass
```

---

### 3. Añadir tests unitarios de validación JWT

**Archivos:** Nuevo archivo `backoffice/tests/test_jwt_validator.py`

**Tests requeridos:**

1. **test_validate_jwt_success**
   - JWT válido
   - Claims correctos
   - Verificar retorno de JWTClaims

2. **test_validate_jwt_expired**
   - Token expirado
   - Verificar JWTValidationError
   - Verificar código `AUTH_TOKEN_EXPIRED`

3. **test_validate_jwt_invalid_signature**
   - Firma inválida
   - Verificar código `AUTH_INVALID_TOKEN`

4. **test_validate_jwt_invalid_issuer**
   - Emisor incorrecto
   - Verificar código `AUTH_PERMISSION_DENIED`

5. **test_validate_jwt_invalid_subject**
   - Subject incorrecto
   - Verificar mensaje de error

6. **test_validate_jwt_missing_audience**
   - Audiencia faltante
   - Verificar código `AUTH_PERMISSION_DENIED`

7. **test_validate_jwt_wrong_expediente**
   - Expediente no autorizado
   - Verificar código `AUTH_EXPEDIENTE_MISMATCH`

8. **test_validate_jwt_insufficient_permissions**
   - Permisos insuficientes
   - Verificar código `AUTH_INSUFFICIENT_PERMISSIONS`

9. **test_get_required_permissions_readonly**
   - Tools de solo lectura
   - Verificar solo permiso "consulta"

10. **test_get_required_permissions_write**
    - Tools de escritura
    - Verificar permisos "consulta" + "gestion"

**Esfuerzo:** 1 hora
**Impacto:** Confianza en seguridad JWT
**Archivos:** 1 nuevo

**Template de inicio:**
```python
# backoffice/tests/test_jwt_validator.py
import pytest
import jwt
from datetime import datetime, timezone, timedelta
from backoffice.auth.jwt_validator import (
    validate_jwt,
    get_required_permissions_for_tools,
    JWTValidationError
)

@pytest.fixture
def jwt_secret():
    return "test-secret-key"

@pytest.fixture
def valid_claims():
    now = datetime.now(timezone.utc)
    return {
        "iss": "agentix-bpmn",
        "sub": "Automático",
        "aud": ["agentix-mcp-expedientes"],
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "jti": "test-jti-123",
        "exp_id": "EXP-2024-001",
        "permisos": ["consulta", "gestion"]
    }

def test_validate_jwt_success(jwt_secret, valid_claims):
    # TODO: Implementar
    pass
```

---

## P2 - Prioridad Media (54 minutos)

### 4. Usar logger en lugar de print ⚡

**Archivo:** `backoffice/mcp/registry.py:80`

**Problema:**
```python
print(f"⚠️  Warning: No se pudieron descubrir tools de MCP '{server_id}': {e}")
```

Inconsistente con el resto del sistema que usa AuditLogger.

**Solución:**

Opción A - Simple (recomendada para Paso 1):
```python
import logging

logger = logging.getLogger(__name__)

# En _discover_tools:
logger.warning(f"No se pudieron descubrir tools de MCP '{server_id}': {e}")
```

Opción B - Completa (para producción):
```python
# Pasar logger al registry
class MCPClientRegistry:
    def __init__(self, config: MCPServersConfig, token: str, logger: Optional[AuditLogger] = None):
        ...
        self.logger = logger

    async def _discover_tools(self, server_id: str):
        ...
        if self.logger:
            self.logger.warning(f"No se pudieron descubrir tools de MCP '{server_id}': {e}")
```

**Esfuerzo:** 2 minutos (Opción A) / 15 minutos (Opción B)
**Impacto:** Consistencia en logging
**Archivos:** 1

---

### 5. Mover endpoint MCP a configuración ⚡

**Archivos:**
- `backoffice/config/models.py`
- `backoffice/mcp/client.py`

**Problema:**
Endpoint `/sse` hardcodeado en 3 lugares.

**Solución:**

**Paso 1:** Añadir campo a configuración
```python
# backoffice/config/models.py
class MCPServerConfig(BaseModel):
    id: str
    name: str
    description: str
    url: HttpUrl
    type: Literal["http", "stdio"] = "http"
    auth: MCPAuthConfig
    timeout: int = 30
    enabled: bool = True
    endpoint: str = "/sse"  # NUEVO: Configurable con default
```

**Paso 2:** Usar en cliente
```python
# backoffice/mcp/client.py
async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        response = await self.client.post(
            self.server_config.endpoint,  # Usar config
            json={...}
        )
```

**Paso 3:** Actualizar YAML (opcional, usa default)
```yaml
# backoffice/config/mcp_servers.yaml
mcp_servers:
  - id: expedientes
    ...
    endpoint: /sse  # Opcional, ya es el default
```

**Esfuerzo:** 5 minutos
**Impacto:** Flexibilidad de configuración
**Archivos:** 2

---

### 6. Externalizar configuración JWT

**Archivos:**
- `backoffice/config.py` (nuevo contenido)
- `backoffice/auth/jwt_validator.py`

**Problema:**
Valores JWT hardcodeados:
- `"agentix-bpmn"` (issuer)
- `"Automático"` (subject)
- `"agentix-mcp-expedientes"` (audience)

**Solución:**

**Paso 1:** Añadir configuración
```python
# backoffice/config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Existing
    MCP_CONFIG_PATH: str = "backoffice/config/mcp_servers.yaml"
    LOG_DIR: str = "logs"
    JWT_SECRET: str = "change-me-in-production"

    # NUEVO: JWT validation
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPECTED_ISSUER: str = "agentix-bpmn"
    JWT_EXPECTED_SUBJECT: str = "Automático"
    JWT_REQUIRED_AUDIENCE: str = "agentix-mcp-expedientes"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

**Paso 2:** Modificar validator
```python
# backoffice/auth/jwt_validator.py
from backoffice.config import settings

def validate_jwt(
    token: str,
    secret: str,
    algorithm: str,
    expected_expediente_id: str,
    required_permissions: List[str] = None,
    # NUEVO: Parámetros opcionales con defaults de config
    expected_issuer: str = None,
    expected_subject: str = None,
    required_audience: str = None
) -> JWTClaims:
    # Usar config si no se proporciona
    expected_issuer = expected_issuer or settings.JWT_EXPECTED_ISSUER
    expected_subject = expected_subject or settings.JWT_EXPECTED_SUBJECT
    required_audience = required_audience or settings.JWT_REQUIRED_AUDIENCE

    ...

    if claims.iss != expected_issuer:
        raise JWTValidationError(...)
```

**Paso 3:** Crear .env.example
```bash
# .env.example
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPECTED_ISSUER=agentix-bpmn
JWT_EXPECTED_SUBJECT=Automático
JWT_REQUIRED_AUDIENCE=agentix-mcp-expedientes
```

**Esfuerzo:** 30 minutos
**Impacto:** Flexibilidad y seguridad (secret en .env)
**Archivos:** 3

---

### 7. Ampliar patrones PII - Teléfonos fijos

**Archivo:** `backoffice/logging/pii_redactor.py`

**Problema:**
Solo detecta móviles (6xx, 7xx, 9xx), no fijos (8xx, 91x, 93x).

**Solución:**
```python
class PIIRedactor:
    PATTERNS: Dict[str, Pattern] = {
        "dni": re.compile(r'\b\d{8}[A-Z]\b'),
        "nie": re.compile(r'\b[XYZ]\d{7}[A-Z]\b'),
        "email": re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'),
        # ACTUALIZADO: Móviles y fijos
        "telefono": re.compile(r'\b[6-9]\d{8}\b'),  # Móviles: 6xx, 7xx, 8xx, 9xx
        "iban": re.compile(r'\bES\d{22}\b'),
        "tarjeta": re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
        "ccc": re.compile(r'\b\d{20}\b'),
    }
```

**Nota:** El patrón `[6-9]\d{8}` ya incluye 8xx (fijos), solo falta documentar.

**Mejora adicional:**
```python
# Opción más explícita
"telefono_movil": re.compile(r'\b[67]\d{8}\b'),    # 6xx, 7xx
"telefono_fijo": re.compile(r'\b[89]\d{8}\b'),     # 8xx, 9xx
```

**Tests adicionales:**
```python
def test_pii_redactor_telefono_fijo():
    """Verifica que teléfonos fijos se redactan"""
    mensaje = "Contacto: 912345678"
    redacted = PIIRedactor.redact(mensaje)
    assert "912345678" not in redacted
    assert "[TELEFONO-REDACTED]" in redacted or "[TELEFONO_FIJO-REDACTED]" in redacted
```

**Esfuerzo:** 15 minutos
**Impacto:** Mayor cobertura de PII
**Archivos:** 2 (redactor + tests)

---

## P3 - Prioridad Baja (7 horas)

### 8. Optimizar regex de PII

**Archivo:** `backoffice/logging/pii_redactor.py`

**Problema:**
7 pases de regex por cada mensaje de log.

**Solución:**
```python
import re
from typing import Dict, Pattern

class PIIRedactor:
    # Regex combinada con grupos nombrados
    COMBINED_PATTERN = re.compile(
        r'(?P<dni>\b\d{8}[A-Z]\b)|'
        r'(?P<nie>\b[XYZ]\d{7}[A-Z]\b)|'
        r'(?P<email>\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b)|'
        r'(?P<telefono>\b[6-9]\d{8}\b)|'
        r'(?P<iban>\bES\d{22}\b)|'
        r'(?P<tarjeta>\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b)|'
        r'(?P<ccc>\b\d{20}\b)',
        re.IGNORECASE
    )

    @classmethod
    def redact(cls, text: str) -> str:
        """Redacta PII en un solo pase de regex"""
        def replacer(match):
            for pii_type, value in match.groupdict().items():
                if value:
                    return f'[{pii_type.upper()}-REDACTED]'
            return match.group(0)

        return cls.COMBINED_PATTERN.sub(replacer, text)
```

**Benchmark recomendado:**
```python
import timeit

# Test con mensaje largo
mensaje = "Solicitante Juan DNI 12345678A email juan@example.com tel 612345678" * 100

# Versión actual (7 pases)
t1 = timeit.timeit(lambda: PIIRedactor.redact(mensaje), number=1000)

# Versión optimizada (1 pase)
t2 = timeit.timeit(lambda: PIIRedactorOptimized.redact(mensaje), number=1000)

print(f"Mejora: {(t1/t2):.2f}x más rápido")
```

**Esfuerzo:** 1 hora
**Impacto:** Performance (no crítico para Paso 1)
**Archivos:** 1

---

### 9. Buffering de logs

**Archivo:** `backoffice/logging/audit_logger.py`

**Problema:**
Escritura síncrona a disco en cada log (I/O blocking).

**Solución:**
```python
import asyncio
from collections import deque
from pathlib import Path

class AuditLogger:
    def __init__(self, expediente_id: str, agent_run_id: str, log_dir: Path,
                 buffer_size: int = 10, flush_interval: float = 1.0):
        self.expediente_id = expediente_id
        self.agent_run_id = agent_run_id
        self.log_dir = Path(log_dir)
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval

        self._buffer = deque(maxlen=buffer_size)
        self._flush_task = None

        # Crear directorio
        self.log_file = self.log_dir / expediente_id / f"{agent_run_id}.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    async def log(self, mensaje: str, metadata: Dict[str, Any] = None):
        """Log asíncrono con buffering"""
        timestamp = datetime.now(timezone.utc).isoformat()
        mensaje_redactado = PIIRedactor.redact(mensaje)

        entry = {
            "timestamp": timestamp,
            "mensaje": mensaje_redactado,
            "metadata": metadata
        }

        self._buffer.append(entry)

        # Flush si buffer lleno
        if len(self._buffer) >= self.buffer_size:
            await self._flush()

    async def _flush(self):
        """Escribe buffer a disco"""
        if not self._buffer:
            return

        entries = list(self._buffer)
        self._buffer.clear()

        with open(self.log_file, "a", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    async def close(self):
        """Flush final al cerrar"""
        await self._flush()
```

**Esfuerzo:** 2 horas
**Impacto:** Performance en alto volumen (no crítico para Paso 1)
**Archivos:** 2 (logger + tests)

---

### 10. Carga dinámica de agentes desde configuración

**Archivos:**
- `backoffice/config/agents.yaml` (nuevo)
- `backoffice/agents/registry.py`

**Problema:**
Registry hardcodea nombres de agentes.

**Solución:**

**Paso 1:** Crear configuración
```yaml
# backoffice/config/agents.yaml
agents:
  - id: validador_documental
    name: ValidadorDocumental
    module: backoffice.agents.validador_documental
    class: ValidadorDocumental
    enabled: true

  - id: analizador_subvencion
    name: AnalizadorSubvencion
    module: backoffice.agents.analizador_subvencion
    class: AnalizadorSubvencion
    enabled: true

  - id: generador_informe
    name: GeneradorInforme
    module: backoffice.agents.generador_informe
    class: GeneradorInforme
    enabled: true
```

**Paso 2:** Registry dinámico
```python
# backoffice/agents/registry.py
import yaml
import importlib
from pathlib import Path
from typing import Dict, Type
from .base import AgentMock

class AgentRegistry:
    _agents: Dict[str, Type[AgentMock]] = {}

    @classmethod
    def load_from_config(cls, config_path: str):
        """Carga agentes desde configuración YAML"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        for agent_config in config['agents']:
            if not agent_config['enabled']:
                continue

            # Importar dinámicamente
            module = importlib.import_module(agent_config['module'])
            agent_class = getattr(module, agent_config['class'])

            cls._agents[agent_config['name']] = agent_class

    @classmethod
    def get_agent_class(cls, nombre: str) -> Type[AgentMock]:
        """Retorna clase de agente por nombre"""
        if not cls._agents:
            cls.load_from_config("backoffice/config/agents.yaml")

        if nombre not in cls._agents:
            raise KeyError(f"Agente '{nombre}' no encontrado. Disponibles: {list(cls._agents.keys())}")

        return cls._agents[nombre]

# Función de compatibilidad
def get_agent_class(nombre: str) -> Type[AgentMock]:
    return AgentRegistry.get_agent_class(nombre)
```

**Esfuerzo:** 4 horas
**Impacto:** Extensibilidad futura
**Archivos:** 3 (config YAML, registry, tests)

---

## Orden de Implementación Recomendado

### Sprint 1: Quick Wins (9 minutos) ⚡
1. Timezone UTC en run_id (2 min)
2. Logger vs print (2 min)
3. Endpoint MCP a config (5 min)

### Sprint 2: Tests Críticos (3 horas)
4. Tests integración MCP (2h)
5. Tests unitarios JWT (1h)

### Sprint 3: Configuración (45 minutos)
6. Externalizar config JWT (30 min)
7. Ampliar PII teléfonos (15 min)

### Sprint 4: Optimizaciones (Futuro - 7h)
8. Optimizar regex PII (1h)
9. Buffering logs (2h)
10. Carga dinámica agentes (4h)

---

## Checklist de Implementación

### Antes de Paso 2 (Mínimo)
- [ ] Timezone UTC en run_id
- [ ] Logger vs print
- [ ] Endpoint MCP a config
- [ ] Tests integración MCP
- [ ] Tests unitarios JWT

### Antes de Pre-Producción
- [ ] Externalizar config JWT
- [ ] Ampliar PII teléfonos
- [ ] .env.example con todos los settings

### Optimizaciones Futuras
- [ ] Optimizar regex PII
- [ ] Buffering logs
- [ ] Carga dinámica agentes

---

## Tracking de Progreso

| # | Mejora | Prioridad | Estado | Completado |
|---|--------|-----------|--------|------------|
| 1 | Timezone UTC | P1 | ⏳ Pendiente | - |
| 2 | Tests MCP | P1 | ⏳ Pendiente | - |
| 3 | Tests JWT | P1 | ⏳ Pendiente | - |
| 4 | Logger vs print | P2 | ⏳ Pendiente | - |
| 5 | Endpoint config | P2 | ⏳ Pendiente | - |
| 6 | Config JWT | P2 | ⏳ Pendiente | - |
| 7 | PII teléfonos | P2 | ⏳ Pendiente | - |
| 8 | Optimizar regex | P3 | ⏳ Pendiente | - |
| 9 | Buffer logs | P3 | ⏳ Pendiente | - |
| 10 | Dynamic agents | P3 | ⏳ Pendiente | - |

**Leyenda:**
- ⏳ Pendiente
- 🔨 En progreso
- ✅ Completado
- ⏸️ En espera

---

**Creado:** 2025-12-05
**Última actualización:** 2025-12-05
**Siguiente revisión:** Al completar Paso 2
