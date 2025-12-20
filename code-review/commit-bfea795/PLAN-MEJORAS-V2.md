# Plan de Mejoras para Tests - Versión 2 (Basado en Estado Real)

**Fecha:** 2025-12-20
**Estado Actual:** 141/141 tests passing
**Objetivo:** Mejorar calidad, mantenibilidad y robustez de los tests

---

## Fase 2: Centralización de Valores (CRÍTICO)

**Tiempo estimado:** 2-3 horas
**Prioridad:** 🔴 ALTA
**Archivos afectados:** 15+ archivos

### Objetivo
Conectar la fixture `test_constants` existente con todos los tests que usan valores hardcoded.

### Tareas Específicas

#### 2.1. Actualizar Fixtures de Expedientes en test_mcp

**Archivo:** `tests/test_mcp/conftest.py`

**Líneas a modificar:** 24-48

```python
# ANTES (líneas 24-30)
@pytest.fixture(scope="session")
def test_expedientes():
    """Fixture que proporciona los IDs de expedientes de prueba"""
    return [
        "EXP-2024-001",  # Subvenciones en trámite
        "EXP-2024-002",  # Licencia pendiente documentación
        "EXP-2024-003"   # Certificado archivado
    ]

# DESPUÉS
@pytest.fixture(scope="session")
def test_expedientes(test_constants):
    """Fixture que proporciona los IDs de expedientes de prueba"""
    return test_constants["default_exp_ids"]
```

```python
# ANTES (líneas 33-48)
@pytest.fixture
def exp_id_subvenciones():
    """ID del expediente de subvenciones"""
    return "EXP-2024-001"

@pytest.fixture
def exp_id_licencia():
    """ID del expediente de licencia"""
    return "EXP-2024-002"

@pytest.fixture
def exp_id_certificado():
    """ID del expediente de certificado"""
    return "EXP-2024-003"

# DESPUÉS
@pytest.fixture
def exp_id_subvenciones(test_constants):
    """ID del expediente de subvenciones"""
    return test_constants["default_exp_ids"][0]

@pytest.fixture
def exp_id_licencia(test_constants):
    """ID del expediente de licencia"""
    return test_constants["default_exp_ids"][1]

@pytest.fixture
def exp_id_certificado(test_constants):
    """ID del expediente de certificado"""
    return test_constants["default_exp_ids"][2]
```

**Validación:**
```bash
# Después del cambio, esto debería mostrar solo 3 (en conftest.py global)
grep -r "EXP-2024-001" tests/test_mcp/conftest.py
```

---

#### 2.2. Refactorizar mock_jwt_validator en test_executor

**Archivo:** `tests/test_backoffice/test_executor.py`

**Líneas a modificar:** 30-45

```python
# ANTES
@pytest.fixture
def mock_jwt_validator():
    """Mock de JWTValidatorProtocol"""
    validator = Mock()
    validator.validate = Mock(return_value=JWTClaims(
        iss="agentix-bpmn",
        sub="Automático",
        aud=["agentix-mcp-expedientes"],
        exp=9999999999,
        iat=1234567890,
        nbf=1234567890,
        jti="test-jti",
        exp_id="EXP-2024-001",
        permisos=["consulta", "gestion"]
    ))
    return validator

# DESPUÉS
@pytest.fixture
def mock_jwt_validator(test_constants):
    """Mock de JWTValidatorProtocol"""
    validator = Mock()
    validator.validate = Mock(return_value=JWTClaims(
        iss=test_constants["issuer"],
        sub=test_constants["subject"],
        aud=[test_constants["audience"]],
        exp=9999999999,
        iat=1234567890,
        nbf=1234567890,
        jti="test-jti",
        exp_id=test_constants["default_exp_ids"][0],
        permisos=["consulta", "gestion"]
    ))
    return validator
```

**Validación:**
```bash
# No debería haber hardcoded strings en la fixture
grep -A 15 "def mock_jwt_validator" tests/test_backoffice/test_executor.py | grep -E "(agentix-bpmn|Automático|EXP-2024)"
# Resultado esperado: vacío
```

---

#### 2.3. Refactorizar Fixtures en test_jwt_validator

**Archivo:** `tests/test_backoffice/test_jwt_validator.py`

**Líneas a modificar:** 16-30

