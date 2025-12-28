# Paso 6.1: Primer Agente Real con CrewAI + Anthropic

## Objetivo

Implementar el agente más simple posible utilizando CrewAI con Anthropic Claude como proveedor LLM, accediendo a los datos del expediente mediante MCP y con configuración externalizada en YAML.

## Contexto del Proyecto

### Estado Actual

- **Sistema de agentes mock**: `src/backoffice/agents/` con clase base `AgentMock`
- **AgentExecutor**: Orquestador principal en `src/backoffice/executor.py`
- **MCP Registry**: Sistema multi-MCP para acceso a herramientas (consultar_expediente, actualizar_datos, etc.)
- **Tests**: 119 tests (100% PASS)
- **ANTHROPIC_API_KEY**: Ya configurada en `.env.example`

### Herramientas MCP Disponibles

El MCP de Expedientes (`mcp_servers.yaml`) expone estas herramientas:

| Herramienta | Descripción |
|-------------|-------------|
| `consultar_expediente` | Obtiene datos completos del expediente |
| `actualizar_datos` | Modifica campos del expediente |
| `añadir_anotacion` | Añade nota al historial |

**IMPORTANTE**: El agente real DEBE acceder a los datos del expediente mediante MCP, igual que los agentes mock actuales.

### Arquitectura Actual de Agentes

```text
AgentExecutor.execute()
    |
    v
1. Validar JWT
2. Cargar configuración MCP
3. Crear MCPClientRegistry
4. Instanciar agente: agent_class(expediente_id, tarea_id, run_id, mcp_registry, logger)
5. Ejecutar: await agent.execute()
6. Retornar AgentExecutionResult
```

### Interfaz que DEBE Mantenerse

```python
# src/backoffice/agents/base.py
class AgentMock(ABC):
    def __init__(
        self,
        expediente_id: str,
        tarea_id: str,
        run_id: str,
        mcp_registry: MCPClientRegistry,
        logger: AuditLogger
    ):
        ...

    @abstractmethod
    async def execute(self) -> Dict[str, Any]:
        """Debe retornar dict con 'completado', 'mensaje', 'datos_actualizados'"""
        pass

    def _track_tool_use(self, tool_name: str): ...
    def get_tools_used(self) -> List[str]: ...
```

---

## Plan de Implementación

### Fase 1: Preparación del Entorno

#### 1.1 Instalar Dependencias

```bash
# Añadir CrewAI con soporte para Anthropic
pip install crewai

# Verificar que LiteLLM está incluido (CrewAI lo usa internamente)
pip list | grep -i litellm
```

#### 1.2 Actualizar requirements.txt

Añadir las siguientes dependencias:

```text
crewai>=0.70.0
```

**Nota**: CrewAI v0.65.2+ ya no depende de LangChain, usa LiteLLM directamente.

---

### Fase 2: Configuración YAML de Agentes

#### 2.1 Crear Archivo de Configuración

Crear archivo: `src/backoffice/config/agents.yaml`

```yaml
# Configuración de Agentes IA
# Cada agente define su comportamiento, modelo LLM y herramientas MCP

agents:
  # Primer agente real con CrewAI
  ClasificadorExpediente:
    type: crewai  # crewai | langgraph | mock
    enabled: true

    # Configuración del LLM
    llm:
      provider: anthropic
      model: claude-3-5-sonnet-20241022
      max_tokens: 4096
      temperature: 0.1  # Bajo para tareas estructuradas

    # Definición del agente CrewAI
    agent:
      role: "Clasificador de Expedientes Administrativos"
      goal: "Clasificar expedientes según tipo y urgencia basándose en los datos obtenidos"
      backstory: |
        Eres un experto en gestión documental de la administración pública española.
        Tu trabajo es analizar la información de expedientes y clasificarlos según:
        - Tipo: subvención, licencia, queja, recurso, otro
        - Urgencia: alta, media, baja
        Siempre consultas los datos reales del expediente antes de clasificar.
      verbose: true
      allow_delegation: false

    # Tarea a ejecutar
    task:
      description: |
        Analiza el expediente {expediente_id} para la tarea BPMN {tarea_id}.

        PASOS OBLIGATORIOS:
        1. Usa la herramienta 'consultar_expediente' para obtener los datos
        2. Analiza el tipo de trámite y documentación
        3. Determina la clasificación y urgencia
        4. Justifica tu decisión
      expected_output: |
        JSON con formato:
        {
          "tipo_expediente": "subvención|licencia|queja|recurso|otro",
          "urgencia": "alta|media|baja",
          "justificacion": "Explicación basada en los datos del expediente"
        }

    # Herramientas MCP que puede usar el agente
    mcp_tools:
      - consultar_expediente  # Lectura de datos
      # No incluimos actualizar_datos ni añadir_anotacion para este agente simple

  # Agentes mock existentes (mantienen compatibilidad)
  ValidadorDocumental:
    type: mock
    enabled: true
    mcp_tools:
      - consultar_expediente
      - actualizar_datos
      - añadir_anotacion

  AnalizadorSubvencion:
    type: mock
    enabled: true
    mcp_tools:
      - consultar_expediente
      - actualizar_datos
      - añadir_anotacion

  GeneradorInforme:
    type: mock
    enabled: true
    mcp_tools:
      - consultar_expediente
      - actualizar_datos
      - añadir_anotacion
```

