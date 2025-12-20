# Plan de Mejoras - Tests aGEntiX

## Objetivo

Pasar de **119/152 tests ejecutándose (78%)** a **152/152 tests ejecutándose (100%)** con código limpio, mantenible y sin antipatrones.

---

## Fase 1: Arreglos Críticos ⚡

**Duración estimada:** 1-2 horas
**Prioridad:** CRÍTICA
**Objetivo:** Hacer que los 33 tests de API se ejecuten

### 1.1 Fix API Tests Imports

**Archivos a modificar:**
- `tests/api/conftest.py`

**Cambios:**

```python
# ANTES (tests/api/conftest.py)
import os
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent
os.chdir(str(root_dir))  # ❌ Antipatrón

# DESPUÉS (tests/api/conftest.py)
# ELIMINAR todo el contenido
# El conftest.py global ya configura sys.path correctamente
```

**Validación:**
```bash
pytest tests/api/ -v
# Debe ejecutar 33 tests (actualmente 0)
```

---

### 1.2 Consolidar sys.path en Conftest Global

**Archivos a modificar:**
- `tests/test_mcp/conftest.py` (eliminar líneas 15-18)
- `tests/test_mcp/fixtures/tokens.py` (eliminar línea 13)

**Cambios en `tests/test_mcp/conftest.py`:**

```python
# ANTES (líneas 14-18)
# Configurar PYTHONPATH para imports desde src/ y fixtures locales
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
# Agregar directorio de tests para imports de fixtures
sys.path.insert(0, str(Path(__file__).parent))

# DESPUÉS
# ELIMINAR estas líneas - ya están en conftest.py global
```

**Cambios en `tests/test_mcp/fixtures/tokens.py`:**

```python
# ANTES (líneas 11-13)
# Configurar path para imports (necesario en entorno de test)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# DESPUÉS
# ELIMINAR estas líneas - fixtures se importan con from fixtures.tokens
```

**Validación:**
```bash
# Verificar que no hay múltiples entradas de src/ en sys.path
python -c "import sys; print([p for p in sys.path if 'aGEntiX' in p])"
# Debe mostrar solo 2 paths: /workspaces/aGEntiX y /workspaces/aGEntiX/src
```

---

### 1.3 Setup Environment con Autouse Fixture

**Archivo a modificar:**
- `conftest.py` (raíz)

**Cambios:**

```python
# Agregar al final de conftest.py
@pytest.fixture(scope="session")
def test_constants():
    """Constantes compartidas entre todos los tests"""
    return {
        "jwt_secret": "test-secret-key",
        "jwt_algorithm": "HS256",
        "issuer": "agentix-bpmn",
        "subject": "Automático",
        "audience": "agentix-mcp-expedientes",
        "default_exp_ids": ["EXP-2024-001", "EXP-2024-002", "EXP-2024-003"]
    }


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(test_constants):
    """
    Configura environment variables para todos los tests.
    autouse=True: se ejecuta automáticamente.
    """
    import os

    original_env = {}

    # Backup valores originales
    for key in ["JWT_SECRET", "JWT_ALGORITHM", "LOG_LEVEL"]:
        original_env[key] = os.environ.get(key)

    # Configurar valores de test
    os.environ["JWT_SECRET"] = test_constants["jwt_secret"]
    os.environ["JWT_ALGORITHM"] = test_constants["jwt_algorithm"]
    os.environ["LOG_LEVEL"] = "INFO"

    yield

    # Cleanup (siempre se ejecuta)
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)


@pytest.fixture(scope="session")
def jwt_secret(test_constants):
    """JWT secret para validación"""
    return test_constants["jwt_secret"]
```

**Archivos donde ELIMINAR `os.environ["JWT_SECRET"] = ...`:**
- `tests/test_mcp/conftest.py:21`
- `tests/test_mcp/test_auth.py:30`
- `tests/test_mcp/test_resources.py:21`
- `tests/test_mcp/test_tools.py:28`

**Validación:**
```bash
# Tests deben pasar sin os.environ hardcoded
pytest tests/test_mcp/test_auth.py -v
```

---

### 1.4 Eliminar Fixtures Duplicadas

