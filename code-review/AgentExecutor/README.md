# Code Review: AgentExecutor

**Clase Central de aGEntiX**

**Fecha:** 2024-12-07
**Revisor:** Claude Code
**Archivo:** `backoffice/executor.py`
**Líneas:** 234
**Criterio:** Prioridad en tests unitarios, robustez, inyección de dependencias

---

## Resumen Ejecutivo

### Estado Actual

**AgentExecutor** es el orquestador principal del sistema aGEntiX, responsable de coordinar:
1. Validación JWT (seguridad)
2. Configuración MCP (infraestructura)
3. Discovery de herramientas (routing)
4. Creación y ejecución de agentes
5. Manejo de errores estructurado
6. Auditoría completa

### Calificación

| Aspecto | Calificación | Observaciones |
|---------|--------------|---------------|
| **Robustez** | ⭐⭐⭐⭐☆ (4/5) | Buen manejo de errores, falta test coverage |
| **Inyección de Dependencias** | ⭐⭐☆☆☆ (2/5) | Acoplamiento alto a implementaciones concretas |
| **Tests Unitarios** | ⭐☆☆☆☆ (1/5) | **CRÍTICO:** No existen tests unitarios de AgentExecutor |
| **Separación de responsabilidades** | ⭐⭐⭐⭐☆ (4/5) | Buena delegación a componentes |
| **Código limpio** | ⭐⭐⭐⭐⭐ (5/5) | Excelente legibilidad y documentación |

### Hallazgos Críticos

🔴 **CRÍTICO - NO HAY TESTS UNITARIOS**
- La clase central del sistema NO tiene tests unitarios dedicados
- Solo hay tests de integración en `test_mcp_integration.py` (15 tests MCP)
- Imposible verificar comportamiento aislado de AgentExecutor

🟡 **IMPORTANTE - Acoplamiento Alto**
- Dependencias concretas hardcodeadas en constructor
- Difícil inyectar mocks para testing
- No hay interfaces/abstracciones para componentes clave

🟡 **IMPORTANTE - Falta Validación de Entrada**
- No valida parámetros de entrada en `execute()`
- Asume que `agent_config` es válido
- No verifica formato de IDs (expediente_id, tarea_id)

---

## Análisis Detallado

### 1. Inyección de Dependencias ⭐⭐☆☆☆ (2/5)

#### Problema Principal: Constructor con Configuración en lugar de Dependencias

**Actual:**
```python
def __init__(self, mcp_config_path: str, log_dir: str,
             jwt_secret: str, jwt_algorithm: str = "HS256"):
    self.mcp_config_path = mcp_config_path
    self.log_dir = Path(log_dir)
    self.jwt_secret = jwt_secret
    self.jwt_algorithm = jwt_algorithm
```

**Problemas:**
1. El constructor recibe **configuración** en lugar de **dependencias**
2. Dentro de `execute()`, instancia directamente:
   - `AuditLogger` (línea 63)
   - `MCPServersConfig.load_from_file()` (línea 103)
   - `MCPClientRegistry` (línea 107)
   - `validate_jwt()` (función global, línea 76)
3. Imposible inyectar mocks para testing unitario
4. Viola el principio de Inversión de Dependencias (SOLID)

#### Líneas Problemáticas

**Línea 63-67: Instanciación directa de AuditLogger**
```python
logger = AuditLogger(
    expediente_id=expediente_id,
    agent_run_id=agent_run_id,
    log_dir=self.log_dir
)
```
❌ No se puede mockear para tests
❌ Acoplado a implementación concreta

**Línea 103: Carga directa de configuración**
```python
mcp_config = MCPServersConfig.load_from_file(self.mcp_config_path)
```
❌ Depende del filesystem
❌ No se puede inyectar configuración mock

**Línea 107-110: Instanciación directa de MCPClientRegistry**
```python
mcp_registry = MCPClientRegistry(
    config=mcp_config,
    token=token
)
```
❌ No se puede mockear para tests
❌ Acopla a implementación concreta HTTP

**Línea 76: Llamada a función global validate_jwt**
```python
claims = validate_jwt(
    token=token,
    secret=self.jwt_secret,
    # ...
)
```
❌ Función global difícil de mockear
❌ Importa settings internamente (acoplamiento oculto)

#### Impacto en Testing

**Escenario imposible de testear unitariamente:**
```python
# ❌ Esto NO es posible actualmente
def test_executor_handles_jwt_error():
    mock_validator = Mock(side_effect=JWTValidationError(...))
    executor = AgentExecutor(validator=mock_validator, ...)

    result = await executor.execute(...)
    assert result.success is False
```

La única forma actual es **test de integración** (con servidor MCP real o mocks HTTP complejos).

### 2. Robustez en Manejo de Errores ⭐⭐⭐⭐☆ (4/5)

#### Fortalezas ✅

**1. Captura exhaustiva de excepciones (líneas 162-228)**
```python
except MCPConnectionError as e:    # Errores de red
except MCPAuthError as e:           # Errores 401/403
except MCPToolError as e:           # Errores de tool
except Exception as e:              # Catch-all final
```
✅ Categorización semántica de errores
✅ Siempre retorna `AgentExecutionResult` estructurado
✅ Nunca lanza excepciones al caller

**2. Logger temprano (línea 62)**
```python
# 0. Crear logger temprano para capturar todos los eventos
logger = AuditLogger(...)
```
✅ Garantiza que incluso errores de JWT se loguean
✅ No se pierde auditoría en ningún caso

