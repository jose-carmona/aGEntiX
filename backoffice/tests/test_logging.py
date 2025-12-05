# backoffice/tests/test_logging.py

"""
Tests obligatorios de redacción de PII (GDPR/LOPD/ENS).

CRÍTICO: Estos tests verifican que datos personales NO aparecen en logs.
"""

import pytest
from pathlib import Path
from backoffice.logging.pii_redactor import PIIRedactor
from backoffice.logging.audit_logger import AuditLogger


def test_pii_redactor_dni():
    """Verifica que DNIs se redactan automáticamente"""
    mensaje = "Solicitante con DNI 12345678A"
    redacted = PIIRedactor.redact(mensaje)
    assert "12345678A" not in redacted
    assert "[DNI-REDACTED]" in redacted


def test_pii_redactor_email():
    """Verifica que emails se redactan automáticamente"""
    mensaje = "Contacto: juan.perez@example.com"
    redacted = PIIRedactor.redact(mensaje)
    assert "juan.perez@example.com" not in redacted
    assert "[EMAIL-REDACTED]" in redacted


def test_pii_redactor_iban():
    """Verifica que IBANs se redactan automáticamente"""
    mensaje = "Cuenta bancaria: ES1234567890123456789012"
    redacted = PIIRedactor.redact(mensaje)
    assert "ES1234567890123456789012" not in redacted
    assert "[IBAN-REDACTED]" in redacted


def test_pii_redactor_telefono():
    """Verifica que teléfonos se redactan automáticamente"""
    mensaje = "Teléfono de contacto: 612345678"
    redacted = PIIRedactor.redact(mensaje)
    assert "612345678" not in redacted
    assert "[TELEFONO-REDACTED]" in redacted


def test_pii_redactor_nie():
    """Verifica que NIEs se redactan automáticamente"""
    mensaje = "Extranjero con NIE X1234567Z"
    redacted = PIIRedactor.redact(mensaje)
    assert "X1234567Z" not in redacted
    assert "[NIE-REDACTED]" in redacted


def test_audit_logger_escribe_logs_redactados(tmp_path):
    """Verifica que el logger escribe logs con PII redactada automáticamente"""
    logger = AuditLogger("EXP-001", "RUN-001", tmp_path)
    logger.log("Usuario con DNI 12345678Z solicita expediente")

    # Leer el archivo de log
    log_file = tmp_path / "EXP-001" / "RUN-001.log"
    content = log_file.read_text()

    # Verificar que NO contiene el DNI original
    assert "12345678Z" not in content
    # Verificar que SÍ contiene la redacción
    assert "[DNI-REDACTED]" in content


def test_audit_logger_redacta_metadata(tmp_path):
    """Verifica que el logger redacta también la metadata"""
    logger = AuditLogger("EXP-001", "RUN-001", tmp_path)
    logger.log(
        "Consultando expediente",
        metadata={"solicitante_email": "juan@example.com", "telefono": "612345678"}
    )

    log_file = tmp_path / "EXP-001" / "RUN-001.log"
    content = log_file.read_text()

    # No debe contener datos originales
    assert "juan@example.com" not in content
    assert "612345678" not in content
    # Debe contener redacciones
    assert "[EMAIL-REDACTED]" in content
    assert "[TELEFONO-REDACTED]" in content


def test_audit_logger_multiples_pii_en_mismo_mensaje(tmp_path):
    """Verifica que múltiples PII en el mismo mensaje se redactan"""
    logger = AuditLogger("EXP-001", "RUN-001", tmp_path)
    logger.log(
        "Solicitante Juan Pérez, DNI 12345678A, email juan@example.com, "
        "teléfono 612345678, IBAN ES1234567890123456789012"
    )

    log_file = tmp_path / "EXP-001" / "RUN-001.log"
    content = log_file.read_text()

    # No debe contener ningún dato original
    assert "12345678A" not in content
    assert "juan@example.com" not in content
    assert "612345678" not in content
    assert "ES1234567890123456789012" not in content

    # Debe contener todas las redacciones
    assert "[DNI-REDACTED]" in content
    assert "[EMAIL-REDACTED]" in content
    assert "[TELEFONO-REDACTED]" in content
    assert "[IBAN-REDACTED]" in content


def test_audit_logger_crea_directorio_si_no_existe(tmp_path):
    """Verifica que el logger crea el directorio si no existe"""
    logger = AuditLogger("EXP-NEW", "RUN-NEW", tmp_path)
    logger.log("Test mensaje")

    log_file = tmp_path / "EXP-NEW" / "RUN-NEW.log"
    assert log_file.exists()
    assert log_file.parent.exists()


def test_audit_logger_get_log_entries_retorna_mensajes_redactados(tmp_path):
    """Verifica que get_log_entries retorna mensajes ya redactados"""
    logger = AuditLogger("EXP-001", "RUN-001", tmp_path)
    logger.log("DNI: 12345678A")

    entries = logger.get_log_entries()
    assert len(entries) == 1
    assert "12345678A" not in entries[0]
    assert "[DNI-REDACTED]" in entries[0]
