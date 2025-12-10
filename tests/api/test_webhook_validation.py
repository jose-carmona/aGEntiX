# tests/api/test_webhook_validation.py

"""
Tests para validación de webhook_url (prevención SSRF).
"""

import pytest
from pydantic import ValidationError
from api.models import ExecuteAgentRequest, AgentConfigRequest


def test_webhook_url_accepts_valid_https():
    """Test: webhook_url acepta HTTPS válido"""
    req = ExecuteAgentRequest(
        expediente_id="EXP-001",
        tarea_id="TAREA-001",
        agent_config=AgentConfigRequest(
            nombre="TestAgent",
            system_prompt="Test",
            modelo="test-model",
            prompt_tarea="Test task",
            herramientas=["tool1"]
        ),
        webhook_url="https://bpmn.example.com/callback",
        timeout_seconds=300
    )
    # HttpUrl normaliza URLs añadiendo trailing slash si es solo hostname/path
    assert "bpmn.example.com" in str(req.webhook_url)
    assert str(req.webhook_url).startswith("https://")


def test_webhook_url_rejects_http_in_production():
    """Test: webhook_url rechaza HTTP en producción (LOG_LEVEL=INFO)"""
    # LOG_LEVEL=INFO en tests (producción), HTTP debe ser rechazado
    with pytest.raises(ValidationError) as exc_info:
        ExecuteAgentRequest(
            expediente_id="EXP-001",
            tarea_id="TAREA-001",
            agent_config=AgentConfigRequest(
                nombre="TestAgent",
                system_prompt="Test",
                modelo="test-model",
                prompt_tarea="Test task",
                herramientas=["tool1"]
            ),
            webhook_url="http://bpmn.example.com/callback",
            timeout_seconds=300
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert "https" in str(errors[0]["ctx"]["error"]).lower()


def test_webhook_url_rejects_localhost():
    """Test: webhook_url rechaza localhost"""
    with pytest.raises(ValidationError) as exc_info:
        ExecuteAgentRequest(
            expediente_id="EXP-001",
            tarea_id="TAREA-001",
            agent_config=AgentConfigRequest(
                nombre="TestAgent",
                system_prompt="Test",
                modelo="test-model",
                prompt_tarea="Test task",
                herramientas=["tool1"]
            ),
            webhook_url="http://localhost:8080/callback",
            timeout_seconds=300
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert "localhost" in str(errors[0]["ctx"]["error"]).lower()
    assert "ssrf" in str(errors[0]["ctx"]["error"]).lower()


def test_webhook_url_rejects_127_0_0_1():
    """Test: webhook_url rechaza 127.0.0.1"""
    with pytest.raises(ValidationError) as exc_info:
        ExecuteAgentRequest(
            expediente_id="EXP-001",
            tarea_id="TAREA-001",
            agent_config=AgentConfigRequest(
                nombre="TestAgent",
                system_prompt="Test",
                modelo="test-model",
                prompt_tarea="Test task",
                herramientas=["tool1"]
            ),
            webhook_url="http://127.0.0.1/callback",
            timeout_seconds=300
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert "localhost" in str(errors[0]["ctx"]["error"]).lower()


def test_webhook_url_rejects_ipv6_loopback():
    """Test: webhook_url rechaza ::1 (IPv6 loopback)"""
    with pytest.raises(ValidationError) as exc_info:
        ExecuteAgentRequest(
            expediente_id="EXP-001",
            tarea_id="TAREA-001",
            agent_config=AgentConfigRequest(
                nombre="TestAgent",
                system_prompt="Test",
                modelo="test-model",
                prompt_tarea="Test task",
                herramientas=["tool1"]
            ),
            webhook_url="https://[::1]/callback",  # HTTPS para pasar validación de scheme primero
            timeout_seconds=300
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    # Puede ser error de localhost (check de string) o loopback (check de IP)
    error_msg = str(errors[0]["ctx"]["error"]).lower()
    assert "localhost" in error_msg or "loopback" in error_msg


def test_webhook_url_rejects_private_ip_192_168():
    """Test: webhook_url rechaza IPs privadas 192.168.x.x"""
    with pytest.raises(ValidationError) as exc_info:
        ExecuteAgentRequest(
            expediente_id="EXP-001",
            tarea_id="TAREA-001",
            agent_config=AgentConfigRequest(
                nombre="TestAgent",
                system_prompt="Test",
                modelo="test-model",
                prompt_tarea="Test task",
                herramientas=["tool1"]
            ),
            webhook_url="http://192.168.1.100/callback",
            timeout_seconds=300
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    error_msg = str(errors[0]["ctx"]["error"]).lower()
    assert "privada" in error_msg or "private" in error_msg
    assert "ssrf" in error_msg


def test_webhook_url_rejects_private_ip_10_x():
    """Test: webhook_url rechaza IPs privadas 10.x.x.x"""
    with pytest.raises(ValidationError) as exc_info:
        ExecuteAgentRequest(
            expediente_id="EXP-001",
            tarea_id="TAREA-001",
            agent_config=AgentConfigRequest(
                nombre="TestAgent",
                system_prompt="Test",
                modelo="test-model",
                prompt_tarea="Test task",
                herramientas=["tool1"]
            ),
            webhook_url="http://10.0.0.1/callback",
            timeout_seconds=300
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    error_msg = str(errors[0]["ctx"]["error"]).lower()
    assert "privada" in error_msg or "private" in error_msg


def test_webhook_url_rejects_private_ip_172_16():
    """Test: webhook_url rechaza IPs privadas 172.16-31.x.x"""
    with pytest.raises(ValidationError) as exc_info:
        ExecuteAgentRequest(
            expediente_id="EXP-001",
            tarea_id="TAREA-001",
            agent_config=AgentConfigRequest(
                nombre="TestAgent",
                system_prompt="Test",
                modelo="test-model",
                prompt_tarea="Test task",
                herramientas=["tool1"]
            ),
            webhook_url="http://172.16.0.1/callback",
            timeout_seconds=300
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    error_msg = str(errors[0]["ctx"]["error"]).lower()
    assert "privada" in error_msg or "private" in error_msg


def test_webhook_url_accepts_public_domain():
    """Test: webhook_url acepta dominios públicos válidos"""
    req = ExecuteAgentRequest(
        expediente_id="EXP-001",
        tarea_id="TAREA-001",
        agent_config=AgentConfigRequest(
            nombre="TestAgent",
            system_prompt="Test",
            modelo="test-model",
            prompt_tarea="Test task",
            herramientas=["tool1"]
        ),
        webhook_url="https://api.example.com/webhooks/callback",
        timeout_seconds=300
    )
    assert "example.com" in str(req.webhook_url)


def test_webhook_url_accepts_subdomain():
    """Test: webhook_url acepta subdominios"""
    req = ExecuteAgentRequest(
        expediente_id="EXP-001",
        tarea_id="TAREA-001",
        agent_config=AgentConfigRequest(
            nombre="TestAgent",
            system_prompt="Test",
            modelo="test-model",
            prompt_tarea="Test task",
            herramientas=["tool1"]
        ),
        webhook_url="https://bpmn.subdomain.example.com/callback",
        timeout_seconds=300
    )
    assert "subdomain.example.com" in str(req.webhook_url)


def test_webhook_url_rejects_invalid_url():
    """Test: webhook_url rechaza URLs inválidas"""
    with pytest.raises(ValidationError):
        ExecuteAgentRequest(
            expediente_id="EXP-001",
            tarea_id="TAREA-001",
            agent_config=AgentConfigRequest(
                nombre="TestAgent",
                system_prompt="Test",
                modelo="test-model",
                prompt_tarea="Test task",
                herramientas=["tool1"]
            ),
            webhook_url="not-a-valid-url",
            timeout_seconds=300
        )


def test_webhook_url_with_non_standard_port():
    """Test: webhook_url acepta puertos no estándar (genera warning en logs)"""
    # Esto debería funcionar pero generar warning en logs
    req = ExecuteAgentRequest(
        expediente_id="EXP-001",
        tarea_id="TAREA-001",
        agent_config=AgentConfigRequest(
            nombre="TestAgent",
            system_prompt="Test",
            modelo="test-model",
            prompt_tarea="Test task",
            herramientas=["tool1"]
        ),
        webhook_url="https://example.com:9999/callback",
        timeout_seconds=300
    )
    assert ":9999" in str(req.webhook_url)