**3. Cleanup garantizado (línea 230-233)**
```python
finally:
    if mcp_registry:
        await mcp_registry.close()
```
✅ Cierra conexiones HTTP siempre
✅ Previene resource leaks

#### Debilidades ⚠️

**1. No valida parámetros de entrada**
```python
async def execute(
    self,
    token: str,              # ¿Vacío? ¿None?
    expediente_id: str,      # ¿Formato válido?
    tarea_id: str,           # ¿Vacío?
    agent_config: AgentConfig
) -> AgentExecutionResult:
```

❌ No verifica que `token` no esté vacío
❌ No valida formato de `expediente_id` (ej: "EXP-YYYY-NNN")
❌ Asume que `agent_config` es válido (podría tener nombre vacío)

**Ejemplo de fallo:**
```python
# Esto NO falla hasta llegar a validate_jwt
await executor.execute(
    token="",  # Token vacío
    expediente_id="invalid",
    tarea_id="",
    agent_config=AgentConfig(nombre="", ...)  # Nombre vacío
)
```

**2. Error handling oculta detalles en Exception genérico**
```python
except Exception as e:
    return AgentExecutionResult(
        success=False,
        error=AgentError(
            codigo="INTERNAL_ERROR",
            mensaje=f"Error interno: {type(e).__name__}",
            detalle=str(e)  # Puede ser críptico
        )
    )
```

⚠️ `INTERNAL_ERROR` es vago (¿qué tipo de error interno?)
⚠️ `detalle` puede no ser útil sin stacktrace

**3. No valida resultado del agente**
```python
resultado = await agent.execute()  # línea 150

return AgentExecutionResult(
    success=True,
    resultado=resultado,  # ¿Y si no es un Dict válido?
    ...
)
```

❌ No verifica que `resultado` tenga estructura esperada
❌ Asume que el agente retorna Dict bien formado

### 3. Tests Unitarios ⭐☆☆☆☆ (1/5)

#### Estado Actual: **CRÍTICO**

**NO EXISTEN TESTS UNITARIOS DEDICADOS A `AgentExecutor`**

**Evidencia:**
```bash
$ grep -r "class.*Test.*Executor" backoffice/tests/
# Sin resultados

$ grep -r "def test.*executor" backoffice/tests/
# Sin resultados

$ ls backoffice/tests/
test_jwt_validator.py      # 19 tests JWT
test_mcp_integration.py    # 15 tests MCP (integración)
test_logging.py            # 12 tests PII
conftest.py
```

#### Cobertura Actual (Indirecta)

Los tests existentes tocan `AgentExecutor` solo de forma **indirecta**:

**test_mcp_integration.py** (15 tests)
- Testa `MCPClient` y `MCPClientRegistry` directamente
- **NO** testa `AgentExecutor.execute()`
- **NO** verifica el flujo completo de ejecución

**test_jwt_validator.py** (19 tests)
- Testa `validate_jwt()` como función standalone
- **NO** testa integración con `AgentExecutor`
- **NO** verifica que AgentExecutor maneje JWTValidationError correctamente

#### Escenarios NO Cubiertos (CRÍTICOS)

❌ **Validación JWT fallida retorna error estructurado**
```python
# Este test NO existe
async def test_executor_jwt_expired_returns_error():
    # Setup
    executor = AgentExecutor(...)
    expired_token = generate_expired_token()

    # Execute
    result = await executor.execute(
        token=expired_token,
        expediente_id="EXP-2024-001",
        ...
    )

    # Assert
    assert result.success is False
    assert result.error.codigo == "AUTH_TOKEN_EXPIRED"
    assert len(result.log_auditoria) > 0  # Logger capturó el error
```

❌ **Agente no configurado retorna error apropiado**
```python
# Este test NO existe
async def test_executor_unknown_agent_returns_error():
    executor = AgentExecutor(...)
    config = AgentConfig(nombre="AgentInexistente", ...)

    result = await executor.execute(...)

    assert result.success is False
    assert result.error.codigo == "AGENT_NOT_CONFIGURED"
```

❌ **Ejecución exitosa retorna resultado esperado**
```python
# Este test NO existe
async def test_executor_success_returns_expected_result():
    # Mock del registry y agente
    mock_registry = Mock()
    mock_agent = Mock()
    mock_agent.execute.return_value = {"completado": True}

    executor = AgentExecutor(registry_factory=lambda: mock_registry, ...)

    result = await executor.execute(...)

    assert result.success is True
    assert result.resultado == {"completado": True}
    assert "ValidadorDocumental" in result.herramientas_usadas
```

❌ **Cleanup se ejecuta incluso con errores**
```python
# Este test NO existe
async def test_executor_closes_registry_on_error():
    mock_registry = Mock()
    mock_registry.initialize = Mock(side_effect=Exception("Boom"))

    executor = AgentExecutor(...)

    result = await executor.execute(...)

    # Verificar que close() se llamó
    mock_registry.close.assert_called_once()
```

❌ **Logger captura todos los pasos**
```python
# Este test NO existe
async def test_executor_logs_all_steps():
    executor = AgentExecutor(...)

    result = await executor.execute(...)

    assert "Iniciando ejecución" in result.log_auditoria[0]
    assert "Validando token JWT" in result.log_auditoria[1]
    assert "Creando registry" in result.log_auditoria[2]
```

#### Comparación con Componentes Similares

