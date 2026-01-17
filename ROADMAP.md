# ROADMAP - aGEntiX

Hoja de ruta del proyecto con el estado de implementación y próximos pasos.

## Estado Actual del Proyecto

**Fase actual:** Paso 11 - Agentes LangGraph ✅ COMPLETADO

### Resumen de Progreso

| Paso | Descripción | Estado | Tests |
|------|-------------|--------|-------|
| 1 | Back-Office Mock | ✅ Completado | 165 |
| 2 | API REST con FastAPI | ✅ Completado | 34 |
| 3 | Frontend Dashboard | ✅ Completado | - |
| 4 | Refinar concepto de agente | ✅ Completado | - |
| 5 | Revisión documentación | ⏳ En progreso | - |
| 6 | Agentes reales con CrewAI | ✅ Completado | - |
| 7 | MCP de documentos | ⏳ En progreso | - |
| 8 | MCP Documentación tipos expediente | ✅ Completado | 78 |
| 9 | Agente generador documentos | 🔜 Pendiente | - |
| 10 | Captura de logs de CrewAI | ✅ Completado | 14 |
| 11 | Agentes LangGraph | ✅ Completado | 46 |
| 12 | Escalabilidad horizontal | 🔜 Pendiente | - |

**Total tests:** 382

---

## Pasos Completados

### Paso 1: Back-Office Mock ✅

Sistema funcional con agentes mock que demuestra la arquitectura completa:

- ✅ **Validación JWT completa** con 10 claims obligatorios (issuer, subject, audience, exp_id, permisos)
- ✅ **Arquitectura multi-MCP plug-and-play** (solo MCP Expedientes habilitado, otros por configuración)
- ✅ **MCPClientRegistry** con routing automático de herramientas entre MCPs
- ✅ **Conexión a servidores MCP reales** vía JSON-RPC 2.0 sobre HTTP/SSE
- ✅ **Propagación de errores estructurados** con códigos semánticos
- ✅ **Redacción automática de PII** en logs (8 tipos: DNI, NIE, email, teléfonos, IBAN, tarjetas, CCC)
- ✅ **Auditoría completa** con logs estructurados JSON lines
- ✅ **Configuración externalizada** (.env para secrets, YAML para MCPs)

Ver [code-review/commit-c039abe](code-review/commit-c039abe/) para análisis detallado.

### Paso 2: API REST con FastAPI ✅

API REST profesional para ejecución asíncrona de agentes:

- ✅ **Endpoints RESTful** (execute, status, health, info, metrics, docs)
- ✅ **Ejecución asíncrona** con FastAPI BackgroundTasks y timeouts configurables
- ✅ **Webhooks automáticos** para notificar a BPMN al completar
- ✅ **Seguridad JWT** con validación completa en endpoints de agentes
- ✅ **Protección SSRF** en webhook_url (previene localhost, IPs privadas, require HTTPS en producción)
- ✅ **Métricas Prometheus** para observabilidad
- ✅ **Documentación OpenAPI** interactiva con Swagger UI
- ✅ **Task tracking** en memoria thread-safe con cleanup automático
- ✅ **Patrón lifespan moderno** (migrado de `on_event` deprecado)
- ✅ **Configuración flexible** vía variables de entorno

Ver [code-review/commit-64fda4d](code-review/commit-64fda4d/) para análisis detallado.

### Paso 3: Dashboard Web Frontend ✅

Dashboard web profesional para gestión y monitorización del sistema aGEntiX.

**Fases completadas:**
- ✅ **Fase 1: Sistema de Autenticación** - Login con token de admin, rutas protegidas, interceptor HTTP
- ✅ **Fase 2: Dashboard de Métricas** - 8 KPIs, 4 gráficos interactivos, auto-refresh, exportación CSV/JSON
- ✅ **Fase 3: Visor de Logs** - Filtros avanzados, búsqueda, streaming SSE, exportación, 2000+ logs sin degradación
- ✅ **Fase 4: Panel de Pruebas** - Selector de agentes, generador JWT, visualización de resultados

**Tecnologías:** React 18, TypeScript, Vite, TailwindCSS, Recharts, date-fns, Axios

**Documentación técnica:**
- [doc/paso-3-fase-1-autenticacion.md](doc/paso-3-fase-1-autenticacion.md)
- [doc/paso-3-fase-2-dashboard-metricas.md](doc/paso-3-fase-2-dashboard-metricas.md)
- [doc/paso-3-fase-3-visor-logs.md](doc/paso-3-fase-3-visor-logs.md)

### Paso 4: Refinar Concepto de Agente ✅

Simplificación del sistema de invocación de agentes:

- ✅ **AgentConfigLoader** - Carga de configuraciones de agente desde YAML
- ✅ **ExecutorFactory** - Factory pattern para crear ejecutores
- ✅ **Configuración declarativa** - Agentes definidos en archivos de configuración

### Paso 6: Agentes Reales con CrewAI ✅

Sistema de agentes reales usando CrewAI con Anthropic:

- ✅ **AgentReal (base_real.py)** - Clase base para agentes CrewAI
- ✅ **ClasificadorExpediente** - Clasifica expedientes por tipo
- ✅ **RedactorSituacion** - Genera resúmenes de situación del expediente
- ✅ **MCPToolWrapper** - Wrapper para exponer herramientas MCP a CrewAI
- ✅ **SchemaBuilder** - Constructor de schemas para tools

### Paso 8: MCP Documentación de Tipos de Expediente ✅

