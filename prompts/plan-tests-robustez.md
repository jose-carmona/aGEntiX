# Plan de Tests de Robustez - Próximos Pasos

**Fecha:** 2025-12-20
**Estado actual:** Tests Error Handling completados ✅ (170 tests totales, 166 passing, 4 skipped)
**Última actualización:** 2025-12-21
**Objetivo:** Fortalecer tests para Paso 2 (API REST) y preparar Paso 3 (AI Agents reales)

---

## 📊 Estado Actual

### Tests Existentes (170 total)
- ✅ **API:** 22 tests (endpoints básicos, webhooks, health)
- ✅ **MCP Mock:** 34 tests (auth, resources, tools, server HTTP) - 33 pass + 1 skip
- ✅ **Backoffice:** 87 tests (executor, JWT, logging, MCP integration, protocols)
- ✅ **Contracts:** 12 tests (MCP client, agent registry, config loader) ⭐ NUEVO
- ✅ **Error Handling:** 15 tests (resilience, error cases) - 12 pass + 3 skip ⭐ NUEVO

### Coverage por Componente
| Componente | Tests | Coverage Estimado | Estado |
|------------|-------|-------------------|--------|
| AgentExecutor | 33 | ~85% | ✅ Bueno |
| JWT Validation | 19 | ~95% | ✅ Excelente |
| PII Redaction | 12 | ~90% | ✅ Excelente |
| MCP Integration | 15 | ~70% | ⚠️ Mejorable |
| API Endpoints | 22 | ~60% | ⚠️ Mejorable |
| Error Handling | ~10 | ~50% | 🔴 Insuficiente |
| Webhooks | 12 | ~70% | ⚠️ Mejorable |

---

## 🎯 Objetivos del Plan

### Objetivo 1: Completar Paso 2 (API REST) con Confianza
- Cubrir todos los casos edge de la API
- Validar comportamiento asíncrono
- Asegurar manejo de errores robusto
- Preparar para carga en producción

### Objetivo 2: Preparar Paso 3 (Real AI Agents)
- Definir contratos entre AgentExecutor y agentes reales
- Tests de regresión para garantizar backward compatibility
- Validar que mocks y agentes reales son intercambiables

### Objetivo 3: Aumentar Confianza para Producción
- Tests de concurrencia
- Tests de resiliencia (retry, timeouts)
- Tests de seguridad adicionales
- Tests de performance

---

## 📋 Categorías de Tests Propuestos

### 1. Tests de Integración End-to-End (E2E)

**Prioridad:** 🔴 ALTA
**Razón:** Validan el flujo completo API → AgentExecutor → MCP → Respuesta
**Tests actuales:** 0
**Tests propuestos:** 8

#### Tests E2E Propuestos:

##### E2E-1: Flujo completo exitoso con agente mock
```python
@pytest.mark.integration
@pytest.mark.slow
async def test_e2e_api_to_mcp_successful_execution():
    """
    Test: API → AgentExecutor → MCP Mock → Webhook exitoso

    Flujo:
    1. POST /api/v1/agent/execute con JWT válido
    2. AgentExecutor valida JWT
    3. AgentExecutor crea MCP registry
    4. Agente mock ejecuta herramientas MCP
    5. Respuesta 202 Accepted con agent_run_id
    6. Webhook llamado con resultado SUCCESS
    7. Logs de auditoría completos

    Validaciones:
    - Status 202
    - agent_run_id en respuesta
    - Webhook recibe resultado correcto
    - Log de auditoría tiene todas las etapas
    - MCP tools fueron llamados correctamente
    """
```

##### E2E-2: Flujo completo con error de JWT
```python
async def test_e2e_api_jwt_error_propagation():
    """
    Test: Error de JWT se propaga correctamente a través del stack

    Flujo:
    1. POST /api/v1/agent/execute con JWT expirado
    2. AgentExecutor detecta token expirado
    3. Respuesta 401 Unauthorized
    4. Webhook NO es llamado
    5. Error loggeado en auditoría

    Validaciones:
    - Status 401
    - Código de error AUTH_TOKEN_EXPIRED
    - Mensaje de error apropiado
    - No se intentó conexión MCP
    - Log de auditoría registra error
    """
```

##### E2E-3: Flujo completo con error de MCP
```python
async def test_e2e_api_mcp_connection_error():
    """
    Test: Error de conexión MCP se maneja correctamente

    Flujo:
    1. POST /api/v1/agent/execute
    2. MCP server no responde (timeout)
    3. Respuesta 202 pero resultado FAILED
    4. Webhook recibe error MCP_CONNECTION_ERROR
    5. Sistema no crashea, error contenido

    Validaciones:
    - Status 202 (aceptado pero fallará)
    - Webhook recibe status=failed
    - Error MCP_CONNECTION_ERROR en webhook
    - Retry logic ejecutado (si implementado)
    - Log completo del error
    """
```

##### E2E-4: Flujo con múltiples herramientas MCP
```python
async def test_e2e_multiple_mcp_tools_orchestration():
    """
    Test: Agente usa múltiples herramientas MCP en secuencia

    Flujo:
    1. Agente ValidadorDocumental ejecuta
    2. Llama consultar_expediente
    3. Llama listar_documentos
    4. Llama obtener_documento (múltiples veces)
    5. Llama añadir_anotacion
    6. Retorna resultado agregado

    Validaciones:
    - Todas las herramientas fueron llamadas
    - Orden correcto de llamadas
    - Datos pasados correctamente entre calls
    - Resultado final agrega todos los datos
    - tools_used lista completa en respuesta
    """
```

