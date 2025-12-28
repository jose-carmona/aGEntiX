# tests/test_backoffice/test_agent_config_loader.py

"""
Tests para AgentConfigLoader.

Verifica la carga de configuración de agentes desde YAML,
incluyendo soporte para agentes mock (Paso 1) y CrewAI (Paso 6).
"""

import pytest
import tempfile
import os
from pathlib import Path

from backoffice.config.agent_config_loader import (
    AgentConfigLoader,
    AgentDefinition,
    LLMConfig,
    CrewAIAgentConfig,
    CrewAITaskConfig,
    get_agent_loader,
    reset_agent_loader
)


class TestAgentDefinition:
    """Tests para el modelo AgentDefinition"""

    def test_create_agent_definition(self):
        """AgentDefinition se crea correctamente con todos los campos"""
        agent = AgentDefinition(
            name="TestAgent",
            type="mock",
            enabled=True,
            description="Agente de prueba",
            model="claude-3-5-sonnet-20241022",
            system_prompt="Eres un agente de prueba",
            tools=["tool1", "tool2"],
            required_permissions=["perm1", "perm2"],
            timeout_seconds=600
        )

        assert agent.name == "TestAgent"
        assert agent.type == "mock"
        assert agent.enabled is True
        assert agent.description == "Agente de prueba"
        assert agent.model == "claude-3-5-sonnet-20241022"
        assert agent.system_prompt == "Eres un agente de prueba"
        assert agent.tools == ["tool1", "tool2"]
        assert agent.required_permissions == ["perm1", "perm2"]
        assert agent.timeout_seconds == 600

    def test_agent_definition_defaults(self):
        """AgentDefinition tiene valores por defecto correctos"""
        agent = AgentDefinition(
            name="MinimalAgent",
            description="Agente mínimo",
            model="test-model",
            system_prompt="Prompt"
        )

        assert agent.type == "mock"
        assert agent.enabled is True
        assert agent.tools == []
        assert agent.required_permissions == []
        assert agent.timeout_seconds == 300
        assert agent.llm is None
        assert agent.crewai_agent is None
        assert agent.crewai_task is None

    def test_is_crewai_property(self):
        """is_crewai retorna True para agentes CrewAI"""
        mock_agent = AgentDefinition(
            name="MockAgent",
            type="mock",
            description="Test",
            model="test",
            system_prompt="Test"
        )
        crewai_agent = AgentDefinition(
            name="CrewAIAgent",
            type="crewai",
            description="Test",
            model="test",
            system_prompt=""
        )

        assert mock_agent.is_mock is True
        assert mock_agent.is_crewai is False
        assert crewai_agent.is_crewai is True
        assert crewai_agent.is_mock is False

    def test_mcp_tools_property(self):
        """mcp_tools es alias de tools"""
        agent = AgentDefinition(
            name="TestAgent",
            description="Test",
            model="test",
            system_prompt="Test",
            tools=["tool1", "tool2"]
        )

        assert agent.mcp_tools == agent.tools
        assert agent.mcp_tools == ["tool1", "tool2"]


class TestLLMConfig:
    """Tests para LLMConfig"""

    def test_create_llm_config(self):
        """LLMConfig se crea correctamente"""
        llm = LLMConfig(
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            temperature=0.1
        )

        assert llm.provider == "anthropic"
        assert llm.model == "claude-3-5-sonnet-20241022"
        assert llm.max_tokens == 4096
        assert llm.temperature == 0.1

    def test_llm_config_defaults(self):
        """LLMConfig tiene defaults"""
        llm = LLMConfig(provider="anthropic", model="test")

        assert llm.max_tokens == 4096
        assert llm.temperature == 0.1


