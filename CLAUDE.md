# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**aGEntiX** is an AI Agent System designed to integrate with GEX (Gestión de Expedientes), a document and process management system used throughout Córdoba province, Spain. The system enables AI agents to automate tasks within administrative workflows while maintaining strict boundaries on decision-making authority.

## Current Project Status

**Current Phase:** Paso 3 - Frontend Dashboard (Fase 2 - Dashboard de Métricas) ✅ COMPLETED

### Completed Phases

#### Paso 1 - Back-Office Mock with Multi-MCP Architecture ✅
#### Paso 2 - API REST con FastAPI ✅
#### Paso 3 - Fase 1: Sistema de Autenticación Frontend ✅
#### Paso 3 - Fase 2: Dashboard de Métricas ✅

### Implemented Features (Paso 1 - Back-Office)

- ✅ **AgentExecutor**: Main orchestrator (`src/backoffice/executor.py`)
- ✅ **JWT Validation**: Complete validation with 10 mandatory claims (`src/backoffice/auth/jwt_validator.py`)
- ✅ **Multi-MCP Architecture**: Plug-and-play registry with automatic tool routing (`src/backoffice/mcp/registry.py`)
- ✅ **MCP Client**: JSON-RPC 2.0 over HTTP/SSE (`src/backoffice/mcp/client.py`)
- ✅ **PII Redaction**: Automatic redaction of 8 types of personal data (GDPR/LOPD/ENS) (`src/backoffice/logging/pii_redactor.py`)
- ✅ **Audit Logging**: Structured JSON lines logs (`src/backoffice/logging/audit_logger.py`)
- ✅ **3 Mock Agents**: ValidadorDocumental, AnalizadorSubvencion, GeneradorInforme (`src/backoffice/agents/`)
- ✅ **Test Suite**: 119 tests total (86 back-office + 33 MCP mock) - 100% PASS
- ✅ **Externalized Configuration**: .env for secrets, YAML for MCP servers

### Quality Metrics

- **Tests:** 119/119 PASS (100%)
  - 19 JWT security tests
  - 15 MCP integration tests
  - 12 PII compliance tests
  - 30 AgentExecutor tests
  - 7 protocols tests
  - 33 MCP mock server tests (10 auth + 9 tools + 7 resources + 7 server)
- **Vulnerabilities:** 0
- **Code Quality:** 4.6/5 ⭐⭐⭐⭐⭐
- **PII Coverage:** 8 types (DNI, NIE, email, mobile/landline phones, IBAN, cards, CCC)

See `code-review/commit-c039abe/` for detailed analysis and improvement plan (100% implemented).

### Implemented Features (Paso 2 - API REST)

- ✅ **FastAPI Application**: REST API with async support (`src/api/main.py`)
- ✅ **Agent Execution Endpoint**: `POST /api/v1/agent/execute` - Async agent execution with background tasks
- ✅ **Status Endpoint**: `GET /api/v1/agent/status/{agent_run_id}` - Query execution status
- ✅ **Health Check**: `GET /health` - Service health monitoring
- ✅ **Prometheus Metrics**: `GET /metrics` - Metrics instrumentation
- ✅ **Webhook Callbacks**: Automatic notifications on completion
- ✅ **Task Tracker**: In-memory tracking of agent executions
- ✅ **CORS Configuration**: Support for local development and Codespaces

### Implemented Features (Paso 3 - Fase 1: Autenticación Frontend)

- ✅ **Frontend React + TypeScript**: Vite setup with TailwindCSS
- ✅ **Authentication System**:
  - Admin Token validation (`POST /api/v1/auth/validate-admin-token`)
  - Login page with error handling
  - Protected routes with automatic redirection
  - AuthContext for state management
  - Token storage in localStorage
  - Logout functionality
- ✅ **UI Components Base**:
  - Layout (Header + Sidebar)
  - Card, Button, Input (reusable components)
  - Dashboard placeholder (Fase 2)