| Componente | Tests Unitarios | Tests Integración | Cobertura |
|------------|-----------------|-------------------|-----------|
| `JWTValidator` | ✅ 19 tests | N/A | ~100% |
| `PIIRedactor` | ✅ 12 tests | N/A | ~100% |
| `MCPClient` | ✅ 10 tests | ✅ 5 tests | ~95% |
| **`AgentExecutor`** | ❌ **0 tests** | ❌ 0 tests | **0%** |

**La clase CENTRAL del sistema tiene 0% de cobertura directa.**

### 4. Separación de Responsabilidades ⭐⭐⭐⭐☆ (4/5)

#### Fortalezas ✅

**Buena delegación:**
```python
# Validación JWT → jwt_validator.py
claims = validate_jwt(...)

# Logging → audit_logger.py
logger = AuditLogger(...)
logger.log("...")

# Routing MCP → mcp/registry.py
mcp_registry = MCPClientRegistry(...)
await mcp_registry.call_tool(...)

# Lógica de negocio → agents/
agent = agent_class(...)
resultado = await agent.execute()
```

✅ AgentExecutor NO contiene lógica de negocio
✅ Responsabilidades claras: orquestar, no implementar
✅ Cada componente tiene una única responsabilidad

#### Debilidades ⚠️

**1. Mezcla configuración con lógica de ejecución**
```python
# En execute(), mezcla setup con lógica
mcp_config = MCPServersConfig.load_from_file(self.mcp_config_path)  # Config
mcp_registry = MCPClientRegistry(config=mcp_config, token=token)    # Setup
await mcp_registry.initialize()                                     # I/O
```

⚠️ `execute()` hace 3 cosas: configurar, setup, ejecutar
⚠️ Dificulta testing de cada fase

**2. Constructor guarda configuración en lugar de dependencias**
```python
def __init__(self, mcp_config_path: str, log_dir: str, ...):
    self.mcp_config_path = mcp_config_path  # Path, no objeto
    self.log_dir = Path(log_dir)            # Path, no logger
```

⚠️ Responsabilidad de crear dependencias está en `execute()`, no en `__init__`
⚠️ Dificulta preparar executor para múltiples ejecuciones

### 5. Código Limpio ⭐⭐⭐⭐⭐ (5/5)

#### Fortalezas ✅

**Excelente documentación:**
```python
"""
Ejecuta un agente y maneja errores del cliente MCP.

Args:
    token: Token JWT completo
    expediente_id: ID del expediente
    tarea_id: ID de la tarea BPMN
    agent_config: Configuración del agente

Returns:
    Resultado de la ejecución del agente
"""
```

✅ Docstrings completos en clase y métodos
✅ Comentarios inline explicativos (ej: "# 0. Crear logger temprano")
✅ Nombres descriptivos de variables

**Estructura clara:**
```python
try:
    # 0. Logger
    # 1. Validar JWT
    # 2. Cargar config
    # 3. Crear registry
    # 4. Inicializar
    # 5. Crear agente
    # 6. Ejecutar
except MCPConnectionError:
except MCPAuthError:
except MCPToolError:
except Exception:
finally:
    # Cleanup
```

✅ Flujo secuencial numerado
✅ Error handling exhaustivo
✅ Cleanup garantizado

**Type hints completos:**
```python
async def execute(
    self,
    token: str,
    expediente_id: str,
    tarea_id: str,
    agent_config: AgentConfig
) -> AgentExecutionResult:
```

✅ Todos los parámetros tipados
✅ Retorno explícito
✅ Usa modelos Pydantic (AgentConfig, AgentExecutionResult)

---

## Hallazgos por Categoría

### 🔴 Críticos (Deben resolverse)

1. **NO HAY TESTS UNITARIOS**
   - Archivo: `backoffice/executor.py`
   - Impacto: Imposible verificar comportamiento de forma aislada
   - Riesgo: Regresiones no detectadas en refactorings
   - Prioridad: **P0 (CRÍTICA)**

2. **Acoplamiento Alto - No hay inyección de dependencias**
   - Líneas: 63, 103, 107, 76
   - Impacto: Imposible mockear componentes para testing
   - Riesgo: Tests solo pueden ser de integración (lentos, frágiles)
   - Prioridad: **P0 (CRÍTICA)**

### 🟡 Importantes (Deberían resolverse)

3. **No valida parámetros de entrada**
   - Línea: 38-44 (firma de execute)
   - Impacto: Errores tardíos, mensajes confusos
   - Riesgo: Fallo silencioso con datos inválidos
   - Prioridad: **P1 (ALTA)**

4. **No valida resultado del agente**
   - Línea: 150-160
   - Impacto: Puede retornar datos mal formados
   - Riesgo: Errores en BPMN al procesar resultado
   - Prioridad: **P1 (ALTA)**

5. **Exception genérico captura demasiado**
   - Línea: 213-228
   - Impacto: Errores inesperados pierden contexto
   - Riesgo: Debugging difícil en producción
   - Prioridad: **P2 (MEDIA)**

### 🟢 Mejoras (Opcional)

6. **Constructor guarda configuración en lugar de dependencias**
   - Línea: 23-36
   - Impacto: Patrón menos flexible
   - Riesgo: Dificulta evolución futura
   - Prioridad: **P3 (BAJA)**

7. **execute() hace demasiadas cosas**
   - Línea: 38-234
   - Impacto: Método muy largo (196 líneas)
   - Riesgo: Difícil de entender de un vistazo
   - Prioridad: **P3 (BAJA)**

---

## Métricas de Calidad

### Complejidad Ciclomática

