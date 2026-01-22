# aGEntiX

Sistema de Agentes IA para Automatización de Workflows Administrativos en GEX

## Descripción

**aGEntiX** es un sistema que permite la integración de agentes de inteligencia artificial con GEX (Gestión de Expedientes) para automatizar tareas específicas dentro de los flujos de trabajo administrativos, manteniendo límites estrictos en la autoridad de toma de decisiones y garantizando la supervisión humana donde sea necesaria.

GEX es la aplicación central de gestión administrativa desarrollada por Eprinsa (Empresa Provincial de Informática de la Excma. Diputación Provincial de Córdoba, España), y constituye el núcleo vertebrador de la administración electrónica en la provincia de Córdoba, utilizado tanto por el sector público institucional de la Diputación como por la práctica totalidad de los Ayuntamientos de la provincia.

## Estado del Proyecto

**Fase actual:** Paso 8 - MCP Documentación de Tipos de Expediente ✅ COMPLETADO

| Paso | Descripción | Estado |
|------|-------------|--------|
| 1-3 | Infraestructura (Back-Office, API, Frontend) | ✅ Completado |
| 4-6 | Agentes reales con CrewAI | ✅ Completado |
| 7-8 | MCPs adicionales (Documentos, Documentación) | ✅ Completado |
| 9-11 | Generador documentos, LangGraph | 🔜 Pendiente |
| 12 | Escalado horizontal (Celery + Redis) | ✅ Completado |

**Ver [ROADMAP.md](ROADMAP.md) para detalles completos de progreso y próximos pasos.**

## Concepto Central

La propuesta de aGEntiX introduce un nuevo tipo de acción en el modelo BPMN de GEX: las **acciones de tipo Agente**. Este enfoque permite:

- **Automatizar tareas operativas**: Extracción de información de documentos entrantes y generación avanzada de documentos contextualizados
- **Asistir en análisis de información**: Proporcionar resúmenes, identificar patrones y elementos relevantes para ayudar en la toma de decisiones
- **Mantener supervisión humana**: Las decisiones legales y análisis normativos permanecen exclusivamente en manos de funcionarios humanos
- **Arquitectura desacoplada**: Los agentes IA no están acoplados directamente a GEX, permitiendo evolución independiente de componentes

## Objetivos del Proyecto

### 1. Automatizar tareas administrativas de bajo riesgo

Reducir la carga de trabajo manual del personal administrativo en tareas repetitivas que no requieren decisiones complejas, pero superan las capacidades de los sistemas de automatización tradicionales basados en plantillas o en reglas.

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
    enabled: true  # ✅ Activo

  - id: documentacion
    name: "MCP Documentación"
    url: http://mcp-documentacion:8001
    enabled: false  # Futuro

  - id: notificaciones
    name: "MCP Notificaciones"
    url: http://mcp-notificaciones:8002
    enabled: false  # Futuro