- ✅ **Configuration**:
  - Vite configured for Codespaces (`host: true`)
  - TypeScript types for `import.meta.env`
  - CORS properly configured for frontend port
  - API client with interceptors

**Documentation:** `/doc/paso-3-fase-1-autenticacion.md`

### Implemented Features (Paso 3 - Fase 2: Dashboard de Métricas)

- ✅ **Dashboard de Métricas**: Complete metrics visualization system
  - 8 KPIs principales (Total, Hoy, Tasa de Éxito, Tiempo Promedio, PII, MCP, Latencia, Llamadas)
  - 4 gráficos interactivos (Histórico Ejecuciones, Por Tipo de Agente, PII Distribución, PII Histórico)
  - Auto-refresh cada 10 segundos
  - Exportación CSV/JSON
- ✅ **Componentes de Dashboard**:
  - MetricsCard (tarjetas KPI reutilizables)
  - AgentExecutionsChart (gráficos de líneas/barras)
  - PIIRedactionChart (gráficos donut/circular)
  - SystemHealthStatus (estado de servidores MCP y servicios externos)
- ✅ **Hook useMetrics**:
  - Auto-refresh configurable
  - Polling paralelo de métricas, historial ejecuciones e historial PII
  - Manejo de estados (loading, error, data)
- ✅ **Servicio de Métricas**:
  - Abstracción mock/API con flag de migración
  - Funciones de exportación CSV/JSON
  - Datos mock realistas para desarrollo
- ✅ **Performance**:
  - Bundle gzipped: 195KB (< 500KB requerido)
  - Gráficos responsivos con Recharts
  - Formateo de fechas con date-fns (locale español)

**Documentation:** `/doc/paso-3-fase-2-dashboard-metricas.md`

## Quick Reference for Common Tasks

### Running the Application

#### Backend (API REST - Port 8080)

```bash
cd /workspaces/aGEntiX

# Iniciar servidor FastAPI
python -m uvicorn src.api.main:app --reload --port 8080

# Verificar que está corriendo
curl http://localhost:8080/health
```

#### Frontend (Dashboard Web - Port 5173)

```bash
cd /workspaces/aGEntiX/frontend

# Instalar dependencias (primera vez)
npm install

# Iniciar servidor de desarrollo
npm run dev

# Acceso:
# - Codespaces: Panel PORTS → Puerto 5173 → Abrir en navegador
# - Local: http://localhost:5173
```

#### MCP Mock Server (Port 8000)

```bash
cd src/mcp_mock/mcp_expedientes

# Iniciar servidor MCP
python -m uvicorn server_http:app --reload --port 8000

# Generar token de prueba
python -m generate_token EXP-2024-001
```

### Running Tests

```bash
# All tests
./run-tests.sh

# Back-office only (86 tests)
./run-tests.sh --backoffice-only

# Specific test suites
./run-tests.sh -k jwt          # JWT validation tests
./run-tests.sh -k pii          # PII redaction tests
./run-tests.sh -k mcp_integration  # MCP integration tests
```

### Configuration Files

- **Backend Environment**: `.env` (created from `.env.example`)
  - **JWT:** JWT_SECRET, JWT_ALGORITHM, JWT_EXPECTED_ISSUER, JWT_EXPECTED_SUBJECT, JWT_REQUIRED_AUDIENCE
  - **Admin Auth:** API_ADMIN_TOKEN (for dashboard access)
  - **Config:** MCP_CONFIG_PATH, LOG_LEVEL, LOG_DIR
  - **CORS:** CORS_ORIGINS (include frontend port 5173)

- **Frontend Environment**: `frontend/.env`
  - VITE_API_URL=http://localhost:8080 (backend API URL)

- **MCP Servers**: `src/backoffice/config/mcp_servers.yaml`
  - List of MCP servers with id, name, url, enabled flag
  - Add new MCP by setting `enabled: true` (no code changes required)

### Key Components Location