```python
# ANTES
@pytest.fixture
def valid_claims():
    """Claims válidos para tests"""
    now = datetime.now(timezone.utc)
    return {
        "iss": "agentix-bpmn",
        "sub": "Automático",
        "aud": ["agentix-mcp-expedientes"],
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "jti": "test-jti-123",
        "exp_id": "EXP-2024-001",
        "permisos": ["consulta", "gestion"]
    }

# DESPUÉS
@pytest.fixture
def valid_claims(test_constants):
    """Claims válidos para tests"""
    now = datetime.now(timezone.utc)
    return {
        "iss": test_constants["issuer"],
        "sub": test_constants["subject"],
        "aud": [test_constants["audience"]],
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "jti": "test-jti-123",
        "exp_id": test_constants["default_exp_ids"][0],
        "permisos": ["consulta", "gestion"]
    }
```

**Y también actualizar todos los tests que usan strings hardcoded:**

```python
# Buscar y reemplazar en todo el archivo:
# "EXP-2024-001" → usar fixture exp_id_subvenciones
# "EXP-2024-999" → dejar como está (es un ID inválido intencional)
# "agentix-bpmn" → test_constants["issuer"]
# "Automático" → test_constants["subject"]
```

**Validación:**
```bash
# Contar ocurrencias (debería ser 0 o muy pocas)
grep "agentix-bpmn" tests/test_backoffice/test_jwt_validator.py | grep -v test_constants
```

---

#### 2.4. Refactorizar Fixtures de Tokens en test_mcp

**Archivo:** `tests/test_mcp/fixtures/tokens.py`

**Actualizar todas las funciones:**

```python
# ANTES
def token_consulta(exp_id: str) -> str:
    claims = {
        "iss": "agentix-bpmn",
        "sub": "Automático",
        # ...
    }

# DESPUÉS
def token_consulta(exp_id: str, test_constants=None) -> str:
    # Si test_constants no se pasa, usar valores por defecto
    # (para mantener compatibilidad)
    if test_constants is None:
        from conftest import test_constants as get_constants
        test_constants = get_constants()

    claims = {
        "iss": test_constants["issuer"],
        "sub": test_constants["subject"],
        # ...
    }
```

**O mejor:** Convertir las funciones en fixtures que reciban test_constants automáticamente.

---

### Validación Final de Fase 2

```bash
# Verificar reducción de hardcoded values
echo "EXP-2024-001 occurrences:"
grep -r "EXP-2024-001" tests/ --include="*.py" | grep -v conftest.py | wc -l
# Objetivo: < 20 (solo en tests que necesitan IDs inválidos)

echo "agentix-bpmn occurrences:"
grep -r "agentix-bpmn" tests/ --include="*.py" | grep -v conftest.py | wc -l
# Objetivo: 0

echo "Automático occurrences:"
grep -r "Automático" tests/ --include="*.py" | grep -v conftest.py | wc -l
# Objetivo: 0

# Ejecutar tests para verificar que nada se rompió
./run-tests.sh
# Objetivo: 141/141 PASSED
```

---

## Fase 3: Eliminar Antipatrón event_loop

**Tiempo estimado:** 15 minutos
**Prioridad:** 🟠 MEDIA
**Archivos afectados:** 1 archivo

### Tarea Específica

**Archivo:** `tests/test_backoffice/conftest.py`

**Cambio:**
```python
# ELIMINAR completamente líneas 1-12

# El archivo debería quedar prácticamente vacío o solo con comentarios:
# tests/test_backoffice/conftest.py

"""
Configuración de pytest para tests de backoffice.

NOTA: pytest-asyncio ya proporciona event_loop con function scope.
No es necesario definir fixtures aquí.
"""
```

**Validación:**
```bash
# Ejecutar tests async para verificar que funcionan
./run-tests.sh --backoffice-only -v
# Objetivo: 86/86 PASSED

# Verificar que no hay warnings sobre event_loop
./run-tests.sh --backoffice-only 2>&1 | grep -i "event.loop"
# Resultado esperado: vacío
```

---

## Fase 4: Mejorar Mock Assertions

**Tiempo estimado:** 30-45 minutos
**Prioridad:** 🟠 MEDIA
**Archivos afectados:** 1 archivo

### Tarea Específica

**Archivo:** `tests/test_backoffice/test_executor.py`

**Buscar y reemplazar:**

