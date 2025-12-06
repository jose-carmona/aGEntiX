# aGEntiX - Back-Office de Agentes IA (Paso 1)

Sistema de back-office para agentes IA que automatizan tareas en expedientes administrativos, con arquitectura multi-MCP plug-and-play.

## Estado del Proyecto

**Fase actual:** Paso 1 - Esqueleto Mock Funcional ✅

Este paso implementa un sistema funcional con agentes mock que:
- ✅ Valida JWT con todos los claims obligatorios
- ✅ Arquitectura multi-MCP plug-and-play (solo MCP Expedientes habilitado)
- ✅ Routing automático de herramientas entre MCPs
- ✅ Conecta con servidor MCP real vía JSON-RPC 2.0
- ✅ Propaga errores estructurados (sin reintentos)
- ✅ Redacta automáticamente PII en logs (GDPR/LOPD/ENS)
- ✅ Auditoría completa con logs estructurados
- ✅ Tres agentes mock funcionales

## Características

### Arquitectura Multi-MCP Plug-and-Play

El sistema está diseñado para soportar múltiples servidores MCP mediante configuración:

```yaml
# backoffice/config/mcp_servers.yaml
mcp_servers:
  - id: expedientes
    enabled: true  # Activo en Paso 1

  - id: firma
    enabled: false  # Futuro

  - id: notificaciones
    enabled: false  # Futuro
```

**Para añadir un nuevo MCP:** Solo editar el YAML y cambiar `enabled: true`. Sin cambios en código.

### Componentes Principales

- **AgentExecutor**: Orquestador principal
- **MCPClientRegistry**: Routing automático entre MCPs
- **MCPClient**: Cliente bajo nivel por servidor MCP
- **AuditLogger**: Logging con redacción automática de PII
- **PIIRedactor**: Protección de datos personales (GDPR/LOPD/ENS)

### Agentes Mock Disponibles

1. **ValidadorDocumental**: Valida documentación completa
2. **AnalizadorSubvencion**: Analiza requisitos de subvención
3. **GeneradorInforme**: Genera informes del expediente

## Instalación

### Requisitos

- Python 3.11+
- Servidor MCP Expedientes ejecutándose en `http://localhost:8000`

### Pasos

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar variables de entorno
cp .env .env.local
# Editar .env con tu JWT_SECRET

# 3. El sistema está listo para usar
```

## Uso

### Ejecutar un Agente

```python
import asyncio
from backoffice.executor import AgentExecutor
from backoffice.models import AgentConfig
from backoffice.config import settings