**Archivos a modificar:**
- `tests/test_mcp/conftest.py` (eliminar fixture jwt_secret líneas 24-27)
- `tests/test_backoffice/test_jwt_validator.py` (eliminar fixture jwt_secret líneas 14-22)

**Antes:**
```python
# tests/test_mcp/conftest.py:24-27
@pytest.fixture(scope="session")
def jwt_secret():
    """Fixture que proporciona la clave secreta JWT"""
    return "test-secret-key"

# tests/test_backoffice/test_jwt_validator.py:14-22
@pytest.fixture
def jwt_secret():
    """Secret para tests"""
    return "test-secret-key"
```

**Después:**
```python
# ELIMINAR ambas fixtures
# Usar la del conftest.py global
```

**Validación:**
```bash
grep -r "def jwt_secret" tests/
# Solo debe aparecer en conftest.py (raíz)
```

---

### Checklist Fase 1

- [ ] Modificar `tests/api/conftest.py` (eliminar contenido)
- [ ] Eliminar sys.path de `tests/test_mcp/conftest.py`
- [ ] Eliminar sys.path de `tests/test_mcp/fixtures/tokens.py`
- [ ] Agregar fixtures a `conftest.py` global
- [ ] Eliminar `os.environ["JWT_SECRET"]` de 4 archivos
- [ ] Eliminar fixture jwt_secret duplicada (2 archivos)
- [ ] Ejecutar `pytest tests/api/ -v` → 33 tests deben pasar
- [ ] Ejecutar `./run-tests.sh` → 152/152 tests deben pasar

---

## Fase 2: Refactoring de Fixtures 🔧

**Duración estimada:** 2-3 horas
**Prioridad:** ALTA
**Objetivo:** Eliminar duplicación, mejorar mantenibilidad

### 2.1 Centralizar Constantes de Tests

**Ya implementado en Fase 1.3** ✅

Todas las constantes ahora vienen de `test_constants` fixture.

---

### 2.2 Mejorar restore_expediente_data con Cleanup

**Archivo a modificar:**
- `tests/test_mcp/conftest.py:58-87`

**Antes:**
```python
@pytest.fixture
def restore_expediente_data():
    # ... restauración ...
    yield

    # Opcionalmente limpiar después del test
    # (por ahora no hacemos nada, dejamos el estado final para debug)
```

**Después:**
```python
@pytest.fixture
def restore_expediente_data():
    """
    Restaura datos de expedientes antes y después de cada test.

    Garantiza idempotencia: ejecutar el mismo test múltiples veces
    produce el mismo resultado.

    Uso:
        @pytest.mark.usefixtures("restore_expediente_data")
        async def test_modificar_datos():
            # Test que modifica datos
            pass
    """
    root_dir = Path(__file__).parent.parent.parent
    data_dir = root_dir / "src" / "mcp_mock" / "mcp_expedientes" / "data" / "expedientes"

    def _restore_from_backup():
        """Helper para restaurar desde archivos .backup"""
        restored_count = 0
        for backup_file in data_dir.glob("*.json.backup"):
            test_file = backup_file.with_suffix("")
            shutil.copy(backup_file, test_file)
            restored_count += 1
        return restored_count

    # Setup: restaurar antes del test
    _restore_from_backup()

    yield

    # Teardown: restaurar después (siempre, incluso si el test falla)
    _restore_from_backup()
```

**Validación:**
```bash
# Test debe ser idempotente
pytest tests/test_mcp/test_tools.py::test_tool_agregar_documento -v
pytest tests/test_mcp/test_tools.py::test_tool_agregar_documento -v
# Ambas ejecuciones deben pasar
```

---

### 2.3 Eliminar event_loop Fixture Session-Scoped

**Archivo a modificar:**
- `tests/test_backoffice/conftest.py`

