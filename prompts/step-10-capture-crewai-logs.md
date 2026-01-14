# Step 10: Capturar Logs de CrewAI

## Contexto

El log es muy importante para el proyecto por trazabilidad y por compliance.
Revisa el código `src/backoffice/logging`

Los agentes CrewAI no utilizan nuestro sistema de logging. Actualmente:
- `AuditLogger` maneja logs con redacción de PII (GDPR/LOPD/ENS)
- Los agentes CrewAI usan su propio logger interno
- Los mensajes de CrewAI (razonamiento del agente, uso de tools, errores) no quedan registrados en nuestro sistema de auditoría

## Problema

Cuando CrewAI ejecuta un agente:
1. El razonamiento del LLM (chain-of-thought) se imprime a stdout
2. Los logs internos van al logger de Python estándar "crewai"
3. Estos logs NO pasan por nuestro `PIIRedactor`
4. Estos logs NO quedan en nuestros archivos de auditoría

Esto es un problema de compliance porque:
- Puede haber PII en los razonamientos del agente
- No tenemos trazabilidad completa de lo que hace el agente
- Los logs de CrewAI no están en formato JSON lines como el resto

## Solución: Interceptar el logger interno de CrewAI

A priori es posible hacer "Interceptar el logger interno de CrewAI". Vamos a implementarlo.

### Ejemplo base sacado de Internet:

```python
import logging

# Crear un handler personalizado
class BPMNLogHandler(logging.Handler):
    def __init__(self, bpmn_logger, process_instance_id):
        super().__init__()
        self.bpmn_logger = bpmn_logger
        self.process_instance_id = process_instance_id

    def emit(self, record):
        log_entry = {
            "timestamp": record.created,
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "process_instance_id": self.process_instance_id,
            "source": "crewai"
        }
        self.bpmn_logger.ingest(log_entry)

# Conectar al logger de CrewAI
crewai_logger = logging.getLogger("crewai")
crewai_logger.addHandler(BPMNLogHandler(tu_sistema_log, process_id))
crewai_logger.setLevel(logging.DEBUG)
```

---

## Plan de Implementación

### Paso 1: Crear CrewAILogHandler

Crear un nuevo archivo `src/backoffice/logging/crewai_handler.py`:

```python
# backoffice/logging/crewai_handler.py

"""
Handler para capturar logs de CrewAI y redirigirlos a AuditLogger.

Este handler intercepta los logs internos de CrewAI (razonamiento del agente,
uso de tools, errores) y los redirige a nuestro sistema de auditoría,
asegurando que pasen por PIIRedactor para compliance GDPR/LOPD/ENS.
"""

import logging
from typing import Optional
from .audit_logger import AuditLogger


class CrewAILogHandler(logging.Handler):
    """
    Handler que redirige logs de CrewAI a AuditLogger.

    Características:
    - Captura todos los niveles de log (DEBUG, INFO, WARNING, ERROR)
    - Los mensajes pasan automáticamente por PIIRedactor vía AuditLogger
    - Añade metadata sobre el origen (módulo, función, línea)
    - Marca los logs con source="crewai" para filtrado posterior
    """

    def __init__(self, audit_logger: AuditLogger):
        """
        Inicializa el handler.

        Args:
            audit_logger: Instancia de AuditLogger donde redirigir los logs
        """
        super().__init__()
        self.audit_logger = audit_logger
        # Formato simple para el handler
        self.setFormatter(logging.Formatter('%(message)s'))

    def emit(self, record: logging.LogRecord) -> None:
        """
        Procesa un log record de CrewAI.

        El mensaje se redirige a AuditLogger, que automáticamente
        aplica PIIRedactor antes de escribir a disco.

        Args:
            record: Log record de Python logging
        """
        try:
            # Obtener mensaje formateado
            mensaje = self.format(record)

            # Mapear nivel de logging a nuestro sistema
            nivel = self._map_level(record.levelno)

            # Metadata del origen
            metadata = {
                "source": "crewai",
                "module": record.module,
                "funcName": record.funcName,
                "lineno": record.lineno,
                "logger_name": record.name
            }

            # Añadir info de excepción si existe
            if record.exc_info:
                metadata["exc_info"] = self.formatException(record.exc_info)

            # Delegar a AuditLogger (que aplica PIIRedactor)
            self.audit_logger.log(
                mensaje=f"[CrewAI] {mensaje}",
                nivel=nivel,
                metadata=metadata
            )

        except Exception:
            # No fallar silenciosamente, pero tampoco romper la ejecución
            self.handleError(record)

    def _map_level(self, levelno: int) -> str:
        """
        Mapea nivel de logging de Python a nuestro sistema.

        Args:
            levelno: Nivel numérico de logging

        Returns:
            String del nivel (INFO, WARNING, ERROR)
        """
        if levelno >= logging.ERROR:
            return "ERROR"
        elif levelno >= logging.WARNING:
            return "WARNING"
        else:
            return "INFO"


def setup_crewai_logging(audit_logger: AuditLogger) -> logging.Handler:
    """
    Configura la captura de logs de CrewAI.

    Esta función debe llamarse antes de ejecutar cualquier Crew.

    Args:
        audit_logger: AuditLogger donde redirigir los logs

    Returns:
        El handler instalado (para poder removerlo después si es necesario)

    Example:
        >>> logger = AuditLogger(expediente_id, run_id, log_dir)
        >>> handler = setup_crewai_logging(logger)
        >>> # ... ejecutar crew ...
        >>> # Al terminar, opcionalmente remover:
        >>> logging.getLogger("crewai").removeHandler(handler)
    """
    handler = CrewAILogHandler(audit_logger)
    handler.setLevel(logging.DEBUG)  # Capturar todo

    # Obtener logger de CrewAI y añadir nuestro handler
    crewai_logger = logging.getLogger("crewai")
    crewai_logger.addHandler(handler)
    crewai_logger.setLevel(logging.DEBUG)

    # También capturar logs de LiteLLM (usado por CrewAI)
    litellm_logger = logging.getLogger("litellm")
    litellm_handler = CrewAILogHandler(audit_logger)
    litellm_handler.setLevel(logging.DEBUG)
    litellm_logger.addHandler(litellm_handler)
    litellm_logger.setLevel(logging.DEBUG)

    return handler


def teardown_crewai_logging(handler: logging.Handler) -> None:
    """
    Remueve el handler de logs de CrewAI.

    Útil para limpiar después de una ejecución.

    Args:
        handler: Handler a remover (retornado por setup_crewai_logging)
    """
    logging.getLogger("crewai").removeHandler(handler)
    logging.getLogger("litellm").removeHandler(handler)
```

### Paso 2: Integrar en base_real.py

Modificar `src/backoffice/agents/base_real.py` para usar el handler:

```python
# En el método execute(), antes de crear el Crew:

from ..logging.crewai_handler import setup_crewai_logging, teardown_crewai_logging

async def execute(self) -> Dict[str, Any]:
    """..."""
    self.logger.log(f"Iniciando agente CrewAI '{self.config.name}'...")

    # Configurar captura de logs de CrewAI
    crewai_handler = setup_crewai_logging(self.logger)

    try:
        # ... resto del código de ejecución del crew ...

        result = await loop.run_in_executor(None, crew.kickoff)

        self.logger.log("Agente completado exitosamente")

        return {
            "completado": True,
            "mensaje": str(result),
            "datos_actualizados": resultado_parseado
        }

    except Exception as e:
        error_msg = f"Error en agente CrewAI: {str(e)}"
        self.logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    finally:
        # Siempre limpiar el handler
        teardown_crewai_logging(crewai_handler)
```

### Paso 3: Actualizar __init__.py

Actualizar `src/backoffice/logging/__init__.py`:

```python
from .audit_logger import AuditLogger
from .pii_redactor import PIIRedactor
from .crewai_handler import (
    CrewAILogHandler,
    setup_crewai_logging,
    teardown_crewai_logging
)

__all__ = [
    "AuditLogger",
    "PIIRedactor",
    "CrewAILogHandler",
    "setup_crewai_logging",
    "teardown_crewai_logging"
]
```

### Paso 4: Tests