**Método `execute()`:**
- Bloques try/except: 5
- Condicionales: ~8
- **Complejidad estimada: ~15** (umbral recomendado: 10)

⚠️ Método complejo, candidato a refactoring

### Cobertura de Tests

| Tipo de Test | Actual | Objetivo | Gap |
|--------------|--------|----------|-----|
| Unitarios | **0%** | 80% | -80% |
| Integración | ~30% (indirecto) | 50% | -20% |
| E2E | 0% | 20% | -20% |
| **Total** | **10%** | **70%** | **-60%** |

🔴 Cobertura CRÍTICA: Solo 10% vs objetivo 70%

### Líneas de Código

- **Total clase:** 234 líneas
- **Método execute():** 196 líneas (84%)
- **Manejo de errores:** 66 líneas (28%)
- **Lógica core:** 61 líneas (26%)
- **Logging:** 15 líneas (6%)

⚠️ execute() concentra 84% del código → candidato a split

---

## Recomendaciones

### 1. Crear Suite de Tests Unitarios (P0 - CRÍTICA)

**Objetivo:** Alcanzar 80% de cobertura con tests rápidos (<100ms cada uno)

**Tests mínimos requeridos:**

```python
# backoffice/tests/test_executor.py (NUEVO ARCHIVO)

class TestAgentExecutor:
    """Tests unitarios de AgentExecutor"""

    # === Validación JWT ===
    async def test_jwt_expired_returns_auth_error(self)
    async def test_jwt_invalid_signature_returns_auth_error(self)
    async def test_jwt_wrong_expediente_returns_mismatch_error(self)
    async def test_jwt_insufficient_permissions_returns_permission_error(self)
    async def test_jwt_valid_proceeds_to_execution(self)

    # === Configuración MCP ===
    async def test_mcp_config_file_not_found_returns_error(self)
    async def test_mcp_config_invalid_yaml_returns_error(self)
    async def test_mcp_config_valid_creates_registry(self)

    # === Inicialización Registry ===
    async def test_registry_init_timeout_returns_connection_error(self)
    async def test_registry_init_success_discovers_tools(self)
    async def test_registry_init_partial_failure_continues(self)

    # === Creación de Agente ===
    async def test_unknown_agent_type_returns_config_error(self)
    async def test_agent_creation_success_returns_instance(self)

    # === Ejecución de Agente ===
    async def test_agent_execute_success_returns_result(self)
    async def test_agent_execute_mcp_error_returns_tool_error(self)
    async def test_agent_execute_unexpected_error_returns_internal_error(self)

    # === Logging y Auditoría ===
    async def test_logger_created_early_captures_jwt_error(self)
    async def test_logger_captures_all_steps_on_success(self)
    async def test_logger_pii_redacted_in_output(self)

    # === Cleanup ===
    async def test_registry_closed_on_success(self)
    async def test_registry_closed_on_error(self)
    async def test_registry_closed_on_exception(self)

    # === Validación de Entrada ===
    async def test_empty_token_returns_validation_error(self)
    async def test_empty_expediente_id_returns_validation_error(self)
    async def test_invalid_agent_config_returns_validation_error(self)

    # === Resultado ===
    async def test_success_result_includes_all_fields(self)
    async def test_error_result_includes_error_details(self)
    async def test_tools_used_tracked_correctly(self)
```

**Total recomendado:** 30 tests unitarios

### 2. Refactorizar para Inyección de Dependencias (P0 - CRÍTICA)

**Objetivo:** Permitir inyección de mocks para testing

**Propuesta de refactoring:**

```python
# Opción A: Inyección por constructor (más estándar)
class AgentExecutor:
    def __init__(
        self,
        jwt_validator: JWTValidatorProtocol,
        config_loader: ConfigLoaderProtocol,
        registry_factory: MCPRegistryFactory,
        logger_factory: AuditLoggerFactory,
        agent_registry: AgentRegistryProtocol
    ):
        self.jwt_validator = jwt_validator
        self.config_loader = config_loader
        self.registry_factory = registry_factory
        self.logger_factory = logger_factory
        self.agent_registry = agent_registry

    async def execute(self, token, expediente_id, tarea_id, agent_config):
        # Usar dependencias inyectadas
        logger = self.logger_factory.create(expediente_id, ...)
        claims = self.jwt_validator.validate(token, ...)
        config = self.config_loader.load()
        registry = self.registry_factory.create(config, token)
        agent = self.agent_registry.get(agent_config.nombre)
        # ...
```

**Ventajas:**
- ✅ Fácil inyectar mocks en tests
- ✅ Sigue principios SOLID
- ✅ Facilita evolución futura

**Opción B: Inyección por método (menos invasivo)**
```python
async def execute(
    self,
    token: str,
    expediente_id: str,
    tarea_id: str,
    agent_config: AgentConfig,
    # Dependencias opcionales para testing
    jwt_validator: Optional[JWTValidatorProtocol] = None,
    registry_factory: Optional[MCPRegistryFactory] = None,
    logger_factory: Optional[AuditLoggerFactory] = None
):
    # Usar defaults si no se inyectan
    jwt_validator = jwt_validator or default_jwt_validator
    # ...
```

**Ventajas:**
- ✅ Menos cambios en código existente
- ✅ Backward compatible
- ⚠️ Firma del método más larga

**Recomendación:** Opción A (constructor) para mejor diseño a largo plazo

### 3. Validar Parámetros de Entrada (P1 - ALTA)

**Propuesta:**