#### 2.2 Loader de Configuración de Agentes

Crear archivo: `src/backoffice/config/agent_config_loader.py`

```python
"""
Carga configuración de agentes desde YAML.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """Configuración del modelo LLM."""
    provider: str
    model: str
    max_tokens: int = 4096
    temperature: float = 0.1


@dataclass
class AgentCrewAIConfig:
    """Configuración específica de CrewAI."""
    role: str
    goal: str
    backstory: str
    verbose: bool = True
    allow_delegation: bool = False


@dataclass
class TaskConfig:
    """Configuración de la tarea."""
    description: str
    expected_output: str


@dataclass
class AgentConfig:
    """Configuración completa de un agente."""
    name: str
    type: str  # crewai | langgraph | mock
    enabled: bool
    llm: Optional[LLMConfig]
    agent: Optional[AgentCrewAIConfig]
    task: Optional[TaskConfig]
    mcp_tools: list[str]


class AgentConfigLoader:
    """Carga y parsea configuración de agentes."""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = os.getenv(
                "AGENTS_CONFIG_PATH",
                "src/backoffice/config/agents.yaml"
            )
        self.config_path = Path(config_path)
        self._config: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, AgentConfig]:
        """Carga todos los agentes configurados."""
        if self._config is None:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)

        agents = {}
        for name, cfg in self._config.get('agents', {}).items():
            agents[name] = self._parse_agent(name, cfg)

        return agents

    def get_agent(self, name: str) -> AgentConfig:
        """Obtiene configuración de un agente específico."""
        agents = self.load()
        if name not in agents:
            available = list(agents.keys())
            raise KeyError(f"Agente '{name}' no encontrado. Disponibles: {available}")
        return agents[name]

    def _parse_agent(self, name: str, cfg: Dict[str, Any]) -> AgentConfig:
        """Parsea configuración de un agente."""
        llm_cfg = None
        if 'llm' in cfg:
            llm_cfg = LLMConfig(**cfg['llm'])

        agent_cfg = None
        if 'agent' in cfg:
            agent_cfg = AgentCrewAIConfig(**cfg['agent'])

        task_cfg = None
        if 'task' in cfg:
            task_cfg = TaskConfig(**cfg['task'])

        return AgentConfig(
            name=name,
            type=cfg.get('type', 'mock'),
            enabled=cfg.get('enabled', True),
            llm=llm_cfg,
            agent=agent_cfg,
            task=task_cfg,
            mcp_tools=cfg.get('mcp_tools', [])
        )
```

---

### Fase 3: Wrapper de Tools MCP para CrewAI

#### 3.1 Crear MCPToolWrapper

CrewAI usa su propio sistema de Tools. Necesitamos un wrapper que conecte las herramientas MCP con CrewAI.

Crear archivo: `src/backoffice/agents/mcp_tool_wrapper.py`