```

**Para añadir un nuevo MCP:** Solo editar el YAML y cambiar `enabled: true`. Sin cambios en código.

## Componentes Principales

El Back-Office de agentes (`src/backoffice/`) se organiza en las siguientes capas:

### Orquestación

| Componente | Ubicación | Descripción |
|------------|-----------|-------------|
| **AgentExecutor** | `executor.py` | Orquestador principal. Coordina validación JWT, configuración MCP, logging y ejecución de agentes. Soporta inyección de dependencias para testing. |
| **ExecutorFactory** | `executor_factory.py` | Factory que crea AgentExecutor con implementaciones por defecto. Provee backward compatibility. |

### Autenticación

| Componente | Ubicación | Descripción |
|------------|-----------|-------------|
| **JWTValidator** | `auth/jwt_validator.py` | Valida tokens JWT con 10 claims obligatorios (iss, sub, aud, exp, iat, nbf, jti, exp_id, permisos, firma). |
| **JWTGenerator** | `auth/jwt_generator.py` | Genera tokens JWT para ejecución de agentes con los claims requeridos. |

### Model Context Protocol (MCP)

| Componente | Ubicación | Descripción |
|------------|-----------|-------------|
| **MCPClient** | `mcp/client.py` | Cliente HTTP dual (sync + async) para comunicación JSON-RPC 2.0 con servidores MCP. Manejo semántico de errores. |
| **MCPClientRegistry** | `mcp/registry.py` | Registro plug-and-play de clientes MCP. Discovery automático de tools y routing transparente. |

### Agentes CrewAI

| Componente | Ubicación | Descripción |
|------------|-----------|-------------|
| **AgentCrewAI** | `agents/base_real.py` | Clase base abstracta para agentes CrewAI. Gestiona LLM, tools MCP y ejecución de crews. |
| **AgentRegistry** | `agents/registry.py` | Registro centralizado de clases de agentes. Mapea nombres a implementaciones. |
| **MCPToolFactory** | `agents/mcp_tool_wrapper.py` | Factory que expone herramientas MCP como Tools de CrewAI con schemas dinámicos. |
| **SchemaBuilder** | `agents/schema_builder.py` | Construye modelos Pydantic dinámicamente desde JSON Schema (MCP → CrewAI). |

### Logging y Compliance

| Componente | Ubicación | Descripción |
|------------|-----------|-------------|
| **PIIRedactor** | `logging/pii_redactor.py` | Redacta automáticamente 8 tipos de PII (DNI, NIE, email, teléfonos, IBAN, tarjetas, CCC). Cumple GDPR/LOPD/ENS. |
| **AuditLogger** | `logging/audit_logger.py` | Genera logs estructurados en JSON lines. Integra PIIRedactor automáticamente. |

### Configuración

| Componente | Ubicación | Descripción |
|------------|-----------|-------------|
| **AgentConfigLoader** | `config/agent_config_loader.py` | Carga definiciones de agentes desde `agents.yaml`. Soporta agentes mock y CrewAI. |
| **MCPServersConfig** | `config/models.py` | Modelos Pydantic para configuración de servidores MCP desde `mcp_servers.yaml`. |

## Agentes Disponibles

### Agentes CrewAI (Reales)

1. **ClasificadorExpediente**: Clasifica expedientes por tipo usando IA
2. **RedactorSituacion**: Genera resúmenes de situación del expediente
3. **RedactorPropuestaResolucion**: Genera propuestas de resolución basadas en plantilla
4. **AgenteTestSimple**: Agente de prueba E2E (solo responde "OK")

### Componentes de Soporte

- **AgentCrewAI (base_real.py)**: Clase base para agentes CrewAI
- **MCPToolWrapper**: Expone herramientas MCP a CrewAI
- **SchemaBuilder**: Constructor de schemas para tools
- **AgentConfigLoader**: Carga configuraciones de agente desde YAML

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
# Ejecutar todos los tests (5 suites)
./run-tests.sh

# Selección de suites
./run-tests.sh --suites=api,contracts
./run-tests.sh --exclude=mcp

# Opciones avanzadas
./run-tests.sh --coverage      # Con coverage
./run-tests.sh --parallel      # En paralelo
./run-tests.sh --quiet         # Solo resultados
./run-tests.sh --fail-fast     # Detener en primer error

# Ayuda
./run-tests.sh --help
./run-tests.sh --list-suites
```

### Suite de Tests

**Total: 306 tests (300 PASS, 6 SKIP)**

| Suite | Tests | Descripción |
|-------|-------|-------------|
| Back-Office | 165 | JWT, MCP, PII, Executor, Protocols, Agents |
| API REST | 34 | Health, Agent endpoints, Webhooks |
| MCP Mock | 78 | Auth, Resources, Tools, Server |
| Contracts | 14 | Interfaces y contratos |
| Error Handling | 15 | Resilience (12 activos, 3 skip) |

## Uso del Sistema

### Verificación Rápida del Sistema

Para comprobar que todo el sistema funciona correctamente, usa el script `test-agent.sh` con el agente de prueba `AgenteTestSimple`:

