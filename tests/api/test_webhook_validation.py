# tests/api/test_webhook_validation.py

"""
Tests para validación de callback_url (prevención SSRF).

Actualizado para usar el request simplificado.
"""

import pytest
from pydantic import ValidationError
from api.models import ExecuteAgentRequest, AgentContext


def create_request_with_callback(callback_url: str) -> ExecuteAgentRequest:
    """Helper para crear request con callback_url específico"""
    return ExecuteAgentRequest(
        agent="ValidadorDocumental",
        prompt="Test prompt",
        context=AgentContext(
            expediente_id="EXP-001",
            tarea_id="TAREA-001"
        ),
        callback_url=callback_url
    )


def test_callback_url_accepts_valid_https():
    """Test: callback_url acepta HTTPS válido"""
    req = create_request_with_callback("https://bpmn.example.com/callback")
    assert "bpmn.example.com" in str(req.callback_url)
    assert str(req.callback_url).startswith("https://")


def test_callback_url_rejects_http_in_production():
    """Test: callback_url rechaza HTTP en producción (LOG_LEVEL=INFO)"""
    with pytest.raises(ValidationError) as exc_info:
        create_request_with_callback("http://bpmn.example.com/callback")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert "https" in str(errors[0]["ctx"]["error"]).lower()


def test_callback_url_rejects_localhost():
    """Test: callback_url rechaza localhost"""
    with pytest.raises(ValidationError) as exc_info:
        create_request_with_callback("http://localhost:8080/callback")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert "localhost" in str(errors[0]["ctx"]["error"]).lower()
    assert "ssrf" in str(errors[0]["ctx"]["error"]).lower()


def test_callback_url_rejects_127_0_0_1():
    """Test: callback_url rechaza 127.0.0.1"""
    with pytest.raises(ValidationError) as exc_info:
        create_request_with_callback("http://127.0.0.1/callback")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert "localhost" in str(errors[0]["ctx"]["error"]).lower()


def test_callback_url_rejects_ipv6_loopback():
    """Test: callback_url rechaza ::1 (IPv6 loopback)"""
    with pytest.raises(ValidationError) as exc_info:
        create_request_with_callback("https://[::1]/callback")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    error_msg = str(errors[0]["ctx"]["error"]).lower()
    assert "localhost" in error_msg or "loopback" in error_msg


def test_callback_url_rejects_private_ip_192_168():
    """Test: callback_url rechaza IPs privadas 192.168.x.x"""
    with pytest.raises(ValidationError) as exc_info:
        create_request_with_callback("http://192.168.1.100/callback")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    error_msg = str(errors[0]["ctx"]["error"]).lower()
    assert "privada" in error_msg or "private" in error_msg
    assert "ssrf" in error_msg


def test_callback_url_rejects_private_ip_10_x():
    """Test: callback_url rechaza IPs privadas 10.x.x.x"""
    with pytest.raises(ValidationError) as exc_info:
        create_request_with_callback("http://10.0.0.1/callback")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    error_msg = str(errors[0]["ctx"]["error"]).lower()
    assert "privada" in error_msg or "private" in error_msg


def test_callback_url_rejects_private_ip_172_16():
    """Test: callback_url rechaza IPs privadas 172.16-31.x.x"""
    with pytest.raises(ValidationError) as exc_info:
        create_request_with_callback("http://172.16.0.1/callback")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    error_msg = str(errors[0]["ctx"]["error"]).lower()
    assert "privada" in error_msg or "private" in error_msg


def test_callback_url_accepts_public_domain():
    """Test: callback_url acepta dominios públicos válidos"""
    req = create_request_with_callback("https://api.example.com/webhooks/callback")
    assert "example.com" in str(req.callback_url)


def test_callback_url_accepts_subdomain():
    """Test: callback_url acepta subdominios"""
    req = create_request_with_callback("https://bpmn.subdomain.example.com/callback")
    assert "subdomain.example.com" in str(req.callback_url)


def test_callback_url_rejects_invalid_url():
    """Test: callback_url rechaza URLs inválidas"""
    with pytest.raises(ValidationError):
        create_request_with_callback("not-a-valid-url")


def test_callback_url_with_non_standard_port():
    """Test: callback_url acepta puertos no estándar (genera warning en logs)"""
    req = create_request_with_callback("https://example.com:9999/callback")
    assert ":9999" in str(req.callback_url)


def test_callback_url_is_optional():
    """Test: callback_url es opcional"""
    req = ExecuteAgentRequest(
        agent="ValidadorDocumental",
        prompt="Test prompt",
        context=AgentContext(
            expediente_id="EXP-001",
            tarea_id="TAREA-001"
        )
        # Sin callback_url
    )
    assert req.callback_url is None