##### E2E-5: Flujo con webhook retry
```python
async def test_e2e_webhook_retry_on_failure():
    """
    Test: Webhook con retry automático en caso de fallo

    Flujo:
    1. Ejecución exitosa del agente
    2. Primer intento webhook → 500 Server Error
    3. Sistema hace retry (exponential backoff)
    4. Segundo intento → 200 OK
    5. Ejecución marcada como completa

    Validaciones:
    - 2 intentos de webhook registrados
    - Delay entre intentos (exponential backoff)
    - Segundo intento exitoso
    - Estado final: completed
    - Log registra ambos intentos
    """
```

##### E2E-6: Flujo con timeout de agente
```python
async def test_e2e_agent_timeout_handling():
    """
    Test: Timeout en ejecución de agente

    Flujo:
    1. Agente tarda más del timeout configurado
    2. Sistema cancela ejecución
    3. Respuesta indica timeout
    4. Webhook notificado con TIMEOUT
    5. Recursos MCP liberados correctamente

    Validaciones:
    - Timeout detectado
    - Cancelación limpia (no cuelga)
    - MCP registry cerrado
    - Webhook recibe TIMEOUT
    - Log indica timeout y cleanup
    """
```

##### E2E-7: Flujo con múltiples agentes concurrentes
```python
async def test_e2e_concurrent_agent_executions():
    """
    Test: Múltiples ejecuciones concurrentes no interfieren

    Flujo:
    1. Lanzar 5 ejecuciones simultáneas
    2. Diferentes expedientes/tareas
    3. Cada uno con su propio MCP registry
    4. Todas completan exitosamente
    5. Sin race conditions ni state leakage

    Validaciones:
    - 5 agent_run_id únicos
    - Cada ejecución independiente
    - Sin contaminación de datos
    - Todos los webhooks llamados
    - Logs separados por run_id
    """
```

##### E2E-8: Flujo con diferentes tipos de agentes
```python
async def test_e2e_different_agent_types():
    """
    Test: Diferentes tipos de agentes funcionan correctamente

    Flujo:
    1. Ejecutar ValidadorDocumental → éxito
    2. Ejecutar AnalizadorSubvencion → éxito
    3. Ejecutar GeneradorInforme → éxito
    4. Cada uno usa herramientas MCP apropiadas
    5. Resultados específicos a cada agente

    Validaciones:
    - 3 ejecuciones exitosas
    - Herramientas MCP correctas por agente
    - Estructura de resultado apropiada
    - Logs identifican tipo de agente
    """
```

**Archivo sugerido:** `tests/test_integration/test_e2e_flows.py`

---

### 2. Tests de Contrato (Contract Testing)

**Prioridad:** 🔴 ALTA
**Razón:** Garantizan que interfaces no cambian al introducir agentes reales
**Tests actuales:** 0
**Tests propuestos:** 12

#### Tests de Contrato Propuestos:

##### CONTRACT-1: Contrato AgentExecutor.execute()
```python
def test_contract_agent_executor_execute_signature():
    """
    Test: Firma de execute() cumple contrato

    Validaciones:
    - Parámetros: token, expediente_id, tarea_id, agent_config
    - Retorna: AgentExecutionResult
    - Es async (coroutine)
    - Acepta kwargs para extensibilidad futura
    """
```

##### CONTRACT-2: Contrato AgentExecutionResult
```python
def test_contract_agent_execution_result_structure():
    """
    Test: Estructura de AgentExecutionResult es estable

    Validaciones:
    - Campos obligatorios: success, agent_run_id, message
    - Campos opcionales: resultado, error_codigo, tools_used, log_auditoria
    - Tipos correctos (Pydantic validation)
    - Serializable a JSON
    - Backward compatible (campos nuevos son opcionales)
    """
```

##### CONTRACT-3: Contrato BaseAgent.execute()
```python
def test_contract_base_agent_execute_interface():
    """
    Test: Interface de BaseAgent es estable para agentes reales

    Validaciones:
    - Método execute() existe
    - Parámetros: expediente_id, tarea_id, mcp_registry, logger
    - Retorna: Dict con estructura específica
    - Es async
    - Subclases pueden extender sin romper
    """
```

##### CONTRACT-4: Contrato MCPClientRegistry
```python
def test_contract_mcp_client_registry_interface():
    """
    Test: Interface de MCP registry es estable

    Validaciones:
    - Métodos: get_available_tools(), call_tool(), close()
    - call_tool acepta: tool_name, arguments, timeout
    - Retorna: Dict con result o error
    - Todos los métodos async
    - Maneja múltiples servers transparentemente
    """
```

##### CONTRACT-5: Contrato API POST /api/v1/agent/execute
```python
def test_contract_api_execute_request_response():
    """
    Test: Contrato de API es estable (OpenAPI spec)

    Request:
    - Headers: Authorization (Bearer JWT)
    - Body: expediente_id, tarea_id, agent_config, webhook_url

    Response 202:
    - Body: agent_run_id, message, webhook_url

    Response 4xx/5xx:
    - Body: detail, status_code

    Validaciones:
    - OpenAPI schema válido
    - Campos opcionales marcados correctamente
    - Tipos coinciden con Pydantic models
    """
```

##### CONTRACT-6: Contrato Webhook Callback
```python
def test_contract_webhook_payload_structure():
    """
    Test: Payload de webhook es estable

    Validaciones:
    - Campos: agent_run_id, status, expediente_id, tarea_id
    - Campos opcionales: resultado, error_codigo, error_mensaje
    - Timestamp incluido
    - Formato JSON válido
    - Versionado del schema (future-proof)
    """
```

##### CONTRACT-7: Contrato JWTClaims
```python
def test_contract_jwt_claims_structure():
    """
    Test: Estructura de JWT claims es estable

    Validaciones:
    - Claims estándar: iss, sub, aud, exp, iat, nbf, jti
    - Claims custom: exp_id, permisos
    - Tipos correctos
    - Validación Pydantic
    - Backward compatible con tokens antiguos
    """
```