```bash
# 1. Iniciar los servidores (en terminales separadas)
./run-api.sh                                    # API REST (puerto 8080) en una shell
./run-mcp.sh                                    # MCP (puerto 8001) en otra shell

# 2. Ejecutar test E2E
./test-agent.sh EXP-2024-001 AgenteTestSimple
```

El script automatiza todo el flujo:
1. Genera un token JWT válido
2. Lista los agentes disponibles
3. Ejecuta el agente seleccionado
4. Consulta el estado de la ejecución

**AgenteTestSimple** es un agente de prueba que solo responde "OK", útil para verificar que:
- La API REST responde correctamente
- La carga de agentes desde `agents.yaml` funciona
- CrewAI se invoca correctamente
- El pipeline completo de ejecución funciona

```bash
# Ejemplos de uso
./test-agent.sh                                  # Usa EXP-2024-001 y ValidadorDocumental
./test-agent.sh EXP-2024-002                     # Especifica expediente
./test-agent.sh EXP-2024-001 ClasificadorExpediente  # Especifica agente
./test-agent.sh EXP-2024-001 AgenteTestSimple    # Agente de prueba (solo responde OK)
```

### Scripts de Inicio

El proyecto incluye scripts para iniciar cada componente:

| Script | Puerto | Descripción |
|--------|--------|-------------|
| `./run-mcp.sh` | 8000 | MCP Mock Server (Expedientes) |
| `./run-api.sh` | 8080 | API REST FastAPI |
| `./run-celery.sh` | - | Celery Worker (requiere Redis) |
| `./run-flower.sh` | 5555 | Flower UI (monitoreo Celery) |
| `cd frontend && npm run dev` | 5173 | Frontend React |

**Modo desarrollo básico (sin Celery):**
```bash
# Terminal 1: MCP Mock
./run-mcp.sh

# Terminal 2: API
./run-api.sh

# Terminal 3: Frontend
cd frontend && npm run dev
```

**Modo desarrollo con Celery (escalable):**
```bash
# Terminal 1: Redis (si no está corriendo)
redis-server --daemonize yes

# Terminal 2: MCP Mock
./run-mcp.sh

# Terminal 3: Celery Worker
./run-celery.sh

# Terminal 4: Flower (opcional, monitoreo)
./run-flower.sh

# Terminal 5: API (con USE_CELERY=true en .env)
./run-api.sh

# Terminal 6: Frontend
cd frontend && npm run dev
```

**Variables de entorno para Celery (.env):**
```bash
USE_CELERY=true                              # Activar modo Celery
CELERY_BROKER_URL=redis://localhost:6379/0   # Redis broker
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Opción A: API REST (Recomendado para Integración)

Para integración programática o automatización:

#### 1. Iniciar Servidor MCP Expedientes

```bash
./run-mcp.sh
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
# Generar token JWT válido (desde la raíz del proyecto)
python3 -c "
import sys; sys.path.insert(0, 'src')
from backoffice.auth.jwt_generator import generate_jwt
result = generate_jwt(expediente_id='EXP-2024-001', permisos=['consulta', 'gestion'])
print(result.token)
"

# Ejecutar agente (reemplazar <TOKEN> con el token generado)
curl -X POST http://localhost:8080/api/v1/agent/execute \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "AgenteTestSimple",
    "context": {
      "expediente_id": "EXP-2024-001",
      "tarea_id": "TAREA-001"
    }
  }'

# Consultar estado (reemplazar <RUN_ID> con el ID retornado)
curl http://localhost:8080/api/v1/agent/status/<RUN_ID>
```

#### Endpoints Disponibles

- **GET** `/api/v1/agent/agents` - Listar agentes disponibles
- **POST** `/api/v1/agent/execute` - Ejecutar agente asíncronamente
- **GET** `/api/v1/agent/status/{run_id}` - Consultar estado de ejecución
- **GET** `/health` - Health check
- **GET** `/metrics` - Métricas Prometheus
- **GET** `/docs` - Documentación Swagger interactiva

### Opción B: Dashboard Web (Demostración)

El dashboard web permite visualizar y gestionar el sistema de forma interactiva:

**Inicio rápido:**

```bash
# Terminal 1: Backend API (puerto 8080)
./run-api.sh