```python
def _validate_inputs(
    self,
    token: str,
    expediente_id: str,
    tarea_id: str,
    agent_config: AgentConfig
) -> Optional[AgentError]:
    """Valida parámetros de entrada antes de ejecutar"""

    # Validar token
    if not token or not token.strip():
        return AgentError(
            codigo="INPUT_VALIDATION_ERROR",
            mensaje="Token JWT vacío o inválido",
            detalle="El parámetro 'token' es obligatorio"
        )

    # Validar expediente_id
    import re
    if not re.match(r'^EXP-\d{4}-\d{3}$', expediente_id):
        return AgentError(
            codigo="INPUT_VALIDATION_ERROR",
            mensaje=f"Formato de expediente_id inválido: '{expediente_id}'",
            detalle="Formato esperado: EXP-YYYY-NNN"
        )

    # Validar tarea_id
    if not tarea_id or not tarea_id.strip():
        return AgentError(
            codigo="INPUT_VALIDATION_ERROR",
            mensaje="tarea_id vacío",
            detalle="El parámetro 'tarea_id' es obligatorio"
        )

    # Validar agent_config
    if not agent_config.nombre or not agent_config.nombre.strip():
        return AgentError(
            codigo="AGENT_CONFIG_INVALID",
            mensaje="Nombre de agente vacío en configuración",
            detalle="agent_config.nombre es obligatorio"
        )

    return None  # Todo OK

async def execute(self, token, expediente_id, tarea_id, agent_config):
    # Validar inputs primero
    validation_error = self._validate_inputs(token, expediente_id, tarea_id, agent_config)
    if validation_error:
        return AgentExecutionResult(
            success=False,
            agent_run_id="INVALID",
            error=validation_error,
            ...
        )

    # Continuar con ejecución normal
    # ...
```

### 4. Validar Resultado del Agente (P1 - ALTA)

**Propuesta:**

```python
def _validate_agent_result(self, resultado: Any) -> Optional[AgentError]:
    """Valida que el resultado del agente tenga estructura esperada"""

    # Debe ser un diccionario
    if not isinstance(resultado, dict):
        return AgentError(
            codigo="OUTPUT_VALIDATION_ERROR",
            mensaje="Resultado del agente no es un diccionario",
            detalle=f"Tipo recibido: {type(resultado).__name__}"
        )

    # Debe tener campo 'completado'
    if "completado" not in resultado:
        return AgentError(
            codigo="OUTPUT_VALIDATION_ERROR",
            mensaje="Resultado del agente falta campo 'completado'",
            detalle=f"Campos presentes: {list(resultado.keys())}"
        )

    # Debe tener campo 'mensaje'
    if "mensaje" not in resultado:
        return AgentError(
            codigo="OUTPUT_VALIDATION_ERROR",
            mensaje="Resultado del agente falta campo 'mensaje'",
            detalle=f"Campos presentes: {list(resultado.keys())}"
        )

    return None  # Todo OK

# En execute():
resultado = await agent.execute()

# Validar antes de retornar
validation_error = self._validate_agent_result(resultado)
if validation_error:
    logger.error(f"Resultado de agente inválido: {validation_error.mensaje}")
    return AgentExecutionResult(
        success=False,
        agent_run_id=agent_run_id,
        error=validation_error,
        ...
    )
```

### 5. Mejorar Logging de Excepciones (P2 - MEDIA)

**Propuesta:**

```python
except Exception as e:
    # Logging mejorado con stacktrace
    import traceback
    stacktrace = traceback.format_exc()

    if logger:
        logger.error(f"Error inesperado: {type(e).__name__}: {str(e)}")
        logger.error(f"Stacktrace: {stacktrace}")

    return AgentExecutionResult(
        success=False,
        agent_run_id=agent_run_id,
        resultado={},
        log_auditoria=logger.get_log_entries() if logger else [],
        herramientas_usadas=[],
        error=AgentError(
            codigo="INTERNAL_ERROR",
            mensaje=f"Error interno del sistema: {type(e).__name__}",
            detalle=f"{str(e)}\n\nStacktrace:\n{stacktrace}"  # Incluir stacktrace
        )
    )
```

### 6. Split execute() en Métodos Privados (P3 - BAJA)

**Propuesta:**

```python
async def execute(self, token, expediente_id, tarea_id, agent_config):
    mcp_registry = None
    logger = None
    agent_run_id = self._generate_run_id()

    try:
        # Fase 1: Setup
        logger = self._create_logger(expediente_id, agent_run_id)

        # Fase 2: Validación
        claims = await self._validate_token(token, expediente_id, agent_config, logger)

        # Fase 3: Infraestructura MCP
        mcp_registry = await self._setup_mcp_registry(token, logger)

        # Fase 4: Ejecución
        resultado = await self._execute_agent(
            expediente_id, tarea_id, agent_run_id,
            agent_config, mcp_registry, logger
        )

        return self._create_success_result(agent_run_id, resultado, logger)

    except MCPConnectionError as e:
        return self._create_error_result(agent_run_id, e, logger)
    # ...

def _generate_run_id(self) -> str:
    return f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}"

def _create_logger(self, expediente_id: str, agent_run_id: str) -> AuditLogger:
    return AuditLogger(
        expediente_id=expediente_id,
        agent_run_id=agent_run_id,
        log_dir=self.log_dir
    )

async def _validate_token(self, token, expediente_id, agent_config, logger) -> JWTClaims:
    logger.log("Validando token JWT...")
    required_permissions = get_required_permissions_for_tools(agent_config.herramientas)
    claims = validate_jwt(...)
    logger.log(f"Token JWT válido para expediente {claims.exp_id}")
    return claims

# etc...
```

