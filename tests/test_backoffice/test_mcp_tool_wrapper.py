# tests/test_backoffice/test_mcp_tool_wrapper.py

"""
Tests para MCPTool wrapper - manejo de errores FAIL-FAST.

Verifica que los errores MCP se propagan como excepciones para
detener inmediatamente la ejecución del agente.
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
    # Para MCPToolFactory - retornar dict vacío para usar fallback schemas
    registry.get_tools_with_schemas = Mock(return_value={})
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
    """Tests para manejo de errores FAIL-FAST"""

    def test_connection_error_raises_exception(self, mcp_tool, mock_registry):
        """Test: MCPConnectionError lanza RuntimeError (fail-fast)"""
        mock_registry.call_tool_sync.side_effect = MCPConnectionError(
            codigo="MCP_TIMEOUT",
            mensaje="Timeout en consultar_expediente",
            detalle="Request timeout after 30s"
        )

        with pytest.raises(RuntimeError) as exc_info:
            mcp_tool._run(expediente_id="EXP-001")

        assert "MCP Connection Error" in str(exc_info.value)
        assert "MCP_TIMEOUT" in str(exc_info.value)

    def test_connection_refused_raises_exception(self, mcp_tool, mock_registry):
        """Test: Error de conexión rechazada lanza RuntimeError"""
        mock_registry.call_tool_sync.side_effect = MCPConnectionError(
            codigo="MCP_CONNECTION_ERROR",
            mensaje="No se puede conectar al servidor MCP",
            detalle="Connection refused"
        )

        with pytest.raises(RuntimeError) as exc_info:
            mcp_tool._run(expediente_id="EXP-001")

        assert "MCP Connection Error" in str(exc_info.value)
        assert "MCP_CONNECTION_ERROR" in str(exc_info.value)

    def test_auth_invalid_token_raises_exception(self, mcp_tool, mock_registry):
        """Test: MCPAuthError con token inválido lanza RuntimeError"""
        mock_registry.call_tool_sync.side_effect = MCPAuthError(
            codigo="AUTH_INVALID_TOKEN",
            mensaje="Token JWT inválido o expirado",
            detalle="Invalid signature"
        )

        with pytest.raises(RuntimeError) as exc_info:
            mcp_tool._run(expediente_id="EXP-001")

        assert "MCP Auth Error" in str(exc_info.value)
        assert "AUTH_INVALID_TOKEN" in str(exc_info.value)

    def test_auth_permission_denied_raises_exception(self, mcp_tool, mock_registry):
        """Test: MCPAuthError por permisos lanza RuntimeError"""
        mock_registry.call_tool_sync.side_effect = MCPAuthError(
            codigo="AUTH_PERMISSION_DENIED",
            mensaje="Permisos insuficientes para ejecutar tool",
            detalle="Missing permission: gestion"
        )

        with pytest.raises(RuntimeError) as exc_info:
            mcp_tool._run(expediente_id="EXP-001")

        assert "MCP Auth Error" in str(exc_info.value)
        assert "AUTH_PERMISSION_DENIED" in str(exc_info.value)

    def test_tool_not_found_raises_exception(self, mcp_tool, mock_registry):
        """Test: MCPToolError por tool no encontrada lanza RuntimeError"""
        mock_registry.call_tool_sync.side_effect = MCPToolError(
            codigo="MCP_TOOL_NOT_FOUND",
            mensaje="Tool 'unknown_tool' no encontrada",
            detalle="Available tools: [consultar_expediente]"
        )

        with pytest.raises(RuntimeError) as exc_info:
            mcp_tool._run(expediente_id="EXP-001")

        assert "MCP Tool Error" in str(exc_info.value)
        assert "MCP_TOOL_NOT_FOUND" in str(exc_info.value)

    def test_tool_conflict_raises_exception(self, mcp_tool, mock_registry):
        """Test: MCP_CONFLICT lanza RuntimeError (fail-fast)"""
        mock_registry.call_tool_sync.side_effect = MCPToolError(
            codigo="MCP_CONFLICT",
            mensaje="Conflicto de modificación concurrente",
            detalle="Version mismatch"
        )

        with pytest.raises(RuntimeError) as exc_info:
            mcp_tool._run(expediente_id="EXP-001")

        assert "MCP Tool Error" in str(exc_info.value)
        assert "MCP_CONFLICT" in str(exc_info.value)

    def test_tool_business_error_raises_exception(self, mcp_tool, mock_registry):
        """Test: Error de negocio de la tool lanza RuntimeError"""
        mock_registry.call_tool_sync.side_effect = MCPToolError(
            codigo="MCP_TOOL_ERROR",
            mensaje="Expediente no encontrado: EXP-999",
            detalle="-32000"
        )

        with pytest.raises(RuntimeError) as exc_info:
            mcp_tool._run(expediente_id="EXP-999")

        assert "MCP Tool Error" in str(exc_info.value)
        assert "Expediente no encontrado" in str(exc_info.value)

    def test_unexpected_exception_raises_runtime_error(self, mcp_tool, mock_registry):
        """Test: Excepciones inesperadas se propagan como RuntimeError"""
        mock_registry.call_tool_sync.side_effect = ValueError("Unexpected bug")

        with pytest.raises(RuntimeError) as exc_info:
            mcp_tool._run(expediente_id="EXP-001")

        assert "Error inesperado" in str(exc_info.value)
        assert "Unexpected bug" in str(exc_info.value)

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
        """Test: Logger se llama con información del error antes de lanzar excepción"""
        mock_registry.call_tool_sync.side_effect = MCPConnectionError(
            codigo="MCP_TIMEOUT",
            mensaje="Timeout en tool",
            detalle="30s"
        )

        with pytest.raises(RuntimeError):
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

    def test_create_tools_with_dynamic_schemas(self, mock_logger):
        """Test: Factory usa schemas dinámicos del servidor MCP"""
        # Mock registry con schemas dinámicos
        registry_with_schemas = Mock()
        registry_with_schemas.call_tool_sync = Mock()
        registry_with_schemas.get_tools_with_schemas = Mock(return_value={
            "mi_tool_dinamica": {
                "name": "mi_tool_dinamica",
                "description": "Descripción dinámica del servidor",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string", "description": "Primer param"},
                        "param2": {"type": "integer", "description": "Segundo param"}
                    },
                    "required": ["param1"]
                },
                "server_id": "test-mcp"
            }
        })

        tools = MCPToolFactory.create_tools(
            tool_names=["mi_tool_dinamica"],
            mcp_registry=registry_with_schemas,
            logger=mock_logger,
            use_dynamic_schemas=True
        )

        assert len(tools) == 1
        tool = tools[0]
        assert tool.name == "mi_tool_dinamica"
        # CrewAI añade metadatos a la descripción, verificamos que contiene nuestra descripción
        assert "Descripción dinámica del servidor" in tool.description
        # Verificar que el schema tiene los campos correctos
        assert hasattr(tool.args_schema, "model_fields")
        assert "param1" in tool.args_schema.model_fields

    def test_create_tools_fallback_on_error(self, mock_logger):
        """Test: Factory usa fallback cuando get_tools_with_schemas falla"""
        # Mock registry que falla al obtener schemas
        registry_failing = Mock()
        registry_failing.call_tool_sync = Mock()
        registry_failing.get_tools_with_schemas = Mock(side_effect=Exception("Connection error"))

        tools = MCPToolFactory.create_tools(
            tool_names=["consultar_expediente"],
            mcp_registry=registry_failing,
            logger=mock_logger,
            use_dynamic_schemas=True  # Intenta dinámico pero fallará
        )

        assert len(tools) == 1
        # Debe usar descripción fallback
        assert "datos completos" in tools[0].description

    def test_create_tools_with_static_schemas(self, mock_registry, mock_logger):
        """Test: Factory usa schemas estáticos cuando use_dynamic_schemas=False"""
        tools = MCPToolFactory.create_tools(
            tool_names=["consultar_expediente"],
            mcp_registry=mock_registry,
            logger=mock_logger,
            use_dynamic_schemas=False
        )

        assert len(tools) == 1
        # No debe llamar a get_tools_with_schemas
        mock_registry.get_tools_with_schemas.assert_not_called()