**Antes:**
```python
@pytest.fixture(scope="session")
def event_loop():
    """Crea un event loop para toda la sesión de tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

**Después:**
```python
# ELIMINAR completamente esta fixture
# pytest-asyncio ya proporciona function-scoped event loops
```

**Validación:**
```bash
pytest tests/test_backoffice/ -v
# No debe haber warnings sobre event_loop
```

---

### 2.4 Fixtures de Expedientes con Session Scope

**Archivo a modificar:**
- `tests/test_mcp/conftest.py:40-55`

**Antes:**
```python
@pytest.fixture  # function scope por default
def exp_id_subvenciones():
    """ID del expediente de subvenciones"""
    return "EXP-2024-001"
```

**Después:**
```python
@pytest.fixture(scope="session")  # datos inmutables → session scope
def exp_id_subvenciones(test_constants):
    """ID del expediente de subvenciones"""
    return test_constants["default_exp_ids"][0]

@pytest.fixture(scope="session")
def exp_id_licencia(test_constants):
    """ID del expediente de licencia"""
    return test_constants["default_exp_ids"][1]

@pytest.fixture(scope="session")
def exp_id_certificado(test_constants):
    """ID del expediente de certificado"""
    return test_constants["default_exp_ids"][2]
```

**Beneficio:**
- Reduce overhead (fixtures se crean 1 vez en lugar de 100+)
- Datos vienen de constantes centralizadas

---

### Checklist Fase 2

- [ ] Mejorar `restore_expediente_data` con cleanup
- [ ] Eliminar `event_loop` fixture session-scoped
- [ ] Cambiar fixtures de expedientes a session scope
- [ ] Conectar fixtures con `test_constants`
- [ ] Ejecutar `./run-tests.sh` → todos deben pasar
- [ ] Verificar tiempo de ejecución (debe ser similar o menor)

---

## Fase 3: Mejorar Assertions 🎯

**Duración estimada:** 1-2 horas
**Prioridad:** MEDIA
**Objetivo:** Assertions más robustas y específicas

### 3.1 Reemplazar `.called` con `assert_called_once()`

**Archivos a modificar:**
- `tests/test_backoffice/test_executor.py` (múltiples líneas)
- `tests/test_backoffice/test_mcp_integration.py` (múltiples líneas)

**Patrón de búsqueda:**
```bash
grep -n "\.called" tests/test_backoffice/test_executor.py
```

**Antes:**
```python
assert mock_jwt_validator.validate.called  # ❌ deprecated
assert mock_logger.log.call_count > 0      # ❌ vago
```

**Después:**
```python
# Opción 1: Verificar que se llamó al menos una vez
mock_jwt_validator.validate.assert_called()

# Opción 2: Verificar que se llamó exactamente una vez
mock_jwt_validator.validate.assert_called_once()

# Opción 3: Verificar argumentos específicos
mock_jwt_validator.validate.assert_called_once_with(
    token="expected-token",
    secret="test-secret-key",
    algorithm="HS256",
    expected_expediente_id="EXP-2024-001"
)

# Para múltiples llamadas, verificar todas
expected_calls = [
    call(level="INFO", message="Iniciando ejecución"),
    call(level="INFO", message="JWT validado correctamente")
]
mock_logger.log.assert_has_calls(expected_calls, any_order=False)
```

**Script de búsqueda y reemplazo:**
```bash
# Encontrar todos los usos de .called
rg "\.called(?!\()" tests/ -l

# Encontrar call_count > 0
rg "call_count\s*>\s*0" tests/ -l
```

---

### 3.2 Mejorar Assertions en test_protocols.py

**Archivo a modificar:**
- `tests/test_backoffice/test_protocols.py`

**Antes:**
```python
def test_jwt_validator_protocol_structure():
    """Test: JWTValidatorProtocol tiene la firma esperada"""
    assert hasattr(JWTValidatorProtocol, 'validate')
```

**Después:**
```python
import inspect
from typing import get_type_hints

def test_jwt_validator_protocol_structure():
    """Test: JWTValidatorProtocol tiene estructura y signatura correctas"""
    # Verificar que es un Protocol
    assert isinstance(JWTValidatorProtocol, type)

    # Verificar que tiene el método validate
    assert hasattr(JWTValidatorProtocol, 'validate')

    # Verificar que es callable
    validate_method = getattr(JWTValidatorProtocol, 'validate')
    # En Protocols, los métodos tienen __annotations__
    assert hasattr(validate_method, '__annotations__'), \
        "validate() debe tener type annotations"

    # Verificar parámetros esperados
    annotations = validate_method.__annotations__
    # Debe tener al menos 'token' y 'return'
    assert len(annotations) > 0, "validate() debe estar anotado"
