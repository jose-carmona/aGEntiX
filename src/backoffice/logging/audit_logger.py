# backoffice/logging/audit_logger.py

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from .pii_redactor import PIIRedactor


class AuditLogger:
    """
    Logger de auditoría con redacción automática de PII.

    Todos los mensajes y metadata se redactan automáticamente antes
    de escribirse a disco para cumplir con GDPR/LOPD/ENS.
    """

    def __init__(self, expediente_id: str, agent_run_id: str, log_dir: Path | str):
        """
        Inicializa el logger de auditoría.

        Args:
            expediente_id: ID del expediente
            agent_run_id: ID único de esta ejecución del agente
            log_dir: Directorio base para logs (Path o string)
        """
        self.expediente_id = expediente_id
        self.agent_run_id = agent_run_id
        # Convertir a Path si es string para evitar TypeError con operador /
        self.log_dir = Path(log_dir) if isinstance(log_dir, str) else log_dir
        self.log_file = self.log_dir / expediente_id / f"{agent_run_id}.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._entries = []

    def log(
        self,
        mensaje: str,
        nivel: str = "INFO",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Registra una entrada en el log CON REDACCIÓN AUTOMÁTICA DE PII.

        IMPORTANTE: Este método redacta automáticamente DNIs, emails,
        IBANs, teléfonos, etc. antes de escribir a disco.

        Args:
            mensaje: Mensaje a logear (será redactado automáticamente)
            nivel: Nivel de log (INFO, WARNING, ERROR)
            metadata: Metadata adicional (también será redactada)

        Examples:
            >>> logger.log("Usuario con DNI 12345678A solicita expediente")
            # Escribe: "Usuario con DNI [DNI-REDACTED] solicita expediente"

            >>> logger.log("Contacto", metadata={"email": "juan@example.com"})
            # Escribe metadata con email redactado
        """
        # REDACTAR PII antes de logear
        mensaje_redactado = PIIRedactor.redact(mensaje)

        entrada = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": nivel,
            "agent_run_id": self.agent_run_id,
            "expediente_id": self.expediente_id,
            "mensaje": mensaje_redactado
        }

        if metadata:
            # Redactar también la metadata
            metadata_str = json.dumps(metadata, ensure_ascii=False)
            metadata_redacted_str = PIIRedactor.redact(metadata_str)
            entrada["metadata"] = json.loads(metadata_redacted_str)

        # Escribir a archivo (JSON lines)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False) + "\n")

        # Guardar en memoria para devolución en resultado
        self._entries.append(mensaje_redactado)

    def error(self, mensaje: str, metadata: Optional[Dict[str, Any]] = None):
        """Registra un mensaje de error"""
        self.log(mensaje, nivel="ERROR", metadata=metadata)

    def warning(self, mensaje: str, metadata: Optional[Dict[str, Any]] = None):
        """Registra un mensaje de advertencia"""
        self.log(mensaje, nivel="WARNING", metadata=metadata)

    def get_log_entries(self) -> list[str]:
        """
        Retorna todas las entradas logeadas.

        Returns:
            Lista de mensajes redactados
        """
        return self._entries.copy()