async def main():
    # 1. Crear executor
    executor = AgentExecutor(
        mcp_config_path=settings.MCP_CONFIG_PATH,
        log_dir=settings.LOG_DIR,
        jwt_secret=settings.JWT_SECRET
    )

    # 2. Configurar agente
    agent_config = AgentConfig(
        nombre="ValidadorDocumental",
        system_prompt="Eres un validador de documentación",
        modelo="claude-3-5-sonnet-20241022",
        prompt_tarea="Valida que todos los documentos estén presentes",
        herramientas=["consultar_expediente", "actualizar_datos", "añadir_anotacion"]
    )

    # 3. Generar token JWT (usar mcp-expedientes/generate_token.py)
    token = "eyJ..."  # Token JWT válido

    # 4. Ejecutar agente
    resultado = await executor.execute(
        token=token,
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-VALIDAR-DOC-001",
        agent_config=agent_config
    )

    # 5. Verificar resultado
    if resultado.success:
        print(f"✅ Agente ejecutado: {resultado.agent_run_id}")
        print(f"   Mensaje: {resultado.resultado['mensaje']}")
        print(f"   Herramientas usadas: {resultado.herramientas_usadas}")
        print("\n📋 Log de auditoría:")
        for log in resultado.log_auditoria:
            print(f"   - {log}")
    else:
        print(f"❌ Error: {resultado.error.codigo}")
        print(f"   {resultado.error.mensaje}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Generar Token JWT

```bash
cd mcp-mock/mcp-expedientes
python -m mcp_expedientes.generate_token EXP-2024-001
```

## Estructura del Proyecto

```
backoffice/
├── executor.py                 # AgentExecutor (punto de entrada)
├── models.py                   # Modelos Pydantic
├── config.py                   # Configuración
├── auth/
│   └── jwt_validator.py        # Validación JWT
├── agents/
│   ├── base.py                 # Clase base
│   ├── registry.py             # Registro de agentes
│   ├── validador_documental.py
│   ├── analizador_subvencion.py
│   └── generador_informe.py
├── config/
│   ├── models.py               # Modelos configuración MCP
│   └── mcp_servers.yaml        # Catálogo de MCPs
├── mcp/
│   ├── client.py               # Cliente MCP (bajo nivel)
│   ├── registry.py             # MCPClientRegistry (routing)
│   └── exceptions.py
├── logging/
│   ├── pii_redactor.py         # Redactor PII (GDPR/LOPD)
│   └── audit_logger.py         # Logger auditoría
└── tests/
    ├── conftest.py
    ├── test_jwt_validator.py   # Tests JWT (19 tests)
    └── test_logging.py         # Tests PII (10 tests)
```

## Tests

### Ejecutar Tests

```bash
# Todos los tests del proyecto
./run-tests.sh

# Solo tests de Back-Office
./run-tests.sh --backoffice-only

# Tests con verbose
./run-tests.sh -v

# Tests específicos
pytest backoffice/tests/ -v
```

**Suite actual:** 29 tests (19 JWT + 10 PII)

### Tests de Validación JWT (19 tests)

Tests de seguridad para autenticación y permisos:

```bash
pytest backoffice/tests/test_jwt_validator.py -v
```

Verifican:
- ✅ Token expirado/inválido/mal formado rechazados
- ✅ Firma inválida rechazada
- ✅ Issuer, subject, audiencia correctos
- ✅ Expediente autorizado coincide
- ✅ Permisos suficientes para herramientas
- ✅ Mapeo correcto de herramientas a permisos

### Tests Obligatorios de PII (10 tests)

Los tests en `test_logging.py` son **CRÍTICOS** para cumplimiento normativo:

```bash
pytest backoffice/tests/test_logging.py -v
```

Verifican que:
- ✅ DNIs, emails, IBANs, teléfonos se redactan automáticamente
- ✅ La metadata también se redacta
- ✅ Múltiples PIIs en un mensaje se redactan correctamente
- ✅ Los logs escritos NO contienen datos personales

## Cumplimiento Normativo

### GDPR/LOPD/ENS

El sistema implementa:

- **Redacción automática de PII** en logs
- **Protección de datos personales**: DNI, email, IBAN, teléfono, NIE, tarjeta, CCC
- **Logs estructurados** en JSON lines
- **Control de acceso** a logs por expediente
- **Retención de logs**: 365 días según normativa

### Patrones Redactados

- DNI: `12345678A` → `[DNI-REDACTED]`
- Email: `juan@example.com` → `[EMAIL-REDACTED]`
- IBAN: `ES1234567890123456789012` → `[IBAN-REDACTED]`
- Teléfono: `612345678` → `[TELEFONO-REDACTED]`
- NIE: `X1234567Z` → `[NIE-REDACTED]`

## Añadir Nuevo MCP (Futuro)

Para añadir MCP de Firma cuando esté disponible:

1. Editar `backoffice/config/mcp_servers.yaml`:

```yaml
  - id: firma
    name: "MCP Firma Electrónica"
    url: http://mcp-firma:8001
    enabled: true  # ⬅️ Cambiar a true
```

2. Reiniciar el servicio (NO cambios en código)

3. El agente puede ahora usar tools de firma:

```python
await mcp_registry.call_tool("firmar_documento", {...})
# El registry automáticamente hace routing al MCP firma
```

## Arquitectura

### Flujo de Ejecución

```
1. BPMN genera JWT con claims completos
2. AgentExecutor recibe request
3. Valida JWT (issuer, subject, audience, exp_id, permisos)
4. Carga configuración MCPs desde YAML
5. Crea MCPClientRegistry (solo MCPs habilitados)
6. Registry descubre tools disponibles
7. Crea agente mock según configuración
8. Agente ejecuta llamando registry.call_tool()
9. Registry hace routing automático al MCP correcto
10. Logs se escriben con PII redactada automáticamente
11. Retorna resultado con logs de auditoría
```

### Principios de Diseño

1. **No Acoplamiento**: Independiente de GEX
2. **Mínimo Privilegio**: JWT valida expediente y permisos
3. **Auditoría Completa**: Logs de todos los pasos
4. **Propagación de Permisos**: JWT sin modificar al MCP
5. **Plug-and-Play**: Nuevos MCPs por configuración

## Variables de Entorno

```bash
# JWT (mismo secret que el servidor MCP)
JWT_SECRET=tu-clave-secreta
JWT_ALGORITHM=HS256

# MCP Configuration
MCP_CONFIG_PATH=backoffice/config/mcp_servers.yaml

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs/agent_runs
```

## Próximos Pasos

### Paso 2: API REST con FastAPI

- Endpoint `POST /api/v1/agent/execute`
- Trabajos asíncronos (background tasks)
- Webhooks para notificar a BPMN
- Métricas (Prometheus)
- Documentación OpenAPI

### Paso 3: Agentes Reales

- Integración LangGraph/CrewAI
- LLMs reales (Anthropic Claude)
- Razonamiento dinámico
- Sistema multi-paso
- Mantiene interfaz `AgentExecutor`

### Paso 4: Escalabilidad Horizontal

- Celery + Redis
- Múltiples workers
- Load balancing automático

## Documentación Adicional

Ver `/doc/index.md` para documentación completa del sistema GEX y arquitectura de aGEntiX.
