# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**aGEntiX** is an AI Agent System designed to integrate with GEX (Gestión de Expedientes), a document and process management system used throughout Córdoba province, Spain. The system enables AI agents to automate tasks within administrative workflows while maintaining strict boundaries on decision-making authority.

## Current Project Status

**Phase:** Paso 1 - Back-Office Mock with Multi-MCP Architecture ✅ COMPLETED

### Implemented Features (Paso 1)

- ✅ **AgentExecutor**: Main orchestrator (`backoffice/executor.py`)
- ✅ **JWT Validation**: Complete validation with 10 mandatory claims (`backoffice/auth/jwt_validator.py`)
- ✅ **Multi-MCP Architecture**: Plug-and-play registry with automatic tool routing (`backoffice/mcp/registry.py`)
- ✅ **MCP Client**: JSON-RPC 2.0 over HTTP/SSE (`backoffice/mcp/client.py`)
- ✅ **PII Redaction**: Automatic redaction of 8 types of personal data (GDPR/LOPD/ENS) (`backoffice/logging/pii_redactor.py`)
- ✅ **Audit Logging**: Structured JSON lines logs (`backoffice/logging/audit_logger.py`)
- ✅ **3 Mock Agents**: ValidadorDocumental, AnalizadorSubvencion, GeneradorInforme (`backoffice/agents/`)
- ✅ **Test Suite**: 79 tests total (46 back-office + 33 MCP mock) - 100% PASS
- ✅ **Externalized Configuration**: .env for secrets, YAML for MCP servers

### Quality Metrics

- **Tests:** 79/79 PASS (100%)
  - 19 JWT security tests
  - 15 MCP integration tests
  - 12 PII compliance tests
  - 33 MCP mock server tests
- **Vulnerabilities:** 0
- **Code Quality:** 4.6/5 ⭐⭐⭐⭐⭐
- **PII Coverage:** 8 types (DNI, NIE, email, mobile/landline phones, IBAN, cards, CCC)

See `code-review/commit-c039abe/` for detailed analysis and improvement plan (100% implemented).

## Quick Reference for Common Tasks

### Running Tests

```bash
# All tests
./run-tests.sh

# Back-office only (46 tests)
./run-tests.sh --backoffice-only

# Specific test suites
./run-tests.sh -k jwt          # JWT validation tests
./run-tests.sh -k pii          # PII redaction tests
./run-tests.sh -k mcp_integration  # MCP integration tests
```

### Configuration Files

- **JWT & Environment**: `.env` (created from `.env.example`)
  - JWT_SECRET, JWT_ALGORITHM, JWT_EXPECTED_ISSUER, JWT_EXPECTED_SUBJECT, JWT_REQUIRED_AUDIENCE
  - MCP_CONFIG_PATH, LOG_LEVEL, LOG_DIR

- **MCP Servers**: `backoffice/config/mcp_servers.yaml`
  - List of MCP servers with id, name, url, enabled flag
  - Add new MCP by setting `enabled: true` (no code changes required)

### Key Components Location

```
backoffice/
├── executor.py              # Main entry point - AgentExecutor
├── settings.py              # Configuration with Pydantic Settings
├── auth/jwt_validator.py    # JWT validation (10 claims)
├── mcp/
│   ├── client.py           # MCPClient - JSON-RPC 2.0 client
│   ├── registry.py         # MCPClientRegistry - routing
│   └── exceptions.py       # MCP exceptions
├── logging/
│   ├── pii_redactor.py     # PII redaction (8 types)
│   └── audit_logger.py     # Structured logging
└── agents/
    ├── base.py             # BaseAgent class
    └── [specific agents]   # Mock implementations
```

### MCP Mock Server

```bash
# Start server
cd mcp-mock/mcp-expedientes
python -m uvicorn mcp_expedientes.server_http:app --reload --port 8000

# Generate JWT token
python -m mcp_expedientes.generate_token EXP-2024-001
```

## Important Implementation Details

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

See `backoffice/tests/test_jwt_validator.py` for all validation scenarios.

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

**CRITICAL:** All 12 PII tests must pass before committing changes to logging system.

### Multi-MCP Architecture

The system supports multiple MCP servers via configuration:

```yaml
# backoffice/config/mcp_servers.yaml
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
- **Test files mirror source structure** (`backoffice/tests/test_*.py`)
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
cd mcp-mock/mcp-expedientes && python -m uvicorn mcp_expedientes.server_http:app --reload --port 8000

# Generate test token
cd mcp-mock/mcp-expedientes && python -m mcp_expedientes.generate_token EXP-2024-001

# Run specific test file
pytest backoffice/tests/test_jwt_validator.py -v

# Run with coverage
pytest --cov=backoffice --cov-report=html

# Check code quality
pylint backoffice/
```

## When in Doubt

1. **Check tests**: They document expected behavior
2. **Read code-review**: `code-review/commit-c039abe/README.md` has overview
3. **Consult Zettelkasten**: `/doc/index.md` is your friend
4. **Maintain quality**: 4.6/5 is the baseline to maintain
