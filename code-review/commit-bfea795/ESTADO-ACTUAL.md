# Estado Actual de Tests - Análisis Real del Código

**Fecha:** 2025-12-20
**Tests Totales:** 141 (22 API + 33 MCP + 86 Backoffice)
**Pass Rate:** 141/141 (100%)

---

## ✅ Mejoras Implementadas (Fase 1)

### 1. Tests de API Funcionando
- ✅ Eliminado `/tests/api/__init__.py` (causa raíz del problema)
- ✅ 22 tests de API ejecutándose correctamente
- ✅ Agregado `pytest_configure` hook en conftest.py global

### 2. Configuración Centralizada Parcial
- ✅ Fixture `test_constants` creada en conftest.py global
- ✅ Fixture `jwt_secret` y `jwt_algorithm` globales
- ✅ Fixture `setup_test_environment` con autouse=True

### 3. run-tests.sh Actualizado
- ✅ Soporte completo para tests de API
- ✅ Opciones `--api-only`, `--mcp-only`, `--backoffice-only`

---

## ❌ Problemas PENDIENTES (No Implementados)

### P1: Valores Hardcoded NO Centralizados (CRÍTICO)

**Problema:** La fixture `test_constants` existe pero NO se usa en los tests.

**Evidencia:**
```bash
$ grep -r "EXP-2024-001" tests/ --include="*.py" | wc -l
107  # ❌ 107 instancias hardcoded

$ grep -r "agentix-bpmn" tests/ --include="*.py" | grep -v conftest.py | wc -l
7    # ❌ 7 instancias hardcoded

$ grep -r "test_constants" tests/ --include="*.py" | grep -v conftest.py | wc -l
0    # ❌ NINGÚN test usa test_constants
```

**Archivos con valores hardcoded:**
- `tests/test_backoffice/test_executor.py` - líneas 35, 36, 42
- `tests/test_backoffice/test_jwt_validator.py` - múltiples líneas
- `tests/test_mcp/conftest.py` - líneas 26-30 (fixtures exp_id)
- Todos los tests que usan expedientes

**Impacto:**
- DRY violation masiva (100+ duplicaciones)
- Cambiar un valor requiere editar 107+ líneas
- Propensa a errores (inconsistencias entre tests)

---

### P2: event_loop con scope="session" (ANTIPATRÓN)

**Archivo:** `tests/test_backoffice/conftest.py:7-12`

```python
@pytest.fixture(scope="session")  # ❌ ANTIPATRÓN
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

**Por qué es problema:**
- pytest-asyncio recomienda function-scoped event loops
- State leakage entre tests async
- Puede causar fallos intermitentes
- Deprecation warnings en versiones nuevas de pytest-asyncio

**Solución:** Eliminar completamente (pytest-asyncio ya proporciona event_loop)

---

### P3: Mock Assertions con .called (DEPRECATED)

**Archivo:** `tests/test_backoffice/test_executor.py`

**Ocurrencias:** 7 instancias

```python
# ❌ Deprecated - no falla si se llama múltiples veces
assert mock_jwt_validator.validate.called
assert mock_registry_factory.create.called
assert mock_registry.get_available_tools.called
assert mock_agent_registry.get.called
assert mock_logger_factory.create.called
assert mock_logger.error.called
```

**Problema:**
- `.called` es un simple booleano - solo verifica SI se llamó
- No verifica CUÁNTAS veces
- No verifica CON QUÉ argumentos

**Solución recomendada:**
```python
# ✅ Mejor - falla si se llama 0 o 2+ veces
mock_jwt_validator.validate.assert_called_once()

# ✅ Mejor aún - verifica argumentos
mock_jwt_validator.validate.assert_called_once_with(
    token="expected-token",
    expected_expediente_id="EXP-2024-001"
)
```

---

### P4: restore_expediente_data Sin Cleanup Completo

**Archivo:** `tests/test_mcp/conftest.py:52-79`

```python
@pytest.fixture
def restore_expediente_data():
    # ... setup code
    yield

    # Opcionalmente limpiar después del test
    # (por ahora no hacemos nada, dejamos el estado final para debug)