Crear `tests/test_backoffice/test_crewai_handler.py`:

```python
# tests/test_backoffice/test_crewai_handler.py

"""
Tests para CrewAILogHandler.
"""

import logging
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile

from src.backoffice.logging.crewai_handler import (
    CrewAILogHandler,
    setup_crewai_logging,
    teardown_crewai_logging
)
from src.backoffice.logging.audit_logger import AuditLogger


@pytest.fixture
def temp_log_dir():
    """Directorio temporal para logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def audit_logger(temp_log_dir):
    """AuditLogger de prueba."""
    return AuditLogger(
        expediente_id="EXP-TEST-001",
        agent_run_id="run-test-001",
        log_dir=temp_log_dir
    )


class TestCrewAILogHandler:
    """Tests para CrewAILogHandler."""

    def test_handler_redirects_to_audit_logger(self, audit_logger):
        """El handler debe redirigir logs a AuditLogger."""
        handler = CrewAILogHandler(audit_logger)

        # Crear un log record simulado
        record = logging.LogRecord(
            name="crewai",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message from CrewAI",
            args=(),
            exc_info=None
        )

        handler.emit(record)

        # Verificar que se logueó
        entries = audit_logger.get_log_entries()
        assert len(entries) == 1
        assert "[CrewAI] Test message from CrewAI" in entries[0]

    def test_handler_maps_error_level(self, audit_logger, temp_log_dir):
        """Los errores deben mapearse correctamente."""
        handler = CrewAILogHandler(audit_logger)

        record = logging.LogRecord(
            name="crewai",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error in agent",
            args=(),
            exc_info=None
        )

        handler.emit(record)

        # Leer el archivo de log para verificar nivel
        log_file = temp_log_dir / "EXP-TEST-001" / "run-test-001.log"
        content = log_file.read_text()
        assert '"level": "ERROR"' in content

    def test_handler_maps_warning_level(self, audit_logger, temp_log_dir):
        """Los warnings deben mapearse correctamente."""
        handler = CrewAILogHandler(audit_logger)

        record = logging.LogRecord(
            name="crewai",
            level=logging.WARNING,
            pathname="test.py",
            lineno=42,
            msg="Warning in agent",
            args=(),
            exc_info=None
        )

        handler.emit(record)

        log_file = temp_log_dir / "EXP-TEST-001" / "run-test-001.log"
        content = log_file.read_text()
        assert '"level": "WARNING"' in content

    def test_handler_includes_metadata(self, audit_logger, temp_log_dir):
        """El handler debe incluir metadata del origen."""
        handler = CrewAILogHandler(audit_logger)

        record = logging.LogRecord(
            name="crewai.agents",
            level=logging.INFO,
            pathname="agents.py",
            lineno=100,
            msg="Agent thinking",
            args=(),
            exc_info=None,
            func="think"
        )
        record.module = "agents"
        record.funcName = "think"

        handler.emit(record)

        log_file = temp_log_dir / "EXP-TEST-001" / "run-test-001.log"
        content = log_file.read_text()
        assert '"source": "crewai"' in content
        assert '"module": "agents"' in content

    def test_handler_redacts_pii(self, audit_logger):
        """Los logs de CrewAI deben pasar por PIIRedactor."""
        handler = CrewAILogHandler(audit_logger)

        # Log con PII
        record = logging.LogRecord(
            name="crewai",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Usuario con DNI 12345678A encontrado",
            args=(),
            exc_info=None
        )

        handler.emit(record)

        # Verificar que el DNI fue redactado
        entries = audit_logger.get_log_entries()
        assert "[DNI-REDACTED]" in entries[0]
        assert "12345678A" not in entries[0]

    def test_handler_redacts_email_in_crewai_logs(self, audit_logger):
        """Los emails en logs de CrewAI deben redactarse."""
        handler = CrewAILogHandler(audit_logger)

        record = logging.LogRecord(
            name="crewai",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Contactando a usuario@example.com",
            args=(),
            exc_info=None
        )

        handler.emit(record)

        entries = audit_logger.get_log_entries()
        assert "[EMAIL-REDACTED]" in entries[0]
        assert "usuario@example.com" not in entries[0]


class TestSetupCrewAILogging:
    """Tests para setup_crewai_logging."""

    def test_setup_adds_handler_to_crewai_logger(self, audit_logger):
        """setup_crewai_logging debe añadir handler al logger de crewai."""
        handler = setup_crewai_logging(audit_logger)

        try:
            crewai_logger = logging.getLogger("crewai")
            assert handler in crewai_logger.handlers
        finally:
            teardown_crewai_logging(handler)

    def test_setup_sets_debug_level(self, audit_logger):
        """setup_crewai_logging debe configurar nivel DEBUG."""
        handler = setup_crewai_logging(audit_logger)

        try:
            crewai_logger = logging.getLogger("crewai")
            assert crewai_logger.level == logging.DEBUG
        finally:
            teardown_crewai_logging(handler)

    def test_teardown_removes_handler(self, audit_logger):
        """teardown_crewai_logging debe remover el handler."""
        handler = setup_crewai_logging(audit_logger)
        crewai_logger = logging.getLogger("crewai")

        assert handler in crewai_logger.handlers

        teardown_crewai_logging(handler)

        assert handler not in crewai_logger.handlers

    def test_logs_are_captured_after_setup(self, audit_logger):
        """Después de setup, los logs de crewai deben capturarse."""
        handler = setup_crewai_logging(audit_logger)

        try:
            # Simular un log de CrewAI
            crewai_logger = logging.getLogger("crewai")
            crewai_logger.info("Agent starting task")

            entries = audit_logger.get_log_entries()
            assert any("Agent starting task" in entry for entry in entries)
        finally:
            teardown_crewai_logging(handler)

    def test_litellm_logs_also_captured(self, audit_logger):
        """Los logs de LiteLLM también deben capturarse."""
        handler = setup_crewai_logging(audit_logger)

        try:
            litellm_logger = logging.getLogger("litellm")
            litellm_logger.info("Making API call")

            entries = audit_logger.get_log_entries()
            assert any("Making API call" in entry for entry in entries)
        finally:
            teardown_crewai_logging(handler)
```

