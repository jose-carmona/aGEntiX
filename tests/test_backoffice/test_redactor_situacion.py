# tests/test_backoffice/test_redactor_situacion.py

"""
Tests para el agente RedactorSituacion.

Verifica:
- Registro correcto en el registry
- Carga de configuración desde YAML
- Inicialización del agente (sin CrewAI/LLM real)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from backoffice.agents.registry import (
    AGENT_REGISTRY,
    get_agent_class,
    list_crewai_agents,
    is_crewai_available
)


class TestRedactorSituacionRegistry:
    """Tests para el registro del agente RedactorSituacion"""

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_situacion_is_registered(self):
        """RedactorSituacion está en el registro de agentes"""
        assert "RedactorSituacion" in AGENT_REGISTRY

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_situacion_in_crewai_list(self):
        """RedactorSituacion aparece en lista de agentes CrewAI"""
        crewai_agents = list_crewai_agents()
        assert "RedactorSituacion" in crewai_agents

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_get_redactor_situacion_class(self):
        """get_agent_class retorna la clase RedactorSituacion"""
        agent_class = get_agent_class("RedactorSituacion")
        assert agent_class.__name__ == "RedactorSituacion"

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_situacion_extends_agent_real(self):
        """RedactorSituacion hereda de AgentReal"""
        from backoffice.agents.base_real import AgentReal
        agent_class = get_agent_class("RedactorSituacion")
        assert issubclass(agent_class, AgentReal)


class TestRedactorSituacionConfig:
    """Tests para la configuración del agente RedactorSituacion"""

    @pytest.fixture
    def mock_registry(self):
        """Mock del MCPClientRegistry"""
        registry = Mock()
        registry.get_tools_with_schemas.return_value = {}
        registry.call_tool_sync.return_value = {
            "content": [{"text": "{}"}]
        }
        return registry

    @pytest.fixture
    def mock_logger(self):
        """Mock del AuditLogger"""
        logger = Mock()
        logger.log = Mock()
        logger.error = Mock()
        logger.warning = Mock()
        return logger

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_situacion_loads_config(self, mock_registry, mock_logger):
        """RedactorSituacion carga configuración desde YAML"""
        from backoffice.agents.redactor_situacion import RedactorSituacion
        from backoffice.config.agent_config_loader import AgentConfigLoader

        loader = AgentConfigLoader()
        config = loader.get("RedactorSituacion")

        assert config.name == "RedactorSituacion"
        assert config.type == "crewai"
        assert config.is_crewai is True

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_situacion_has_required_tools(self):
        """RedactorSituacion tiene las herramientas MCP requeridas"""
        from backoffice.config.agent_config_loader import AgentConfigLoader

        loader = AgentConfigLoader()
        config = loader.get("RedactorSituacion")

        required_tools = [
            "consultar_expediente",
            "listar_documentos",
            "obtener_texto_documento",
            "crear_documento_desde_markdown"
        ]

        for tool in required_tools:
            assert tool in config.tools, f"Falta herramienta: {tool}"

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_situacion_has_write_permission(self):
        """RedactorSituacion tiene permiso de escritura de documentos"""
        from backoffice.config.agent_config_loader import AgentConfigLoader

        loader = AgentConfigLoader()
        config = loader.get("RedactorSituacion")

        assert "documento.escritura" in config.required_permissions


class TestRedactorSituacionInitialization:
    """Tests para la inicialización del agente"""

    @pytest.fixture
    def mock_settings(self):
        """Mock de settings"""
        with patch('backoffice.agents.base_real.get_settings') as mock:
            mock.return_value = Mock(ANTHROPIC_API_KEY="test-key")
            yield mock

    @pytest.fixture
    def mock_crewai(self):
        """Mock de CrewAI components"""
        with patch('backoffice.agents.base_real.LLM') as mock_llm:
            mock_llm.return_value = Mock()
            yield mock_llm

    @pytest.fixture
    def mock_mcp_tools(self):
        """Mock de MCPToolFactory"""
        with patch('backoffice.agents.mcp_tool_wrapper.MCPToolFactory') as mock:
            mock.create_tools.return_value = []
            yield mock

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_situacion_init(
        self,
        mock_settings,
        mock_crewai,
        mock_mcp_tools
    ):
        """RedactorSituacion se inicializa correctamente"""
        from backoffice.agents.redactor_situacion import RedactorSituacion

        mock_registry = Mock()
        mock_registry.get_tools_with_schemas.return_value = {}
        mock_logger = Mock()

        agent = RedactorSituacion(
            expediente_id="EXP-2024-001",
            tarea_id="TASK-001",
            run_id="RUN-001",
            mcp_registry=mock_registry,
            logger=mock_logger
        )

        assert agent.expediente_id == "EXP-2024-001"
        assert agent.tarea_id == "TASK-001"
        assert agent.run_id == "RUN-001"
        assert agent.config.name == "RedactorSituacion"

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_situacion_with_additional_goal(
        self,
        mock_settings,
        mock_crewai,
        mock_mcp_tools
    ):
        """RedactorSituacion acepta additional_goal"""
        from backoffice.agents.redactor_situacion import RedactorSituacion

        mock_registry = Mock()
        mock_registry.get_tools_with_schemas.return_value = {}
        mock_logger = Mock()

        agent = RedactorSituacion(
            expediente_id="EXP-2024-001",
            tarea_id="TASK-001",
            run_id="RUN-001",
            mcp_registry=mock_registry,
            logger=mock_logger,
            additional_goal="Enfócate en los documentos de tipo DNI"
        )

        assert agent.additional_goal == "Enfócate en los documentos de tipo DNI"


class TestRedactorSituacionDocumentation:
    """Tests para verificar la documentación del agente"""

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_situacion_has_docstring(self):
        """RedactorSituacion tiene docstring"""
        from backoffice.agents.redactor_situacion import RedactorSituacion

        assert RedactorSituacion.__doc__ is not None
        assert len(RedactorSituacion.__doc__) > 100

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_situacion_docstring_mentions_workflow(self):
        """Docstring menciona el flujo de trabajo"""
        from backoffice.agents.redactor_situacion import RedactorSituacion

        doc = RedactorSituacion.__doc__

        # Verificar que menciona pasos clave del flujo
        assert "consultar_expediente" in doc
        assert "listar_documentos" in doc
        assert "obtener_texto_documento" in doc
        assert "crear_documento_desde_markdown" in doc