```

**Problema:**
- Comentario indica intención incompleta
- No hay cleanup después del test
- Tests que modifican datos pueden afectar tests subsecuentes

**Solución:**
```python
@pytest.fixture
def restore_expediente_data():
    def _restore():
        for backup_file in data_dir.glob("*.json.backup"):
            test_file = backup_file.with_suffix("")
            shutil.copy(backup_file, test_file)

    _restore()  # Restaurar ANTES
    yield
    _restore()  # Restaurar DESPUÉS (garantiza idempotencia)
```

---

### P5: Fixtures de Expedientes No Usan test_constants

**Archivo:** `tests/test_mcp/conftest.py:24-48`

```python
@pytest.fixture(scope="session")
def test_expedientes():
    return [
        "EXP-2024-001",  # ❌ Hardcoded, debería usar test_constants
        "EXP-2024-002",
        "EXP-2024-003"
    ]

@pytest.fixture
def exp_id_subvenciones():
    return "EXP-2024-001"  # ❌ Hardcoded

@pytest.fixture
def exp_id_licencia():
    return "EXP-2024-002"  # ❌ Hardcoded
```

**Debería ser:**
```python
@pytest.fixture(scope="session")
def test_expedientes(test_constants):
    return test_constants["default_exp_ids"]

@pytest.fixture
def exp_id_subvenciones(test_constants):
    return test_constants["default_exp_ids"][0]
```

---

### P6: test_protocols.py con Assertions Débiles

**Archivo:** `tests/test_backoffice/test_protocols.py`

**Ejemplo de assertion débil:**
```python
def test_jwt_validator_protocol_structure():
    assert hasattr(JWTValidatorProtocol, 'validate')  # ❌ Solo verifica existencia
```

**No verifica:**
- Que sea callable (podría ser un atributo)
- Signatura del método
- Type hints
- Return type

**Solución:**
```python
import inspect
from typing import get_type_hints

def test_jwt_validator_protocol_structure():
    assert hasattr(JWTValidatorProtocol, 'validate')
    validate_func = getattr(JWTValidatorProtocol, 'validate')
    assert callable(validate_func)

    # Verificar signatura
    sig = inspect.signature(validate_func)
    assert 'token' in sig.parameters
    assert 'secret' in sig.parameters
```

---

### P7: Tests Skipped Sin Issue Tracker

**Archivo:** `tests/test_mcp/test_server_http.py`

```python
@pytest.mark.skip(reason="SSE not implemented")  # ❌ Sin issue tracker
async def test_sse_subscribe():
    pass
```

**Problema:**
- No hay referencia a GitHub issue
- No hay forma de trackear cuándo implementar
- Fácil de olvidar

**Solución:**
```python
@pytest.mark.skip(reason="SSE not implemented - Issue #42")
async def test_sse_subscribe():
    pass
```

---

## Plan de Mejoras Actualizado

### Fase 2: Refactoring de Fixtures (PRIORIDAD ALTA)

**Tiempo estimado:** 2-3 horas

#### 2.1. Conectar test_constants con Fixtures de Expedientes
**Archivos:** `tests/test_mcp/conftest.py`

**Cambios:**
```python
# ANTES
@pytest.fixture(scope="session")
def test_expedientes():
    return ["EXP-2024-001", "EXP-2024-002", "EXP-2024-003"]

# DESPUÉS
@pytest.fixture(scope="session")
def test_expedientes(test_constants):
    return test_constants["default_exp_ids"]
```

**Beneficio:** Un solo lugar para cambiar IDs de expedientes

---

#### 2.2. Refactorizar Mocks en test_executor.py
**Archivos:** `tests/test_backoffice/test_executor.py`

**Cambios:**
```python
# ANTES
@pytest.fixture
def mock_jwt_validator():
    validator = Mock()
    validator.validate = Mock(return_value=JWTClaims(
        iss="agentix-bpmn",  # ❌ Hardcoded
        exp_id="EXP-2024-001",  # ❌ Hardcoded
        # ...
    ))
    return validator

# DESPUÉS
@pytest.fixture
def mock_jwt_validator(test_constants):
    validator = Mock()
    validator.validate = Mock(return_value=JWTClaims(
        iss=test_constants["issuer"],  # ✅ Centralizado
        exp_id=test_constants["default_exp_ids"][0],  # ✅ Centralizado
        # ...
    ))
    return validator