class TestCrewAIAgentConfig:
    """Tests para CrewAIAgentConfig"""

    def test_create_crewai_agent_config(self):
        """CrewAIAgentConfig se crea correctamente"""
        config = CrewAIAgentConfig(
            role="Test Role",
            goal="Test Goal",
            backstory="Test Backstory",
            verbose=True,
            allow_delegation=False
        )

        assert config.role == "Test Role"
        assert config.goal == "Test Goal"
        assert config.backstory == "Test Backstory"
        assert config.verbose is True
        assert config.allow_delegation is False


class TestAgentConfigLoader:
    """Tests para AgentConfigLoader"""

    @pytest.fixture
    def valid_yaml_content(self):
        """Contenido YAML válido para tests (formato mock)"""
        return """
agents:
  ValidadorDocumental:
    type: mock
    enabled: true
    description: "Valida documentación"
    model: "claude-3-5-sonnet-20241022"
    system_prompt: "Eres un validador"
    tools:
      - consultar_expediente
      - actualizar_datos
    required_permissions:
      - expediente.lectura
    timeout_seconds: 300

  AnalizadorSubvencion:
    type: mock
    enabled: true
    description: "Analiza subvenciones"
    model: "claude-3-5-sonnet-20241022"
    system_prompt: "Eres un analizador"
    tools:
      - consultar_expediente
    required_permissions:
      - subvencion.analisis
    timeout_seconds: 600
"""

    @pytest.fixture
    def crewai_yaml_content(self):
        """Contenido YAML con agente CrewAI"""
        return """
agents:
  ClasificadorExpediente:
    type: crewai
    enabled: true
    description: "Clasifica expedientes"
    llm:
      provider: anthropic
      model: claude-3-5-sonnet-20241022
      max_tokens: 4096
      temperature: 0.1
    crewai_agent:
      role: "Clasificador"
      goal: "Clasificar expediente {expediente_id}"
      backstory: "Experto en clasificación"
      verbose: true
      allow_delegation: false
    crewai_task:
      description: "Clasifica el expediente {expediente_id}"
      expected_output: "JSON con clasificación"
    tools:
      - consultar_expediente
    required_permissions:
      - expediente.lectura
    timeout_seconds: 300
"""

    @pytest.fixture
    def temp_yaml_file(self, valid_yaml_content):
        """Crea un archivo YAML temporal para tests"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(valid_yaml_content)
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def temp_crewai_yaml_file(self, crewai_yaml_content):
        """Crea archivo YAML temporal con agente CrewAI"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(crewai_yaml_content)
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_load_valid_yaml(self, temp_yaml_file):
        """Carga correctamente un archivo YAML válido"""
        loader = AgentConfigLoader(temp_yaml_file)

        assert loader.exists("ValidadorDocumental")
        assert loader.exists("AnalizadorSubvencion")
        assert not loader.exists("AgenteInexistente")

    def test_get_agent(self, temp_yaml_file):
        """Obtiene correctamente la definición de un agente"""
        loader = AgentConfigLoader(temp_yaml_file)
        agent = loader.get("ValidadorDocumental")

        assert agent.name == "ValidadorDocumental"
        assert agent.type == "mock"
        assert agent.description == "Valida documentación"
        assert agent.model == "claude-3-5-sonnet-20241022"
        assert "consultar_expediente" in agent.tools
        assert "actualizar_datos" in agent.tools
        assert agent.timeout_seconds == 300

    def test_get_agent_alias(self, temp_yaml_file):
        """get_agent() es alias de get()"""
        loader = AgentConfigLoader(temp_yaml_file)
        agent1 = loader.get("ValidadorDocumental")
        agent2 = loader.get_agent("ValidadorDocumental")

        assert agent1.name == agent2.name

    def test_get_nonexistent_agent_raises(self, temp_yaml_file):
        """get() lanza KeyError para agente inexistente"""
        loader = AgentConfigLoader(temp_yaml_file)

        with pytest.raises(KeyError) as exc_info:
            loader.get("AgenteInexistente")

        assert "AgenteInexistente" in str(exc_info.value)
        assert "Agentes disponibles" in str(exc_info.value)

    def test_list_agents(self, temp_yaml_file):
        """list_agents() retorna todas las definiciones"""
        loader = AgentConfigLoader(temp_yaml_file)
        agents = loader.list_agents()

        assert len(agents) == 2
        names = [a.name for a in agents]
        assert "ValidadorDocumental" in names
        assert "AnalizadorSubvencion" in names

    def test_list_agent_names(self, temp_yaml_file):
        """list_agent_names() retorna los nombres"""
        loader = AgentConfigLoader(temp_yaml_file)
        names = loader.list_agent_names()

        assert len(names) == 2
        assert "ValidadorDocumental" in names
        assert "AnalizadorSubvencion" in names

    def test_list_by_type_mock(self, temp_yaml_file):
        """list_by_type() filtra por tipo mock"""
        loader = AgentConfigLoader(temp_yaml_file)
        mock_agents = loader.list_by_type("mock")

        assert len(mock_agents) == 2
        assert "ValidadorDocumental" in mock_agents

    def test_list_by_type_crewai(self, temp_crewai_yaml_file):
        """list_by_type() filtra por tipo crewai"""
        loader = AgentConfigLoader(temp_crewai_yaml_file)
        crewai_agents = loader.list_by_type("crewai")

        assert len(crewai_agents) == 1
        assert "ClasificadorExpediente" in crewai_agents

    def test_load_crewai_agent(self, temp_crewai_yaml_file):
        """Carga correctamente un agente CrewAI"""
        loader = AgentConfigLoader(temp_crewai_yaml_file)
        agent = loader.get("ClasificadorExpediente")

        assert agent.type == "crewai"
        assert agent.is_crewai is True
        assert agent.llm is not None
        assert agent.llm.provider == "anthropic"
        assert agent.llm.model == "claude-3-5-sonnet-20241022"
        assert agent.crewai_agent is not None
        assert agent.crewai_agent.role == "Clasificador"
        assert agent.crewai_task is not None
        assert "expediente_id" in agent.crewai_task.description

    def test_load_nonexistent_file(self):
        """Maneja archivo inexistente sin error"""
        loader = AgentConfigLoader("/path/to/nonexistent/file.yaml")

        assert loader.list_agents() == []
        assert loader.list_agent_names() == []
        assert not loader.exists("AnyAgent")

    def test_load_empty_yaml(self):
        """Maneja YAML vacío sin error"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write("")
            temp_path = f.name

        try:
            loader = AgentConfigLoader(temp_path)
            assert loader.list_agents() == []
        finally:
            os.unlink(temp_path)

    def test_load_yaml_without_agents_section(self):
        """Maneja YAML sin sección agents"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write("other_section:\n  key: value\n")
            temp_path = f.name

        try:
            loader = AgentConfigLoader(temp_path)
            assert loader.list_agents() == []
        finally:
            os.unlink(temp_path)

    def test_reload_config(self, temp_yaml_file):
        """reload() recarga la configuración"""
        loader = AgentConfigLoader(temp_yaml_file)
        initial_count = len(loader.list_agents())

        # Modificar el archivo
        with open(temp_yaml_file, 'a', encoding='utf-8') as f:
            f.write("""
  NuevoAgente:
    type: mock
    enabled: true
    description: "Agente nuevo"
    model: "test-model"
    system_prompt: "Test"
    tools:
      - tool1
""")

        # Recargar
        loader.reload()

        assert len(loader.list_agents()) == initial_count + 1
        assert loader.exists("NuevoAgente")


