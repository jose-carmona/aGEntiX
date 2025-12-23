# tests/test_backoffice/test_agent_config_loader.py

"""
Tests para AgentConfigLoader.

Verifica la carga de configuración de agentes desde YAML.
"""

import pytest
import tempfile
import os
from pathlib import Path

from backoffice.config.agent_config_loader import (
    AgentConfigLoader,
    AgentDefinition,
    get_agent_loader,
    reset_agent_loader
)


class TestAgentDefinition:
    """Tests para el modelo AgentDefinition"""

    def test_create_agent_definition(self):
        """AgentDefinition se crea correctamente con todos los campos"""
        agent = AgentDefinition(
            name="TestAgent",
            description="Agente de prueba",
            model="claude-3-5-sonnet-20241022",
            system_prompt="Eres un agente de prueba",
            tools=["tool1", "tool2"],
            required_permissions=["perm1", "perm2"],
            timeout_seconds=600
        )

        assert agent.name == "TestAgent"
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

        assert agent.tools == []
        assert agent.required_permissions == []
        assert agent.timeout_seconds == 300


class TestAgentConfigLoader:
    """Tests para AgentConfigLoader"""

    @pytest.fixture
    def valid_yaml_content(self):
        """Contenido YAML válido para tests"""
        return """
agents:
  ValidadorDocumental:
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
        assert agent.description == "Valida documentación"
        assert agent.model == "claude-3-5-sonnet-20241022"
        assert "consultar_expediente" in agent.tools
        assert "actualizar_datos" in agent.tools
        assert agent.timeout_seconds == 300

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
    description: "Agente nuevo"
    model: "test-model"
    system_prompt: "Test"
""")

        # Recargar
        loader.reload()

        assert len(loader.list_agents()) == initial_count + 1
        assert loader.exists("NuevoAgente")

    def test_agent_with_minimal_config(self):
        """Agente con configuración mínima usa defaults"""
        yaml_content = """
agents:
  MinimalAgent:
    description: "Agente mínimo"
    model: "test-model"
    system_prompt: "Prompt mínimo"
"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            loader = AgentConfigLoader(temp_path)
            agent = loader.get("MinimalAgent")

            assert agent.tools == []
            assert agent.required_permissions == []
            assert agent.timeout_seconds == 300
        finally:
            os.unlink(temp_path)


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

    def test_validador_documental_config(self):
        """ValidadorDocumental tiene configuración correcta"""
        config_path = Path(__file__).parent.parent.parent / "src" / "backoffice" / "config" / "agents.yaml"

        if not config_path.exists():
            pytest.skip("agents.yaml no existe todavía")

        loader = AgentConfigLoader(str(config_path))
        agent = loader.get("ValidadorDocumental")

        assert agent.description == "Valida documentación administrativa de expedientes"
        assert "consultar_expediente" in agent.tools
        assert "actualizar_datos" in agent.tools
        assert "añadir_anotacion" in agent.tools
        assert agent.timeout_seconds == 300

    def test_all_agents_have_required_fields(self):
        """Todos los agentes tienen campos requeridos"""
        config_path = Path(__file__).parent.parent.parent / "src" / "backoffice" / "config" / "agents.yaml"

        if not config_path.exists():
            pytest.skip("agents.yaml no existe todavía")

        loader = AgentConfigLoader(str(config_path))

        for agent in loader.list_agents():
            assert agent.name, f"Agente sin nombre"
            assert agent.description, f"{agent.name}: sin descripción"
            assert agent.model, f"{agent.name}: sin modelo"
            assert agent.system_prompt, f"{agent.name}: sin system_prompt"
            assert len(agent.tools) > 0, f"{agent.name}: sin herramientas"
            assert agent.timeout_seconds > 0, f"{agent.name}: timeout inválido"