##### CONTRACT-8: Contrato AuditLogger
```python
def test_contract_audit_logger_methods():
    """
    Test: Interface de AuditLogger es estable

    Validaciones:
    - Métodos: info(), error(), warning(), redact_pii()
    - info/error aceptan: mensaje, **context
    - Retorna: None
    - Log lines escritas a archivo
    - Formato JSON lines
    """
```

##### CONTRACT-9: Contrato MCP Tool Call
```python
def test_contract_mcp_tool_call_format():
    """
    Test: Formato de llamada MCP tool es estable

    Request:
    - method: tools/call
    - params: name, arguments
    - headers: Authorization

    Response:
    - content: result o error
    - Formato JSON-RPC 2.0

    Validaciones:
    - Cumple spec MCP
    - Manejo de errores estándar
    """
```

##### CONTRACT-10: Contrato Error Codes
```python
def test_contract_error_codes_are_stable():
    """
    Test: Códigos de error son estables y documentados

    Validaciones:
    - Códigos JWT: AUTH_TOKEN_EXPIRED, AUTH_INVALID_TOKEN, etc.
    - Códigos MCP: MCP_CONNECTION_ERROR, MCP_TOOL_ERROR, etc.
    - Códigos Agent: AGENT_EXECUTION_ERROR, AGENT_TIMEOUT, etc.
    - Códigos API: API_VALIDATION_ERROR, API_WEBHOOK_ERROR, etc.
    - Todos documentados en enum o constantes
    - No se eliminan códigos (solo deprecan)
    """
```

##### CONTRACT-11: Contrato Pydantic Models Serialization
```python
def test_contract_pydantic_models_json_serializable():
    """
    Test: Todos los Pydantic models serializan a JSON

    Validaciones:
    - AgentConfigRequest → JSON
    - ExecuteAgentRequest → JSON
    - AgentExecutionResult → JSON (vía model_dump())
    - JWTClaims → JSON
    - Sin pérdida de datos en round-trip
    """
```

##### CONTRACT-12: Contrato Backward Compatibility
```python
def test_contract_backward_compatibility_old_requests():
    """
    Test: Requests antiguos siguen funcionando

    Validaciones:
    - Request sin campos nuevos opcionales → OK
    - Response con campos nuevos → cliente antiguo ignora
    - Versionado de API (v1) permite evolución
    - Deprecation warnings para features removidos
    """
```

**Archivo sugerido:** `tests/test_contracts/test_interfaces.py`

---

### 3. Tests de Error Handling y Resiliencia ✅ COMPLETADO

**Prioridad:** 🟡 MEDIA-ALTA
**Razón:** Producción requiere manejo robusto de errores
**Tests actuales:** 15 (12 activos + 3 skip)
**Tests propuestos:** 15

**Estado:** ✅ IMPLEMENTADO (2025-12-21)

#### Tests de Error Handling Propuestos:

##### ERROR-1: MCP Server Down
```python
async def test_error_mcp_server_completely_down():
    """
    Test: MCP server completamente caído

    Escenario:
    - MCP server no responde (connection refused)
    - Sistema intenta conectar
    - Timeout después de N segundos
    - Error propagado limpiamente

    Validaciones:
    - No crashea la aplicación
    - Error MCP_CONNECTION_ERROR
    - Mensaje descriptivo
    - Log con detalles de conexión
    - Registry cleanup correcto
    """
```

##### ERROR-2: MCP Tool Error
```python
async def test_error_mcp_tool_execution_fails():
    """
    Test: Herramienta MCP falla durante ejecución

    Escenario:
    - Tool consultar_expediente retorna error
    - Error 404 expediente no encontrado
    - Agente recibe error
    - Decide cómo continuar

    Validaciones:
    - Error MCP_TOOL_ERROR
    - Mensaje incluye nombre del tool
    - Stack trace disponible en logs
    - Agente puede manejar error
    """
```

##### ERROR-3: Network Timeout
```python
async def test_error_network_timeout_during_mcp_call():
    """
    Test: Timeout de red durante llamada MCP

    Escenario:
    - MCP call tarda >timeout configurado
    - Sistema cancela request
    - Error propagado a agente

    Validaciones:
    - Timeout detectado
    - Request cancelado (no cuelga)
    - Error MCP_TIMEOUT
    - Recursos liberados
    """
```

##### ERROR-4: Invalid JWT Format
```python
def test_error_malformed_jwt_token():
    """
    Test: JWT malformado es rechazado

    Escenarios:
    - Token no es JWT válido
    - Token con firma inválida
    - Token sin claims requeridos
    - Token con claim exp_id null

    Validaciones:
    - Error AUTH_INVALID_TOKEN
    - Mensaje específico del problema
    - No expone información sensible
    - Log registra intento
    """
```

##### ERROR-5: Webhook Delivery Failure
```python
async def test_error_webhook_delivery_fails_permanently():
    """
    Test: Webhook falla después de todos los retries

    Escenario:
    - Webhook endpoint retorna 500
    - Sistema intenta N veces
    - Todos fallan
    - Sistema marca como failed

    Validaciones:
    - N retries ejecutados
    - Backoff exponencial aplicado
    - Estado final: webhook_failed
    - Log con todos los intentos
    - Ejecución marcada como completa (no cuelga)
    """
```

##### ERROR-6: Agent Crashes
```python
async def test_error_agent_raises_unhandled_exception():
    """
    Test: Agente lanza excepción no manejada

    Escenario:
    - Agente tiene bug (NoneType error)
    - Excepción no es capturada por agente
    - Sistema la captura en executor

    Validaciones:
    - Error AGENT_EXECUTION_ERROR
    - Stack trace completo en log
    - MCP registry cerrado
    - Webhook notificado de error
    - Sistema sigue funcionando (isolated failure)
    """
```