**Ventajas:**
- ✅ execute() más legible (solo ~30 líneas)
- ✅ Métodos privados testeables individualmente
- ✅ Más fácil de mantener

---

## Plan de Mejoras Priorizado

### Fase 1: Tests Unitarios y DI (Sprint 1-2 semanas)

**P0.1 - Crear abstracciones (Protocols)**
- Archivo: `backoffice/protocols.py` (NUEVO)
- Definir: `JWTValidatorProtocol`, `ConfigLoaderProtocol`, `MCPRegistryFactory`, etc.
- Tiempo: 2-3 horas

**P0.2 - Refactorizar AgentExecutor para DI**
- Archivo: `backoffice/executor.py`
- Cambiar constructor para inyectar dependencias
- Crear factory por defecto para backward compatibility
- Tiempo: 4-6 horas

**P0.3 - Crear suite de tests unitarios**
- Archivo: `backoffice/tests/test_executor.py` (NUEVO)
- Implementar 30 tests unitarios
- Objetivo: 80% cobertura
- Tiempo: 8-12 horas

### Fase 2: Validaciones (Sprint 2-1 semana)

**P1.1 - Validación de parámetros de entrada**
- Archivo: `backoffice/executor.py`
- Método: `_validate_inputs()`
- Tiempo: 2-3 horas

**P1.2 - Validación de resultado del agente**
- Archivo: `backoffice/executor.py`
- Método: `_validate_agent_result()`
- Tiempo: 1-2 horas

**P1.3 - Tests de validaciones**
- Archivo: `backoffice/tests/test_executor.py`
- 8 tests adicionales
- Tiempo: 2-3 horas

### Fase 3: Mejoras (Sprint 3-opcional)

**P2.1 - Mejorar logging de excepciones**
- Archivo: `backoffice/executor.py`
- Incluir stacktraces en INTERNAL_ERROR
- Tiempo: 1 hora

**P3.1 - Split execute() en métodos privados**
- Archivo: `backoffice/executor.py`
- Refactorizar en 6-8 métodos privados
- Tiempo: 4-6 horas

**P3.2 - Documentación de arquitectura**
- Archivo: `code-review/AgentExecutor/arquitectura.md`
- Diagramas de flujo y secuencia
- Tiempo: 2-3 horas

### Resumen de Esfuerzo

| Fase | Prioridad | Tiempo Estimado | Impacto |
|------|-----------|-----------------|---------|
| Fase 1 | P0 (CRÍTICA) | 14-21 horas | Testing robusto, DI |
| Fase 2 | P1 (ALTA) | 5-8 horas | Validación entrada/salida |
| Fase 3 | P2-P3 (MEDIA-BAJA) | 7-10 horas | Mantenibilidad |
| **TOTAL** | | **26-39 horas** | **3-5 días** |

---

## Conclusiones

### Fortalezas de AgentExecutor

1. ✅ **Manejo de errores exhaustivo** - Captura todas las excepciones MCP
2. ✅ **Logging temprano** - Garantiza auditoría completa
3. ✅ **Cleanup garantizado** - Cierra conexiones siempre
4. ✅ **Código limpio** - Excelente legibilidad y documentación
5. ✅ **Delegación clara** - No contiene lógica de negocio

### Debilidades Críticas

1. 🔴 **0% cobertura de tests unitarios** - La clase central NO está testeada
2. 🔴 **Acoplamiento alto** - Imposible inyectar mocks para testing
3. 🟡 **Sin validación de entrada** - Puede fallar con inputs inválidos
4. 🟡 **Sin validación de salida** - Puede retornar datos mal formados

### Recomendación Final

**AgentExecutor es FUNCIONALMENTE correcto pero ESTRUCTURALMENTE frágil.**

La clase funciona bien en el "happy path", pero:
- Es imposible testear unitariamente (sin servidor MCP real)
- No hay red de seguridad ante refactorings
- Difícil evolucionar sin romper funcionalidad existente

**Acción Recomendada:**

1. **PRIORIDAD INMEDIATA (P0):** Implementar Fase 1 (Tests + DI) antes de continuar con Paso 2 (API REST)
2. **PRIORIDAD ALTA (P1):** Implementar Fase 2 (Validaciones) en paralelo con Paso 2
3. **OPCIONAL (P2-P3):** Implementar Fase 3 (Mejoras) como deuda técnica en Paso 3

**Sin tests unitarios robustos, el riesgo de regresiones en Paso 2 y Paso 3 es ALTO.**

---

## Estado de Implementación

### Checklist de Mejoras

#### Fase 1: Tests Unitarios y Dependency Injection (P0 - CRÍTICA)

**P0.1 - Crear Abstracciones (Protocols)**
- [x] Crear archivo `backoffice/protocols.py`
- [x] Definir `JWTValidatorProtocol` con método `validate()`
- [x] Definir `ConfigLoaderProtocol` con método `load()`
- [x] Definir `MCPRegistryFactoryProtocol` con método `create()`
- [x] Definir `AuditLoggerFactoryProtocol` con método `create()`
- [x] Definir `AgentRegistryProtocol` con método `get()`
- [x] Verificar que todos los protocols importan sin errores
- [x] Ejecutar MyPy para validar tipos

**Estimación:** 2-3 horas | **Estado:** ✅ COMPLETADA (commit f80a3fa)

---

