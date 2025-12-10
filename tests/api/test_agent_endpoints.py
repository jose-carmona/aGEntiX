# tests/api/test_agent_endpoints.py

"""
Tests para endpoints de ejecución de agentes.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from api.main import app

client = TestClient(app)


def test_execute_agent_without_token_returns_401():
    """Test: Request sin token retorna 401"""
    response = client.post("/api/v1/agent/execute", json={
        "expediente_id": "EXP-2024-001",
        "tarea_id": "TAREA-001",
        "agent_config": {
            "nombre": "ValidadorDocumental",
            "system_prompt": "Test",
            "modelo": "claude-3-5-sonnet",
            "prompt_tarea": "Test task",
            "herramientas": ["consultar_expediente"]
        },
        "webhook_url": "http://example.com/callback",
        "timeout_seconds": 300
    })

    assert response.status_code == 401
    assert "JWT" in response.json()["detail"]


def test_execute_agent_with_invalid_data_returns_422():
    """Test: Request con datos inválidos retorna 422"""
    response = client.post(
        "/api/v1/agent/execute",
        json={
            "expediente_id": "EXP-2024-001",
            # Falta tarea_id y otros campos requeridos
        },
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 422


@patch('api.routers.agent.create_default_executor')
def test_execute_agent_with_valid_token_returns_202(mock_executor):
    """Test: Request válido retorna 202 Accepted"""
    # Mock del executor para evitar ejecución real
    from backoffice.models import AgentExecutionResult
    mock_instance = Mock()
    mock_instance.execute = AsyncMock(return_value=AgentExecutionResult(
        success=True,
        agent_run_id="RUN-TEST",
        resultado={"message": "Test completed"},
        log_auditoria=[],
        herramientas_usadas=[]
    ))
    mock_executor.return_value = mock_instance

    response = client.post(
        "/api/v1/agent/execute",
        json={
            "expediente_id": "EXP-2024-001",
            "tarea_id": "TAREA-001",
            "agent_config": {
                "nombre": "ValidadorDocumental",
                "system_prompt": "Test",
                "modelo": "claude-3-5-sonnet",
                "prompt_tarea": "Test task",
                "herramientas": ["consultar_expediente"]
            },
            "webhook_url": "http://example.com/callback",
            "timeout_seconds": 300
        },
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert "agent_run_id" in data
    assert data["agent_run_id"].startswith("RUN-")
    assert data["webhook_url"] == "http://example.com/callback"


def test_get_agent_status_not_found_returns_404():
    """Test: Consultar status de run_id inexistente retorna 404"""
    response = client.get("/api/v1/agent/status/RUN-INEXISTENTE")

    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"]


@patch('api.routers.agent.create_default_executor')
def test_execute_then_get_status_returns_valid_status(mock_executor):
    """Test: Después de execute, status es válido (pending/running/completed)"""
    # Mock del executor con execute que devuelve AgentExecutionResult
    from backoffice.models import AgentExecutionResult
    mock_instance = Mock()
    mock_instance.execute = AsyncMock(return_value=AgentExecutionResult(
        success=True,
        agent_run_id="RUN-TEST",
        resultado={"message": "Test completed"},
        log_auditoria=[],
        herramientas_usadas=[]
    ))
    mock_executor.return_value = mock_instance

    # Ejecutar agente
    exec_response = client.post(
        "/api/v1/agent/execute",
        json={
            "expediente_id": "EXP-2024-001",
            "tarea_id": "TAREA-001",
            "agent_config": {
                "nombre": "ValidadorDocumental",
                "system_prompt": "Test",
                "modelo": "claude-3-5-sonnet",
                "prompt_tarea": "Test task",
                "herramientas": ["consultar_expediente"]
            },
            "webhook_url": "http://example.com/callback",
            "timeout_seconds": 300
        },
        headers={"Authorization": "Bearer test-token"}
    )

    assert exec_response.status_code == 202
    agent_run_id = exec_response.json()["agent_run_id"]

    # Consultar status
    status_response = client.get(f"/api/v1/agent/status/{agent_run_id}")

    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["agent_run_id"] == agent_run_id
    # Con mock puede completarse instantáneamente, aceptar cualquier estado válido
    assert status_data["status"] in ["pending", "running", "completed"]
    assert status_data["expediente_id"] == "EXP-2024-001"
    assert status_data["tarea_id"] == "TAREA-001"


def test_execute_with_timeout_out_of_range_returns_422():
    """Test: Timeout fuera de rango (10-600) retorna 422"""
    # Timeout demasiado corto
    response = client.post(
        "/api/v1/agent/execute",
        json={
            "expediente_id": "EXP-2024-001",
            "tarea_id": "TAREA-001",
            "agent_config": {
                "nombre": "ValidadorDocumental",
                "system_prompt": "Test",
                "modelo": "claude-3-5-sonnet",
                "prompt_tarea": "Test task",
                "herramientas": ["consultar_expediente"]
            },
            "webhook_url": "http://example.com/callback",
            "timeout_seconds": 5  # Menos de 10
        },
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 422

    # Timeout demasiado largo
    response = client.post(
        "/api/v1/agent/execute",
        json={
            "expediente_id": "EXP-2024-001",
            "tarea_id": "TAREA-001",
            "agent_config": {
                "nombre": "ValidadorDocumental",
                "system_prompt": "Test",
                "modelo": "claude-3-5-sonnet",
                "prompt_tarea": "Test task",
                "herramientas": ["consultar_expediente"]
            },
            "webhook_url": "http://example.com/callback",
            "timeout_seconds": 700  # Más de 600
        },
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 422