##### ERROR-7: MCP JSON-RPC Error
```python
async def test_error_mcp_jsonrpc_error_response():
    """
    Test: MCP retorna error JSON-RPC válido

    Escenario:
    - MCP retorna error code -32600 (Invalid Request)
    - Mensaje de error del servidor
    - Sistema lo convierte a MCP_TOOL_ERROR

    Validaciones:
    - Error code preservado
    - Mensaje de MCP incluido
    - Log con request/response completo
    """
```

##### ERROR-8: Database Unavailable (future-proof)
```python
@pytest.mark.skip("Para Paso 4: cuando se agregue BD")
async def test_error_database_connection_lost():
    """
    Test: Base de datos no disponible

    Escenario:
    - Conexión BD se pierde
    - Sistema detecta error
    - Fallback a logs en archivo

    Validaciones:
    - Error DB_CONNECTION_ERROR
    - Sistema sigue funcionando degraded mode
    - Logs escritos a archivo
    - Retry automático de conexión
    """
```

##### ERROR-9: Invalid Agent Configuration
```python
def test_error_invalid_agent_configuration():
    """
    Test: Configuración de agente inválida

    Escenarios:
    - Nombre de agente desconocido
    - system_prompt vacío
    - herramientas no disponibles en MCP
    - modelo LLM inválido

    Validaciones:
    - Error AGENT_CONFIG_ERROR
    - Mensaje específico del problema
    - Validación Pydantic activada
    - No se intenta ejecución
    """
```

##### ERROR-10: Concurrent Modification Conflict
```python
async def test_error_concurrent_modification_same_expediente():
    """
    Test: Dos agentes intentan modificar mismo expediente

    Escenario:
    - Agente A actualiza expediente
    - Agente B intenta actualizar mismo expediente
    - MCP detecta conflicto
    - Uno falla con CONFLICT error

    Validaciones:
    - Error MCP_CONFLICT
    - Versión del expediente preservada
    - Agente puede retry
    - No se pierde ninguna actualización
    """
```

##### ERROR-11: Out of Memory (stress)
```python
@pytest.mark.slow
@pytest.mark.skip("Solo para stress testing")
async def test_error_out_of_memory_handling():
    """
    Test: Sistema maneja out of memory gracefully

    Escenario:
    - Agente procesa documento enorme
    - Memoria se agota
    - Sistema detecta y cancela

    Validaciones:
    - No crashea proceso completo
    - Error AGENT_RESOURCE_ERROR
    - Memoria liberada
    - Otros agentes siguen funcionando
    """
```

##### ERROR-12: Invalid Webhook URL
```python
def test_error_invalid_webhook_url_format():
    """
    Test: URL de webhook inválida es rechazada

    Escenarios:
    - URL no HTTP/HTTPS
    - URL con localhost (SSRF)
    - URL con IP privada
    - URL malformada

    Validaciones:
    - Error API_VALIDATION_ERROR
    - Request rechazado inmediatamente (antes de ejecutar)
    - Validación SSRF funciona
    - Mensaje claro del problema
    """
```

##### ERROR-13: MCP Authorization Error
```python
async def test_error_mcp_authorization_denied():
    """
    Test: MCP rechaza por permisos insuficientes

    Escenario:
    - JWT con permiso 'consulta'
    - Agente intenta tool que requiere 'gestion'
    - MCP rechaza con 403

    Validaciones:
    - Error MCP_PERMISSION_DENIED
    - Mensaje indica permiso faltante
    - Agente notificado del error
    - No retry (error definitivo)
    """
```

##### ERROR-14: PII Redaction Failure
```python
def test_error_pii_redaction_handles_invalid_data():
    """
    Test: PII redactor maneja datos inválidos

    Escenarios:
    - String con encoding inválido
    - Datos binarios en log
    - Ciclos de referencia en objetos

    Validaciones:
    - No crashea el redactor
    - Fallback: redacta todo el objeto
    - Log warning de redaction failure
    - Sistema continúa funcionando
    """
```

##### ERROR-15: API Rate Limiting (future)
```python
@pytest.mark.skip("Para Paso 4: cuando se agregue rate limiting")
async def test_error_api_rate_limit_exceeded():
    """
    Test: Rate limiting protege el sistema

    Escenario:
    - Cliente envía >N requests/segundo
    - Sistema rechaza con 429 Too Many Requests
    - Header Retry-After incluido

    Validaciones:
    - Status 429
    - Header Retry-After presente
    - Rate limit por IP/cliente
    - Log del rate limit
    """
```

**Archivo sugerido:** `tests/test_error_handling/test_resilience.py`

---

### 4. Tests de Concurrencia y Performance

**Prioridad:** 🟡 MEDIA
**Razón:** Importante para producción, pero no bloqueante para Paso 3
**Tests actuales:** 1
**Tests propuestos:** 8

#### Tests de Concurrencia Propuestos:

##### PERF-1: Concurrencia Básica
```python
@pytest.mark.slow
async def test_perf_concurrent_agent_executions_no_interference():
    """
    Test: 10 ejecuciones concurrentes sin interferencia

    Escenario:
    - Lanzar 10 ejecuciones simultáneas
    - Diferentes expedientes
    - Medir tiempo total vs secuencial

    Validaciones:
    - Todas completan exitosamente
    - Sin race conditions
    - Speedup razonable (>5x)
    - Memoria estable
    """
```

##### PERF-2: MCP Connection Pool
```python
async def test_perf_mcp_connection_reuse():
    """
    Test: Conexiones MCP se reusan eficientemente

    Escenario:
    - Múltiples calls a mismo MCP server
    - Verificar que se reusan conexiones HTTP

    Validaciones:
    - 1 conexión TCP para N requests
    - Connection pooling funciona
    - Mejor latencia en calls subsecuentes
    """
```

