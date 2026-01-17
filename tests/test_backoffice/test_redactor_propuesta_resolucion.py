# tests/test_backoffice/test_redactor_propuesta_resolucion.py

"""
Tests para el agente RedactorPropuestaResolucion.

Verifica:
- Registro correcto en el registry
- Carga de configuración desde YAML
- Inicialización del agente (sin CrewAI/LLM real)
- Herramientas MCP requeridas (incluyendo documentación)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from backoffice.agents.registry import (
    AGENT_REGISTRY,
    get_agent_class,
    list_crewai_agents,
    is_crewai_available
)


class TestRedactorPropuestaResolucionRegistry:
    """Tests para el registro del agente RedactorPropuestaResolucion"""

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_propuesta_resolucion_is_registered(self):
        """RedactorPropuestaResolucion está en el registro de agentes"""
        assert "RedactorPropuestaResolucion" in AGENT_REGISTRY

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_propuesta_resolucion_in_crewai_list(self):
        """RedactorPropuestaResolucion aparece en lista de agentes CrewAI"""
        crewai_agents = list_crewai_agents()
        assert "RedactorPropuestaResolucion" in crewai_agents

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_get_redactor_propuesta_resolucion_class(self):
        """get_agent_class retorna la clase RedactorPropuestaResolucion"""
        agent_class = get_agent_class("RedactorPropuestaResolucion")
        assert agent_class.__name__ == "RedactorPropuestaResolucion"

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_propuesta_resolucion_extends_agent_crewai(self):
        """RedactorPropuestaResolucion hereda de AgentCrewAI"""
        from backoffice.agents.base_real import AgentCrewAI
        agent_class = get_agent_class("RedactorPropuestaResolucion")
        assert issubclass(agent_class, AgentCrewAI)


class TestRedactorPropuestaResolucionConfig:
    """Tests para la configuración del agente RedactorPropuestaResolucion"""

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
    def test_redactor_propuesta_resolucion_loads_config(self, mock_registry, mock_logger):
        """RedactorPropuestaResolucion carga configuración desde YAML"""
        from backoffice.agents.redactor_propuesta_resolucion import RedactorPropuestaResolucion
        from backoffice.config.agent_config_loader import AgentConfigLoader

        loader = AgentConfigLoader()
        config = loader.get("RedactorPropuestaResolucion")

        assert config.name == "RedactorPropuestaResolucion"
        assert config.type == "crewai"
        assert config.is_crewai is True

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_propuesta_resolucion_has_expedientes_tools(self):
        """RedactorPropuestaResolucion tiene las herramientas MCP de expedientes"""
        from backoffice.config.agent_config_loader import AgentConfigLoader

        loader = AgentConfigLoader()
        config = loader.get("RedactorPropuestaResolucion")

        expedientes_tools = [
            "consultar_expediente",
            "listar_documentos",
            "obtener_texto_documento",
            "crear_documento_desde_markdown",
            "añadir_anotacion"
        ]

        for tool in expedientes_tools:
            assert tool in config.tools, f"Falta herramienta de expedientes: {tool}"

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_propuesta_resolucion_has_documentacion_tools(self):
        """RedactorPropuestaResolucion tiene las herramientas MCP de documentación"""
        from backoffice.config.agent_config_loader import AgentConfigLoader

        loader = AgentConfigLoader()
        config = loader.get("RedactorPropuestaResolucion")

        documentacion_tools = [
            "listar_documentacion",
            "obtener_doc_documentacion"
        ]

        for tool in documentacion_tools:
            assert tool in config.tools, f"Falta herramienta de documentación: {tool}"

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_propuesta_resolucion_has_gestion_permission(self):
        """RedactorPropuestaResolucion tiene permiso de gestión"""
        from backoffice.config.agent_config_loader import AgentConfigLoader

        loader = AgentConfigLoader()
        config = loader.get("RedactorPropuestaResolucion")

        assert "gestion" in config.required_permissions

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_propuesta_resolucion_has_documentacion_permission(self):
        """RedactorPropuestaResolucion tiene permiso de lectura de documentación"""
        from backoffice.config.agent_config_loader import AgentConfigLoader

        loader = AgentConfigLoader()
        config = loader.get("RedactorPropuestaResolucion")

        assert "documentacion:leer" in config.required_permissions


class TestRedactorPropuestaResolucionInitialization:
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
    def test_redactor_propuesta_resolucion_init(
        self,
        mock_settings,
        mock_crewai,
        mock_mcp_tools
    ):
        """RedactorPropuestaResolucion se inicializa correctamente"""
        from backoffice.agents.redactor_propuesta_resolucion import RedactorPropuestaResolucion

        mock_registry = Mock()
        mock_registry.get_tools_with_schemas.return_value = {}
        mock_logger = Mock()

        agent = RedactorPropuestaResolucion(
            expediente_id="EXP-2024-001",
            tarea_id="TASK-001",
            run_id="RUN-001",
            mcp_registry=mock_registry,
            logger=mock_logger
        )

        assert agent.expediente_id == "EXP-2024-001"
        assert agent.tarea_id == "TASK-001"
        assert agent.run_id == "RUN-001"
        assert agent.config.name == "RedactorPropuestaResolucion"

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_propuesta_resolucion_with_additional_goal(
        self,
        mock_settings,
        mock_crewai,
        mock_mcp_tools
    ):
        """RedactorPropuestaResolucion acepta additional_goal"""
        from backoffice.agents.redactor_propuesta_resolucion import RedactorPropuestaResolucion

        mock_registry = Mock()
        mock_registry.get_tools_with_schemas.return_value = {}
        mock_logger = Mock()

        agent = RedactorPropuestaResolucion(
            expediente_id="EXP-2024-001",
            tarea_id="TASK-001",
            run_id="RUN-001",
            mcp_registry=mock_registry,
            logger=mock_logger,
            additional_goal="La propuesta debe enfatizar el impacto social del proyecto"
        )

        assert agent.additional_goal == "La propuesta debe enfatizar el impacto social del proyecto"


class TestRedactorPropuestaResolucionDocumentation:
    """Tests para verificar la documentación del agente"""

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_propuesta_resolucion_has_docstring(self):
        """RedactorPropuestaResolucion tiene docstring"""
        from backoffice.agents.redactor_propuesta_resolucion import RedactorPropuestaResolucion

        assert RedactorPropuestaResolucion.__doc__ is not None
        assert len(RedactorPropuestaResolucion.__doc__) > 100

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_propuesta_resolucion_docstring_mentions_workflow(self):
        """Docstring menciona el flujo de trabajo"""
        from backoffice.agents.redactor_propuesta_resolucion import RedactorPropuestaResolucion

        doc = RedactorPropuestaResolucion.__doc__

        # Verificar que menciona pasos clave del flujo
        assert "consultar_expediente" in doc
        assert "obtener_doc_documentacion" in doc
        assert "listar_documentos" in doc
        assert "crear_documento_desde_markdown" in doc

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_propuesta_resolucion_docstring_mentions_plantilla(self):
        """Docstring menciona el uso de plantilla"""
        from backoffice.agents.redactor_propuesta_resolucion import RedactorPropuestaResolucion

        doc = RedactorPropuestaResolucion.__doc__

        assert "plantilla" in doc.lower()


class TestRedactorPropuestaResolucionLLMConfig:
    """Tests para la configuración del LLM"""

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_propuesta_resolucion_has_high_max_tokens(self):
        """RedactorPropuestaResolucion tiene max_tokens suficientes para documentos largos"""
        from backoffice.config.agent_config_loader import AgentConfigLoader

        loader = AgentConfigLoader()
        config = loader.get("RedactorPropuestaResolucion")

        # El agente necesita generar documentos largos
        assert config.llm.max_tokens >= 4096

    @pytest.mark.skipif(
        not is_crewai_available(),
        reason="CrewAI no está instalado"
    )
    def test_redactor_propuesta_resolucion_has_low_temperature(self):
        """RedactorPropuestaResolucion tiene temperatura baja para consistencia"""
        from backoffice.config.agent_config_loader import AgentConfigLoader

        loader = AgentConfigLoader()
        config = loader.get("RedactorPropuestaResolucion")

        # Documentos formales requieren consistencia
        assert config.llm.temperature <= 0.2