```

Aplicar patrón similar a:
- `test_mcp_client_protocol_structure()`
- `test_audit_logger_protocol_structure()`
- Todos los tests de protocols

---

### 3.3 Agregar Verificación de Args en Mocks Críticos

**Archivos a modificar:**
- `tests/test_backoffice/test_executor.py`

**Tests a mejorar:**

```python
def test_tc_ex_001_ejecucion_exitosa(executor, mock_jwt_validator, ...):
    """Test: Ejecución exitosa completa del AgentExecutor"""
    # ... setup ...

    result = await executor.execute(
        agent_config=agent_config,
        jwt_token="valid-token",
        expediente_id="EXP-2024-001",
        task_description="Descripción tarea"
    )

    # MEJORAR: Verificar argumentos específicos
    mock_jwt_validator.validate.assert_called_once_with(
        token="valid-token",
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        expected_expediente_id="EXP-2024-001"
    )

    # Verificar que registry se creó con config correcto
    mock_registry_class.assert_called_once()
    call_args = mock_registry_class.call_args
    assert call_args[0][0] == settings.mcp_config_path
    assert call_args[1]['jwt_token'] == "valid-token"
```

---

### Checklist Fase 3

- [ ] Buscar y reemplazar `.called` → `assert_called_once()`
- [ ] Mejorar assertions en `test_protocols.py` (7 tests)
- [ ] Agregar verificación de args en mocks de `test_executor.py`
- [ ] Ejecutar tests afectados individualmente
- [ ] Verificar que assertions más específicas atrapan bugs

---

## Fase 4: Cleanup y Documentación 📝

**Duración estimada:** 1 hora
**Prioridad:** BAJA
**Objetivo:** Código más limpio y mejor documentado

### 4.1 Re-enable Test Skipped con Issue Tracker

**Archivo a modificar:**
- `tests/test_mcp/test_server_http.py:116`

**Antes:**
```python
def test_sse_endpoint_token_valido_permite_procesamiento():
    """..."""
    pytest.skip("Test deshabilitado: transporte SSE causa timeouts en tests unitarios")
```

**Después:**
```python
@pytest.mark.skip(reason="SSE transport causes timeouts in unit tests - Issue #TODO")
def test_sse_endpoint_token_valido_permite_procesamiento():
    """
    Test de endpoint SSE con token válido.

    DISABLED: El transporte SSE en tests unitarios causa timeouts.
    Ver issue GitHub #TODO para tracking.

    Posibles soluciones:
    - Mock del EventSourceResponse
    - Usar pytest-timeout
    - Refactor a test de integración con timeout mayor
    """
    # TODO: Implementar cuando se resuelva issue
```

**Acción adicional:**
- Crear issue en GitHub describiendo el problema
- Actualizar `#TODO` con número de issue real

---

### 4.2 Estandarizar Nombres de Fixtures

**Archivos a modificar:**
- `tests/test_mcp/conftest.py`

**Antes (mezcla español/inglés):**
```python
test_expedientes()      # español
jwt_secret()           # inglés
exp_id_subvenciones()  # español abreviado
```

**Después (inglés consistente):**
```python
test_expediente_ids()      # inglés
jwt_secret()              # inglés
subvenciones_exp_id()     # inglés (más natural)
# o mantener exp_id_* si es el estándar del equipo
```

**Decisión de equipo:** ¿Inglés o español?
- Si código está en español → fixtures en español
- Si código mixto → usar inglés (estándar Python)

---

### 4.3 Mejorar Docstrings Redundantes

**Patrón a buscar:**
```bash
grep -A 2 "def test_" tests/ | grep '"""Test:'
```

**Antes:**
```python
def test_jwt_expired_returns_auth_error(...):
    """Test: Token expirado retorna error AUTH_TOKEN_EXPIRED"""
    # Setup
    # Execute
    # Assert
```