1. **Patrón 1: assert .called**
```python
# ANTES (7 instancias)
assert mock_jwt_validator.validate.called

# DESPUÉS
mock_jwt_validator.validate.assert_called_once()
```

2. **Patrón 2: Agregar verificación de argumentos en tests críticos**

**Ejemplo en `test_execute_agent_success`:**
```python
# ANTES
assert mock_jwt_validator.validate.called

# DESPUÉS
mock_jwt_validator.validate.assert_called_once()
# Opcional pero recomendado:
call_args = mock_jwt_validator.validate.call_args
assert call_args.kwargs["token"] == valid_token
assert call_args.kwargs["expected_expediente_id"] == "EXP-2024-001"
```

**Lista de tests a actualizar:**
```bash
# Encontrar todos los .called
grep -n "\.called" tests/test_backoffice/test_executor.py

# Resultado esperado: ~7 líneas
# Actualizar cada una a assert_called_once()
```

**Validación:**
```bash
# No debería haber .called
grep "\.called" tests/test_backoffice/test_executor.py
# Resultado esperado: vacío

# Tests deben pasar
./run-tests.sh --backoffice-only -k test_executor
# Objetivo: todos los tests de executor pasan
```

---

## Fase 5: Mejorar restore_expediente_data

**Tiempo estimado:** 30 minutos
**Prioridad:** 🟠 MEDIA
**Archivos afectados:** 1 archivo

### Tarea Específica

**Archivo:** `tests/test_mcp/conftest.py`

**Líneas a modificar:** 52-79

```python
# ANTES
@pytest.fixture
def restore_expediente_data():
    """
    Restaura los datos de expedientes desde archivos .backup.
    ...
    """
    root_dir = Path(__file__).parent.parent.parent
    data_dir = root_dir / "src" / "mcp_mock" / "mcp_expedientes" / "data" / "expedientes"

    # Restaurar todos los expedientes desde backup
    for backup_file in data_dir.glob("*.json.backup"):
        test_file = backup_file.with_suffix("")
        shutil.copy(backup_file, test_file)

    yield

    # Opcionalmente limpiar después del test
    # (por ahora no hacemos nada, dejamos el estado final para debug)


# DESPUÉS
@pytest.fixture
def restore_expediente_data():
    """
    Restaura los datos de expedientes desde archivos .backup.

    Esta fixture garantiza idempotencia: el test puede ejecutarse
    múltiples veces y siempre partirá del mismo estado.

    Los archivos .backup contienen el estado original de los expedientes
    y siempre deben existir en data/expedientes/*.json.backup
    """
    root_dir = Path(__file__).parent.parent.parent
    data_dir = root_dir / "src" / "mcp_mock" / "mcp_expedientes" / "data" / "expedientes"

    def _restore():
        """Función helper para restaurar desde backups"""
        for backup_file in data_dir.glob("*.json.backup"):
            test_file = backup_file.with_suffix("")
            shutil.copy(backup_file, test_file)

    # Setup: restaurar ANTES del test
    _restore()

    yield

    # Teardown: restaurar DESPUÉS del test (garantiza idempotencia)
    _restore()
```

**Validación:**
```bash
# Ejecutar un test de escritura dos veces seguidas
pytest tests/test_mcp/test_tools.py::test_tc_tool_005_añadir_documento -v
pytest tests/test_mcp/test_tools.py::test_tc_tool_005_añadir_documento -v

# Ambas ejecuciones deben PASAR
# (antes, la segunda ejecución podría fallar porque el documento ya existe)
```

---

## Fase 6: Mejorar test_protocols.py

**Tiempo estimado:** 30 minutos
**Prioridad:** 🟡 BAJA
**Archivos afectados:** 1 archivo

### Tarea Específica

**Archivo:** `tests/test_backoffice/test_protocols.py`

**Mejorar cada test de Protocol:**