```
src/
├── api/                        # API REST con FastAPI (Paso 2)
│   ├── main.py                # FastAPI application
│   ├── models.py              # Pydantic models
│   ├── routers/
│   │   ├── auth.py           # Authentication endpoints (Paso 3)
│   │   ├── agent.py          # Agent execution endpoints
│   │   └── health.py         # Health check
│   └── services/
│       ├── webhook.py        # Webhook callbacks
│       └── task_tracker.py   # Task tracking
│
├── backoffice/                # Back-Office de Agentes (Paso 1)
│   ├── executor.py           # Main entry point - AgentExecutor
│   ├── settings.py           # Configuration with Pydantic Settings
│   ├── auth/jwt_validator.py # JWT validation (10 claims)
│   ├── mcp/
│   │   ├── client.py        # MCPClient - JSON-RPC 2.0 client
│   │   ├── registry.py      # MCPClientRegistry - routing
│   │   └── exceptions.py    # MCP exceptions
│   ├── logging/
│   │   ├── pii_redactor.py  # PII redaction (8 types)
│   │   └── audit_logger.py  # Structured logging
│   └── agents/
│       ├── base.py          # BaseAgent class
│       └── [specific agents]  # Mock implementations
│
└── mcp_mock/                  # MCP Mock Servers
    └── mcp_expedientes/       # Expedientes MCP server
        ├── server_http.py     # HTTP/SSE server
        ├── server_stdio.py    # STDIO server
        ├── auth.py            # JWT validation
        └── data/              # Mock data

frontend/                      # Dashboard Web (Paso 3)
├── src/
│   ├── components/
│   │   ├── auth/             # Authentication components
│   │   ├── layout/           # Layout (Header, Sidebar)
│   │   └── ui/               # Reusable UI components
│   ├── contexts/
│   │   └── AuthContext.tsx   # Authentication state
│   ├── pages/
│   │   ├── Login.tsx         # Login page
│   │   ├── Dashboard.tsx     # Main dashboard
│   │   ├── Logs.tsx          # Logs viewer (Fase 3)
│   │   └── TestPanel.tsx     # Agent testing (Fase 4)
│   ├── services/
│   │   ├── api.ts            # Axios client with interceptors
│   │   └── authService.ts    # Authentication service
│   └── types/                # TypeScript type definitions
├── vite.config.ts            # Vite configuration
└── .env                      # VITE_API_URL
```

### MCP Mock Server

```bash
# Start server
cd src/mcp_mock/mcp_expedientes
python -m uvicorn server_http:app --reload --port 8000

# Generate JWT token
python -m generate_token EXP-2024-001
```

## Important Implementation Details

### Dual Token Authentication

The system uses **two different tokens**:

| Token | Purpose | Type | Endpoints |
|-------|---------|------|-----------|
| **Admin Token** | Dashboard access | Fixed string | `/generate-jwt`, `/agents`, `/logs`, `/metrics` |
| **JWT Token** | Agent execution | Signed JWT | `/execute`, `/status/{id}` |

**Key points:**
- Admin token is stored in `localStorage`, configured via `API_ADMIN_TOKEN` in `.env`
- JWT is generated per execution via `/generate-jwt` (requires admin token)
- JWT is NOT persisted, only kept in memory during execution
- Public endpoints (`/health`, `/metrics`) require no authentication

See `/doc/060-autenticacion-dual.md` for full documentation.

### JWT Validation

The system validates 10 JWT claims:
1. **iss** (issuer): Must match `JWT_EXPECTED_ISSUER` (default: "agentix-bpmn")
2. **sub** (subject): Must match `JWT_EXPECTED_SUBJECT` (default: "Automático")
3. **aud** (audience): Must include `JWT_REQUIRED_AUDIENCE` (default: "agentix-mcp-expedientes")
4. **exp** (expiration): Token must not be expired
5. **iat** (issued at): Must be present
6. **nbf** (not before): Token must be valid now
7. **jti** (JWT ID): Unique identifier
8. **exp_id** (expediente ID): Must match requested expediente
9. **permisos** (permissions): Must include required permissions for tools
10. **Signature**: Must be valid with JWT_SECRET

