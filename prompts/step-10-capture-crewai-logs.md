# Step 10: Capturar Logs de CrewAI

## Contexto

El log es muy importante para el proyecto por trazabilidad y por compliance.
Revisa el código `src/backoffice/logging`

Los agentes CrewAI no utilizan nuestro sistema de logging. Actualmente:
- `AuditLogger` maneja logs con redacción de PII (GDPR/LOPD/ENS)
- Los agentes CrewAI usan su propio logger interno basado en https://github.com/Textualize/rich
- Los mensajes de CrewAI (razonamiento del agente, uso de tools, errores) no quedan registrados en nuestro sistema de auditoría

## Problema

Cuando CrewAI ejecuta un agente:
1. El razonamiento del LLM (chain-of-thought) se imprime a stdout usando rich
2. Estos logs NO pasan por nuestro `PIIRedactor`
3. Estos logs NO quedan en nuestros archivos de auditoría

Esto es un problema de compliance porque:
- Puede haber PII en los razonamientos del agente
- No tenemos trazabilidad completa de lo que hace el agente
- Los logs de CrewAI no están en formato JSON lines como el resto

## Solución

Según la documentación de CrewAI, es posible acceder a los logs usando `output_log_file`:
- Documentación: https://docs.crewai.com/concepts/crews
- PR con soporte JSON: https://github.com/crewAIInc/crewAI/pull/1985

```python
crew = Crew(
    agents=[agent],
    tasks=[task],
    output_log_file="crewai_logs.json",
    save_as_json=True  # Formato JSON estructurado
)
```

El plan es:
1. Crear un archivo temporal para los logs de CrewAI
2. Ejecutar el crew con `output_log_file` apuntando a ese archivo
3. Después de la ejecución, leer el archivo JSON
4. Procesar cada entrada y pasarla por `AuditLogger` (que aplica `PIIRedactor`)
5. Eliminar el archivo temporal

---

## Plan de Implementación

### Paso 1: Crear módulo de procesamiento de logs

Crear `src/backoffice/logging/crewai_log_processor.py`:

```python
# backoffice/logging/crewai_log_processor.py

"""
Procesador de logs de CrewAI.

Lee los logs generados por CrewAI (output_log_file) y los redirige
a AuditLogger, asegurando redacción de PII para compliance GDPR/LOPD/ENS.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Optional
from .audit_logger import AuditLogger


def create_crewai_log_file(run_id: str) -> Path:
    """
    Crea un archivo temporal para los logs de CrewAI.

    Args:
        run_id: ID único de la ejecución para nombrar el archivo

    Returns:
        Path al archivo temporal
    """
    # Usar directorio temporal del sistema
    temp_dir = Path(tempfile.gettempdir()) / "crewai_logs"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir / f"{run_id}_crewai.json"


def process_crewai_logs(
    log_file: Path,
    audit_logger: AuditLogger,
    delete_after: bool = True
) -> int:
    """
    Procesa los logs de CrewAI y los redirige a AuditLogger.

    Lee el archivo JSON generado por CrewAI, procesa cada entrada
    y la envía a AuditLogger (que aplica PIIRedactor automáticamente).

    Args:
        log_file: Path al archivo de logs de CrewAI
        audit_logger: Logger de auditoría donde redirigir
        delete_after: Si True, elimina el archivo después de procesar

    Returns:
        Número de entradas procesadas
    """
    if not log_file.exists():
        audit_logger.warning(
            f"Archivo de logs de CrewAI no encontrado: {log_file}"
        )
        return 0

    entries_processed = 0

    try:
        content = log_file.read_text(encoding="utf-8")

        # El archivo puede ser un array JSON o líneas JSON
        try:
            # Intentar como array JSON
            log_entries = json.loads(content)
            if not isinstance(log_entries, list):
                log_entries = [log_entries]
        except json.JSONDecodeError:
            # Intentar como JSON lines
            log_entries = []
            for line in content.strip().split("\n"):
                if line.strip():
                    try:
                        log_entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        # Línea no es JSON, loguear como texto plano
                        log_entries.append({"message": line})

        # Procesar cada entrada
        for entry in log_entries:
            _process_single_entry(entry, audit_logger)
            entries_processed += 1

    except Exception as e:
        audit_logger.error(
            f"Error procesando logs de CrewAI: {str(e)}",
            metadata={"log_file": str(log_file)}
        )

    finally:
        if delete_after and log_file.exists():
            try:
                log_file.unlink()
            except OSError as e:
                audit_logger.warning(
                    f"No se pudo eliminar archivo temporal: {str(e)}"
                )

    return entries_processed


def _process_single_entry(entry: dict, audit_logger: AuditLogger) -> None:
    """
    Procesa una entrada individual de log de CrewAI.

    Args:
        entry: Diccionario con la entrada de log
        audit_logger: Logger donde escribir
    """
    # Extraer mensaje principal
    message = entry.get("message", entry.get("content", str(entry)))

    # Determinar nivel de log
    level = entry.get("level", entry.get("type", "INFO")).upper()
    if level not in ("INFO", "WARNING", "ERROR", "DEBUG"):
        level = "INFO"

    # DEBUG se mapea a INFO en nuestro sistema
    if level == "DEBUG":
        level = "INFO"

    # Construir metadata
    metadata = {
        "source": "crewai",
        "original_entry": entry
    }

    # Extraer campos comunes de CrewAI
    for field in ["agent", "task", "tool", "timestamp", "type"]:
        if field in entry and field != "message":
            metadata[f"crewai_{field}"] = entry[field]

    # Loguear con prefijo [CrewAI]
    audit_logger.log(
        mensaje=f"[CrewAI] {message}",
        nivel=level,
        metadata=metadata
    )
```