**Después:**
```python
def test_jwt_expired_returns_auth_error(...):
    """
    Verifica rechazo de tokens JWT expirados.

    El AgentExecutor debe detectar tokens expirados durante validación
    JWT y retornar AgentExecutionResult con:
    - success=False
    - error.codigo="AUTH_TOKEN_EXPIRED"
    - Sin intentar crear MCP registry

    Esto previene uso de credenciales expiradas en llamadas a MCPs.
    """
```

Eliminar comentarios vacíos:
- `# Setup`
- `# Execute`
- `# Assert`

(Solo útiles en tests complejos donde cada sección tiene 10+ líneas)

---

### 4.4 Crear pytest.ini

**Archivo a crear:**
- `pytest.ini` (raíz del proyecto)

```ini
[pytest]
# Directorio de tests
testpaths = tests

# Patrón de archivos de test
python_files = test_*.py

# Patrón de clases de test
python_classes = Test*

# Patrón de funciones de test
python_functions = test_*

# Opciones por defecto
addopts =
    # Output verboso
    -v
    # Mostrar resumen de tests
    -ra
    # Mostrar warnings
    --strict-markers
    # Asyncio mode
    --asyncio-mode=auto

# Markers personalizados
markers =
    slow: tests lentos (>1s)
    integration: tests de integración
    unit: tests unitarios

# Asyncio configuration
asyncio_mode = auto

# Warnings
filterwarnings =
    # Convertir PydanticDeprecatedSince20 en errores (forzar fix)
    error::pydantic.warnings.PydanticDeprecatedSince20
    # Ignorar warnings de dependencias externas
    ignore::DeprecationWarning:starlette.*
```

**Uso:**
```bash
# Tests rápidos solamente
pytest -m "not slow"

# Solo tests unitarios
pytest -m unit

# Ver markers disponibles
pytest --markers
```

---

### 4.5 Eliminar Imports Redundantes

**Script de búsqueda:**
```bash
# Encontrar imports no usados
ruff check tests/ --select F401
# o
flake8 tests/ --select=F401
```

**Ejemplos comunes:**
```python
# Si httpx solo se usa en mocks
import httpx  # ❌ Redundante

# Usar lazy import o eliminar
from unittest.mock import AsyncMock
# ... en test:
mock_response = AsyncMock(spec=httpx.Response)  # No requiere import
```

---

### Checklist Fase 4

- [ ] Crear issue para test skipped SSE
- [ ] Actualizar skip marker con issue number
- [ ] Decidir estándar de nombres (inglés/español)
- [ ] Renombrar fixtures según estándar
- [ ] Mejorar docstrings redundantes (10-20 tests)
- [ ] Crear `pytest.ini` con configuración
- [ ] Eliminar imports no usados
- [ ] Ejecutar `pytest --markers` para validar

---

## Fase 5: Métricas y CI/CD 📊

**Duración estimada:** 2-3 horas
**Prioridad:** OPCIONAL
**Objetivo:** Visibility sobre calidad y cobertura

### 5.1 Configurar Coverage.py

**Instalar:**
```bash
pip install pytest-cov
```

**Crear `.coveragerc`:**
```ini
[run]
source = src/
omit =
    */tests/*
    */conftest.py
    */__pycache__/*
    */venv/*

[report]
precision = 2
show_missing = True
skip_covered = False

exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod

[html]
directory = htmlcov
```

**Actualizar pytest.ini:**
```ini
addopts =
    ...
    # Coverage
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
```

**Ejecutar:**
```bash
pytest --cov
# Ver reporte HTML
open htmlcov/index.html
```

---

### 5.2 Pre-commit Hook

**Crear `.pre-commit-config.yaml`:**
```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-quick
        name: Run fast tests
        entry: pytest
        args: ["-m", "not slow", "--tb=short"]
        language: system
        pass_filenames: false
        always_run: true
```

**Instalar:**
```bash
pip install pre-commit
pre-commit install
```

**Uso:**
```bash
# Se ejecuta automáticamente en git commit
git commit -m "mensaje"
# Tests rápidos se ejecutan antes de permitir commit
```

---

### 5.3 GitHub Actions CI

