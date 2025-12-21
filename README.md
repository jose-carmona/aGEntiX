# aGEntiX

**Sistema de Agentes IA para Automatización de Workflows Administrativos en GEX**

## Descripción

**aGEntiX** es un sistema que permite la integración de agentes de inteligencia artificial con GEX (Gestión de Expedientes) para automatizar tareas específicas dentro de los flujos de trabajo administrativos, manteniendo límites estrictos en la autoridad de toma de decisiones y garantizando la supervisión humana donde sea necesaria.

GEX es la aplicación central de gestión administrativa desarrollada por Eprinsa (Empresa Provincial de Informática de la Excma. Diputación Provincial de Córdoba, España), y constituye el núcleo vertebrador de la administración electrónica en la provincia de Córdoba, utilizado tanto por el sector público institucional de la Diputación como por la práctica totalidad de los Ayuntamientos de la provincia.

## Estado del Proyecto

**Fase actual:** Paso 3 - Frontend Dashboard (Fase 1: Autenticación) ✅ COMPLETADO

### Implementado

#### Paso 1: Back-Office Mock ✅

Sistema funcional con agentes mock que demuestra la arquitectura completa:

- ✅ **Validación JWT completa** con 10 claims obligatorios (issuer, subject, audience, exp_id, permisos)
- ✅ **Arquitectura multi-MCP plug-and-play** (solo MCP Expedientes habilitado, otros por configuración)
- ✅ **MCPClientRegistry** con routing automático de herramientas entre MCPs
- ✅ **Conexión a servidores MCP reales** vía JSON-RPC 2.0 sobre HTTP/SSE
- ✅ **Propagación de errores estructurados** con códigos semánticos
- ✅ **Redacción automática de PII** en logs (8 tipos: DNI, NIE, email, teléfonos, IBAN, tarjetas, CCC)
- ✅ **Auditoría completa** con logs estructurados JSON lines
- ✅ **3 agentes mock funcionales** (validador documental, analizador subvención, generador informe)
- ✅ **Suite de 86 tests** (19 JWT + 15 MCP + 12 PII + 33 unitarios) - 100% PASS
- ✅ **Configuración externalizada** (.env para secrets, YAML para MCPs)

Ver [code-review/commit-c039abe](code-review/commit-c039abe/) para análisis detallado.

#### Paso 2: API REST con FastAPI ✅

API REST profesional para ejecución asíncrona de agentes:

- ✅ **6 endpoints RESTful** (execute, status, health, info, metrics, docs)
- ✅ **Ejecución asíncrona** con FastAPI BackgroundTasks y timeouts configurables
- ✅ **Webhooks automáticos** para notificar a BPMN al completar
- ✅ **Seguridad JWT** con validación completa en endpoints de agentes
- ✅ **Protección SSRF** en webhook_url (previene localhost, IPs privadas, require HTTPS en producción)
- ✅ **Métricas Prometheus** para observabilidad
- ✅ **Documentación OpenAPI** interactiva con Swagger UI
- ✅ **Task tracking** en memoria thread-safe con cleanup automático
- ✅ **Patrón lifespan moderno** (migrado de `on_event` deprecado)
- ✅ **Configuración flexible** vía variables de entorno
- ✅ **Suite de 22 tests** de API (health, agent endpoints, webhook validation) - 100% PASS

Ver [code-review/commit-64fda4d](code-review/commit-64fda4d/) para análisis detallado y plan de mejoras (2/11 implementadas: P1.1 y P2.1).

#### Paso 3 - Fase 1: Sistema de Autenticación Frontend ✅

Dashboard web con autenticación para gestión y monitorización del sistema:

- ✅ **Frontend React + TypeScript** con Vite y TailwindCSS
- ✅ **Sistema de Autenticación Dual**:
  - Token de Admin (API_ADMIN_TOKEN) para acceso al dashboard
  - JWT de Agente (ya existente) para ejecutar agentes
- ✅ **Endpoints de Autenticación**:
  - `POST /api/v1/auth/validate-admin-token` - Validar token de admin
  - Middleware de protección de endpoints del dashboard
- ✅ **Componentes UI Base**:
  - Login page con validación y manejo de errores
  - Layout con Header y Sidebar
  - ProtectedRoute para rutas privadas
  - Card, Button, Input (componentes reutilizables)
