# tests/api/test_agent_endpoints.py

"""
Tests para endpoints de ejecución de agentes.

Incluye tests para:
- POST /api/v1/agent/execute (request simplificado)
- GET /api/v1/agent/status/{agent_run_id}
- GET /api/v1/agent/agents
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from api.main import app
from backoffice.config import reset_agent_loader

client = TestClient(app)


# =============================================================================
# Tests para GET /api/v1/agent/agents
# =============================================================================

class TestListAgents:
    """Tests para el endpoint de listado de agentes"""

    def test_list_agents_returns_200(self):
        """GET /agents retorna 200 con lista de agentes"""
        response = client.get("/api/v1/agent/agents")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)

    def test_list_agents_contains_expected_agents(self):
        """GET /agents contiene los agentes configurados"""
        response = client.get("/api/v1/agent/agents")

        assert response.status_code == 200
        data = response.json()
        agent_names = [a["name"] for a in data["agents"]]

        assert "ValidadorDocumental" in agent_names
        assert "AnalizadorSubvencion" in agent_names
        assert "GeneradorInforme" in agent_names

    def test_list_agents_includes_description(self):
        """GET /agents incluye descripción de cada agente"""
        response = client.get("/api/v1/agent/agents")

        assert response.status_code == 200
        data = response.json()

        for agent in data["agents"]:
            assert "name" in agent
            assert "description" in agent
            assert len(agent["description"]) > 0

    def test_list_agents_includes_permissions(self):
        """GET /agents incluye permisos requeridos"""
        response = client.get("/api/v1/agent/agents")

        assert response.status_code == 200
        data = response.json()

        for agent in data["agents"]:
            assert "required_permissions" in agent
            assert isinstance(agent["required_permissions"], list)


# =============================================================================
# Tests para POST /api/v1/agent/execute (Request Simplificado)
# =============================================================================

class TestExecuteAgentSimplified:
    """Tests para el endpoint de ejecución con request simplificado"""

    def test_execute_without_token_returns_401(self):
        """Request sin token retorna 401"""
        response = client.post("/api/v1/agent/execute", json={
            "agent": "ValidadorDocumental",
            "prompt": "Valida los documentos del expediente",
            "context": {
                "expediente_id": "EXP-2024-001",
                "tarea_id": "TAREA-001"
            }
        })

        assert response.status_code == 401
        assert "JWT" in response.json()["detail"]

    def test_execute_with_missing_agent_field_returns_422(self):
        """Request sin campo 'agent' retorna 422"""
        response = client.post(
            "/api/v1/agent/execute",
            json={
                "prompt": "Valida los documentos",
                "context": {
                    "expediente_id": "EXP-2024-001",
                    "tarea_id": "TAREA-001"
                }
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422

    def test_execute_with_missing_prompt_returns_422(self):
        """Request sin campo 'prompt' retorna 422"""
        response = client.post(
            "/api/v1/agent/execute",
            json={
                "agent": "ValidadorDocumental",
                "context": {
                    "expediente_id": "EXP-2024-001",
                    "tarea_id": "TAREA-001"
                }
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422

    def test_execute_with_missing_context_returns_422(self):
        """Request sin campo 'context' retorna 422"""
        response = client.post(
            "/api/v1/agent/execute",
            json={
                "agent": "ValidadorDocumental",
                "prompt": "Valida los documentos"
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422

    def test_execute_with_nonexistent_agent_returns_404(self):
        """Request con agente inexistente retorna 404"""
        response = client.post(
            "/api/v1/agent/execute",
            json={
                "agent": "AgenteQueNoExiste",
                "prompt": "Valida los documentos",
                "context": {
                    "expediente_id": "EXP-2024-001",
                    "tarea_id": "TAREA-001"
                }
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"]
        assert "Agentes disponibles" in response.json()["detail"]

    @patch('api.routers.agent.create_default_executor')
    def test_execute_with_valid_request_returns_202(self, mock_executor):
        """Request válido retorna 202 Accepted"""
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
                "agent": "ValidadorDocumental",
                "prompt": "Valida los documentos del expediente y verifica el NIF",
                "context": {
                    "expediente_id": "EXP-2024-001",
                    "tarea_id": "TAREA-001"
                },
                "callback_url": "https://example.com/callback"
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        assert "agent_run_id" in data
        assert data["agent_run_id"].startswith("RUN-")
        assert data["callback_url"] == "https://example.com/callback"

    @patch('api.routers.agent.create_default_executor')
    def test_execute_without_callback_url_returns_202(self, mock_executor):
        """Request sin callback_url retorna 202 (callback_url es opcional)"""
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
                "agent": "ValidadorDocumental",
                "prompt": "Valida los documentos del expediente",
                "context": {
                    "expediente_id": "EXP-2024-001",
                    "tarea_id": "TAREA-001"
                }
                # Sin callback_url
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        assert data["callback_url"] is None


# =============================================================================
# Tests para GET /api/v1/agent/status/{agent_run_id}
# =============================================================================

class TestGetAgentStatus:
    """Tests para el endpoint de consulta de estado"""

    def test_status_not_found_returns_404(self):
        """Consultar status de run_id inexistente retorna 404"""
        response = client.get("/api/v1/agent/status/RUN-INEXISTENTE")

        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"]

    @patch('api.routers.agent.create_default_executor')
    def test_execute_then_get_status_returns_valid_status(self, mock_executor):
        """Después de execute, status es válido"""
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
                "agent": "ValidadorDocumental",
                "prompt": "Valida los documentos",
                "context": {
                    "expediente_id": "EXP-2024-001",
                    "tarea_id": "TAREA-001"
                }
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
        assert status_data["status"] in ["pending", "running", "completed"]
        assert status_data["expediente_id"] == "EXP-2024-001"
        assert status_data["tarea_id"] == "TAREA-001"


# =============================================================================
# Tests de Validación de callback_url (SSRF Prevention)
# =============================================================================

class TestCallbackUrlValidation:
    """Tests para validación de callback_url y prevención de SSRF"""

    def test_callback_url_localhost_rejected(self):
        """callback_url con localhost es rechazado"""
        response = client.post(
            "/api/v1/agent/execute",
            json={
                "agent": "ValidadorDocumental",
                "prompt": "Test",
                "context": {
                    "expediente_id": "EXP-2024-001",
                    "tarea_id": "TAREA-001"
                },
                "callback_url": "http://localhost:8080/callback"
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422
        # Verificar que el error menciona SSRF o localhost
        detail = str(response.json())
        assert "localhost" in detail.lower() or "ssrf" in detail.lower()

    def test_callback_url_private_ip_rejected(self):
        """callback_url con IP privada es rechazado"""
        response = client.post(
            "/api/v1/agent/execute",
            json={
                "agent": "ValidadorDocumental",
                "prompt": "Test",
                "context": {
                    "expediente_id": "EXP-2024-001",
                    "tarea_id": "TAREA-001"
                },
                "callback_url": "http://192.168.1.1/callback"
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422

    def test_callback_url_loopback_rejected(self):
        """callback_url con 127.0.0.1 es rechazado"""
        response = client.post(
            "/api/v1/agent/execute",
            json={
                "agent": "ValidadorDocumental",
                "prompt": "Test",
                "context": {
                    "expediente_id": "EXP-2024-001",
                    "tarea_id": "TAREA-001"
                },
                "callback_url": "http://127.0.0.1:8080/callback"
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422


# =============================================================================
# Tests de Integración Agent Config
# =============================================================================

class TestAgentConfigIntegration:
    """Tests de integración entre endpoints y configuración de agentes"""

    @patch('api.routers.agent.create_default_executor')
    def test_execute_uses_agent_config_from_yaml(self, mock_executor):
        """Execute usa la configuración del agente desde YAML"""
        from backoffice.models import AgentExecutionResult
        mock_instance = Mock()

        # Capturar los argumentos pasados a execute
        captured_config = {}

        async def capture_execute(token, expediente_id, tarea_id, agent_config):
            captured_config['nombre'] = agent_config.nombre
            captured_config['system_prompt'] = agent_config.system_prompt
            captured_config['modelo'] = agent_config.modelo
            captured_config['prompt_tarea'] = agent_config.prompt_tarea
            captured_config['herramientas'] = agent_config.herramientas
            return AgentExecutionResult(
                success=True,
                agent_run_id="RUN-TEST",
                resultado={"message": "Test completed"},
                log_auditoria=[],
                herramientas_usadas=[]
            )

        mock_instance.execute = capture_execute
        mock_executor.return_value = mock_instance

        response = client.post(
            "/api/v1/agent/execute",
            json={
                "agent": "ValidadorDocumental",
                "prompt": "Prompt específico del usuario",
                "context": {
                    "expediente_id": "EXP-2024-001",
                    "tarea_id": "TAREA-001"
                }
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 202

        # Verificar que se usó la configuración del YAML
        assert captured_config['nombre'] == "ValidadorDocumental"
        assert "validador" in captured_config['system_prompt'].lower() or \
               "documentación" in captured_config['system_prompt'].lower()
        assert captured_config['modelo'] == "claude-3-5-sonnet-20241022"
        assert captured_config['prompt_tarea'] == "Prompt específico del usuario"
        assert "consultar_expediente" in captured_config['herramientas']