##### PERF-3: Memory Leak Detection
```python
@pytest.mark.slow
async def test_perf_no_memory_leaks_after_executions():
    """
    Test: No hay memory leaks en ejecuciones repetidas

    Escenario:
    - Ejecutar 100 agentes secuencialmente
    - Medir memoria antes/después

    Validaciones:
    - Memoria se mantiene estable
    - GC funciona correctamente
    - No acumulación de objetos
    """
```

##### PERF-4: API Response Time
```python
@pytest.mark.slow
def test_perf_api_response_time_p95():
    """
    Test: P95 de response time de API < 500ms

    Escenario:
    - 1000 requests a API
    - Medir latencias

    Validaciones:
    - P50 < 100ms
    - P95 < 500ms
    - P99 < 1000ms
    """
```

##### PERF-5: MCP Tool Call Latency
```python
async def test_perf_mcp_tool_call_latency():
    """
    Test: Latencia de MCP tool call razonable

    Escenario:
    - Llamar tool simple 100 veces
    - Medir latencia promedio

    Validaciones:
    - Promedio < 50ms
    - Sin degradación con tiempo
    """
```

##### PERF-6: Webhook Delivery Time
```python
@pytest.mark.slow
async def test_perf_webhook_delivery_time():
    """
    Test: Webhooks se envían rápidamente

    Escenario:
    - Agente completa ejecución
    - Medir tiempo hasta webhook enviado

    Validaciones:
    - Webhook enviado < 100ms después de completion
    - No queueing si webhook responde rápido
    """
```

##### PERF-7: Stress Test
```python
@pytest.mark.slow
@pytest.mark.skip("Solo CI nocturno")
async def test_perf_stress_100_concurrent_agents():
    """
    Test: Sistema maneja 100 agentes concurrentes

    Escenario:
    - 100 ejecuciones simultáneas
    - Sistema bajo carga

    Validaciones:
    - Todas completan (puede tardar)
    - Sin crashes
    - Error rate < 1%
    """
```

##### PERF-8: Resource Cleanup Under Load
```python
@pytest.mark.slow
async def test_perf_resource_cleanup_under_load():
    """
    Test: Recursos se limpian correctamente bajo carga

    Escenario:
    - 50 ejecuciones concurrentes
    - Algunas con errores
    - Verificar cleanup

    Validaciones:
    - Conexiones MCP cerradas
    - Archivos temporales eliminados
    - Memoria liberada
    - No file descriptor leaks
    """
```

**Archivo sugerido:** `tests/test_performance/test_concurrency.py`

---

### 5. Tests de Seguridad Adicionales

**Prioridad:** 🟡 MEDIA
**Razón:** Buena cobertura actual, pero se puede mejorar
**Tests actuales:** 19 (JWT) + 12 (PII)
**Tests propuestos:** 10

#### Tests de Seguridad Propuestos:

##### SEC-1: JWT Replay Attack
```python
def test_sec_jwt_replay_attack_prevention():
    """
    Test: JWT con jti duplicado es rechazado (si se implementa)

    Escenario:
    - Token válido usado 2 veces
    - jti debería ser único

    Validaciones:
    - Segunda vez rechazada (si se implementa cache jti)
    - O documentar que no se previene (stateless)
    """
```

##### SEC-2: SSRF Prevention
```python
def test_sec_webhook_url_ssrf_prevention():
    """
    Test: URLs peligrosas son rechazadas

    URLs rechazadas:
    - http://localhost:8000
    - http://127.0.0.1
    - http://192.168.1.1
    - http://169.254.169.254 (AWS metadata)
    - http://10.0.0.1
    - file:// protocol

    Validaciones:
    - Todas rechazadas con VALIDATION_ERROR
    - Solo URLs públicas permitidas
    """
```

##### SEC-3: SQL Injection (future-proof)
```python
@pytest.mark.skip("Para Paso 4: cuando se agregue BD")
def test_sec_sql_injection_prevention():
    """
    Test: Queries parametrizadas previenen SQL injection

    Escenario:
    - Input con ' OR 1=1--
    - Sistema usa parameterized queries

    Validaciones:
    - No SQL injection
    - ORM escapa correctamente
    """
```

##### SEC-4: XSS Prevention
```python
def test_sec_api_response_sanitizes_html():
    """
    Test: Respuestas API no incluyen HTML sin escapar

    Escenario:
    - Agente retorna <script>alert(1)</script>
    - API retorna como JSON (auto-escaped)

    Validaciones:
    - Content-Type: application/json
    - HTML escaped en strings
    - No interpretación de HTML
    """
```

##### SEC-5: Sensitive Data Logging
```python
def test_sec_sensitive_data_not_logged():
    """
    Test: Datos sensibles nunca en logs

    Escenario:
    - JWT token en request
    - PII en datos de expediente
    - Secrets en environment

    Validaciones:
    - JWT redacted en logs
    - PII redacted (8 tipos)
    - Secrets nunca loggeados
    """
```

##### SEC-6: Authorization Escalation
```python
def test_sec_cannot_access_different_expediente():
    """
    Test: No se puede acceder a expediente no autorizado

    Escenario:
    - JWT con exp_id=EXP-001
    - Request para exp_id=EXP-002

    Validaciones:
    - Error AUTH_EXPEDIENTE_MISMATCH
    - Acceso denegado
    - Intento loggeado
    """
```

##### SEC-7: Header Injection
```python
def test_sec_header_injection_prevention():
    """
    Test: Headers malformados son rechazados

    Escenario:
    - Header con \\r\\n injection
    - Intento de inyectar headers adicionales

    Validaciones:
    - FastAPI rechaza headers malformados
    - No header injection posible
    """
```