- ✅ **Configuración para Desarrollo**:
  - Vite configurado para GitHub Codespaces (`host: true`)
  - CORS configurado para frontend (puerto 5173)
  - Tipos TypeScript para `import.meta.env`
  - Interceptor HTTP con token automático
- ✅ **Páginas Implementadas**:
  - Login (funcional) con token: `agentix-admin-dev-token-2024`
  - Dashboard (placeholder para Fase 2)
  - Logs (placeholder para Fase 3)
  - TestPanel (placeholder para Fase 4)

Ver [doc/paso-3-fase-1-autenticacion.md](doc/paso-3-fase-1-autenticacion.md) para documentación completa, problemas resueltos y próximas fases.

#### Mejoras de Robustez y Error Handling ✅

Sistema fortalecido con manejo completo de errores y casos edge:

- ✅ **15 tests de error handling** (12 activos + 3 skip para futuro)
  - Errores MCP (conexión, timeout, tools, auth, conflict 409)
  - Errores JWT (formato inválido, firma incorrecta)
  - Errores de webhook (retry con exponential backoff)
  - Errores de agente (crashes, configuración inválida)
  - Errores de PII redaction (datos inválidos)
- ✅ **Webhook retry logic** con exponential backoff (3 intentos, factor 2.0)
- ✅ **PII redactor robusto** que maneja None, bytes inválidos, tipos incorrectos
- ✅ **Manejo HTTP 409 Conflict** para detección de modificación concurrente
- ✅ **Código de error MCP_CONFLICT** agregado al catálogo

**Commits recientes:**
- `ae55815` - Mejorar suite de tests: 7 fases de refactorización completadas
- `bfea795` - Reorganizar código bajo /src con estructura plana
- `fea91f8` - Estado actual antes de reorganización /src
- `(actual)` - Implementar tests de error handling (ERROR-1 a ERROR-15)

### Calidad del Código

- **Tests:** 166/170 PASS (97.6%) - 87 backoffice + 22 API + 34 MCP + 12 contracts + 15 error handling
  - 166 tests activos pasando
  - 4 tests skip (1 MCP SSE + 3 error handling futuro)
  - 0 tests fallando ✅
- **Cobertura PII:** 8 tipos de datos personales redactados (con error handling robusto)
- **Vulnerabilidades:** 0
- **Seguridad:** OWASP A10:2021 (SSRF) mitigado
- **Resiliencia:** Manejo completo de errores MCP, JWT, webhooks, agentes
- **Cumplimiento:** GDPR Art. 32, LOPD, ENS
- **Calidad promedio:** 4.7/5 ⭐⭐⭐⭐⭐

## Concepto Central

La propuesta de aGEntiX introduce un nuevo tipo de acción en el modelo BPMN de GEX: las **acciones de tipo Agente**. Este enfoque permite:

- **Automatizar tareas operativas**: Extracción de información de documentos entrantes y generación avanzada de documentos contextualizados
- **Asistir en análisis de información**: Proporcionar resúmenes, identificar patrones y elementos relevantes para ayudar en la toma de decisiones
- **Mantener supervisión humana**: Las decisiones legales y análisis normativos permanecen exclusivamente en manos de funcionarios humanos
- **Arquitectura desacoplada**: Los agentes IA no están acoplados directamente a GEX, permitiendo evolución independiente de componentes

## Objetivos del Proyecto

### 1. Automatizar tareas administrativas de bajo riesgo

Reducir la carga de trabajo manual del personal administrativo en tareas repetitivas que no requieren decisiones complejas, pero superan las capacidades de los sistemas de automatización tradicionales basados en plantillas.

### 2. Asistir en el análisis de información sin reemplazar el juicio humano

Proporcionar herramientas de análisis y síntesis de información que aceleren la revisión de documentación, manteniendo el control y responsabilidad final en manos del funcionario humano.

### 3. Garantizar integración segura y desacoplada

Implementar una arquitectura con permisos granulares, trazabilidad completa y acceso a través de Model Context Protocol (MCP), que permita actualizaciones independientes sin modificar el núcleo de GEX.

### 4. Adoptar un enfoque conservador

Comenzar con casos de uso de bajo riesgo, establecer límites claros en la toma de decisiones, y permitir evolución gradual del sistema según se gane experiencia y confianza.