**P0.2 - Refactorizar AgentExecutor para DI**
- [ ] Modificar constructor de `AgentExecutor` para recibir dependencias
  - [ ] Inyectar `jwt_validator: JWTValidatorProtocol`
  - [ ] Inyectar `config_loader: ConfigLoaderProtocol`
  - [ ] Inyectar `registry_factory: MCPRegistryFactoryProtocol`
  - [ ] Inyectar `logger_factory: AuditLoggerFactoryProtocol`
  - [ ] Inyectar `agent_registry: AgentRegistryProtocol`
- [ ] Actualizar método `execute()` para usar dependencias inyectadas
  - [ ] Usar `self.jwt_validator.validate()` en lugar de `validate_jwt()`
  - [ ] Usar `self.config_loader.load()` en lugar de `MCPServersConfig.load_from_file()`
  - [ ] Usar `self.registry_factory.create()` en lugar de instanciación directa
  - [ ] Usar `self.logger_factory.create()` en lugar de `AuditLogger()`
  - [ ] Usar `self.agent_registry.get()` en lugar de `get_agent_class()`
- [ ] Crear archivo `backoffice/executor_factory.py`
  - [ ] Implementar `DefaultJWTValidator`
  - [ ] Implementar `DefaultConfigLoader`
  - [ ] Implementar `DefaultMCPRegistryFactory`
  - [ ] Implementar `DefaultAuditLoggerFactory`
  - [ ] Implementar `DefaultAgentRegistry`
  - [ ] Implementar función `create_default_executor()`
- [ ] Verificar backward compatibility con código existente
- [ ] Actualizar tests de integración existentes

**Estimación:** 4-6 horas | **Estado:** ❌ Pendiente

---

**P0.3 - Crear Suite de Tests Unitarios**
- [ ] Crear archivo `backoffice/tests/test_executor.py`
- [ ] Implementar fixtures comunes
  - [ ] `mock_jwt_validator`
  - [ ] `mock_config_loader`
  - [ ] `mock_registry_factory`
  - [ ] `mock_logger_factory`
  - [ ] `mock_agent_registry`
  - [ ] `executor` (con todas las dependencias mockeadas)
  - [ ] `agent_config`
- [ ] **Tests de Validación JWT (5 tests)**
  - [ ] `test_jwt_expired_returns_auth_error`
  - [ ] `test_jwt_invalid_signature_returns_auth_error`
  - [ ] `test_jwt_wrong_expediente_returns_mismatch_error`
  - [ ] `test_jwt_insufficient_permissions_returns_permission_error`
  - [ ] `test_jwt_valid_proceeds_to_execution`
- [ ] **Tests de Configuración MCP (3 tests)**
  - [ ] `test_mcp_config_file_not_found_returns_error`
  - [ ] `test_mcp_config_invalid_yaml_returns_error`
  - [ ] `test_mcp_config_valid_creates_registry`
- [ ] **Tests de Inicialización Registry (3 tests)**
  - [ ] `test_registry_init_timeout_returns_connection_error`
  - [ ] `test_registry_init_success_discovers_tools`
  - [ ] `test_registry_init_partial_failure_continues`
- [ ] **Tests de Creación de Agente (2 tests)**
  - [ ] `test_unknown_agent_type_returns_config_error`
  - [ ] `test_agent_creation_success_returns_instance`
- [ ] **Tests de Ejecución de Agente (3 tests)**
  - [ ] `test_agent_execute_success_returns_result`
  - [ ] `test_agent_execute_mcp_error_returns_tool_error`
  - [ ] `test_agent_execute_unexpected_error_returns_internal_error`
- [ ] **Tests de Logging y Auditoría (3 tests)**
  - [ ] `test_logger_created_early_captures_jwt_error`
  - [ ] `test_logger_captures_all_steps_on_success`
  - [ ] `test_logger_pii_redacted_in_output`
- [ ] **Tests de Cleanup (3 tests)**
  - [ ] `test_registry_closed_on_success`
  - [ ] `test_registry_closed_on_error`
  - [ ] `test_registry_closed_on_exception`
- [ ] **Tests de Validación de Entrada (3 tests)**
  - [ ] `test_empty_token_returns_validation_error`
  - [ ] `test_empty_expediente_id_returns_validation_error`
  - [ ] `test_invalid_agent_config_returns_validation_error`
- [ ] **Tests de Resultado (3 tests)**
  - [ ] `test_success_result_includes_all_fields`
  - [ ] `test_error_result_includes_error_details`
  - [ ] `test_tools_used_tracked_correctly`
- [ ] Ejecutar suite completa: `pytest backoffice/tests/test_executor.py -v`
- [ ] Verificar cobertura: `pytest --cov=backoffice.executor --cov-report=html`
- [ ] Validar que cobertura > 80%
- [ ] Verificar que todos los tests pasan (30/30)
- [ ] Verificar tiempo de ejecución < 5 segundos

**Estimación:** 8-12 horas | **Estado:** ❌ Pendiente

---

#### Fase 2: Validaciones de Entrada/Salida (P1 - ALTA)

**P1.1 - Validación de Parámetros de Entrada**
- [ ] Implementar método `_validate_inputs()` en `AgentExecutor`
  - [ ] Validar token no vacío
  - [ ] Validar formato expediente_id (`EXP-YYYY-NNN`)
  - [ ] Validar tarea_id no vacío
  - [ ] Validar agent_config.nombre no vacío
  - [ ] Validar agent_config.herramientas no vacío
- [ ] Llamar `_validate_inputs()` al inicio de `execute()`
- [ ] Retornar error estructurado si validación falla