# Terminal 2: Frontend Dashboard (puerto 5173)
cd frontend && npm run dev
```

**Acceso:**
- GitHub Codespaces: Panel PORTS → Puerto 5173 → Abrir en navegador
- Local: `http://localhost:5173`

**Login:** Token de desarrollo: `agentix-admin-dev-token-2024`

**Documentación completa del frontend:** Ver [frontend/README.md](frontend/README.md)

### Generar Token JWT

```bash
# Desde la raíz del proyecto
python3 -c "
import sys; sys.path.insert(0, 'src')
from backoffice.auth.jwt_generator import generate_jwt
result = generate_jwt(expediente_id='EXP-2024-001', permisos=['consulta', 'gestion'])
print(result.token)
"
```

O usar el script `test-agent.sh` que genera el token automáticamente.

## Estructura del Proyecto

```
aGEntiX/
├── frontend/                        # Dashboard Web
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/               # Autenticación
│   │   │   ├── dashboard/          # Métricas y KPIs
│   │   │   ├── logs/               # Visor de logs
│   │   │   ├── jwt/                # Generador JWT
│   │   │   ├── mcp/                # Exploradores MCP
│   │   │   │   ├── explorer/       # Explorador genérico
│   │   │   │   ├── documentacion/  # Panel documentación
│   │   │   │   └── expedientes/    # Panel expedientes
│   │   │   ├── test-panel/         # Panel de pruebas
│   │   │   ├── layout/             # Header, Sidebar
│   │   │   └── ui/                 # Componentes UI
│   │   ├── contexts/               # AuthContext
│   │   ├── hooks/                  # Custom hooks
│   │   ├── pages/                  # Páginas principales
│   │   ├── services/               # API clients
│   │   └── types/                  # TypeScript types
│   └── README.md                   # Documentación frontend
│
├── src/                            # Código fuente Python
│   ├── api/                        # API REST con FastAPI
│   │   ├── main.py                 # FastAPI app
│   │   ├── models.py               # Modelos Pydantic
│   │   ├── routers/
│   │   │   ├── auth.py             # Autenticación
│   │   │   ├── agent.py            # Ejecución de agentes
│   │   │   ├── expedientes.py      # Endpoints expedientes
│   │   │   ├── logs.py             # Endpoints logs
│   │   │   └── health.py           # Health check
│   │   └── services/               # Webhook, task_tracker
│   │
│   ├── backoffice/                 # Back-Office de Agentes IA
│   │   ├── executor.py             # AgentExecutor
│   │   ├── executor_factory.py     # Factory pattern
│   │   ├── models.py               # Modelos Pydantic
│   │   ├── settings.py             # Configuración
│   │   ├── protocols.py            # Interfaces
│   │   ├── auth/
│   │   │   ├── jwt_validator.py    # Validación JWT
│   │   │   └── jwt_generator.py    # Generación JWT
│   │   ├── agents/
│   │   │   ├── base_real.py        # Base para CrewAI
│   │   │   ├── clasificador_expediente.py
│   │   │   ├── redactor_situacion.py
│   │   │   ├── redactor_propuesta_resolucion.py
│   │   │   ├── agente_test_simple.py  # Agente E2E de prueba
│   │   │   ├── registry.py         # Registro de agentes
│   │   │   ├── mcp_tool_wrapper.py # Wrapper MCP → CrewAI
│   │   │   └── schema_builder.py   # Constructor schemas
│   │   ├── config/
│   │   │   ├── agent_config_loader.py
│   │   │   └── mcp_servers.yaml
│   │   ├── mcp/
│   │   │   ├── client.py           # MCPClient
│   │   │   ├── registry.py         # MCPClientRegistry
│   │   │   └── exceptions.py
│   │   └── logging/
│   │       ├── pii_redactor.py     # Redactor PII
│   │       └── audit_logger.py     # Logger auditoría
│   │
│   └── mcp_mock/                   # Servidores MCP
│       ├── mcp_expedientes/        # MCP Expedientes
│       │   ├── server_http.py
│       │   ├── auth.py
│       │   ├── tools.py
│       │   ├── resources.py
│       │   ├── generate_token.py
│       │   └── data/
│       └── mcp_documentacion/      # MCP Documentación
│           ├── data_loader.py
│           ├── tools.py
│           └── resources.py
│
├── tests/                          # Tests por componente
│   ├── api/                        # 34 tests
│   ├── test_backoffice/            # 165 tests
│   ├── test_mcp/                   # 78 tests
│   ├── test_contracts/             # 14 tests
│   └── test_error_handling/        # 15 tests
│
├── doc/                            # Documentación Zettelkasten
├── code-review/                    # Code reviews por commit
├── scripts/                        # Scripts de producción
│   ├── start_worker.sh            # Worker Celery (producción)
│   └── start_flower.sh            # Flower UI (producción)
├── ROADMAP.md                      # Hoja de ruta del proyecto
├── run-tests.sh                    # Script unificado de tests
├── run-api.sh                      # Script para iniciar API
├── run-mcp.sh                      # Script para iniciar MCP Mock
├── run-celery.sh                   # Script para iniciar Celery Worker
├── run-flower.sh                   # Script para iniciar Flower UI
├── test-agent.sh                   # Script para probar agentes E2E
├── docker-compose.prod.yml         # Docker Compose para producción
└── README.md                       # Este archivo
```