### 5. Crear un sistema modular, escalable y reutilizable

Desarrollar agentes configurables que puedan adaptarse a diferentes tipos de procedimientos administrativos mediante parámetros como prompts de sistema, modelos LLM, herramientas disponibles y permisos específicos.

## Principios de Diseño

1. **No acoplamiento**: Los agentes IA no están acoplados a GEX, permitiendo evolución independiente
2. **Modularidad**: Componentes independientemente desplegables y actualizables
3. **Acceso vía MCP**: Información y herramientas accesibles mediante Model Context Protocol (estándar de la industria)
4. **Enfoque conservador**: Las decisiones legales permanecen exclusivamente humanas con supervisión obligatoria
5. **Auditoría completa**: Todos los pasos del agente quedan registrados para debugging, verificación y cumplimiento normativo

## Arquitectura Multi-MCP Plug-and-Play

El sistema está diseñado para soportar múltiples servidores MCP mediante configuración:

```yaml
# backoffice/config/mcp_servers.yaml
mcp_servers:
  - id: expedientes
    name: "MCP Expedientes"
    url: http://localhost:8000
    enabled: true  # ✅ Activo en Paso 1

  - id: firma
    name: "MCP Firma Electrónica"
    url: http://mcp-firma:8001
    enabled: false  # Futuro

  - id: notificaciones
    name: "MCP Notificaciones"
    url: http://mcp-notificaciones:8002
    enabled: false  # Futuro
```

**Para añadir un nuevo MCP:** Solo editar el YAML y cambiar `enabled: true`. Sin cambios en código.

### Componentes Principales

- **AgentExecutor**: Orquestador principal del sistema
- **MCPClientRegistry**: Routing automático de herramientas entre múltiples MCPs
- **MCPClient**: Cliente de bajo nivel para comunicación JSON-RPC 2.0 con servidores MCP
- **JWTValidator**: Validación completa de tokens (10 claims)
- **AuditLogger**: Logging estructurado con redacción automática de PII
- **PIIRedactor**: Protección de datos personales (GDPR/LOPD/ENS)

### Agentes Mock Disponibles

1. **ValidadorDocumental**: Valida documentación completa del expediente
2. **AnalizadorSubvencion**: Analiza requisitos y elegibilidad de subvención
3. **GeneradorInforme**: Genera informes estructurados del expediente

## Getting Started

### Opción Recomendada: Dev Container

El proyecto está configurado para usar **Dev Containers** de VS Code, que proporciona un entorno de desarrollo completamente configurado:

**Requisitos:**
- Docker Desktop instalado y ejecutándose
- Visual Studio Code con la extensión Dev Containers

**Inicio rápido:**
1. Abre el proyecto en VS Code
2. Haz clic en "Reopen in Container" cuando aparezca la notificación
3. Espera a que el container se construya (primera vez: ~5-10 min)
4. ¡Listo! El entorno incluye Python, Node.js, herramientas MCP y todas las dependencias

Ver [.devcontainer/README.md](.devcontainer/README.md) para documentación completa.

### Opción Alternativa: Instalación Local

```bash
# 1. Instalar dependencias del servidor MCP
cd src/mcp_mock/mcp_expedientes
pip install -r requirements.txt

# 2. Instalar dependencias del back-office
cd ../../
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con valores apropiados

# 4. Instalar herramientas MCP (opcional)
npm install -g @modelcontextprotocol/inspector
```

## Ejecución de Tests

El proyecto incluye un **script unificado v2.0** con configuración declarativa y opciones avanzadas:

```bash
# Ejecutar todos los tests (5 suites: API, MCP, Back-Office, Contracts, Error Handling)
./run-tests.sh

# ============================================================================
# SELECCIÓN DE SUITES
# ============================================================================

# Ejecutar suites específicas (NUEVO)
./run-tests.sh --suites=api,contracts
./run-tests.sh --suites=backoffice,error

# Excluir suites específicas (NUEVO)
./run-tests.sh --exclude=mcp
./run-tests.sh --exclude=mcp,backoffice

# Flags compatibles con versión anterior
./run-tests.sh --api-only
./run-tests.sh --mcp-only
./run-tests.sh --backoffice-only
./run-tests.sh --contracts-only      # NUEVO
./run-tests.sh --error-only          # NUEVO

# ============================================================================
# OPCIONES AVANZADAS
# ============================================================================

# Ejecutar con coverage (NUEVO - requiere pytest-cov)
./run-tests.sh --coverage

# Ejecutar en paralelo (NUEVO - requiere pytest-xdist)
./run-tests.sh --parallel

# Modo silencioso (NUEVO - solo muestra resultados finales)
./run-tests.sh --quiet

# Detener en el primer error de cualquier suite (NUEVO)
./run-tests.sh --fail-fast

# ============================================================================
# COMBINACIONES ÚTILES
# ============================================================================

# API y Contracts con coverage
./run-tests.sh --suites=api,contracts --coverage

# Todo excepto MCP en modo silencioso
./run-tests.sh --exclude=mcp --quiet

# Solo tests de autenticación con verbose
./run-tests.sh -k auth -v

# Re-ejecutar solo tests fallidos
./run-tests.sh --failed

# ============================================================================
# AYUDA Y UTILIDADES
# ============================================================================

# Ver todas las opciones disponibles
./run-tests.sh --help

# Listar suites disponibles
./run-tests.sh --list-suites
```

### Características del Script v2.0

- ✅ **Configuración declarativa**: Agregar nueva suite = 1 línea de código
- ✅ **Selección múltiple**: `--suites=api,contracts` o `--exclude=mcp`
- ✅ **Coverage integrado**: `--coverage` con pytest-cov
- ✅ **Ejecución paralela**: `--parallel` con pytest-xdist
- ✅ **Modo silencioso**: `--quiet` para CI/CD
- ✅ **Compatibilidad**: Todos los flags anteriores funcionan
- ✅ **Resumen detallado**: Muestra estado por suite automáticamente

### Suite de Tests Actual

**Total: 170 tests (166 PASS, 4 SKIP)**

#### Back-Office (87 tests)
- **19 tests JWT** - Validación de seguridad y autenticación
- **15 tests MCP** - Integración con servidores MCP
- **12 tests PII** - Cumplimiento normativo GDPR/LOPD/ENS
- **34 tests Executor** - Tests unitarios del AgentExecutor
- **7 tests Protocols** - Interfaces y abstracciones

#### API REST (22 tests)
- **4 tests Health** - Health check, metrics, docs
- **18 tests Agent Endpoints** - Execute, status, webhook validation, error handling

#### MCP Mock Expedientes (34 tests)
- **10 tests Auth** - Validación JWT en servidor MCP
- **7 tests Resources** - Recursos MCP (expedientes, documentos)
- **7 tests Server HTTP** - Servidor HTTP/SSE (1 skip SSE)
- **10 tests Tools** - Herramientas MCP (consulta, actualización)

#### Contracts (12 tests)
- **4 tests MCP Client** - Contract testing para MCPClient
- **4 tests Agent Registry** - Contract testing para AgentRegistry
- **4 tests Config Loader** - Contract testing para ConfigLoader

#### Error Handling (15 tests)
- **12 tests activos** - Manejo de errores MCP, JWT, webhook, agente, PII
- **3 tests skip** - Casos futuros (BD, OOM, rate limiting)

## Uso del Sistema

### Opción A: Dashboard Web (Recomendado - Paso 3)

La forma más intuitiva de usar aGEntiX es mediante el dashboard web:

#### 1. Iniciar Servidores

```bash
# Terminal 1: Backend API (puerto 8080)
python -m uvicorn src.api.main:app --reload --port 8080

# Terminal 2: Frontend Dashboard (puerto 5173)
cd frontend && npm run dev

# Terminal 3 (opcional): Servidor MCP Expedientes (puerto 8000)
cd src/mcp_mock/mcp_expedientes
python -m uvicorn server_http:app --reload --port 8000
```

#### 2. Acceder al Dashboard

- **GitHub Codespaces:**
  - Ve al panel **PORTS** en VS Code
  - Puerto **5173** → Haz clic en el ícono de globo 🌐

- **Local:**
  - `http://localhost:5173`

#### 3. Login

- **Token de desarrollo:** `agentix-admin-dev-token-2024`
- Introduce el token en la página de login
- Serás redirigido al dashboard

