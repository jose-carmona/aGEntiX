# tests/test_backoffice/test_mcp_tool_wrapper.py

"""
Tests para MCPTool wrapper - manejo de errores semánticos.

Verifica que los errores MCP se propagan con códigos semánticos
para que el agente pueda tomar decisiones de retry diferenciadas.
"""

import pytest
import json
from unittest.mock import Mock, MagicMock

from backoffice.mcp.exceptions import (
    MCPConnectionError,
    MCPAuthError,
    MCPToolError,
    MCPError
)
from backoffice.agents.mcp_tool_wrapper import MCPTool, MCPToolFactory, CREWAI_AVAILABLE


# Skip tests si CrewAI no está disponible
pytestmark = pytest.mark.skipif(
    not CREWAI_AVAILABLE,
    reason="CrewAI no está instalado"
)


@pytest.fixture
def mock_registry():
    """Registry mock para tests"""
    registry = Mock()
    registry.call_tool_sync = Mock()
    return registry


@pytest.fixture
def mock_logger():
    """Logger mock para tests"""
    logger = Mock()
    logger.log = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    return logger


@pytest.fixture
def mcp_tool(mock_registry, mock_logger):
    """MCPTool configurada para tests"""
    from backoffice.agents.mcp_tool_wrapper import ConsultarExpedienteArgs

    return MCPTool(
        name="consultar_expediente",
        description="Test tool",
        args_schema=ConsultarExpedienteArgs,
        mcp_registry=mock_registry,
        logger=mock_logger
    )


class TestMCPToolErrorHandling:
    """Tests para manejo de errores semánticos"""

    def test_connection_error_preserves_code(self, mcp_tool, mock_registry):
        """Test: MCPConnectionError preserva código y es retriable"""
        mock_registry.call_tool_sync.side_effect = MCPConnectionError(
            codigo="MCP_TIMEOUT",
            mensaje="Timeout en consultar_expediente",
            detalle="Request timeout after 30s"
        )

        result = mcp_tool._run(expediente_id="EXP-001")
        parsed = json.loads(result)

        assert parsed["error"] == "MCP_TIMEOUT"
        assert "Timeout" in parsed["message"]
        assert parsed["type"] == "connection"
        assert parsed["retriable"] is True

    def test_connection_refused_error(self, mcp_tool, mock_registry):
        """Test: Error de conexión rechazada"""
        mock_registry.call_tool_sync.side_effect = MCPConnectionError(
            codigo="MCP_CONNECTION_ERROR",
            mensaje="No se puede conectar al servidor MCP",
            detalle="Connection refused"
        )

        result = mcp_tool._run(expediente_id="EXP-001")
        parsed = json.loads(result)

        assert parsed["error"] == "MCP_CONNECTION_ERROR"
        assert parsed["type"] == "connection"
        assert parsed["retriable"] is True

    def test_auth_invalid_token_error(self, mcp_tool, mock_registry):
        """Test: MCPAuthError con token inválido no es retriable"""
        mock_registry.call_tool_sync.side_effect = MCPAuthError(
            codigo="AUTH_INVALID_TOKEN",
            mensaje="Token JWT inválido o expirado",
            detalle="Invalid signature"
        )

        result = mcp_tool._run(expediente_id="EXP-001")
        parsed = json.loads(result)

        assert parsed["error"] == "AUTH_INVALID_TOKEN"
        assert parsed["type"] == "auth"
        assert parsed["retriable"] is False

    def test_auth_permission_denied_error(self, mcp_tool, mock_registry):
        """Test: MCPAuthError por permisos no es retriable"""
        mock_registry.call_tool_sync.side_effect = MCPAuthError(
            codigo="AUTH_PERMISSION_DENIED",
            mensaje="Permisos insuficientes para ejecutar tool",
            detalle="Missing permission: gestion"
        )

        result = mcp_tool._run(expediente_id="EXP-001")
        parsed = json.loads(result)

        assert parsed["error"] == "AUTH_PERMISSION_DENIED"
        assert parsed["type"] == "auth"
        assert parsed["retriable"] is False

    def test_tool_not_found_error(self, mcp_tool, mock_registry):
        """Test: MCPToolError por tool no encontrada"""
        mock_registry.call_tool_sync.side_effect = MCPToolError(
            codigo="MCP_TOOL_NOT_FOUND",
            mensaje="Tool 'unknown_tool' no encontrada",
            detalle="Available tools: [consultar_expediente]"
        )

        result = mcp_tool._run(expediente_id="EXP-001")
        parsed = json.loads(result)

        assert parsed["error"] == "MCP_TOOL_NOT_FOUND"
        assert parsed["type"] == "tool"
        assert parsed["retriable"] is False

    def test_tool_conflict_is_retriable(self, mcp_tool, mock_registry):
        """Test: MCP_CONFLICT es retriable (modificación concurrente)"""
        mock_registry.call_tool_sync.side_effect = MCPToolError(
            codigo="MCP_CONFLICT",
            mensaje="Conflicto de modificación concurrente",
            detalle="Version mismatch"
        )

        result = mcp_tool._run(expediente_id="EXP-001")
        parsed = json.loads(result)

        assert parsed["error"] == "MCP_CONFLICT"
        assert parsed["type"] == "tool"
        assert parsed["retriable"] is True  # Conflictos son retriables

    def test_tool_business_error(self, mcp_tool, mock_registry):
        """Test: Error de negocio de la tool"""
        mock_registry.call_tool_sync.side_effect = MCPToolError(
            codigo="MCP_TOOL_ERROR",
            mensaje="Expediente no encontrado: EXP-999",
            detalle="-32000"
        )

        result = mcp_tool._run(expediente_id="EXP-999")
        parsed = json.loads(result)

        assert parsed["error"] == "MCP_TOOL_ERROR"
        assert "Expediente no encontrado" in parsed["message"]
        assert parsed["type"] == "tool"
        assert parsed["retriable"] is False

    def test_unexpected_exception_handled(self, mcp_tool, mock_registry):
        """Test: Excepciones inesperadas se manejan gracefully"""
        mock_registry.call_tool_sync.side_effect = RuntimeError("Unexpected bug")

        result = mcp_tool._run(expediente_id="EXP-001")
        parsed = json.loads(result)

        assert parsed["error"] == "INTERNAL_ERROR"
        assert "Unexpected bug" in parsed["message"]
        assert parsed["type"] == "internal"
        assert parsed["retriable"] is False

    def test_successful_execution(self, mcp_tool, mock_registry):
        """Test: Ejecución exitosa retorna contenido"""
        mock_registry.call_tool_sync.return_value = {
            "content": [{"type": "text", "text": '{"id": "EXP-001", "estado": "activo"}'}]
        }

        result = mcp_tool._run(expediente_id="EXP-001")
        parsed = json.loads(result)

        assert parsed["id"] == "EXP-001"
        assert parsed["estado"] == "activo"

    def test_logger_called_on_error(self, mcp_tool, mock_registry, mock_logger):
        """Test: Logger se llama con información del error"""
        mock_registry.call_tool_sync.side_effect = MCPConnectionError(
            codigo="MCP_TIMEOUT",
            mensaje="Timeout en tool",
            detalle="30s"
        )

        mcp_tool._run(expediente_id="EXP-001")

        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args[0][0]
        assert "MCP_TIMEOUT" in error_call
        assert "Timeout" in error_call


