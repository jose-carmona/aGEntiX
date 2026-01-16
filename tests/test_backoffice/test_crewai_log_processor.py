# tests/test_backoffice/test_crewai_log_processor.py

"""
Tests para el procesador de logs de CrewAI.
"""

import json
import pytest

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

    def test_handles_plain_text_lines(self, tmp_path, audit_logger):
        """Debe manejar líneas de texto plano (no JSON)."""
        log_file = tmp_path / "test_logs.json"
        content = "Plain text line 1\nPlain text line 2\n"
        log_file.write_text(content)

        count = process_crewai_logs(log_file, audit_logger, delete_after=False)

        assert count == 2
        entries = audit_logger.get_log_entries()
        assert any("Plain text line 1" in e for e in entries)

    def test_handles_empty_file(self, tmp_path, audit_logger):
        """Debe manejar archivo vacío sin error."""
        log_file = tmp_path / "test_logs.json"
        log_file.write_text("")

        count = process_crewai_logs(log_file, audit_logger, delete_after=False)

        assert count == 0