**Próximas fases del dashboard:**
- Fase 2: Dashboard de Métricas (gráficos, KPIs, auto-refresh)
- Fase 3: Visor de Logs en tiempo real
- Fase 4: Panel de Pruebas de Agentes

### Opción B: API REST (Programático)

Para integración programática o testing automatizado:

#### 1. Iniciar Servidor MCP Expedientes

```bash
cd src/mcp_mock/mcp_expedientes
python -m uvicorn mcp_expedientes.server_http:app --reload --port 8000
```

#### 2. Lanzar API REST

```bash
# Desarrollo con auto-reload
API_RELOAD=true ./run-api.sh

# Producción con múltiples workers
API_WORKERS=8 ./run-api.sh
```

La API estará disponible en `http://localhost:8080` con documentación interactiva en `http://localhost:8080/docs`.

#### 3. Ejecutar Agente vía API

```bash
# Generar token JWT válido
cd src/mcp_mock/mcp_expedientes
python -m mcp_expedientes.generate_token EXP-2024-001

# Ejecutar agente (reemplazar <TOKEN> con el token generado)
curl -X POST http://localhost:8080/api/v1/agent/execute \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "expediente_id": "EXP-2024-001",
    "tarea_id": "TAREA-001",
    "agent_config": {
      "nombre": "ValidadorDocumental",
      "system_prompt": "Eres un validador de documentación administrativa",
      "modelo": "claude-3-5-sonnet",
      "prompt_tarea": "Valida que todos los documentos requeridos estén presentes",
      "herramientas": ["consultar_expediente"]
    },
    "webhook_url": "http://example.com/callback",
    "timeout_seconds": 300
  }'

# Consultar estado (reemplazar <RUN_ID> con el ID retornado)
curl http://localhost:8080/api/v1/agent/status/<RUN_ID>
```

#### Endpoints Disponibles

- **POST** `/api/v1/agent/execute` - Ejecutar agente asíncronamente
- **GET** `/api/v1/agent/status/{run_id}` - Consultar estado de ejecución
- **GET** `/health` - Health check
- **GET** `/metrics` - Métricas Prometheus
- **GET** `/docs` - Documentación Swagger interactiva
- **GET** `/` - Info de la API

### Opción B: Uso Programático (Back-Office Directo)

Para integración avanzada o testing, puedes usar el back-office directamente:

#### 1. Iniciar Servidor MCP Expedientes

```bash
cd src/mcp_mock/mcp_expedientes
python -m uvicorn mcp_expedientes.server_http:app --reload --port 8000
```

#### 2. Ejecutar un Agente