```python
"""
Wrapper para exponer herramientas MCP como Tools de CrewAI.

Permite que los agentes CrewAI usen las herramientas del MCPClientRegistry.
"""
import json
import asyncio
from typing import Any, Callable, List
from crewai.tools import BaseTool
from pydantic import Field

from ..mcp.registry import MCPClientRegistry
from ..logging.audit_logger import AuditLogger


class MCPTool(BaseTool):
    """
    Tool de CrewAI que ejecuta una herramienta MCP.
    """
    name: str = Field(description="Nombre de la herramienta")
    description: str = Field(description="Descripción de la herramienta")
    mcp_registry: Any = Field(exclude=True)
    logger: Any = Field(exclude=True)
    tool_tracker: Any = Field(exclude=True)

    def _run(self, **kwargs) -> str:
        """
        Ejecuta la herramienta MCP de forma síncrona.

        CrewAI es síncrono, así que envolvemos la llamada async.
        """
        try:
            # Obtener o crear event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Ejecutar llamada MCP
            result = loop.run_until_complete(
                self.mcp_registry.call_tool(self.name, kwargs)
            )

            # Registrar uso de herramienta
            if self.tool_tracker:
                self.tool_tracker(self.name)

            # Loguear resultado
            self.logger.log(f"MCP Tool '{self.name}' ejecutada correctamente")

            # Extraer contenido del resultado MCP
            content = result.get("content", [{}])
            if content and isinstance(content, list):
                text = content[0].get("text", "{}")
                return text

            return json.dumps(result)

        except Exception as e:
            self.logger.error(f"Error en MCP Tool '{self.name}': {str(e)}")
            return json.dumps({"error": str(e)})


class MCPToolFactory:
    """
    Factory para crear Tools de CrewAI desde el MCPClientRegistry.
    """

    # Descripciones de herramientas conocidas
    TOOL_DESCRIPTIONS = {
        "consultar_expediente": (
            "Consulta los datos completos de un expediente. "
            "Requiere parámetro: expediente_id (str). "
            "Retorna JSON con datos del expediente incluyendo documentos, "
            "estado, fechas y metadatos."
        ),
        "actualizar_datos": (
            "Actualiza un campo específico del expediente. "
            "Requiere: expediente_id (str), campo (str), valor (any). "
            "Retorna confirmación de la actualización."
        ),
        "añadir_anotacion": (
            "Añade una anotación al historial del expediente. "
            "Requiere: expediente_id (str), texto (str). "
            "Retorna confirmación con timestamp."
        ),
    }

    @classmethod
    def create_tools(
        cls,
        tool_names: List[str],
        mcp_registry: MCPClientRegistry,
        logger: AuditLogger,
        tool_tracker: Callable[[str], None]
    ) -> List[MCPTool]:
        """
        Crea lista de Tools de CrewAI para las herramientas MCP especificadas.

        Args:
            tool_names: Lista de nombres de herramientas MCP a exponer
            mcp_registry: Registry de clientes MCP
            logger: Logger de auditoría
            tool_tracker: Callback para registrar uso de herramientas

        Returns:
            Lista de MCPTool configuradas
        """
        tools = []

        for name in tool_names:
            description = cls.TOOL_DESCRIPTIONS.get(
                name,
                f"Herramienta MCP: {name}"
            )

            tool = MCPTool(
                name=name,
                description=description,
                mcp_registry=mcp_registry,
                logger=logger,
                tool_tracker=tool_tracker
            )
            tools.append(tool)

        return tools
```

---

### Fase 4: Clase Base para Agentes Reales

#### 4.1 Nueva Clase Base `AgentReal`

Crear archivo: `src/backoffice/agents/base_real.py`

