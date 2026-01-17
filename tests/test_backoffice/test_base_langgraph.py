# tests/test_backoffice/test_base_langgraph.py

"""
Tests para AgentLangGraph.

Verifica la clase base de agentes LangGraph (Paso 11).
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import json

# Importación condicional - puede fallar si LangGraph no está instalado
try:
    from backoffice.agents.base_langgraph import AgentLangGraph, LANGGRAPH_AVAILABLE
    from backoffice.config.agent_config_loader import (
        AgentDefinition,
        LLMConfig,
        LangGraphConfig
    )
except ImportError:
    LANGGRAPH_AVAILABLE = False
    AgentLangGraph = None


@pytest.fixture
def mock_mcp_registry():
    """Mock del MCPClientRegistry."""
    registry = Mock()
    registry.call_tool_sync = Mock(return_value={"status": "ok", "data": "test"})
    return registry


@pytest.fixture
def mock_logger():
    """Mock del AuditLogger."""
    logger = Mock()
    logger.log = Mock()
    logger.error = Mock()
    return logger


@pytest.fixture
def langgraph_config():
    """Configuración LangGraph de prueba."""
    return AgentDefinition(
        name="TestLangGraphAgent",
        type="langgraph",
        enabled=True,
        description="Agente de prueba LangGraph",
        llm=LLMConfig(
            provider="anthropic",
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            temperature=0.1
        ),
        langgraph_config=LangGraphConfig(
            system_prompt="Eres un agente de prueba",
            task_prompt="Ejecuta la tarea para {expediente_id}",
            max_iterations=5
        ),
        tools=["consultar_expediente", "listar_documentos"],
        required_permissions=["expediente.lectura"],
        timeout_seconds=300
    )


@pytest.mark.skipif(
    not LANGGRAPH_AVAILABLE,
    reason="LangGraph no está instalado"
)
class TestAgentLangGraphInit:
    """Tests de inicialización de AgentLangGraph."""

    def test_init_requires_langgraph_type(self, mock_mcp_registry, mock_logger):
        """Debe fallar si el agente no es tipo langgraph."""
        crewai_config = AgentDefinition(
            name="CrewAIAgent",
            type="crewai",
            description="Test",
            llm=LLMConfig(provider="anthropic", model="test"),
            langgraph_config=None,
            tools=[]
        )

        with pytest.raises(ValueError) as exc_info:
            # Crear clase concreta para test
            class TestAgent(AgentLangGraph):
                pass

            TestAgent(
                expediente_id="EXP-001",
                tarea_id="TASK-001",
                run_id="RUN-001",
                mcp_registry=mock_mcp_registry,
                logger=mock_logger,
                config=crewai_config
            )

        assert "no es de tipo 'langgraph'" in str(exc_info.value)


@pytest.mark.skipif(
    not LANGGRAPH_AVAILABLE,
    reason="LangGraph no está instalado"
)
class TestAgentLangGraphSanitizeToolName:
    """Tests de sanitización de nombres de herramientas."""

    def test_sanitize_tool_name_with_spanish_chars(self, mock_mcp_registry, mock_logger, langgraph_config):
        """Debe reemplazar caracteres españoles."""

        class TestAgent(AgentLangGraph):
            pass

        with patch.object(TestAgent, '_create_llm', return_value=Mock()):
            with patch.object(TestAgent, '_create_langchain_tools', return_value=[]):
                agent = TestAgent(
                    expediente_id="EXP-001",
                    tarea_id="TASK-001",
                    run_id="RUN-001",
                    mcp_registry=mock_mcp_registry,
                    logger=mock_logger,
                    config=langgraph_config
                )

        result = agent._sanitize_tool_name("añadir_anotación")
        assert result == "anadir_anotacion"
        assert "ñ" not in result
        assert "ó" not in result

    def test_sanitize_tool_name_with_special_chars(self, mock_mcp_registry, mock_logger, langgraph_config):
        """Debe reemplazar caracteres especiales con guión bajo."""

        class TestAgent(AgentLangGraph):
            pass

        with patch.object(TestAgent, '_create_llm', return_value=Mock()):
            with patch.object(TestAgent, '_create_langchain_tools', return_value=[]):
                agent = TestAgent(
                    expediente_id="EXP-001",
                    tarea_id="TASK-001",
                    run_id="RUN-001",
                    mcp_registry=mock_mcp_registry,
                    logger=mock_logger,
                    config=langgraph_config
                )

        result = agent._sanitize_tool_name("tool@name#with$special")
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result

    def test_sanitize_tool_name_valid_unchanged(self, mock_mcp_registry, mock_logger, langgraph_config):
        """No debe modificar nombres válidos."""

        class TestAgent(AgentLangGraph):
            pass

        with patch.object(TestAgent, '_create_llm', return_value=Mock()):
            with patch.object(TestAgent, '_create_langchain_tools', return_value=[]):
                agent = TestAgent(
                    expediente_id="EXP-001",
                    tarea_id="TASK-001",
                    run_id="RUN-001",
                    mcp_registry=mock_mcp_registry,
                    logger=mock_logger,
                    config=langgraph_config
                )

        result = agent._sanitize_tool_name("consultar_expediente")
        assert result == "consultar_expediente"


@pytest.mark.skipif(
    not LANGGRAPH_AVAILABLE,
    reason="LangGraph no está instalado"
)
class TestAgentLangGraphToolCreation:
    """Tests de creación de herramientas LangChain."""

    def test_get_tool_description_known_tool(self, mock_mcp_registry, mock_logger, langgraph_config):
        """Debe retornar descripción para herramientas conocidas."""

        class TestAgent(AgentLangGraph):
            pass

        with patch.object(TestAgent, '_create_llm', return_value=Mock()):
            with patch.object(TestAgent, '_create_langchain_tools', return_value=[]):
                agent = TestAgent(
                    expediente_id="EXP-001",
                    tarea_id="TASK-001",
                    run_id="RUN-001",
                    mcp_registry=mock_mcp_registry,
                    logger=mock_logger,
                    config=langgraph_config
                )

        desc = agent._get_tool_description("consultar_expediente")
        assert "expediente" in desc.lower()
        assert "expediente_id" in desc

    def test_get_tool_description_unknown_tool(self, mock_mcp_registry, mock_logger, langgraph_config):
        """Debe retornar descripción genérica para herramientas desconocidas."""

        class TestAgent(AgentLangGraph):
            pass

        with patch.object(TestAgent, '_create_llm', return_value=Mock()):
            with patch.object(TestAgent, '_create_langchain_tools', return_value=[]):
                agent = TestAgent(
                    expediente_id="EXP-001",
                    tarea_id="TASK-001",
                    run_id="RUN-001",
                    mcp_registry=mock_mcp_registry,
                    logger=mock_logger,
                    config=langgraph_config
                )

        desc = agent._get_tool_description("herramienta_nueva")
        assert "herramienta_nueva" in desc


@pytest.mark.skipif(
    not LANGGRAPH_AVAILABLE,
    reason="LangGraph no está instalado"
)
class TestAgentLangGraphFormatTemplate:
    """Tests de formateo de templates."""

    def test_format_template_with_variables(self, mock_mcp_registry, mock_logger, langgraph_config):
        """Debe sustituir variables en el template."""

        class TestAgent(AgentLangGraph):
            pass

        with patch.object(TestAgent, '_create_llm', return_value=Mock()):
            with patch.object(TestAgent, '_create_langchain_tools', return_value=[]):
                agent = TestAgent(
                    expediente_id="EXP-2024-001",
                    tarea_id="TASK-123",
                    run_id="RUN-456",
                    mcp_registry=mock_mcp_registry,
                    logger=mock_logger,
                    config=langgraph_config
                )

        template = "Procesa expediente {expediente_id} en tarea {tarea_id}"
        result = agent._format_template(template)

        assert "EXP-2024-001" in result
        assert "TASK-123" in result
        assert "{expediente_id}" not in result

    def test_format_template_with_additional_goal(self, mock_mcp_registry, mock_logger, langgraph_config):
        """Debe incluir additional_goal en el template."""

        class TestAgent(AgentLangGraph):
            pass

        with patch.object(TestAgent, '_create_llm', return_value=Mock()):
            with patch.object(TestAgent, '_create_langchain_tools', return_value=[]):
                agent = TestAgent(
                    expediente_id="EXP-001",
                    tarea_id="TASK-001",
                    run_id="RUN-001",
                    mcp_registry=mock_mcp_registry,
                    logger=mock_logger,
                    config=langgraph_config,
                    additional_goal="Objetivo adicional de prueba"
                )

        template = "Tarea: {additional_goal}"
        result = agent._format_template(template)

        assert "Objetivo adicional de prueba" in result


@pytest.mark.skipif(
    not LANGGRAPH_AVAILABLE,
    reason="LangGraph no está instalado"
)
class TestAgentLangGraphParseResult:
    """Tests de parseo de resultados."""

    def test_parse_result_valid_json(self, mock_mcp_registry, mock_logger, langgraph_config):
        """Debe parsear JSON válido."""

        class TestAgent(AgentLangGraph):
            pass

        with patch.object(TestAgent, '_create_llm', return_value=Mock()):
            with patch.object(TestAgent, '_create_langchain_tools', return_value=[]):
                agent = TestAgent(
                    expediente_id="EXP-001",
                    tarea_id="TASK-001",
                    run_id="RUN-001",
                    mcp_registry=mock_mcp_registry,
                    logger=mock_logger,
                    config=langgraph_config
                )

        result = agent._parse_result('{"completado": true, "mensaje": "OK"}')

        assert result["completado"] is True
        assert result["mensaje"] == "OK"

    def test_parse_result_json_in_text(self, mock_mcp_registry, mock_logger, langgraph_config):
        """Debe extraer JSON de texto."""

        class TestAgent(AgentLangGraph):
            pass

        with patch.object(TestAgent, '_create_llm', return_value=Mock()):
            with patch.object(TestAgent, '_create_langchain_tools', return_value=[]):
                agent = TestAgent(
                    expediente_id="EXP-001",
                    tarea_id="TASK-001",
                    run_id="RUN-001",
                    mcp_registry=mock_mcp_registry,
                    logger=mock_logger,
                    config=langgraph_config
                )

        text = 'Aquí está el resultado: {"status": "success"} fin.'
        result = agent._parse_result(text)

        assert result["status"] == "success"

    def test_parse_result_invalid_json(self, mock_mcp_registry, mock_logger, langgraph_config):
        """Debe retornar dict vacío para JSON inválido."""

        class TestAgent(AgentLangGraph):
            pass

        with patch.object(TestAgent, '_create_llm', return_value=Mock()):
            with patch.object(TestAgent, '_create_langchain_tools', return_value=[]):
                agent = TestAgent(
                    expediente_id="EXP-001",
                    tarea_id="TASK-001",
                    run_id="RUN-001",
                    mcp_registry=mock_mcp_registry,
                    logger=mock_logger,
                    config=langgraph_config
                )

        result = agent._parse_result("Esto no es JSON")

        assert result == {}


@pytest.mark.skipif(
    not LANGGRAPH_AVAILABLE,
    reason="LangGraph no está instalado"
)
class TestAgentLangGraphToolTracking:
    """Tests de tracking de herramientas usadas."""

    def test_track_tool_use(self, mock_mcp_registry, mock_logger, langgraph_config):
        """Debe registrar herramientas usadas."""

        class TestAgent(AgentLangGraph):
            pass

        with patch.object(TestAgent, '_create_llm', return_value=Mock()):
            with patch.object(TestAgent, '_create_langchain_tools', return_value=[]):
                agent = TestAgent(
                    expediente_id="EXP-001",
                    tarea_id="TASK-001",
                    run_id="RUN-001",
                    mcp_registry=mock_mcp_registry,
                    logger=mock_logger,
                    config=langgraph_config
                )

        agent._track_tool_use("consultar_expediente")
        agent._track_tool_use("listar_documentos")
        agent._track_tool_use("consultar_expediente")  # Duplicado

        tools = agent.get_tools_used()
        assert "consultar_expediente" in tools
        assert "listar_documentos" in tools
        assert len(tools) == 2  # Sin duplicados

    def test_get_tools_used_returns_copy(self, mock_mcp_registry, mock_logger, langgraph_config):
        """get_tools_used debe retornar copia."""

        class TestAgent(AgentLangGraph):
            pass

        with patch.object(TestAgent, '_create_llm', return_value=Mock()):
            with patch.object(TestAgent, '_create_langchain_tools', return_value=[]):
                agent = TestAgent(
                    expediente_id="EXP-001",
                    tarea_id="TASK-001",
                    run_id="RUN-001",
                    mcp_registry=mock_mcp_registry,
                    logger=mock_logger,
                    config=langgraph_config
                )

        agent._track_tool_use("test_tool")
        tools1 = agent.get_tools_used()
        tools2 = agent.get_tools_used()

        assert tools1 is not tools2
        assert tools1 == tools2
