# aGEntiX

**Sistema de Agentes IA para Automatización de Workflows Administrativos en GEX**

## Descripción

**aGEntiX** es un sistema que permite la integración de agentes de inteligencia artificial con GEX (Gestión de Expedientes) para automatizar tareas específicas dentro de los flujos de trabajo administrativos, manteniendo límites estrictos en la autoridad de toma de decisiones y garantizando la supervisión humana donde sea necesaria.

GEX es la aplicación central de gestión administrativa desarrollada por Eprinsa (Empresa Provincial de Informática de la Excma. Diputación Provincial de Córdoba, España), y constituye el núcleo vertebrador de la administración electrónica en la provincia de Córdoba, utilizado tanto por el sector público institucional de la Diputación como por la práctica totalidad de los Ayuntamientos de la provincia.

## Estado del Proyecto

**Fase actual:** Paso 2 - API REST con FastAPI ✅ COMPLETADO

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

### Calidad del Código

- **Tests:** 108/108 PASS (100%) - 86 backoffice + 22 API
- **Cobertura PII:** 8 tipos de datos personales redactados
- **Vulnerabilidades:** 0
- **Seguridad:** OWASP A10:2021 (SSRF) mitigado
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
cd mcp-mock/mcp-expedientes
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

El proyecto incluye un script unificado para ejecutar todos los tests:

```bash
# Ejecutar todos los tests (MCP + Back-Office)
./run-tests.sh

# Solo tests de Back-Office
./run-tests.sh --backoffice-only

# Solo tests de MCP Mock
./run-tests.sh --mcp-only

# Tests con verbose
./run-tests.sh -v

# Tests específicos
./run-tests.sh -k jwt
./run-tests.sh -k pii
./run-tests.sh -k mcp_integration

# Detener en el primer error
./run-tests.sh -x

# Re-ejecutar solo tests fallidos
./run-tests.sh --failed

# Ver todas las opciones disponibles
./run-tests.sh --help
```

### Suite de Tests Actual

**Total: 96 tests (100% PASS)**

#### Back-Office (86 tests)
- **19 tests JWT** - Validación de seguridad y autenticación
- **15 tests MCP** - Integración con servidores MCP
- **12 tests PII** - Cumplimiento normativo GDPR/LOPD/ENS
- **33 tests Executor** - Tests unitarios del AgentExecutor
- **7 tests Protocols** - Interfaces y abstracciones

#### API REST (10 tests)
- **4 tests Health** - Health check, metrics, docs
- **6 tests Agent Endpoints** - Execute, status, validaciones

#### MCP Mock Expedientes (33 tests)
- **10 tests Auth** - Validación JWT en servidor MCP
- **7 tests Resources** - Recursos MCP (expedientes, documentos)
- **7 tests Server HTTP** - Servidor HTTP/SSE
- **9 tests Tools** - Herramientas MCP (consulta, actualización)

## Uso del Sistema

### Opción A: API REST (Recomendado)

La forma más simple de usar aGEntiX es mediante la API REST:

#### 1. Iniciar Servidor MCP Expedientes

```bash
cd mcp-mock/mcp-expedientes
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
cd mcp-mock/mcp-expedientes
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
cd mcp-mock/mcp-expedientes
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
cd mcp-mock/mcp-expedientes
python -m mcp_expedientes.generate_token EXP-2024-001
```

## Estructura del Proyecto

```
aGEntiX/
├── backoffice/                      # Back-Office de Agentes IA (Paso 1)
│   ├── executor.py                  # AgentExecutor (punto de entrada)
│   ├── models.py                    # Modelos Pydantic
│   ├── settings.py                  # Configuración con variables de entorno
│   ├── auth/
│   │   └── jwt_validator.py         # Validación JWT (10 claims)
│   ├── agents/
│   │   ├── base.py                  # Clase base agentes
│   │   ├── registry.py              # Registro de agentes
│   │   ├── validador_documental.py
│   │   ├── analizador_subvencion.py
│   │   └── generador_informe.py
│   ├── config/
│   │   ├── models.py                # Modelos configuración MCP
│   │   └── mcp_servers.yaml         # Catálogo de servidores MCP
│   ├── mcp/
│   │   ├── client.py                # Cliente MCP (JSON-RPC 2.0)
│   │   ├── registry.py              # MCPClientRegistry (routing)
│   │   └── exceptions.py            # Excepciones MCP
│   ├── logging/
│   │   ├── pii_redactor.py          # Redactor PII (GDPR/LOPD)
│   │   └── audit_logger.py          # Logger auditoría
│   └── tests/
│       ├── test_jwt_validator.py    # 19 tests JWT
│       ├── test_mcp_integration.py  # 15 tests MCP
│       └── test_logging.py          # 12 tests PII
│
├── mcp-mock/
│   └── mcp-expedientes/             # Servidor MCP Mock
│       ├── mcp_expedientes/
│       │   ├── server_http.py       # Servidor HTTP/SSE
│       │   ├── auth.py              # Validación JWT
│       │   ├── models.py            # Modelos de datos
│       │   └── generate_token.py    # Generador de tokens
│       ├── data/                    # Datos mock
│       │   └── expedientes/
│       └── tests/                   # 33 tests
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
├── .env.example                     # Template de configuración
├── run-tests.sh                     # Script unificado de tests
├── requirements.txt                 # Dependencias Python
└── README.md                        # Este archivo
```

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

### Variables de Entorno (.env)

```bash
# JWT - Autenticación y Seguridad
JWT_SECRET=your-secret-key-here  # PRODUCCIÓN: openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_EXPECTED_ISSUER=agentix-bpmn
JWT_EXPECTED_SUBJECT=Automático
JWT_REQUIRED_AUDIENCE=agentix-mcp-expedientes

# MCP Configuration
MCP_CONFIG_PATH=backoffice/config/mcp_servers.yaml

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs/agent_runs
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

### Paso 2: API REST con FastAPI
- Endpoint `POST /api/v1/agent/execute`
- Trabajos asíncronos (background tasks)
- Webhooks para notificar a BPMN
- Métricas (Prometheus)
- Documentación OpenAPI/Swagger

### Paso 3: Agentes Reales con LLMs
- Integración LangGraph/CrewAI
- LLMs reales (Anthropic Claude, OpenAI)
- Razonamiento dinámico multi-paso
- Sistema de memoria y contexto
- Mantiene interfaz `AgentExecutor` (retrocompatible)

### Paso 4: Escalabilidad Horizontal
- Celery + Redis para cola de trabajos
- Múltiples workers concurrentes
- Load balancing automático
- Monitorización y métricas

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