```python
import asyncio
from backoffice.executor import AgentExecutor
from backoffice.models import AgentConfig
from backoffice.settings import settings

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
        system_prompt="Eres un validador de documentación administrativa",
        modelo="claude-3-5-sonnet-20241022",
        prompt_tarea="Valida que todos los documentos requeridos estén presentes",
        herramientas=["consultar_expediente", "actualizar_datos", "añadir_anotacion"]
    )

    # 3. Generar token JWT (usar generate_token.py)
    token = "eyJ..."  # Token JWT válido para EXP-2024-001

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

### 3. Generar Token JWT

```bash
cd src/mcp_mock/mcp_expedientes
python -m mcp_expedientes.generate_token EXP-2024-001
```

## Estructura del Proyecto

```
aGEntiX/
├── frontend/                        # Dashboard Web (Paso 3)
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/                # Autenticación (Login, ProtectedRoute, Logout)
│   │   │   ├── layout/              # Layout (Header, Sidebar)
│   │   │   └── ui/                  # Componentes UI (Card, Button, Input)
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx      # Contexto de autenticación
│   │   ├── pages/
│   │   │   ├── Login.tsx            # Página de login
│   │   │   ├── Dashboard.tsx        # Dashboard principal
│   │   │   ├── Logs.tsx             # Visor de logs (Fase 3)
│   │   │   └── TestPanel.tsx        # Panel de pruebas (Fase 4)
│   │   ├── services/
│   │   │   ├── api.ts               # Cliente HTTP con interceptors
│   │   │   └── authService.ts       # Servicio de autenticación
│   │   ├── types/                   # Tipos TypeScript
│   │   ├── App.tsx                  # Componente principal
│   │   └── main.tsx                 # Entry point
│   ├── vite.config.ts               # Configuración Vite
│   ├── tailwind.config.js           # Configuración TailwindCSS
│   ├── package.json                 # Dependencias npm
│   └── .env                         # VITE_API_URL
│
├── src/                             # Código fuente Python (estructura plana)
│   ├── api/                         # API REST con FastAPI (Paso 2)
│   │   ├── main.py                  # FastAPI app
│   │   ├── models.py                # Modelos Pydantic
│   │   ├── routers/                 # Endpoints REST
│   │   │   ├── auth.py              # Autenticación admin (Paso 3)
│   │   │   ├── agent.py             # Ejecución de agentes
│   │   │   └── health.py            # Health check
│   │   └── services/                # Servicios (webhook, task_tracker)
│   │
│   ├── backoffice/                  # Back-Office de Agentes IA (Paso 1)
│   │   ├── executor.py              # AgentExecutor (punto de entrada)
│   │   ├── models.py                # Modelos Pydantic
│   │   ├── settings.py              # Configuración con variables de entorno
│   │   ├── auth/
│   │   │   └── jwt_validator.py     # Validación JWT (10 claims)
│   │   ├── agents/
│   │   │   ├── base.py              # Clase base agentes
│   │   │   ├── registry.py          # Registro de agentes
│   │   │   ├── validador_documental.py
│   │   │   ├── analizador_subvencion.py
│   │   │   └── generador_informe.py
│   │   ├── config/
│   │   │   ├── models.py            # Modelos configuración MCP
│   │   │   └── mcp_servers.yaml     # Catálogo de servidores MCP
│   │   ├── mcp/
│   │   │   ├── client.py            # Cliente MCP (JSON-RPC 2.0)
│   │   │   ├── registry.py          # MCPClientRegistry (routing)
│   │   │   └── exceptions.py        # Excepciones MCP
│   │   └── logging/
│   │       ├── pii_redactor.py      # Redactor PII (GDPR/LOPD)
│   │       └── audit_logger.py      # Logger auditoría
│   │
│   └── mcp_mock/                    # Servidores MCP Mock (renombrado de mcp-mock)
│       └── mcp_expedientes/         # Servidor MCP Expedientes
│           ├── server_http.py       # Servidor HTTP/SSE
│           ├── server_stdio.py      # Servidor STDIO
│           ├── auth.py              # Validación JWT
│           ├── models.py            # Modelos de datos
│           ├── tools.py             # Tools MCP
│           ├── resources.py         # Resources MCP
│           ├── generate_token.py    # Generador de tokens
│           └── data/                # Datos mock
│               └── expedientes/
│
├── tests/                           # Tests organizados por componente
│   ├── api/                         # Tests de API REST (22 tests)
│   │   ├── test_health.py           # 4 tests health/metrics/docs
│   │   └── test_agent_endpoints.py  # 18 tests execute/status/webhook
│   ├── test_backoffice/             # Tests de Back-Office (87 tests)
│   │   ├── test_jwt_validator.py    # 19 tests JWT
│   │   ├── test_mcp_integration.py  # 15 tests MCP
│   │   ├── test_logging.py          # 12 tests PII
│   │   ├── test_executor.py         # 34 tests AgentExecutor
│   │   └── test_protocols.py        # 7 tests protocolos
│   ├── test_mcp/                    # Tests de MCP Mock (34 tests)
│   │   ├── test_auth.py             # 10 tests autenticación
│   │   ├── test_tools.py            # 10 tests tools
│   │   ├── test_resources.py        # 7 tests resources
│   │   └── test_server_http.py      # 7 tests servidor
│   ├── test_contracts/              # Tests de Contracts (12 tests)
│   │   └── test_interfaces.py  # 12 tests de interfaces y contratos
│   └── test_error_handling/         # Tests de Error Handling (15 tests)
│       └── test_resilience.py       # 12 activos + 3 skip
│
├── doc/                             # Documentación Zettelkasten
│   ├── index.md                     # Índice de temas
│   ├── memoria.md                   # Memoria del proyecto
│   └── [001-099].md                 # Notas interconectadas
│
├── code-review/                     # Code reviews por commit
│   ├── README.md                    # Estructura de reviews
│   ├── commit-c039abe/              # Review Paso 1
│   │   ├── README.md                # Resumen ejecutivo
│   │   ├── revision-commit-*.md     # Análisis detallado
│   │   ├── metricas.md              # Métricas de calidad
│   │   └── plan-mejoras.md          # Plan de mejoras (✅ 100% implementadas)
│   └── fix-*/                       # Reviews de fixes
│
├── setup.py                         # Configuración del paquete (package_dir="src")
├── conftest.py                      # Configuración global de pytest
├── .env.example                     # Template de configuración
├── run-tests.sh                     # Script unificado de tests (170 tests)
├── requirements.txt                 # Dependencias Python
└── README.md                        # Este archivo
```

**Nota sobre la estructura:**
- Todo el código Python está bajo `/src` siguiendo las mejores prácticas de Python
- Los tests están organizados bajo `/tests` en la raíz del proyecto
- Los nombres de directorios siguen PEP-8 (`mcp_mock` en lugar de `mcp-mock`)
- Los imports usan la estructura plana: `from backoffice.executor import AgentExecutor`

## Cumplimiento Normativo

### GDPR/LOPD/ENS

El sistema implementa protección de datos personales según normativa europea y española:

- **Redacción automática de PII** en todos los logs
- **8 tipos de datos protegidos**: DNI, NIE, email, teléfonos móviles, teléfonos fijos, IBAN, tarjetas, CCC
- **Logs estructurados** en JSON lines para auditoría
- **Control de acceso** a logs por expediente
- **Retención configurable** de logs
- **12 tests obligatorios** que verifican cumplimiento

### Patrones Redactados

| Dato Personal | Ejemplo | Redacción |
|---------------|---------|-----------|
| DNI | `12345678A` | `[DNI-REDACTED]` |
| NIE | `X1234567Z` | `[NIE-REDACTED]` |
| Email | `juan@example.com` | `[EMAIL-REDACTED]` |
| Teléfono móvil | `612345678` | `[TELEFONO_MOVIL-REDACTED]` |
| Teléfono fijo | `957123456` | `[TELEFONO_FIJO-REDACTED]` |
| IBAN | `ES1234...` | `[IBAN-REDACTED]` |
| Tarjeta | `4532...` | `[TARJETA-REDACTED]` |
| CCC | `12345678901234567890` | `[CCC-REDACTED]` |

## Configuración

### Variables de Entorno Backend (.env)

```bash
# JWT - Autenticación de Agentes (Paso 1)
JWT_SECRET=your-secret-key-here  # PRODUCCIÓN: openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_EXPECTED_ISSUER=agentix-bpmn
JWT_EXPECTED_SUBJECT=Automático
JWT_REQUIRED_AUDIENCE=agentix-mcp-expedientes