```python
# ANTES (ejemplo con JWTValidatorProtocol)
def test_jwt_validator_protocol_structure():
    """Test: JWTValidatorProtocol tiene estructura correcta"""
    assert hasattr(JWTValidatorProtocol, 'validate')

# DESPUÉS
import inspect

def test_jwt_validator_protocol_structure():
    """Test: JWTValidatorProtocol tiene estructura correcta"""
    # Verificar que existe el método
    assert hasattr(JWTValidatorProtocol, 'validate')

    # Verificar que es callable
    validate_func = getattr(JWTValidatorProtocol, 'validate')
    assert callable(validate_func) or hasattr(validate_func, '__call__')

    # Verificar signatura (si está definida)
    if hasattr(validate_func, '__annotations__'):
        sig = inspect.signature(validate_func)
        # Verificar parámetros esperados
        assert 'token' in sig.parameters
        assert 'secret' in sig.parameters
        assert 'algorithm' in sig.parameters
```

**Aplicar mismo patrón a todos los Protocols:**
- JWTValidatorProtocol
- MCPRegistryFactoryProtocol
- AuditLoggerFactoryProtocol
- ConfigLoaderProtocol
- AgentRegistryProtocol

---

## Fase 7: Cleanup Final

**Tiempo estimado:** 30 minutos
**Prioridad:** 🟡 BAJA

### 7.1. Agregar Issue Tracker a Tests Skipped

**Archivo:** `tests/test_mcp/test_server_http.py`

```python
# ANTES
@pytest.mark.skip(reason="SSE not implemented")
async def test_sse_subscribe():
    pass

# DESPUÉS (crear issue en GitHub primero)
@pytest.mark.skip(reason="SSE not implemented - Issue #XX")
async def test_sse_subscribe():
    pass
```

### 7.2. Crear pytest.ini

**Crear archivo:** `pytest.ini`

```ini
[pytest]
# Directorios donde buscar tests
testpaths = tests

# Patrones de archivos/funciones/clases
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Configuración de asyncio
asyncio_mode = auto

# Mostrar warnings
filterwarnings =
    error::DeprecationWarning
    ignore::pytest.PytestUnraisableExceptionWarning

# Verbosity por defecto
addopts = --strict-markers

# Markers personalizados
markers =
    slow: tests que tardan más de 1 segundo
    integration: tests de integración (requieren servicios externos)
```

---

## Resumen del Plan

| Fase | Tiempo | Prioridad | Tests Afectados | Archivos |
|------|--------|-----------|-----------------|----------|
| 2. Centralización | 2-3h | 🔴 ALTA | Todos | 15+ |
| 3. event_loop | 15min | 🟠 MEDIA | 86 backoffice | 1 |
| 4. Assertions | 45min | 🟠 MEDIA | ~30 executor | 1 |
| 5. restore cleanup | 30min | 🟠 MEDIA | ~10 tools | 1 |
| 6. Protocols | 30min | 🟡 BAJA | 7 protocols | 1 |
| 7. Cleanup | 30min | 🟡 BAJA | 1 skipped | 2 |

**Total:** ~5 horas para todas las fases

**Recomendación:** Implementar en orden (Fase 2 → Fase 3 → etc.)

---

## Criterios de Éxito

### Métricas Objetivo

| Métrica | Actual | Objetivo | Cómo Verificar |
|---------|--------|----------|----------------|
| Hardcoded "EXP-2024-001" | 107 | < 20 | `grep -r "EXP-2024-001" tests/ \| wc -l` |
| Hardcoded "agentix-bpmn" | 7 | 0 | `grep -r "agentix-bpmn" tests/ \| wc -l` |
| Mock .called | 7 | 0 | `grep "\.called" tests/ \| wc -l` |
| event_loop session | 1 | 0 | `grep "scope=\"session\"" tests/**/conftest.py \| grep event_loop` |
| Tests passing | 141/141 | 141/141 | `./run-tests.sh` |

### Validación Final

```bash
# 1. Ejecutar suite completa
./run-tests.sh
# Esperado: 141/141 PASSED

# 2. Verificar hardcoded values reducidos
grep -r "EXP-2024-001" tests/ --include="*.py" | grep -v conftest.py | wc -l
# Esperado: < 20

# 3. Verificar .called eliminado
grep -r "\.called" tests/ --include="*.py"
# Esperado: vacío

# 4. Verificar event_loop eliminado
grep -r "scope=\"session\"" tests/ --include="*.py" | grep event_loop
# Esperado: vacío

# 5. Test de idempotencia
pytest tests/test_mcp/test_tools.py::test_tc_tool_005_añadir_documento
pytest tests/test_mcp/test_tools.py::test_tc_tool_005_añadir_documento
# Esperado: ambos PASS
```