```

**Beneficio:** 7+ fixtures reutilizan test_constants

---

#### 2.3. Eliminar event_loop Session-Scoped
**Archivos:** `tests/test_backoffice/conftest.py`

**Cambios:**
```python
# ELIMINAR completamente (líneas 7-12)
# pytest-asyncio ya proporciona event_loop con function scope
```

**Beneficio:** Elimina antipatrón, mejor aislamiento de tests async

---

#### 2.4. Mejorar restore_expediente_data
**Archivos:** `tests/test_mcp/conftest.py`

**Cambios:**
```python
@pytest.fixture
def restore_expediente_data():
    root_dir = Path(__file__).parent.parent.parent
    data_dir = root_dir / "src" / "mcp_mock" / "mcp_expedientes" / "data" / "expedientes"

    def _restore():
        for backup_file in data_dir.glob("*.json.backup"):
            test_file = backup_file.with_suffix("")
            shutil.copy(backup_file, test_file)

    _restore()  # Setup
    yield
    _restore()  # Teardown - garantiza idempotencia
```

**Beneficio:** Tests son idempotentes, pueden ejecutarse múltiples veces

---

### Fase 3: Mejorar Assertions (PRIORIDAD MEDIA)

**Tiempo estimado:** 1-2 horas

#### 3.1. Reemplazar .called con assert_called_once()
**Archivos:** `tests/test_backoffice/test_executor.py`

**Cambios:** 7 instancias de `.called` → `assert_called_once()`

**Beneficio:** Tests más estrictos, detectan llamadas duplicadas

---

#### 3.2. Agregar Verificación de Argumentos en Mocks Críticos
**Archivos:** `tests/test_backoffice/test_executor.py`

**Ejemplo:**
```python
# ANTES
assert mock_jwt_validator.validate.called

# DESPUÉS
mock_jwt_validator.validate.assert_called_once()
# O mejor:
mock_jwt_validator.validate.assert_called_once_with(
    token=valid_token,
    expected_expediente_id="EXP-2024-001"
)
```

**Beneficio:** Verifica que se llaman con argumentos correctos

---

#### 3.3. Mejorar test_protocols.py
**Archivos:** `tests/test_backoffice/test_protocols.py`

**Agregar verificaciones de:**
- Callable
- Signatura de métodos
- Type hints

**Beneficio:** Tests más robustos para Protocols

---

### Fase 4: Cleanup y Documentación (PRIORIDAD BAJA)

**Tiempo estimado:** 1 hora

#### 4.1. Agregar Issue Tracker a Tests Skipped
**Archivos:** `tests/test_mcp/test_server_http.py`

#### 4.2. Crear pytest.ini con Configuración
**Crear:** `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

---

## Resumen de Impacto

| Problema | Estado | Archivos Afectados | Líneas Afectadas | Prioridad |
|----------|--------|-------------------|------------------|-----------|
| Valores hardcoded | ❌ PENDIENTE | 15+ archivos | 107+ líneas | 🔴 ALTA |
| event_loop session | ❌ PENDIENTE | 1 archivo | 6 líneas | 🟠 MEDIA |
| .called deprecated | ❌ PENDIENTE | 1 archivo | 7 líneas | 🟠 MEDIA |
| restore sin cleanup | ❌ PENDIENTE | 1 archivo | 1 fixture | 🟠 MEDIA |
| Assertions débiles | ❌ PENDIENTE | 1 archivo | 7 tests | 🟡 BAJA |
| Tests sin issue | ❌ PENDIENTE | 1 archivo | 1 test | 🟡 BAJA |

---

## Conclusión

**Lo que SÍ se implementó:**
- ✅ Tests de API funcionando (22 tests)
- ✅ Infraestructura de test_constants (fixture creada)
- ✅ Environment cleanup automático
- ✅ run-tests.sh actualizado

**Lo que NO se implementó:**
- ❌ Centralización real de valores (fixture existe pero no se usa)
- ❌ Eliminación de event_loop session-scoped
- ❌ Mejora de assertions (.called → assert_called_once)
- ❌ Cleanup completo en restore_expediente_data

**Próximos pasos recomendados:**
1. **Fase 2.1-2.2** (2h): Conectar test_constants con todos los tests
2. **Fase 2.3** (15min): Eliminar event_loop
3. **Fase 3.1** (30min): Reemplazar .called
4. **Fase 2.4** (30min): Mejorar restore_expediente_data

**Total tiempo estimado:** ~3.5 horas para completar todas las mejoras pendientes.