# Admin Authentication - Dashboard Web (Paso 3)
API_ADMIN_TOKEN=agentix-admin-dev-token-2024  # PRODUCCIÓN: python -c "import secrets; print(secrets.token_urlsafe(32))"

# CORS - Incluir puerto del frontend
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080,*

# MCP Configuration
MCP_CONFIG_PATH=backoffice/config/mcp_servers.yaml

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs/agent_runs
```

### Variables de Entorno Frontend (frontend/.env)

```bash
# URL del backend API
VITE_API_URL=http://localhost:8080
```

Ver [.env.example](.env.example) para documentación completa de configuración.

## Añadir Nuevo MCP (Futuro)

Para añadir MCP de Firma cuando esté disponible:

1. **Editar configuración** (`backoffice/config/mcp_servers.yaml`):

```yaml
  - id: firma
    name: "MCP Firma Electrónica"
    url: http://mcp-firma:8001
    enabled: true  # ⬅️ Cambiar a true
```

2. **Reiniciar el servicio** (NO requiere cambios en código)

3. **Usar en agentes**:

```python
# El registry automáticamente descubre y enruta herramientas
await mcp_registry.call_tool("firmar_documento", {
    "documento_id": "DOC-123",
    "tipo_firma": "avanzada"
})
```

## Próximos Pasos

### Paso 3 - Fase 2: Dashboard de Métricas (En Progreso)
- Endpoint `GET /api/v1/dashboard/metrics`
- Gráficos interactivos con Recharts
- KPIs del sistema (ejecuciones, tasa de éxito, performance)
- Auto-refresh cada 10 segundos
- Exportación de datos a CSV

### Paso 3 - Fase 3: Visor de Logs
- Endpoint `GET /api/v1/logs` con filtros
- Endpoint `GET /api/v1/logs/stream` (SSE)
- Sistema de filtros (nivel, componente, agente, fecha)
- Búsqueda de texto completo
- Resaltado de PII redactado

### Paso 3 - Fase 4: Panel de Pruebas de Agentes
- Endpoint `POST /api/v1/auth/generate-jwt`
- Selector de agentes disponibles
- Generador de JWT de prueba
- Visualización de resultados en tiempo real
- Historial de ejecuciones

### Paso 4: Agentes Reales con LLMs
- Integración LangGraph/CrewAI
- LLMs reales (Anthropic Claude, OpenAI)
- Razonamiento dinámico multi-paso
- Sistema de memoria y contexto
- Mantiene interfaz `AgentExecutor` (retrocompatible)

### Paso 5: Escalabilidad Horizontal
- Celery + Redis para cola de trabajos
- Múltiples workers concurrentes
- Load balancing automático
- Monitorización y métricas avanzadas

## Documentación

### Memoria del Proyecto

Para una visión completa y detallada del proyecto, consulta la [Memoria Inicial del Proyecto Capstone](doc/memoria.md) ([versión PDF](doc/memoria.pdf)), que incluye:

- Introducción contextualizada sobre GEX y la oportunidad de integración de IA
- Descripción detallada de los 5 objetivos principales del proyecto
- Análisis de viabilidad técnica y organizativa
- Clarificación del alcance: qué se automatiza y qué permanece exclusivamente humano

### Sistema de Notas Zettelkasten

La documentación técnica completa del proyecto está organizada en un sistema **Zettelkasten** en el directorio `/doc`, donde cada nota representa un concepto individual e incluye referencias a notas relacionadas.

**Punto de entrada**: [doc/index.md](doc/index.md)

**Temas principales cubiertos:**

- **Sistema GEX**: Componentes, flujos de información e integraciones → [doc/001-gex-definicion.md](doc/001-gex-definicion.md)
- **Automatización de Tareas**: Tipos de tareas y candidatas para IA → [doc/010-tipos-tareas.md](doc/010-tipos-tareas.md)
- **Modelo BPMN**: Estructura de workflows y acciones de agente → [doc/020-bpmn-modelo.md](doc/020-bpmn-modelo.md)
- **Agentes IA**: Configuración, contexto y auditoría → [doc/030-propuesta-agentes.md](doc/030-propuesta-agentes.md)
- **Arquitectura**: Criterios de diseño y acceso MCP → [doc/040-criterios-diseño.md](doc/040-criterios-diseño.md)
- **Permisos**: Sistema de permisos y propagación → [doc/050-permisos-agente.md](doc/050-permisos-agente.md)

### Code Reviews

Los code reviews del proyecto están organizados por commit en [code-review/](code-review/):

- **commit-c039abe**: Análisis completo del Paso 1 con métricas, plan de mejoras (100% implementado) y verificación de cumplimiento normativo

## Viabilidad del Proyecto

El proyecto se considera viable por las siguientes razones:

- **Base tecnológica sólida**: Utiliza tecnologías maduras (Python, FastAPI, Model Context Protocol) y modelos LLM disponibles comercialmente
- **Integración no invasiva**: El diseño desacoplado permite incorporar IA sin modificar el núcleo de GEX, reduciendo riesgos técnicos
- **Alcance acotado inicialmente**: El enfoque conservador limita el alcance inicial a tareas de bajo riesgo, permitiendo validación progresiva
- **Sistema de permisos existente**: GEX ya dispone de un sistema de permisos y un usuario "Automático" para acciones del sistema, que puede aprovecharse para los agentes IA
- **Infraestructura BPMN existente**: El modelo de workflows BPMN de GEX proporciona el marco estructural donde integrar las acciones de agente
- **Cumplimiento normativo demostrado**: Suite de tests garantiza GDPR/LOPD/ENS desde el diseño

## Licencia

Este proyecto es parte de un Capstone Project académico desarrollado para Eprinsa (Empresa Provincial de Informática de Córdoba).

## Contacto

Para preguntas sobre este proyecto, consulta la documentación en `/doc` o revisa los code reviews en `/code-review`.