##### SEC-8: Path Traversal (future)
```python
@pytest.mark.skip("Cuando se agregue file upload")
def test_sec_path_traversal_prevention():
    """
    Test: Path traversal prevenido en file operations

    Escenario:
    - Filename con ../../../etc/passwd
    - Sistema sanitiza path

    Validaciones:
    - Path normalizado
    - Solo permite directorio configurado
    """
```

##### SEC-9: DoS via Large Payloads
```python
def test_sec_large_payload_rejected():
    """
    Test: Payloads enormes son rechazados

    Escenario:
    - Request con body de 100MB
    - FastAPI lo rechaza

    Validaciones:
    - Error 413 Payload Too Large
    - Límite configurado (ej: 10MB)
    """
```

##### SEC-10: Timing Attack on JWT
```python
def test_sec_jwt_validation_constant_time():
    """
    Test: Validación JWT es constant-time

    Escenario:
    - JWT válido vs inválido
    - Medir tiempo de validación

    Validaciones:
    - Diferencia < 10ms (evita timing attacks)
    - Usa comparación constant-time para firma
    """
```

**Archivo sugerido:** `tests/test_security/test_additional_security.py`

---

### 6. Tests de Regresión para Paso 3

**Prioridad:** 🔴 ALTA (antes de Paso 3)
**Razón:** Garantizan que agentes reales no rompen comportamiento actual
**Tests actuales:** 0
**Tests propuestos:** 8

#### Tests de Regresión Propuestos:

##### REG-1: Mock Agent Baseline
```python
def test_regression_mock_agent_behavior_baseline():
    """
    Test: Capturar comportamiento actual de agentes mock

    Escenario:
    - Ejecutar ValidadorDocumental con datos conocidos
    - Guardar resultado exacto como baseline

    Validaciones:
    - Resultado idéntico a baseline guardado
    - Si cambia, test falla (regression detected)
    - Baseline versionado en git
    """
```

##### REG-2: API Response Format Stability
```python
def test_regression_api_response_format_unchanged():
    """
    Test: Formato de respuesta API no cambia

    Escenario:
    - POST /api/v1/agent/execute
    - Verificar estructura exacta de respuesta

    Validaciones:
    - Campos esperados presentes
    - Sin campos removidos
    - Tipos de datos correctos
    - Schema validation
    """
```

##### REG-3: Webhook Payload Format Stability
```python
def test_regression_webhook_payload_unchanged():
    """
    Test: Payload de webhook mantiene formato

    Validaciones:
    - Campos obligatorios presentes
    - Estructura JSON estable
    - Clientes existentes no se rompen
    """
```

##### REG-4: Error Codes Stability
```python
def test_regression_error_codes_not_changed():
    """
    Test: Códigos de error no cambian

    Validaciones:
    - Todos los códigos de error existentes preservados
    - Mensajes de error no cambian radicalmente
    - Códigos nuevos OK, pero no remover
    """
```

##### REG-5: MCP Tool Usage Pattern
```python
def test_regression_mcp_tool_usage_pattern():
    """
    Test: Patrón de uso de MCP tools no cambia

    Escenario:
    - Agente ValidadorDocumental
    - Verificar qué tools usa y en qué orden

    Validaciones:
    - Mismo conjunto de tools
    - Orden similar (puede variar con AI)
    - No tools faltantes
    """
```

##### REG-6: Performance Baseline
```python
@pytest.mark.slow
def test_regression_performance_not_degraded():
    """
    Test: Performance no se degrada

    Escenario:
    - Ejecutar 10 agentes
    - Medir tiempo total

    Validaciones:
    - Tiempo < baseline * 1.2 (20% tolerancia)
    - No degradación significativa
    """
```

##### REG-7: Log Format Stability
```python
def test_regression_log_format_unchanged():
    """
    Test: Formato de logs de auditoría no cambia

    Validaciones:
    - JSON lines format
    - Campos obligatorios presentes
    - Parsers externos no se rompen
    """
```

##### REG-8: Agent Interface Compatibility
```python
def test_regression_agent_interface_backward_compatible():
    """
    Test: Interface de agente es backward compatible

    Escenario:
    - Crear agente mock simple (como los actuales)
    - Verificar que sigue funcionando con agentes reales

    Validaciones:
    - BaseAgent interface no cambió
    - Métodos nuevos son opcionales
    - Agentes antiguos siguen funcionando
    """
```

**Archivo sugerido:** `tests/test_regression/test_paso3_compatibility.py`

---

### 7. Tests de Datos y Validación

**Prioridad:** 🟢 BAJA-MEDIA
**Razón:** Pydantic ya valida, pero casos edge pueden mejorarse
**Tests actuales:** Implícito en otros tests
**Tests propuestos:** 6

#### Tests de Validación Propuestos:

##### DATA-1: Pydantic Validation Comprehensive
```python
def test_data_pydantic_models_validate_edge_cases():
    """
    Test: Modelos Pydantic validan casos edge

    Casos:
    - Strings vacíos
    - Campos None en opcionales
    - Listas vacías
    - Números negativos
    - Strings muy largos (>10000 chars)

    Validaciones:
    - Validation error apropiado
    - Mensajes claros
    """
```

##### DATA-2: Date/Time Handling
```python
def test_data_datetime_formats_accepted():
    """
    Test: Diferentes formatos de fecha aceptados

    Formatos:
    - ISO 8601 con Z
    - ISO 8601 con +00:00
    - Unix timestamp

    Validaciones:
    - Todos parseados correctamente
    - Conversiónión a UTC
    - Timezone aware
    """
```