### Paso 2: Integrar en base_real.py

Modificar `src/backoffice/agents/base_real.py`:

```python
# Añadir import
from ..logging.crewai_log_processor import create_crewai_log_file, process_crewai_logs

# En el método execute(), modificar la creación del Crew:

async def execute(self) -> Dict[str, Any]:
    """..."""
    self.logger.log(
        f"Iniciando agente CrewAI '{self.config.name}' "
        f"para expediente {self.expediente_id}"
    )
    self.logger.log(f"Herramientas MCP disponibles: {self.config.mcp_tools}")

    # Crear archivo temporal para logs de CrewAI
    crewai_log_file = create_crewai_log_file(self.run_id)

    try:
        # ... código existente para crear agent y task ...

        # Crear crew CON captura de logs
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True,
            output_log_file=str(crewai_log_file),
            save_as_json=True  # Formato JSON estructurado
        )

        # Ejecutar crew
        self.logger.log("Ejecutando crew...")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, crew.kickoff)

        self.logger.log("Agente completado exitosamente")

        # Procesar logs de CrewAI DESPUÉS de la ejecución
        entries = process_crewai_logs(crewai_log_file, self.logger)
        self.logger.log(f"Procesadas {entries} entradas de logs de CrewAI")

        # ... resto del código ...

    except Exception as e:
        # Procesar logs incluso en caso de error
        process_crewai_logs(crewai_log_file, self.logger)
        error_msg = f"Error en agente CrewAI: {str(e)}"
        self.logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    finally:
        # Asegurar que el archivo temporal se elimine
        if crewai_log_file.exists():
            crewai_log_file.unlink()
```

### Paso 3: Actualizar __init__.py

Actualizar `src/backoffice/logging/__init__.py`:

```python
from .audit_logger import AuditLogger
from .pii_redactor import PIIRedactor
from .crewai_log_processor import (
    create_crewai_log_file,
    process_crewai_logs
)

__all__ = [
    "AuditLogger",
    "PIIRedactor",
    "create_crewai_log_file",
    "process_crewai_logs"
]
```

### Paso 4: Tests

Crear `tests/test_backoffice/test_crewai_log_processor.py`:

