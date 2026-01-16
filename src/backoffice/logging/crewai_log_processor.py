# backoffice/logging/crewai_log_processor.py

"""
Procesador de logs de CrewAI.

Lee los logs generados por CrewAI (output_log_file) y los redirige
a AuditLogger, asegurando redacción de PII para compliance GDPR/LOPD/ENS.
"""

import json
import tempfile
from pathlib import Path
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