##### DATA-3: Unicode Handling
```python
def test_data_unicode_characters_handled():
    """
    Test: Caracteres Unicode manejados correctamente

    Casos:
    - Nombres con tildes: José, María
    - Emojis: 🎉 (si se permiten)
    - Caracteres especiales: €, £

    Validaciones:
    - Encoding UTF-8 correcto
    - No corrupción de datos
    - JSON serialization OK
    """
```

##### DATA-4: Numeric Precision
```python
def test_data_numeric_precision_preserved():
    """
    Test: Precisión numérica preservada

    Casos:
    - Decimales: 1234.56789
    - Muy grandes: 1e308
    - Muy pequeños: 1e-308

    Validaciones:
    - Sin pérdida de precisión
    - JSON number format
    """
```

##### DATA-5: List/Dict Edge Cases
```python
def test_data_list_dict_edge_cases():
    """
    Test: Listas y dicts edge cases

    Casos:
    - Lista vacía: []
    - Dict vacío: {}
    - Nested deep: 10 niveles
    - Listas grandes: 10000 elementos

    Validaciones:
    - Serialization funciona
    - No stack overflow
    - Performance aceptable
    """
```

##### DATA-6: URL Validation
```python
def test_data_url_validation_comprehensive():
    """
    Test: Validación de URLs completa

    URLs válidas:
    - https://example.com
    - https://example.com:8443
    - https://example.com/path?query=1

    URLs inválidas:
    - javascript:alert(1)
    - data:text/html,<script>
    - ftp://example.com

    Validaciones:
    - Pydantic HttpUrl funciona
    - Solo HTTP/HTTPS permitidos
    """
```

**Archivo sugerido:** `tests/test_data_validation/test_pydantic_edge_cases.py`

---

## 📂 Estructura de Tests Propuesta

```
tests/
├── test_api/                      # 22 tests existentes
│   ├── test_agent_endpoints.py
│   ├── test_health_endpoints.py
│   └── test_webhook_validation.py
│
├── test_mcp/                      # 34 tests existentes
│   ├── test_auth.py
│   ├── test_resources.py
│   ├── test_server_http.py
│   └── test_tools.py
│
├── test_backoffice/               # 87 tests existentes
│   ├── test_executor.py
│   ├── test_jwt_validator.py
│   ├── test_logging.py
│   ├── test_mcp_integration.py
│   └── test_protocols.py
│
├── test_contracts/                # 12 tests existentes ✅
│   └── test_interfaces.py
│
├── test_error_handling/           # 15 tests existentes ✅
│   └── test_resilience.py
│
├── test_integration/              # NUEVO: 8 tests E2E propuestos
│   ├── conftest.py
│   └── test_e2e_flows.py
│
├── test_performance/              # NUEVO: 8 tests de performance propuestos
│   └── test_concurrency.py
│
├── test_security/                 # NUEVO: 10 tests de seguridad propuestos
│   └── test_additional_security.py
│
├── test_regression/               # NUEVO: 8 tests de regresión propuestos
│   └── test_paso3_compatibility.py
│
└── test_data_validation/          # NUEVO: 6 tests de validación propuestos
    └── test_pydantic_edge_cases.py
```

**Tests implementados:** 27 (12 contracts + 15 error handling) ✅
**Tests propuestos restantes:** +40 tests nuevos
**Total actual:** 170 tests (166 pass + 4 skip)
**Total proyectado final:** 142 + 67 = **209 tests**

---

## 🎯 Plan de Implementación Sugerido

### Fase 1: Tests Críticos para Paso 2 (Prioridad ALTA)
**Duración:** 1-2 semanas
**Tests:** 28

1. **E2E Tests (8)** - Validar flujos completos
2. **Contract Tests (12)** - Garantizar estabilidad de interfaces
3. **Regression Tests (8)** - Preparar para Paso 3

**Objetivo:** Asegurar que API REST está lista para producción

### Fase 2: Tests de Robustez (Prioridad MEDIA)
**Duración:** 1 semana
**Tests:** 25

1. **Error Handling (15)** - Cubrir todos los casos de error
2. **Security (10)** - Fortalecer seguridad

**Objetivo:** Sistema resiliente ante errores

### Fase 3: Tests de Performance (Prioridad BAJA)
**Duración:** 1 semana
**Tests:** 14

1. **Concurrency (8)** - Validar comportamiento bajo carga
2. **Data Validation (6)** - Edge cases de datos

**Objetivo:** Sistema listo para carga de producción

---

## 🔧 Herramientas y Configuración Recomendadas

### pytest-asyncio
```ini
# pytest.ini (ya configurado)
asyncio_mode = strict
```

### pytest-timeout
```bash
pip install pytest-timeout
```

```python
@pytest.mark.timeout(30)  # Test no debe tardar >30s
async def test_e2e_...():
    ...
```

### pytest-benchmark
```bash
pip install pytest-benchmark
```

```python
def test_perf_api_latency(benchmark):
    result = benchmark(lambda: call_api())
    assert result < 100  # ms
```

### pytest-httpx (para mock HTTP)
```bash
pip install pytest-httpx
```

```python
def test_webhook_delivery(httpx_mock):
    httpx_mock.add_response(url="https://example.com/webhook", status_code=200)
    # Test webhook delivery
```

### Coverage mínimo
```ini
# pytest.ini
[coverage:report]
fail_under = 80  # 80% coverage mínimo
```

---

## 📊 Métricas de Éxito

### Cobertura de Tests
- **Actual:** ~75% estimado
- **Objetivo Fase 1:** 85%
- **Objetivo Fase 2:** 90%
- **Objetivo Final:** 95%

### Tests por Categoría
| Categoría | Actual | Objetivo |
|-----------|--------|----------|
| Unit | 80 | 100 |
| Integration | 15 | 35 |
| E2E | 0 | 8 |
| Contract | 0 | 12 |
| Security | 31 | 41 |
| Performance | 1 | 9 |
| **TOTAL** | **142** | **209** |