```python
# tests/test_backoffice/test_crewai_log_processor.py

"""
Tests para el procesador de logs de CrewAI.
"""

import json
import pytest
from pathlib import Path

from backoffice.logging.crewai_log_processor import (
    create_crewai_log_file,
    process_crewai_logs
)
from backoffice.logging.audit_logger import AuditLogger


@pytest.fixture
def audit_logger(tmp_path):
    """AuditLogger de prueba."""
    return AuditLogger(
        expediente_id="EXP-TEST-001",
        agent_run_id="run-test-001",
        log_dir=tmp_path
    )


class TestCreateCrewaiLogFile:
    """Tests para create_crewai_log_file."""

    def test_creates_file_path(self):
        """Debe crear un path válido."""
        path = create_crewai_log_file("run-123")
        assert path.name == "run-123_crewai.json"
        assert "crewai_logs" in str(path)

    def test_creates_parent_directory(self):
        """Debe crear el directorio padre si no existe."""
        path = create_crewai_log_file("run-456")
        assert path.parent.exists()


class TestProcessCrewaiLogs:
    """Tests para process_crewai_logs."""

    def test_processes_json_array(self, tmp_path, audit_logger):
        """Debe procesar un array JSON de logs."""
        log_file = tmp_path / "test_logs.json"
        logs = [
            {"message": "Agent starting", "type": "info"},
            {"message": "Using tool", "type": "info", "tool": "search"}
        ]
        log_file.write_text(json.dumps(logs))

        count = process_crewai_logs(log_file, audit_logger, delete_after=False)

        assert count == 2
        entries = audit_logger.get_log_entries()
        assert any("Agent starting" in e for e in entries)
        assert any("Using tool" in e for e in entries)

    def test_processes_json_lines(self, tmp_path, audit_logger):
        """Debe procesar formato JSON lines."""
        log_file = tmp_path / "test_logs.json"
        content = '{"message": "Line 1"}\n{"message": "Line 2"}\n'
        log_file.write_text(content)

        count = process_crewai_logs(log_file, audit_logger, delete_after=False)

        assert count == 2

    def test_deletes_file_after_processing(self, tmp_path, audit_logger):
        """Debe eliminar el archivo después de procesar."""
        log_file = tmp_path / "test_logs.json"
        log_file.write_text('{"message": "test"}')

        process_crewai_logs(log_file, audit_logger, delete_after=True)

        assert not log_file.exists()

    def test_keeps_file_when_delete_after_false(self, tmp_path, audit_logger):
        """Debe mantener el archivo si delete_after=False."""
        log_file = tmp_path / "test_logs.json"
        log_file.write_text('{"message": "test"}')

        process_crewai_logs(log_file, audit_logger, delete_after=False)

        assert log_file.exists()

    def test_handles_missing_file(self, tmp_path, audit_logger):
        """Debe manejar archivo inexistente sin error."""
        log_file = tmp_path / "nonexistent.json"

        count = process_crewai_logs(log_file, audit_logger)

        assert count == 0

    def test_redacts_pii_in_logs(self, tmp_path, audit_logger):
        """Debe redactar PII en los logs de CrewAI."""
        log_file = tmp_path / "test_logs.json"
        logs = [{"message": "Usuario con DNI 12345678A contactado"}]
        log_file.write_text(json.dumps(logs))

        process_crewai_logs(log_file, audit_logger, delete_after=False)

        entries = audit_logger.get_log_entries()
        assert any("[DNI-REDACTED]" in e for e in entries)
        assert not any("12345678A" in e for e in entries)

    def test_redacts_email_in_logs(self, tmp_path, audit_logger):
        """Debe redactar emails en los logs."""
        log_file = tmp_path / "test_logs.json"
        logs = [{"message": "Enviando a usuario@example.com"}]
        log_file.write_text(json.dumps(logs))

        process_crewai_logs(log_file, audit_logger, delete_after=False)

        entries = audit_logger.get_log_entries()
        assert any("[EMAIL-REDACTED]" in e for e in entries)
        assert not any("usuario@example.com" in e for e in entries)

    def test_adds_crewai_prefix(self, tmp_path, audit_logger):
        """Debe añadir prefijo [CrewAI] a los mensajes."""
        log_file = tmp_path / "test_logs.json"
        logs = [{"message": "Test message"}]
        log_file.write_text(json.dumps(logs))

        process_crewai_logs(log_file, audit_logger, delete_after=False)

        entries = audit_logger.get_log_entries()
        assert any("[CrewAI]" in e for e in entries)

    def test_maps_error_level(self, tmp_path, audit_logger):
        """Debe mapear nivel ERROR correctamente."""
        log_file = tmp_path / "test_logs.json"
        logs = [{"message": "Error occurred", "level": "ERROR"}]
        log_file.write_text(json.dumps(logs))

        process_crewai_logs(log_file, audit_logger, delete_after=False)

        # Verificar en el archivo de log
        log_content = (tmp_path / "EXP-TEST-001" / "run-test-001.log").read_text()
        assert '"level": "ERROR"' in log_content

    def test_extracts_crewai_metadata(self, tmp_path, audit_logger):
        """Debe extraer metadata específica de CrewAI."""
        log_file = tmp_path / "test_logs.json"
        logs = [{
            "message": "Task completed",
            "agent": "Analyst",
            "task": "Analysis",
            "tool": "search_tool"
        }]
        log_file.write_text(json.dumps(logs))

        process_crewai_logs(log_file, audit_logger, delete_after=False)

        log_content = (tmp_path / "EXP-TEST-001" / "run-test-001.log").read_text()
        assert "crewai_agent" in log_content
        assert "crewai_task" in log_content
        assert "crewai_tool" in log_content
```