class TestAgentLoaderSingleton:
    """Tests para el singleton get_agent_loader"""

    def setup_method(self):
        """Reset singleton antes de cada test"""
        reset_agent_loader()

    def teardown_method(self):
        """Reset singleton después de cada test"""
        reset_agent_loader()

    def test_get_agent_loader_default_path(self):
        """get_agent_loader() usa ruta por defecto"""
        loader = get_agent_loader()

        # Debe cargar el archivo agents.yaml del proyecto
        assert loader is not None
        # Verificar que carga los agentes del proyecto
        assert loader.exists("ValidadorDocumental")

    def test_get_agent_loader_singleton(self):
        """get_agent_loader() retorna la misma instancia"""
        loader1 = get_agent_loader()
        loader2 = get_agent_loader()

        assert loader1 is loader2

    def test_reset_agent_loader(self):
        """reset_agent_loader() permite crear nueva instancia"""
        loader1 = get_agent_loader()
        reset_agent_loader()
        loader2 = get_agent_loader()

        # Son instancias diferentes después del reset
        assert loader1 is not loader2


class TestAgentConfigLoaderWithRealFile:
    """Tests con el archivo agents.yaml real del proyecto"""

    def test_load_project_agents_yaml(self):
        """Carga el archivo agents.yaml del proyecto"""
        config_path = Path(__file__).parent.parent.parent / "src" / "backoffice" / "config" / "agents.yaml"

        if not config_path.exists():
            pytest.skip("agents.yaml no existe todavía")

        loader = AgentConfigLoader(str(config_path))

        # Verificar agentes esperados
        assert loader.exists("ValidadorDocumental")
        assert loader.exists("AnalizadorSubvencion")
        assert loader.exists("GeneradorInforme")

    def test_clasificador_expediente_config(self):
        """ClasificadorExpediente tiene configuración CrewAI correcta"""
        config_path = Path(__file__).parent.parent.parent / "src" / "backoffice" / "config" / "agents.yaml"

        if not config_path.exists():
            pytest.skip("agents.yaml no existe todavía")

        loader = AgentConfigLoader(str(config_path))

        if not loader.exists("ClasificadorExpediente"):
            pytest.skip("ClasificadorExpediente no configurado")

        agent = loader.get("ClasificadorExpediente")

        assert agent.type == "crewai"
        assert agent.is_crewai is True
        assert agent.llm is not None
        assert agent.llm.provider == "anthropic"
        assert agent.crewai_agent is not None
        assert agent.crewai_task is not None
        assert "consultar_expediente" in agent.tools

    def test_validador_documental_config(self):
        """ValidadorDocumental tiene configuración mock correcta"""
        config_path = Path(__file__).parent.parent.parent / "src" / "backoffice" / "config" / "agents.yaml"

        if not config_path.exists():
            pytest.skip("agents.yaml no existe todavía")

        loader = AgentConfigLoader(str(config_path))
        agent = loader.get("ValidadorDocumental")

        assert agent.type == "mock"
        assert agent.is_mock is True
        assert "consultar_expediente" in agent.tools
        assert "actualizar_datos" in agent.tools
        assert "añadir_anotacion" in agent.tools

    def test_all_agents_have_required_fields(self):
        """Todos los agentes tienen campos requeridos"""
        config_path = Path(__file__).parent.parent.parent / "src" / "backoffice" / "config" / "agents.yaml"

        if not config_path.exists():
            pytest.skip("agents.yaml no existe todavía")

        loader = AgentConfigLoader(str(config_path))

        for agent in loader.list_agents():
            assert agent.name, "Agente sin nombre"
            assert agent.type in ["mock", "crewai", "langgraph"], f"{agent.name}: tipo inválido"
            assert agent.description, f"{agent.name}: sin descripción"
            assert len(agent.tools) > 0, f"{agent.name}: sin herramientas"
            assert agent.timeout_seconds > 0, f"{agent.name}: timeout inválido"

            # Verificar campos específicos de CrewAI
            if agent.is_crewai:
                assert agent.llm is not None, f"{agent.name}: sin configuración LLM"
                assert agent.crewai_agent is not None, f"{agent.name}: sin configuración crewai_agent"
                assert agent.crewai_task is not None, f"{agent.name}: sin configuración crewai_task"
            else:
                assert agent.system_prompt, f"{agent.name}: sin system_prompt"