## Cumplimiento Normativo

### GDPR/LOPD/ENS

El sistema implementa protección de datos personales según normativa europea y española:

- **Redacción automática de PII** en todos los logs
- **8 tipos de datos protegidos**: DNI, NIE, email, teléfonos móviles, teléfonos fijos, IBAN, tarjetas, CCC
- **Logs estructurados** en JSON lines para auditoría
- **Control de acceso** a logs por expediente
- **Retención configurable** de logs

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
# JWT - Autenticación de Agentes
JWT_SECRET=your-secret-key-here  # PRODUCCIÓN: openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_EXPECTED_ISSUER=agentix-bpmn
JWT_EXPECTED_SUBJECT=Automático
JWT_REQUIRED_AUDIENCE=agentix-mcp-expedientes

# Admin Authentication - Dashboard Web
API_ADMIN_TOKEN=agentix-admin-dev-token-2024  # PRODUCCIÓN: secrets.token_urlsafe(32)

# LLM Provider
ANTHROPIC_API_KEY=your-anthropic-api-key

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080,*

# MCP Configuration
MCP_CONFIG_PATH=backoffice/config/mcp_servers.yaml

# Celery + Redis (Paso 12 - Escalado Horizontal)
USE_CELERY=false                             # true para modo distribuido
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_TIME_LIMIT=3600

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs/agent_runs
```

### Variables de Entorno Frontend (frontend/.env)

```bash
VITE_API_URL=http://localhost:8080
```

Ver [.env.example](.env.example) para documentación completa.

## Añadir Nuevo MCP

Para añadir un nuevo servidor MCP:

1. **Editar configuración** (`src/backoffice/config/mcp_servers.yaml`):

```yaml
  - id: nuevo_mcp
    name: "MCP Nuevo Servicio"
    description: "Descripción del nuevo MCP"
    url: http://mcp-nuevo:8003
    type: http
    auth:
      type: jwt
      audience: agentix-mcp-nuevo
    timeout: 30
    enabled: true  # ⬅️ Activar
```

2. **Reiniciar el servicio** (NO requiere cambios en código)

3. **Usar en agentes**:

```python
# El registry automáticamente descubre y enruta herramientas
await mcp_registry.call_tool("nueva_herramienta", {
    "param": "valor"
})
```

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

### Code Reviews

Los code reviews del proyecto están organizados por commit en [code-review/](code-review/)

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