---

## Verificación

Después de implementar, verificar:

1. **Tests pasan:**
   ```bash
   pytest tests/test_backoffice/test_crewai_log_processor.py -v
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

4. **Archivo temporal eliminado:**
   ```bash
   # Verificar que no quedan archivos en /tmp/crewai_logs/
   ```

5. **Logs en formato correcto:**
   ```bash
   # Los logs deben estar en JSON lines con:
   # - timestamp
   # - level
   # - mensaje con prefijo [CrewAI]
   # - metadata.source = "crewai"
   ```

---

## Ventajas de esta solución

1. **Usa API oficial de CrewAI** - `output_log_file` está documentado y soportado
2. **Formato JSON estructurado** - Fácil de parsear con `save_as_json=True`
3. **No requiere monkey-patching** - No interceptamos internals de CrewAI
4. **Captura completa** - Obtiene todos los logs que CrewAI genera
5. **Limpieza automática** - El archivo temporal se elimina después de procesar

## Consideraciones

### Logs en tiempo real vs post-ejecución

Esta solución procesa los logs DESPUÉS de la ejecución del crew. Si se necesitan logs en tiempo real durante la ejecución, habría que considerar:

1. Un thread separado que monitoree el archivo
2. Usar el sistema de callbacks de CrewAI (más complejo)

Para compliance, el procesamiento post-ejecución es suficiente ya que todos los logs quedan registrados.

### Verbose mode

El `verbose=True` en el Crew sigue imprimiendo a stdout. Los logs capturados con `output_log_file` son independientes. Para producción, considerar `verbose=False` para reducir ruido en stdout.

---

## Resultado Esperado

Después de esta implementación:

1. ✅ Todos los logs de CrewAI pasan por PIIRedactor
2. ✅ Los razonamientos del agente quedan en auditoría
3. ✅ Formato JSON lines consistente con el resto del sistema
4. ✅ Metadata indica origen (source: crewai)
5. ✅ Archivo temporal eliminado automáticamente
6. ✅ Tests de compliance PII incluyen logs de CrewAI
7. ✅ Usa API oficial de CrewAI (no hacks)