See `tests/test_backoffice/test_jwt_validator.py` for all validation scenarios.

### PII Redaction (GDPR/LOPD/ENS Compliance)

All logs automatically redact 8 types of personal data:

| Type | Pattern | Example | Redacted |
|------|---------|---------|----------|
| DNI | `\d{8}[A-Z]` | 12345678A | [DNI-REDACTED] |
| NIE | `[XYZ]\d{7}[A-Z]` | X1234567Z | [NIE-REDACTED] |
| Email | Standard email | juan@example.com | [EMAIL-REDACTED] |
| Mobile | `[67]\d{8}` | 612345678 | [TELEFONO_MOVIL-REDACTED] |
| Landline | `[89]\d{8}` | 957123456 | [TELEFONO_FIJO-REDACTED] |
| IBAN | `ES\d{22}` | ES12... | [IBAN-REDACTED] |
| Card | Standard format | 4532... | [TARJETA-REDACTED] |
| CCC | `\d{20}` | 123... | [CCC-REDACTED] |

**CRITICAL:** All 12 PII tests must pass before committing changes to logging system. Tests located in `tests/test_backoffice/test_logging.py`.

### Multi-MCP Architecture

The system supports multiple MCP servers via configuration:

```yaml
# src/backoffice/config/mcp_servers.yaml
mcp_servers:
  - id: expedientes
    enabled: true    # Active
  - id: firma
    enabled: false   # Future
```

**To add a new MCP:** Edit YAML and set `enabled: true`. The `MCPClientRegistry` will:
1. Automatically discover available tools via `tools/list`
2. Route tool calls to the correct MCP server
3. Propagate JWT headers without modification
4. Handle errors with semantic codes

## Documentation Structure

### Zettelkasten System (`/doc`)

The project uses a **Zettelkasten** system for documentation:

- Each note represents a single concept
- Notes are interconnected via `[note-name](note-file.md)` references
- **Start here:** `/doc/index.md` for complete overview

**Key topics:**
- **GEX System**: `/doc/001-gex-definicion.md` (components, flows, integrations)
- **BPMN Workflows**: `/doc/020-bpmn-modelo.md` (tasks, actions, agent actions)
- **AI Agents**: `/doc/030-propuesta-agentes.md` (configuration, context, audit)
- **Architecture**: `/doc/040-criterios-diseño.md` (principles, MCP access)
- **Permissions**: `/doc/050-permisos-agente.md` (system, propagation)
- **Task Types**: `/doc/010-tipos-tareas.md` (human vs AI boundaries)

### Code Reviews (`/code-review`)

Organized by commit hash:

- **commit-c039abe/**: Paso 1 implementation
  - `README.md`: Executive summary, implementation status
  - `revision-commit-*.md`: Detailed analysis
  - `metricas.md`: Quality metrics
  - `plan-mejoras.md`: Improvement plan (✅ P1+P2 100% implemented)

## Architecture Principles

1. **No Coupling, No Intrusion**: AI agents must not be tightly coupled to GEX
2. **Modularity**: Components should be modular and independently deployable
3. **MCP Access**: Information and tools accessed via Model Context Protocol (MCP)
4. **Conservative Approach**: Legal decisions remain exclusively human
5. **Full Audit**: All agent steps logged for debugging, verification, compliance

See `/doc/040-criterios-diseño.md` and `/doc/041-enfoque-conservador.md` for details.

## Human vs. AI Task Boundaries

**Tasks Reserved for Humans:**
- Legal analysis and decision-making based on regulations
- Final quality control over processes

**Tasks AI Can Automate:**
- Information extraction from incoming documents
- Document generation (beyond basic template substitution)
- Data validation and verification

**Tasks AI Can Assist With:**
- Analysis support for decision-making
- Information summarization
- Pattern detection

**Tasks Already Automated (No AI needed):**
- Numeric operations on external systems
- Accounting entries
- Basic document generation from templates

See `/doc/010-tipos-tareas.md` through `/doc/013-tareas-ia-candidatas.md` for detailed categorization.

## Development Workflow

### Before Making Changes

1. **Check tests**: Run `./run-tests.sh` to ensure baseline
2. **Review code-review**: Check `code-review/commit-c039abe/` for context
3. **Consult documentation**: Use `/doc/index.md` for architectural decisions

### When Adding Features

1. **Write tests first**: Follow TDD approach
2. **Maintain PII compliance**: Ensure new logs are redacted
3. **Update documentation**: Add/update relevant `/doc` notes
4. **Run full test suite**: Ensure 79/79 tests pass

### When Modifying Security

- **JWT validation**: All 19 JWT tests must pass
- **PII redaction**: All 12 PII tests must pass
- **MCP integration**: All 15 MCP integration tests must pass

### Commit Guidelines

- Reference commit hash in code-review when applicable
- Include test results in commit message
- Use semantic commit messages (e.g., "Implementar P2.7: Ampliar patrones PII...")

## Next Steps (Roadmap)

### Paso 2: API REST with FastAPI
- Endpoint `POST /api/v1/agent/execute`
- Background async tasks
- Webhooks to notify BPMN
- Prometheus metrics
- OpenAPI documentation

### Paso 3: Real AI Agents
- LangGraph/CrewAI integration
- Real LLMs (Anthropic Claude, OpenAI)
- Multi-step dynamic reasoning
- Maintains `AgentExecutor` interface (backward compatible)

### Paso 4: Horizontal Scalability
- Celery + Redis task queue
- Multiple concurrent workers
- Automatic load balancing
- Monitoring and metrics

## Language

The primary language of this project is **Spanish**. Code comments, documentation, and domain terminology will be in Spanish as this is a system for Spanish public administration.

## File Naming Conventions

- **Python modules**: snake_case (e.g., `jwt_validator.py`, `pii_redactor.py`)
- **Config files**: lowercase with extension (e.g., `mcp_servers.yaml`, `.env`)
- **Documentation**: kebab-case with number prefix (e.g., `001-gex-definicion.md`)
- **Code reviews**: `commit-<hash>/` or `fix-<description>/`

## Testing Philosophy

- **100% test pass required** before commits
- **Critical tests** (PII, JWT) must NEVER be skipped or modified to pass
- **Test files organized by component** (`tests/test_backoffice/test_*.py`, `tests/test_mcp/test_*.py`, `tests/api/test_*.py`)
- **Use fixtures** for common test data (see `conftest.py`)
- **Mock external dependencies** (MCP servers, LLM APIs)

## Common Pitfalls to Avoid

1. **Don't hardcode secrets**: Always use `.env` variables
2. **Don't skip PII redaction**: All logs must go through `PIIRedactor`
3. **Don't modify JWT claims**: Token propagates unchanged to MCP servers
4. **Don't couple to GEX**: Keep architecture decoupled via MCP
5. **Don't break tests**: Maintain 100% pass rate
6. **Don't commit .env**: It's in `.gitignore` for security

## Useful Commands

```bash
# Start MCP server
cd src/mcp_mock/mcp_expedientes
python -m uvicorn server_http:app --reload --port 8000

# Generate test token
cd src/mcp_mock/mcp_expedientes
python -m generate_token EXP-2024-001

# Run specific test file
pytest tests/test_backoffice/test_jwt_validator.py -v

# Run all tests
./run-tests.sh  # 119 tests total

# Run only backoffice tests
./run-tests.sh --backoffice-only  # 86 tests

# Run only MCP tests
./run-tests.sh --mcp-only  # 33 tests

# Run with coverage
pytest --cov=src/backoffice --cov=src/mcp_mock --cov-report=html

# Check code quality
pylint src/backoffice/
pylint src/mcp_mock/
```

## When in Doubt

1. **Check tests**: They document expected behavior
2. **Read code-review**: `code-review/commit-c039abe/README.md` has overview
3. **Consult Zettelkasten**: `/doc/index.md` is your friend
4. **Maintain quality**: 4.6/5 is the baseline to maintain