---

## Verificación

Después de implementar, verificar:

1. **Tests pasan:**
   ```bash
   pytest tests/test_backoffice/test_crewai_handler.py -v
   ```

2. **Integración funciona:**
   ```bash
   # Ejecutar un agente real y verificar que los logs de CrewAI aparecen
   # en el archivo de auditoría con [CrewAI] prefix
   ```

3. **PII redactado:**
   ```bash
   # Verificar que DNIs, emails, etc. en razonamientos del agente
   # aparecen redactados en los logs
   ```

4. **Logs en formato correcto:**
   ```bash
   # Los logs deben estar en JSON lines con:
   # - timestamp
   # - level
   # - mensaje con prefijo [CrewAI]
   # - metadata.source = "crewai"
   ```

---

## Consideraciones Adicionales

### Verbose mode de CrewAI

CrewAI tiene `verbose=True` que imprime a stdout. Esto es independiente del logger de Python. Opciones:

1. **Capturar stdout** (más complejo, no recomendado)
2. **Deshabilitar verbose** y confiar solo en nuestros logs
3. **Dejar ambos** (verbose para desarrollo, logs para producción)

Recomendación: Opción 3 por ahora, evaluar en producción.

### Rate limiting de logs

Si CrewAI genera muchos logs DEBUG, considerar:
- Filtrar por nivel (solo INFO+)
- Agregar sampling para DEBUG
- Configurar nivel via variable de entorno

### Logs de LangChain

Si se usa LangChain internamente, también habría que capturar:
```python
langchain_logger = logging.getLogger("langchain")
langchain_logger.addHandler(handler)
```

---

## Resultado Esperado

Después de esta implementación:

1. ✅ Todos los logs de CrewAI pasan por PIIRedactor
2. ✅ Los razonamientos del agente quedan en auditoría
3. ✅ Formato JSON lines consistente con el resto del sistema
4. ✅ Metadata indica origen (source: crewai)
5. ✅ Limpieza automática del handler al terminar ejecución
6. ✅ Tests de compliance PII incluyen logs de CrewAI