```python
"""
Clase base para agentes reales usando CrewAI.

Mantiene compatibilidad con AgentMock mientras usa CrewAI internamente.
Los agentes acceden a datos del expediente mediante herramientas MCP.
"""
import asyncio
import json
from abc import ABC
from typing import Dict, Any, List

from crewai import Agent, Task, Crew, LLM

from ..mcp.registry import MCPClientRegistry
from ..logging.audit_logger import AuditLogger
from ..settings import get_settings
from ..config.agent_config_loader import AgentConfigLoader, AgentConfig
from .mcp_tool_wrapper import MCPToolFactory


class AgentReal(ABC):
    """
    Clase base para agentes reales con CrewAI.

    Implementa la misma interfaz que AgentMock para mantener
    compatibilidad con AgentExecutor.

    IMPORTANTE: Accede a datos del expediente mediante MCP tools,
    NO directamente. El LLM razona sobre los datos obtenidos.
    """

    def __init__(
        self,
        expediente_id: str,
        tarea_id: str,
        run_id: str,
        mcp_registry: MCPClientRegistry,
        logger: AuditLogger,
        config: AgentConfig = None
    ):
        self.expediente_id = expediente_id
        self.tarea_id = tarea_id
        self.run_id = run_id
        self.mcp_registry = mcp_registry
        self.logger = logger
        self._tools_used: List[str] = []

        # Cargar configuración si no se proporciona
        if config is None:
            loader = AgentConfigLoader()
            config = loader.get_agent(self.__class__.__name__)
        self.config = config

        # Configurar LLM de Anthropic
        settings = get_settings()
        self.llm = self._create_llm(settings)

        # Crear tools MCP para CrewAI
        self.mcp_tools = MCPToolFactory.create_tools(
            tool_names=config.mcp_tools,
            mcp_registry=mcp_registry,
            logger=logger,
            tool_tracker=self._track_tool_use
        )

    def _create_llm(self, settings) -> LLM:
        """Crea instancia del LLM según configuración."""
        llm_config = self.config.llm

        # Construir model string en formato LiteLLM
        model = f"{llm_config.provider}/{llm_config.model}"

        return LLM(
            model=model,
            api_key=settings.anthropic_api_key,
            max_tokens=llm_config.max_tokens,
            temperature=llm_config.temperature
        )

    def _format_task_description(self) -> str:
        """Formatea la descripción de la tarea con variables."""
        description = self.config.task.description
        return description.format(
            expediente_id=self.expediente_id,
            tarea_id=self.tarea_id,
            run_id=self.run_id
        )

    async def execute(self) -> Dict[str, Any]:
        """
        Ejecuta el agente usando CrewAI con acceso a MCP.

        El agente usará las herramientas MCP configuradas para
        acceder a los datos del expediente.
        """
        self.logger.log(
            f"Iniciando agente CrewAI '{self.config.name}' "
            f"para expediente {self.expediente_id}"
        )
        self.logger.log(f"Herramientas MCP disponibles: {self.config.mcp_tools}")

        try:
            # Crear agente CrewAI con configuración YAML
            agent_cfg = self.config.agent
            agent = Agent(
                role=agent_cfg.role,
                goal=agent_cfg.goal.format(expediente_id=self.expediente_id),
                backstory=agent_cfg.backstory,
                llm=self.llm,
                tools=self.mcp_tools,  # Tools MCP disponibles
                verbose=agent_cfg.verbose,
                allow_delegation=agent_cfg.allow_delegation
            )

            # Crear tarea con descripción formateada
            task = Task(
                description=self._format_task_description(),
                expected_output=self.config.task.expected_output,
                agent=agent
            )

            # Crear y ejecutar crew
            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=True
            )

            # Ejecutar (CrewAI es síncrono, lo envolvemos)
            self.logger.log("Ejecutando crew...")
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, crew.kickoff)

            self.logger.log(f"Agente completado exitosamente")

            # Intentar parsear resultado como JSON
            resultado_parseado = self._parse_result(str(result))

            return {
                "completado": True,
                "mensaje": str(result),
                "datos_actualizados": resultado_parseado
            }

        except Exception as e:
            self.logger.error(f"Error en agente CrewAI: {str(e)}")
            return {
                "completado": False,
                "mensaje": f"Error: {str(e)}",
                "datos_actualizados": {}
            }

    def _parse_result(self, result: str) -> Dict[str, Any]:
        """Intenta extraer JSON del resultado."""
        try:
            # Buscar JSON en el resultado
            import re
            json_match = re.search(r'\{[^{}]*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass
        return {}

    def _track_tool_use(self, tool_name: str):
        """Registra el uso de una herramienta."""
        if tool_name not in self._tools_used:
            self._tools_used.append(tool_name)
            self.logger.log(f"Herramienta usada: {tool_name}")

    def get_tools_used(self) -> List[str]:
        """Retorna lista de herramientas usadas."""
        return self._tools_used.copy()
```

---

### Fase 5: Implementar Primer Agente Real

#### 5.1 Agente ClasificadorExpediente

Crear archivo: `src/backoffice/agents/clasificador_expediente.py`