**Estimación:** 2-3 horas | **Estado:** ❌ Pendiente

---

**P1.2 - Validación de Resultado del Agente**
- [ ] Implementar método `_validate_agent_result()` en `AgentExecutor`
  - [ ] Validar resultado es dict
  - [ ] Validar campo `completado` presente y bool
  - [ ] Validar campo `mensaje` presente y str
- [ ] Llamar `_validate_agent_result()` después de `agent.execute()`
- [ ] Retornar error estructurado si validación falla

**Estimación:** 1-2 horas | **Estado:** ❌ Pendiente

---

**P1.3 - Tests de Validaciones**
- [ ] Añadir tests de validación de entrada (5 tests)
  - [ ] `test_empty_token_returns_validation_error`
  - [ ] `test_empty_expediente_id_returns_validation_error`
  - [ ] `test_invalid_expediente_format_returns_validation_error`
  - [ ] `test_empty_tarea_id_returns_validation_error`
  - [ ] `test_invalid_agent_config_returns_validation_error`
- [ ] Añadir tests de validación de salida (3 tests)
  - [ ] `test_agent_result_not_dict_returns_validation_error`
  - [ ] `test_agent_result_missing_completado_returns_validation_error`
  - [ ] `test_agent_result_missing_mensaje_returns_validation_error`
- [ ] Ejecutar suite completa y verificar 38/38 tests pasan

**Estimación:** 2-3 horas | **Estado:** ❌ Pendiente

---

#### Fase 3: Mejoras Opcionales (P2-P3 - MEDIA-BAJA)

**P2.1 - Mejorar Logging de Excepciones**
- [ ] Modificar bloque `except Exception` para incluir stacktrace
- [ ] Usar `traceback.format_exc()` para capturar stacktrace completo
- [ ] Incluir stacktrace en `error.detalle`
- [ ] Logear stacktrace línea por línea en logger

**Estimación:** 1 hora | **Estado:** ❌ Pendiente

---

**P3.1 - Split execute() en Métodos Privados**
- [ ] Crear método `_generate_run_id()` → retorna agent_run_id
- [ ] Crear método `_create_logger()` → retorna AuditLogger
- [ ] Crear método `_validate_jwt_and_log()` → valida JWT y loguea
- [ ] Crear método `_setup_mcp_infrastructure()` → carga config y crea registry
- [ ] Crear método `_execute_agent()` → crea y ejecuta agente
- [ ] Crear método `_create_success_result()` → construye resultado exitoso
- [ ] Crear método `_create_error_result()` → construye resultado de error
- [ ] Crear métodos `_handle_*_error()` para cada tipo de excepción
- [ ] Refactorizar `execute()` para usar métodos privados
- [ ] Verificar que `execute()` tiene < 50 líneas
- [ ] Ejecutar tests y verificar que todos siguen pasando

**Estimación:** 4-6 horas | **Estado:** ❌ Pendiente

---

**P3.2 - Documentación de Arquitectura**
- [ ] Crear archivo `code-review/AgentExecutor/arquitectura.md`
- [ ] Añadir diagrama de flujo de `execute()`
- [ ] Añadir diagrama de secuencia con dependencias
- [ ] Documentar patrones de diseño utilizados
- [ ] Añadir ejemplos de uso

**Estimación:** 2-3 horas | **Estado:** ❌ Pendiente

---

### Progreso General

| Fase | Tareas | Completadas | Pendientes | Progreso |
|------|--------|-------------|------------|----------|
| **Fase 1 (P0)** | 8 | 1 | 7 | ⬛⬜⬜⬜⬜⬜⬜⬜⬜⬜ 12.5% |
| **Fase 2 (P1)** | 3 | 0 | 3 | ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0% |
| **Fase 3 (P2-P3)** | 3 | 0 | 3 | ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0% |
| **TOTAL** | **14** | **1** | **13** | **⬛⬜⬜⬜⬜⬜⬜⬜⬜⬜ 7%** |

### Métricas de Calidad

| Métrica | Inicial | Actual (P0.1) | Post-Fase 1 | Post-Fase 2 | Post-Fase 3 | Objetivo |
|---------|---------|---------------|-------------|-------------|-------------|----------|
| Tests unitarios | 0 | 7 protocols | 30 | 38 | 38 | 30+ |
| Cobertura | 0% | 0% executor | >80% | >85% | >85% | >80% |
| Acoplamiento | Alto | Alto | Bajo | Bajo | Bajo | Bajo |
| Validaciones | 0 | 0 | 0 | 2 | 2 | 2 |
| Líneas execute() | 196 | 196 | ~180 | ~210 | ~40 | <50 |
| Complejidad execute() | ~15 | ~15 | ~15 | ~17 | ~8 | <10 |

### Próximos Pasos

**ACCIÓN INMEDIATA:**

```bash
# 1. Crear feature branch
git checkout -b feature/executor-tests-di

# 2. Comenzar con P0.1 (Crear Protocols)
touch backoffice/protocols.py

# 3. Ver plan-mejoras.md para implementación completa
```

**Orden de implementación recomendado:**
1. ✅ P0.1 → P0.2 → P0.3 (Fase 1 completa - CRÍTICA)
2. ✅ P1.1 → P1.2 → P1.3 (Fase 2 completa - ALTA)
3. ✅ P2.1 → P3.1 → P3.2 (Fase 3 - OPCIONAL)

---

**Revisor:** Claude Code
**Fecha:** 2024-12-07
**Versión:** 1.0