### Calidad
- **Flakiness:** 0% (tests deben ser deterministas)
- **Test Execution Time:** <5 minutos suite completa
- **CI/CD:** Todos los tests pasan en cada commit

---

## 🚀 Próximos Pasos Inmediatos

### Acción 1: Crear estructura de carpetas
```bash
mkdir -p tests/test_integration
mkdir -p tests/test_contracts
mkdir -p tests/test_error_handling
mkdir -p tests/test_performance
mkdir -p tests/test_security
mkdir -p tests/test_regression
mkdir -p tests/test_data_validation
```

### Acción 2: Implementar tests E2E (Fase 1)
Comenzar con `tests/test_integration/test_e2e_flows.py` - 8 tests más críticos

### Acción 3: Implementar tests de contrato (Fase 1)
Definir contratos en `tests/test_contracts/test_interfaces.py` - 12 tests

### Acción 4: Configurar CI/CD
Asegurar que todos los tests corren en cada PR

---

## 📝 Notas Finales

### ¿Por qué estos tests?

1. **E2E:** Validan que el sistema funciona de punta a punta
2. **Contratos:** Garantizan que cambios no rompen integraciones
3. **Errores:** Producción siempre tiene errores, debemos manejarlos
4. **Performance:** Sistema debe escalar
5. **Seguridad:** Protección contra ataques
6. **Regresión:** Cambios futuros no rompen lo actual

### ¿Cuándo NO escribir un test?

- Test trivial que no aporta valor
- Test que duplica otro test
- Test que es más código que la feature
- Test flaky (aleatorio)

### Filosofía

> "Tests no son para encontrar bugs, son para **prevenir** que bugs lleguen a producción"

---

---

## ✅ Estado de Implementación

**Última actualización:** 2025-12-21

### Tests de Error Handling - COMPLETADOS ✅

**Archivo:** `tests/test_error_handling/test_resilience.py`

**Tests implementados: 15 (12 activos + 3 skip)**

| Test | Estado | Descripción |
|------|--------|-------------|
| ERROR-1 | ✅ PASS | MCP Server Down |
| ERROR-2 | ✅ PASS | MCP Tool Error |
| ERROR-3 | ✅ PASS | Network Timeout |
| ERROR-4 | ✅ PASS | Invalid JWT Format |
| ERROR-5 | ✅ PASS | Webhook Delivery Failure (con retry) |
| ERROR-6 | ✅ PASS | Agent Crashes |
| ERROR-7 | ✅ PASS | MCP JSON-RPC Error |
| ERROR-8 | ⏭️ SKIP | Database Unavailable (Paso 4) |
| ERROR-9 | ✅ PASS | Invalid Agent Configuration |
| ERROR-10 | ✅ PASS | Concurrent Modification Conflict |
| ERROR-11 | ⏭️ SKIP | Out of Memory (stress testing) |
| ERROR-12 | ✅ PASS | Invalid Webhook URL (SSRF) |
| ERROR-13 | ✅ PASS | MCP Authorization Error |
| ERROR-14 | ✅ PASS | PII Redaction Failure |
| ERROR-15 | ⏭️ SKIP | API Rate Limiting (Paso 4) |

**Código de producción modificado:**
1. `src/backoffice/models.py` - Agregado código `MCP_CONFLICT`
2. `src/backoffice/mcp/client.py` - Manejo HTTP 409
3. `src/backoffice/logging/pii_redactor.py` - Error handling robusto
4. `src/api/services/webhook.py` - Función `send_webhook_with_retry()`

**Métricas:**
- Total tests: 170 (166 pass + 4 skip)
- Tests nuevos: 15 (12 pass + 3 skip)
- Código producción: ~95 LOC
- Código tests: ~750 LOC
- Tiempo ejecución: ~0.6s (error handling), ~3s (suite completa)

---

### Tests de Contracts - COMPLETADOS ✅

**Archivo:** `tests/test_contracts/test_interfaces.py`

**Tests implementados: 12 (100% pass)**

| Test | Estado | Descripción |
|------|--------|-------------|
| CONTRACT-1 | ✅ PASS | MCPClient.call_tool signature |
| CONTRACT-2 | ✅ PASS | MCPClient.list_tools signature |
| CONTRACT-3 | ✅ PASS | MCPClient exception contracts |
| CONTRACT-4 | ✅ PASS | MCPClient async behavior |
| CONTRACT-5 | ✅ PASS | AgentRegistry.get signature |
| CONTRACT-6 | ✅ PASS | AgentRegistry.list signature |
| CONTRACT-7 | ✅ PASS | AgentRegistry exception contracts |
| CONTRACT-8 | ✅ PASS | AgentRegistry lifecycle |
| CONTRACT-9 | ✅ PASS | ConfigLoader.load signature |
| CONTRACT-10 | ✅ PASS | ConfigLoader.validate signature |
| CONTRACT-11 | ✅ PASS | ConfigLoader exception contracts |
| CONTRACT-12 | ✅ PASS | ConfigLoader immutability |

**Propósito:**
- Garantizar estabilidad de interfaces públicas
- Detectar cambios incompatibles antes de Paso 3
- Documentar contratos esperados para agentes reales

**Métricas:**
- Total tests: 12 (100% pass)
- Código tests: ~480 LOC
- Tiempo ejecución: ~0.3s
- Cobertura: Interfaces críticas para backward compatibility

**Integración:**
- Incluidos en `run-tests.sh` junto con otras suites
- Ejecutados automáticamente en cada run
- Parte del total de 170 tests

---

**Documento creado:** 2025-12-20
**Implementación completada:** 2025-12-21
**Autor:** Claude Code
**Estado:** ✅ IMPLEMENTADO - Tests de Error Handling y Contracts completos