```python
"""
Primer agente real: Clasificador de Expedientes.

Clasifica un expediente según su tipo y urgencia usando IA,
accediendo a los datos reales del expediente mediante MCP.
"""
from .base_real import AgentReal


class ClasificadorExpediente(AgentReal):
    """
    Agente que clasifica expedientes usando CrewAI + Anthropic.

    Flujo de ejecución:
    1. Usa herramienta MCP 'consultar_expediente' para obtener datos
    2. LLM analiza los datos y determina clasificación
    3. Retorna clasificación con justificación

    La configuración (role, goal, backstory, task) se carga desde
    src/backoffice/config/agents.yaml
    """
    pass  # Toda la lógica está en AgentReal + configuración YAML
```

**Nota**: El agente es muy simple porque toda la configuración está externalizada en YAML. La clase solo existe para tener un nombre registrable en el registry.

---

### Fase 6: Actualizar Configuración

#### 6.1 Añadir ANTHROPIC_API_KEY a Settings

Modificar `src/backoffice/settings.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... campos existentes ...

    # Anthropic
    anthropic_api_key: str = ""

    # Configuración de agentes
    agents_config_path: str = "src/backoffice/config/agents.yaml"

    class Config:
        env_file = ".env"
        extra = "ignore"
```

#### 6.2 Actualizar Registry de Agentes

Modificar `src/backoffice/agents/registry.py`:

```python
from typing import Dict, Type, Union
from .base import AgentMock
from .base_real import AgentReal
from .validador_documental import ValidadorDocumental
from .analizador_subvencion import AnalizadorSubvencion
from .generador_informe import GeneradorInforme
from .clasificador_expediente import ClasificadorExpediente

# Tipo unificado para agentes mock y reales
AgentType = Union[Type[AgentMock], Type[AgentReal]]

AGENT_REGISTRY: Dict[str, AgentType] = {
    # Agentes mock existentes
    "ValidadorDocumental": ValidadorDocumental,
    "AnalizadorSubvencion": AnalizadorSubvencion,
    "GeneradorInforme": GeneradorInforme,
    # Agentes reales con CrewAI
    "ClasificadorExpediente": ClasificadorExpediente,
}
```

#### 6.3 Actualizar .env.example

Añadir variable de configuración:

```bash
# Configuración de Agentes IA
AGENTS_CONFIG_PATH=src/backoffice/config/agents.yaml
```

---

### Fase 7: Tests

#### 7.1 Test Unitario del Wrapper MCP

Crear archivo: `tests/test_backoffice/test_mcp_tool_wrapper.py`

```python
"""Tests para MCPToolWrapper."""
import pytest
from unittest.mock import MagicMock, AsyncMock
import json

from src.backoffice.agents.mcp_tool_wrapper import MCPTool, MCPToolFactory


class TestMCPTool:
    """Tests para MCPTool."""

    def test_run_calls_mcp_registry(self):
        """Test que _run llama al mcp_registry correctamente."""
        # Preparar mocks
        mock_registry = MagicMock()
        mock_registry.call_tool = AsyncMock(return_value={
            "content": [{"text": '{"estado": "ok"}'}]
        })
        mock_logger = MagicMock()
        tracker_calls = []

        tool = MCPTool(
            name="consultar_expediente",
            description="Test tool",
            mcp_registry=mock_registry,
            logger=mock_logger,
            tool_tracker=lambda x: tracker_calls.append(x)
        )

        # Ejecutar
        result = tool._run(expediente_id="EXP-001")

        # Verificar
        mock_registry.call_tool.assert_called_once_with(
            "consultar_expediente",
            {"expediente_id": "EXP-001"}
        )
        assert "estado" in result
        assert "consultar_expediente" in tracker_calls


class TestMCPToolFactory:
    """Tests para MCPToolFactory."""

    def test_create_tools_returns_correct_count(self):
        """Test que create_tools retorna el número correcto de tools."""
        mock_registry = MagicMock()
        mock_logger = MagicMock()

        tools = MCPToolFactory.create_tools(
            tool_names=["consultar_expediente", "actualizar_datos"],
            mcp_registry=mock_registry,
            logger=mock_logger,
            tool_tracker=lambda x: None
        )

        assert len(tools) == 2
        assert tools[0].name == "consultar_expediente"
        assert tools[1].name == "actualizar_datos"

    def test_tools_have_descriptions(self):
        """Test que las tools tienen descripciones."""
        mock_registry = MagicMock()
        mock_logger = MagicMock()

        tools = MCPToolFactory.create_tools(
            tool_names=["consultar_expediente"],
            mcp_registry=mock_registry,
            logger=mock_logger,
            tool_tracker=lambda x: None
        )

        assert "expediente" in tools[0].description.lower()
```