class TestMCPToolFactory:
    """Tests para MCPToolFactory"""

    def test_create_tools_with_known_tool(self, mock_registry, mock_logger):
        """Test: Factory crea tools con descripción conocida"""
        tools = MCPToolFactory.create_tools(
            tool_names=["consultar_expediente"],
            mcp_registry=mock_registry,
            logger=mock_logger
        )

        assert len(tools) == 1
        assert tools[0].name == "consultar_expediente"
        assert "datos completos" in tools[0].description

    def test_create_tools_with_unknown_tool(self, mock_registry, mock_logger):
        """Test: Factory crea tools desconocidas con descripción genérica"""
        tools = MCPToolFactory.create_tools(
            tool_names=["tool_desconocida"],
            mcp_registry=mock_registry,
            logger=mock_logger
        )

        assert len(tools) == 1
        assert tools[0].name == "tool_desconocida"
        assert "Herramienta MCP" in tools[0].description

    def test_create_multiple_tools(self, mock_registry, mock_logger):
        """Test: Factory crea múltiples tools"""
        tools = MCPToolFactory.create_tools(
            tool_names=["consultar_expediente", "actualizar_datos"],
            mcp_registry=mock_registry,
            logger=mock_logger
        )

        assert len(tools) == 2
        names = [t.name for t in tools]
        assert "consultar_expediente" in names
        assert "actualizar_datos" in names

    def test_get_tool_description(self):
        """Test: get_tool_description retorna descripción correcta"""
        desc = MCPToolFactory.get_tool_description("consultar_expediente")
        assert "datos completos" in desc

        desc_unknown = MCPToolFactory.get_tool_description("unknown")
        assert "Herramienta MCP" in desc_unknown