Servidor MCP para consultar documentación de tipos de expediente:

- ✅ **MCP Documentación** implementado (`src/mcp_mock/mcp_documentacion/`)
- ✅ **Tools**: consultar documentación por tipo de expediente
- ✅ **Resources**: acceso a documentación estructurada
- ✅ **DataLoader**: carga de datos desde archivos YAML/JSON
- ✅ **Panel MCP en frontend** con tabs y explorador

**Componentes frontend:**
- `components/mcp/explorer/` - Explorador de MCPs
- `components/mcp/documentacion/` - Panel de documentación
- `components/mcp/expedientes/` - Panel de expedientes

### Paso 10: Captura de Logs de CrewAI ✅

Sistema para capturar logs internos de CrewAI y redirigirlos al sistema de auditoría:

- ✅ **crewai_log_processor.py** - Procesador de logs de CrewAI
- ✅ **Integración con output_log_file** - Usa API oficial de CrewAI
- ✅ **Redacción automática de PII** - Logs pasan por PIIRedactor
- ✅ **Formato JSON estructurado** - Compatible con sistema de auditoría
- ✅ **Limpieza automática** - Archivos temporales eliminados después de procesar
- ✅ **14 tests** de cobertura completa

**Características:**
- Prefijo `[CrewAI]` en todos los mensajes
- Metadata con `source: "crewai"` para filtrado
- Soporta JSON array, JSON lines y texto plano
- Procesa logs incluso en caso de error del agente

**Documentación:** [prompts/step-10-capture-crewai-logs.md](prompts/step-10-capture-crewai-logs.md)

### Paso 11: Agentes LangGraph ✅

Soporte para agentes usando LangChain/LangGraph como alternativa a CrewAI:

- ✅ **AgentLangGraph (base_langgraph.py)** - Clase base para agentes LangGraph
- ✅ **RedactorResolucion** - Primer agente LangGraph para generar resoluciones
- ✅ **LangGraphConfig** - Configuración específica en agent_config_loader.py
- ✅ **Integración con create_react_agent** - Agente ReAct de LangGraph
- ✅ **StructuredTool automático** - Conversión de tools MCP a LangChain
- ✅ **Sanitización de nombres** - Compatibilidad con API Anthropic (ñ→n)
- ✅ **46 tests** de cobertura completa

**Características:**
- Misma interfaz que AgentReal (`execute() -> Dict`)
- Reutiliza captura de logs de CrewAI
- Soporte para `additional_goal` en prompts
- Parseo automático de JSON en respuestas

**Documentación:** [prompts/step-11-langchain-agent.md](prompts/step-11-langchain-agent.md)

---

## Pasos En Progreso

### Paso 5: Revisión de Documentación ⏳

Revisión y actualización de toda la documentación del proyecto:

- ✅ Actualización de CLAUDE.md
- ⏳ Actualización de README.md
- 🔜 Creación de ROADMAP.md
- 🔜 Revisión del sistema Zettelkasten en /doc

### Paso 7: MCP de Documentos ⏳

Servidor MCP para gestión avanzada de documentos:

- ⏳ En desarrollo junto con Paso 8

---

## Próximos Pasos

### Paso 9: Agente Generador de Documentos 🔜

Agente capaz de generar documentos basados en plantillas:

- [ ] Definir formato de plantillas
- [ ] Implementar agente GeneradorDocumentos
- [ ] Integración con MCP Documentación
- [ ] Tests de generación

### Paso 12: Escalabilidad Horizontal 🔜

Mejorar el sistema para escalar horizontalmente:

- [ ] Integración con Celery + Redis
- [ ] Múltiples workers concurrentes
- [ ] Load balancing automático
- [ ] Monitorización y métricas avanzadas

---

## Mejoras Transversales Implementadas

### Robustez y Error Handling ✅

Sistema fortalecido con manejo completo de errores:

- ✅ **15 tests de error handling** (12 activos + 3 skip para futuro)
- ✅ **Webhook retry logic** con exponential backoff
- ✅ **PII redactor robusto** que maneja datos inválidos
- ✅ **Manejo HTTP 409 Conflict** para modificación concurrente

### Sistema de Autenticación Dual ✅

- ✅ **Admin Token** para acceso al dashboard
- ✅ **JWT Token** para ejecución de agentes
- ✅ **Generador JWT** integrado en frontend

---

## Métricas de Calidad

| Métrica | Valor |
|---------|-------|
| Tests totales | 382 |
| Tests pasando | 376+ |
| Tests skip | ~6 |
| Cobertura PII | 8 tipos |
| Vulnerabilidades | 0 |
| Calidad código | 4.7/5 |
| Cumplimiento | GDPR/LOPD/ENS |

### Distribución de Tests

| Suite | Tests | Descripción |
|-------|-------|-------------|
| Back-Office | 214 | JWT, MCP, PII, Executor, Protocols, CrewAI Logs, LangGraph |
| API REST | 34 | Health, Agent endpoints |
| MCP Mock | 78 | Auth, Resources, Tools, Server |
| Contracts | 14 | Interfaces y contratos |
| Error Handling | 15 | Resilience (12 activos, 3 skip) |
| LangGraph | 46 | AgentLangGraph, config, sanitization |

---

## Referencias

- [README.md](README.md) - Documentación principal
- [CLAUDE.md](CLAUDE.md) - Guía para Claude Code
- [doc/index.md](doc/index.md) - Sistema Zettelkasten
- [frontend/README.md](frontend/README.md) - Documentación frontend