#### 7.2 Test del AgentConfigLoader

Crear archivo: `tests/test_backoffice/test_agent_config_loader.py`

```python
"""Tests para AgentConfigLoader."""
import pytest
import tempfile
import yaml
from pathlib import Path

from src.backoffice.config.agent_config_loader import (
    AgentConfigLoader,
    AgentConfig,
    LLMConfig
)


@pytest.fixture
def sample_config():
    """Configuración de ejemplo."""
    return {
        "agents": {
            "TestAgent": {
                "type": "crewai",
                "enabled": True,
                "llm": {
                    "provider": "anthropic",
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 4096,
                    "temperature": 0.1
                },
                "agent": {
                    "role": "Test Role",
                    "goal": "Test Goal",
                    "backstory": "Test Backstory"
                },
                "task": {
                    "description": "Test task for {expediente_id}",
                    "expected_output": "JSON output"
                },
                "mcp_tools": ["consultar_expediente"]
            }
        }
    }


@pytest.fixture
def config_file(sample_config):
    """Crea archivo temporal de configuración."""
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.yaml',
        delete=False
    ) as f:
        yaml.dump(sample_config, f)
        return f.name


class TestAgentConfigLoader:
    """Tests para AgentConfigLoader."""

    def test_load_agents(self, config_file):
        """Test carga de agentes."""
        loader = AgentConfigLoader(config_file)
        agents = loader.load()

        assert "TestAgent" in agents
        assert agents["TestAgent"].type == "crewai"
        assert agents["TestAgent"].enabled is True

    def test_get_agent(self, config_file):
        """Test obtener agente específico."""
        loader = AgentConfigLoader(config_file)
        agent = loader.get_agent("TestAgent")

        assert agent.name == "TestAgent"
        assert agent.llm.provider == "anthropic"
        assert agent.llm.model == "claude-3-5-sonnet-20241022"

    def test_get_agent_not_found(self, config_file):
        """Test error cuando agente no existe."""
        loader = AgentConfigLoader(config_file)

        with pytest.raises(KeyError) as exc_info:
            loader.get_agent("NonExistent")

        assert "NonExistent" in str(exc_info.value)

    def test_mcp_tools_loaded(self, config_file):
        """Test que las herramientas MCP se cargan."""
        loader = AgentConfigLoader(config_file)
        agent = loader.get_agent("TestAgent")

        assert "consultar_expediente" in agent.mcp_tools
```

#### 7.3 Test de Integración del Agente

Crear archivo: `tests/test_backoffice/test_clasificador_expediente.py`