**Crear `.github/workflows/tests.yml`:**
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -e .
        pip install pytest pytest-asyncio pytest-cov

    - name: Run tests with coverage
      run: |
        pytest --cov=src --cov-report=xml --cov-fail-under=80

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

### 5.4 Coverage Badge

**Agregar a README.md:**
```markdown
[![Coverage](https://codecov.io/gh/USUARIO/aGEntiX/branch/main/graph/badge.svg)](https://codecov.io/gh/USUARIO/aGEntiX)
[![Tests](https://github.com/USUARIO/aGEntiX/workflows/Tests/badge.svg)](https://github.com/USUARIO/aGEntiX/actions)
```

---

### Checklist Fase 5

- [ ] Instalar pytest-cov
- [ ] Crear `.coveragerc`
- [ ] Actualizar pytest.ini con coverage
- [ ] Ejecutar y verificar coverage > 80%
- [ ] Crear `.pre-commit-config.yaml`
- [ ] Instalar pre-commit hooks
- [ ] Crear GitHub Actions workflow
- [ ] Configurar Codecov
- [ ] Agregar badges a README

---

## Resumen de Archivos Modificados

### Crear
- [ ] `pytest.ini`
- [ ] `.coveragerc` (Fase 5)
- [ ] `.pre-commit-config.yaml` (Fase 5)
- [ ] `.github/workflows/tests.yml` (Fase 5)

### Modificar
- [ ] `conftest.py` (agregar fixtures)
- [ ] `tests/api/conftest.py` (simplificar)
- [ ] `tests/test_mcp/conftest.py` (eliminar duplicación)
- [ ] `tests/test_mcp/fixtures/tokens.py` (eliminar sys.path)
- [ ] `tests/test_backoffice/conftest.py` (eliminar event_loop)
- [ ] `tests/test_backoffice/test_executor.py` (assertions)
- [ ] `tests/test_backoffice/test_protocols.py` (assertions)
- [ ] `tests/test_mcp/test_*.py` (eliminar os.environ)

### Eliminar código de
- [ ] 4 archivos con `os.environ["JWT_SECRET"]`
- [ ] 3 archivos con manipulación de sys.path
- [ ] 2 archivos con fixture jwt_secret duplicada
- [ ] 1 archivo con event_loop session-scoped

---

## Estimación de Esfuerzo

| Fase | Duración | Prioridad | ROI |
|------|----------|-----------|-----|
| Fase 1 | 1-2h | CRÍTICA | 🔴 Alto - Fix 33 tests rotos |
| Fase 2 | 2-3h | ALTA | 🟠 Alto - Elimina duplicación |
| Fase 3 | 1-2h | MEDIA | 🟡 Medio - Mejora robustez |
| Fase 4 | 1h | BAJA | 🟢 Bajo - Limpieza |
| Fase 5 | 2-3h | OPCIONAL | 🔵 Variable - Según needs |

**Total (Fases 1-4):** 5-8 horas
**Total (con Fase 5):** 7-11 horas

---

## Criterios de Éxito

### Después de Fase 1
- ✅ 152/152 tests ejecutándose (100%)
- ✅ 0 warnings de sys.path
- ✅ 1 solo lugar con manipulación de sys.path

### Después de Fase 2
- ✅ 0 fixtures duplicadas
- ✅ restore_expediente_data idempotente
- ✅ 0 session-scoped event_loop fixtures

### Después de Fase 3
- ✅ 0 usos de `.called` (deprecated)
- ✅ Assertions específicas en mocks críticos
- ✅ test_protocols.py con verificaciones robustas

### Después de Fase 4
- ✅ pytest.ini configurado
- ✅ Docstrings mejorados
- ✅ Issue tracker para test skipped

### Después de Fase 5
- ✅ Coverage > 80%
- ✅ CI/CD ejecutando tests
- ✅ Badges de coverage en README

---

## Siguiente Paso

**¿Implementar Fase 1 ahora?**

Puedo implementar los arreglos críticos de Fase 1 inmediatamente para hacer que los 33 tests de API se ejecuten.

```bash
# Comando para validar después de implementar
pytest tests/api/ -v
./run-tests.sh
# Debe mostrar: 152 tests PASSED
```