```python
"""Tests para ClasificadorExpediente."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import json

from src.backoffice.agents.clasificador_expediente import ClasificadorExpediente


@pytest.fixture
def mock_mcp_registry():
    """Mock del MCPClientRegistry."""
    registry = MagicMock()
    registry.call_tool = AsyncMock(return_value={
        "content": [{
            "text": json.dumps({
                "id": "EXP-2024-001",
                "tipo": "subvencion",
                "estado": "en_tramite",
                "documentos": [
                    {"tipo": "SOLICITUD", "nombre": "solicitud.pdf"},
                    {"tipo": "IDENTIFICACION", "nombre": "dni.pdf"}
                ]
            })
        }]
    })
    return registry


@pytest.fixture
def mock_logger():
    """Mock del AuditLogger."""
    logger = MagicMock()
    logger.log = MagicMock()
    logger.error = MagicMock()
    return logger


@pytest.fixture
def mock_agent_config():
    """Configuración mock del agente."""
    from src.backoffice.config.agent_config_loader import (
        AgentConfig, LLMConfig, AgentCrewAIConfig, TaskConfig
    )
    return AgentConfig(
        name="ClasificadorExpediente",
        type="crewai",
        enabled=True,
        llm=LLMConfig(
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            temperature=0.1
        ),
        agent=AgentCrewAIConfig(
            role="Clasificador",
            goal="Clasificar expediente {expediente_id}",
            backstory="Experto en clasificación"
        ),
        task=TaskConfig(
            description="Clasifica {expediente_id}",
            expected_output="JSON con clasificación"
        ),
        mcp_tools=["consultar_expediente"]
    )


class TestClasificadorExpediente:
    """Tests para el clasificador de expedientes."""

    def test_init_loads_config(
        self,
        mock_mcp_registry,
        mock_logger,
        mock_agent_config
    ):
        """Test inicialización carga configuración."""
        with patch(
            'src.backoffice.agents.base_real.get_settings'
        ) as mock_settings:
            mock_settings.return_value.anthropic_api_key = "test-key"

            with patch(
                'src.backoffice.agents.base_real.AgentConfigLoader'
            ) as mock_loader:
                mock_loader.return_value.get_agent.return_value = mock_agent_config

                agent = ClasificadorExpediente(
                    expediente_id="EXP-2024-001",
                    tarea_id="TASK-001",
                    run_id="RUN-001",
                    mcp_registry=mock_mcp_registry,
                    logger=mock_logger
                )

                assert agent.expediente_id == "EXP-2024-001"
                assert len(agent.mcp_tools) == 1

    def test_mcp_tools_created(
        self,
        mock_mcp_registry,
        mock_logger,
        mock_agent_config
    ):
        """Test que se crean las herramientas MCP."""
        with patch(
            'src.backoffice.agents.base_real.get_settings'
        ) as mock_settings:
            mock_settings.return_value.anthropic_api_key = "test-key"

            agent = ClasificadorExpediente(
                expediente_id="EXP-2024-001",
                tarea_id="TASK-001",
                run_id="RUN-001",
                mcp_registry=mock_mcp_registry,
                logger=mock_logger,
                config=mock_agent_config
            )

            # Verificar que hay una tool MCP
            assert len(agent.mcp_tools) == 1
            assert agent.mcp_tools[0].name == "consultar_expediente"


@pytest.mark.integration
class TestClasificadorExpedienteIntegration:
    """Tests de integración (requieren API key real)."""

    @pytest.mark.skipif(
        True,  # Cambiar a False para ejecutar con API real
        reason="Requiere ANTHROPIC_API_KEY y CrewAI instalado"
    )
    async def test_execute_with_real_llm(
        self,
        mock_mcp_registry,
        mock_logger,
        mock_agent_config
    ):
        """Test ejecución real con LLM."""
        import os
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY no configurada")

        agent = ClasificadorExpediente(
            expediente_id="EXP-2024-001",
            tarea_id="TASK-001",
            run_id="RUN-001",
            mcp_registry=mock_mcp_registry,
            logger=mock_logger,
            config=mock_agent_config
        )

        result = await agent.execute()

        assert "completado" in result
        assert "mensaje" in result
        # Verificar que usó la herramienta MCP
        assert "consultar_expediente" in agent.get_tools_used()
```

---

### Fase 8: Documentación

#### 8.1 Crear Nota Zettelkasten

Crear `doc/060-agentes-crewai.md`:

```markdown
# Agentes Reales con CrewAI

## Introducción

A partir del paso 6.1, el sistema soporta agentes reales usando CrewAI
con Anthropic Claude como proveedor LLM.

## Acceso a Datos

Los agentes reales acceden a los datos del expediente mediante **herramientas MCP**,
igual que los agentes mock. El LLM no tiene acceso directo a datos; debe usar
las tools configuradas.

## Arquitectura

```text
AgentReal (base_real.py)
    |
    +-- MCPToolFactory --> MCPTool (wrapper)
    |                          |
    |                          v
    +-- CrewAI Agent ----> MCPClientRegistry --> MCP Server
```

## Configuración YAML

Archivo: `src/backoffice/config/agents.yaml`

Define:

- Tipo de agente (crewai, langgraph, mock)
- Configuración LLM (provider, model, tokens)
- Definición del agente (role, goal, backstory)
- Tarea a ejecutar (description, expected_output)
- Herramientas MCP permitidas

## Relaciones

- Ver: [Propuesta general](030-propuesta-agentes.md)
- Ver: [Configuración](031-configuracion-agente.md)
- Ver: [MCP Registry](mcp-registry.md)
```

---

## Consideraciones Importantes

### Acceso a Datos via MCP

| Aspecto | Detalle |
|---------|---------|
| **Herramienta principal** | `consultar_expediente` |
| **Formato respuesta** | JSON en `content[0].text` |
| **Wrapper** | `MCPTool` convierte async a sync |
| **Tracking** | Automático via `_track_tool_use` |

### Configuración YAML vs Código

| En YAML | En Código |
|---------|-----------|
| role, goal, backstory | Nada (hereda de AgentReal) |
| task description | Variables: {expediente_id}, {tarea_id} |
| mcp_tools permitidas | MCPToolFactory crea wrappers |
| llm config | LLM se instancia automáticamente |

### Compatibilidad Hacia Atrás

1. **Interfaz Idéntica**: `AgentReal` implementa misma interfaz que `AgentMock`
2. **AgentExecutor sin cambios**: El orquestador funciona igual con ambos tipos
3. **Registry unificado**: Ambos tipos de agentes en el mismo registro

### Limitaciones de CrewAI

1. **Ejecución Síncrona**: CrewAI es síncrono, se envuelve con `run_in_executor`
2. **Tools síncronas**: MCPTool usa `run_until_complete` para llamadas async
3. **Sin memoria persistente**: Cada ejecución es independiente

---

## Checklist de Implementación

- [ ] Instalar dependencias: `pip install crewai`
- [ ] Actualizar `requirements.txt`
- [ ] Crear `src/backoffice/config/agents.yaml`
- [ ] Crear `src/backoffice/config/agent_config_loader.py`
- [ ] Crear `src/backoffice/agents/mcp_tool_wrapper.py`
- [ ] Crear `src/backoffice/agents/base_real.py`
- [ ] Crear `src/backoffice/agents/clasificador_expediente.py`
- [ ] Añadir `anthropic_api_key` y `agents_config_path` a `settings.py`
- [ ] Actualizar `registry.py` con nuevo agente
- [ ] Actualizar `.env.example`
- [ ] Crear tests unitarios (wrapper, config loader)
- [ ] Crear tests del agente
- [ ] Crear documentación Zettelkasten
- [ ] Ejecutar suite completa de tests: `./run-tests.sh`

---

## Estructura de Archivos Final

```text
src/backoffice/
├── config/
│   ├── mcp_servers.yaml      # (existente)
│   ├── agents.yaml           # NUEVO: configuración de agentes
│   └── agent_config_loader.py # NUEVO: loader de configuración
├── agents/
│   ├── base.py               # (existente) AgentMock
│   ├── base_real.py          # NUEVO: AgentReal con CrewAI
│   ├── mcp_tool_wrapper.py   # NUEVO: wrapper MCP -> CrewAI Tool
│   ├── clasificador_expediente.py  # NUEVO: primer agente real
│   └── registry.py           # (modificado) incluye nuevo agente
└── settings.py               # (modificado) nuevas variables
```

---

## Próximos Pasos (Paso 6.2+)

1. **Agentes con escritura**: Añadir `actualizar_datos` y `añadir_anotacion`
2. **Multi-agente**: Crews con varios agentes colaborando
3. **LangGraph alternativo**: Implementar misma interfaz con LangGraph
4. **Validación de permisos**: Verificar que agente solo usa tools permitidas

---

## Referencias

- [CrewAI Quickstart](https://docs.crewai.com/en/quickstart)
- [CrewAI LLM Configuration](https://docs.crewai.com/en/concepts/llms)
- [CrewAI Tools](https://docs.crewai.com/en/concepts/tools)
- [LiteLLM Anthropic Provider](https://docs.litellm.ai/docs/providers/anthropic)

---

## Notas Técnicas

### Versión de Python

CrewAI requiere Python >= 3.10 y < 3.14. Verificar compatibilidad:

```bash
python --version  # Debe ser 3.10, 3.11, 3.12 o 3.13
```

### Issue Conocido: Stop Sequences

En CrewAI 1.2.0 hay un bug donde las stop sequences no se envían a Anthropic.
Esto puede causar respuestas muy largas. Monitorear consumo de tokens.

Workaround: Limitar `max_tokens` y ser específico en `expected_output`.

### Async vs Sync

CrewAI es completamente síncrono. Para integrarlo con nuestro sistema async:

```python
# En AgentReal.execute()
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, crew.kickoff)

# En MCPTool._run()
result = loop.run_until_complete(self.mcp_registry.call_tool(...))
```
