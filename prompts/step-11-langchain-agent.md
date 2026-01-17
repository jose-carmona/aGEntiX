# Step 11: Agentes con LangChain/LangGraph

## Contexto

Actualmente el sistema soporta agentes CrewAI (tipo `crewai` en agents.yaml). Queremos añadir soporte para agentes LangChain/LangGraph para tener flexibilidad y poder comparar frameworks.

### Arquitectura Actual

```
src/backoffice/agents/
├── base_real.py              # Clase base para CrewAI (AgentReal)
├── registry.py               # Registro de agentes disponibles
├── mcp_tool_wrapper.py       # Wrapper de tools MCP para CrewAI
├── clasificador_expediente.py
├── redactor_situacion.py
└── redactor_propuesta_resolucion.py
```

Los agentes CrewAI:
- Heredan de `AgentReal`
- Se configuran en `agents.yaml` con `type: crewai`
- Usan `MCPToolFactory` para crear tools compatibles con CrewAI
- Ejecutan vía `crew.kickoff()`

## Objetivo

Crear un agente **RedactorResolucion** usando LangChain/LangGraph que:
1. Se configure de igual modo que los agentes CrewAI (en agents.yaml)
2. Use las mismas herramientas MCP
3. Se ejecute con la misma interfaz (`execute() -> Dict`)
4. Genere un documento de "Resolución" basado en plantilla

### Flujo del RedactorResolucion

1. Consultar expediente para obtener tipo y datos
2. Obtener plantilla de Resolución del tipo de expediente
3. Buscar y leer la Propuesta de Resolución existente
4. Generar documento de Resolución rellenando la plantilla
5. Guardar documento en el expediente

---

## Plan de Implementación

### Paso 1: Crear clase base AgentLangGraph

Crear `src/backoffice/agents/base_langgraph.py`:

```python
# backoffice/agents/base_langgraph.py

"""
Clase base para agentes reales usando LangChain/LangGraph.

Los agentes acceden a datos del expediente mediante herramientas MCP.
"""

import asyncio
import json
import re
from abc import ABC
from typing import Dict, Any, List, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent

from ..mcp.registry import MCPClientRegistry
from ..logging.audit_logger import AuditLogger
from ..logging.crewai_log_processor import create_crewai_log_file, process_crewai_logs
from ..settings import get_settings
from ..config.agent_config_loader import AgentConfigLoader, AgentDefinition


class AgentLangGraph(ABC):
    """
    Clase base para agentes reales con LangGraph.

    Implementa la misma interfaz que AgentReal para compatibilidad.

    Atributos:
        expediente_id: ID del expediente a procesar
        tarea_id: ID de la tarea BPMN
        run_id: ID único de esta ejecución
        mcp_registry: Registry para acceso a herramientas MCP
        logger: Logger de auditoría
        config: Configuración del agente desde YAML
    """

    def __init__(
        self,
        expediente_id: str,
        tarea_id: str,
        run_id: str,
        mcp_registry: MCPClientRegistry,
        logger: AuditLogger,
        config: Optional[AgentDefinition] = None,
        additional_goal: Optional[str] = None
    ):
        """Inicializa el agente LangGraph."""
        self.expediente_id = expediente_id
        self.tarea_id = tarea_id
        self.run_id = run_id
        self.mcp_registry = mcp_registry
        self.logger = logger
        self.additional_goal = additional_goal or ""
        self._tools_used: List[str] = []

        # Cargar configuración si no se proporciona
        if config is None:
            loader = AgentConfigLoader()
            config = loader.get(self.__class__.__name__)
        self.config = config

        # Verificar que es un agente LangGraph
        if not config.is_langgraph:
            raise ValueError(
                f"Agente '{config.name}' no es de tipo 'langgraph'. "
                f"Tipo actual: {config.type}"
            )

        # Configurar LLM
        settings = get_settings()
        self.llm = self._create_llm(settings)

        # Crear tools MCP para LangChain
        self.tools = self._create_langchain_tools()

    def _create_llm(self, settings) -> ChatAnthropic:
        """Crea instancia del LLM Anthropic para LangChain."""
        llm_config = self.config.llm

        if llm_config is None:
            raise ValueError(
                f"Agente '{self.config.name}' no tiene configuración LLM"
            )

        return ChatAnthropic(
            model=llm_config.model,
            api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=llm_config.max_tokens,
            temperature=llm_config.temperature,
            timeout=llm_config.request_timeout,
            max_retries=llm_config.num_retries
        )

    def _create_langchain_tools(self) -> List[StructuredTool]:
        """
        Crea herramientas LangChain desde las tools MCP configuradas.

        Returns:
            Lista de StructuredTool para LangChain
        """
        from .mcp_tool_wrapper import MCPToolFactory

        # Reutilizar la lógica de MCPToolFactory pero adaptar para LangChain
        tools = []
        for tool_name in self.config.mcp_tools:
            tool = self._create_single_tool(tool_name)
            if tool:
                tools.append(tool)

        return tools

    def _create_single_tool(self, tool_name: str) -> Optional[StructuredTool]:
        """Crea una herramienta LangChain para un tool MCP."""
        # Obtener descripción del tool
        tool_info = self.mcp_registry.get_tool_info(tool_name)
        if not tool_info:
            self.logger.warning(f"Tool MCP no encontrada: {tool_name}")
            return None

        description = tool_info.get("description", f"Herramienta MCP: {tool_name}")
        schema = tool_info.get("inputSchema", {})

        def make_tool_func(name: str):
            """Crea función de ejecución para el tool."""
            def tool_func(**kwargs) -> str:
                self._track_tool_use(name)
                self.logger.log(
                    f"Ejecutando tool MCP: {name}",
                    metadata={"tool": name, "args": kwargs}
                )

                try:
                    # Llamar al MCP de forma síncrona
                    loop = asyncio.get_event_loop()
                    result = loop.run_until_complete(
                        self.mcp_registry.call_tool(name, kwargs)
                    )
                    return json.dumps(result, ensure_ascii=False)
                except Exception as e:
                    error_msg = f"Error en tool {name}: {str(e)}"
                    self.logger.error(error_msg)
                    return json.dumps({"error": error_msg})

            return tool_func

        return StructuredTool.from_function(
            func=make_tool_func(tool_name),
            name=tool_name,
            description=description
        )

    def _format_template(self, template: str) -> str:
        """Formatea un template con las variables del contexto."""
        return template.format(
            expediente_id=self.expediente_id,
            tarea_id=self.tarea_id,
            run_id=self.run_id,
            additional_goal=self.additional_goal
        )

    async def execute(self) -> Dict[str, Any]:
        """
        Ejecuta el agente usando LangGraph.

        Returns:
            Dict con 'completado', 'mensaje', 'datos_actualizados'
        """
        self.logger.log(
            f"Iniciando agente LangGraph '{self.config.name}' "
            f"para expediente {self.expediente_id}"
        )
        self.logger.log(f"Herramientas MCP disponibles: {self.config.mcp_tools}")

        # Crear archivo temporal para logs
        log_file = create_crewai_log_file(self.run_id)

        try:
            # Verificar configuración LangGraph
            if not self.config.langgraph_config:
                raise ValueError("Configuración 'langgraph_config' no encontrada")

            lg_cfg = self.config.langgraph_config

            # Crear el agente ReAct de LangGraph
            agent = create_react_agent(
                model=self.llm,
                tools=self.tools
            )

            # Preparar mensajes
            system_message = SystemMessage(content=lg_cfg.system_prompt)
            task_message = HumanMessage(
                content=self._format_template(lg_cfg.task_prompt)
            )

            # Ejecutar agente
            self.logger.log("Ejecutando agente LangGraph...")

            # LangGraph es síncrono, envolver en executor
            loop = asyncio.get_event_loop()

            def run_agent():
                return agent.invoke({
                    "messages": [system_message, task_message]
                })

            result = await loop.run_in_executor(None, run_agent)

            self.logger.log("Agente completado exitosamente")

            # Extraer respuesta final
            final_message = result["messages"][-1].content

            # Procesar logs
            entries = process_crewai_logs(log_file, self.logger, delete_after=False)
            self.logger.log(f"Procesadas {entries} entradas de logs")

            # Parsear resultado
            resultado_parseado = self._parse_result(final_message)

            return {
                "completado": True,
                "mensaje": final_message,
                "datos_actualizados": resultado_parseado
            }

        except Exception as e:
            process_crewai_logs(log_file, self.logger, delete_after=False)
            error_msg = f"Error en agente LangGraph: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e

        finally:
            if log_file.exists():
                try:
                    log_file.unlink()
                except OSError:
                    pass

    def _parse_result(self, result: str) -> Dict[str, Any]:
        """Intenta extraer JSON del resultado del agente."""
        try:
            json_match = re.search(r'\{[^{}]*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(result)
        except (json.JSONDecodeError, AttributeError):
            return {}

    def _track_tool_use(self, tool_name: str):
        """Registra el uso de una herramienta."""
        if tool_name not in self._tools_used:
            self._tools_used.append(tool_name)
            self.logger.log(f"Herramienta MCP usada: {tool_name}")

    def get_tools_used(self) -> List[str]:
        """Retorna lista de herramientas usadas."""
        return self._tools_used.copy()
```

### Paso 2: Actualizar AgentDefinition

Modificar `src/backoffice/config/agent_config_loader.py` para soportar LangGraph:

```python
# Añadir nuevo modelo de configuración
class LangGraphConfig(BaseModel):
    """Configuración específica del agente LangGraph."""
    system_prompt: str = Field(..., description="Prompt del sistema")
    task_prompt: str = Field(..., description="Prompt de la tarea")
    max_iterations: int = Field(10, description="Máximo de iteraciones del agente")


# En AgentDefinition, añadir:
class AgentDefinition(BaseModel):
    # ... campos existentes ...

    # Campos específicos de LangGraph (Paso 11)
    langgraph_config: Optional[LangGraphConfig] = Field(
        None,
        description="Configuración del agente LangGraph"
    )

    @property
    def is_langgraph(self) -> bool:
        """Indica si es un agente LangGraph."""
        return self.type == "langgraph"
```

### Paso 3: Definir RedactorResolucion en agents.yaml

Añadir al archivo `src/backoffice/config/agents.yaml`:

```yaml
  # ==========================================================================
  # RedactorResolucion - Genera Resoluciones con LangGraph (Paso 11)
  # ==========================================================================

  RedactorResolucion:
    type: langgraph
    enabled: true
    description: "Genera documento de Resolución formal basado en plantilla y propuesta"

    # Configuración del LLM
    llm:
      provider: anthropic
      model: claude-sonnet-4-5-20250929
      max_tokens: 4096
      temperature: 0.1
      num_retries: 5
      request_timeout: 180

    # Configuración específica de LangGraph
    langgraph_config:
      system_prompt: |
        Eres un experto jurídico-administrativo de la administración pública española,
        especializado en la redacción de Resoluciones administrativas.

        Tu trabajo es generar el documento de Resolución final para un expediente,
        basándote en:
        1. La plantilla oficial de Resolución del tipo de expediente
        2. La Propuesta de Resolución previamente generada
        3. Los datos del expediente

        Reglas:
        - Sustituye TODOS los campos {{campo}} por los valores correspondientes
        - El documento debe ser formalmente correcto y completo
        - Incluye fundamentación jurídica apropiada
        - Responde siempre en Español

      task_prompt: |
        Genera el documento de Resolución para el expediente {expediente_id}.

        PASOS:

        1. Consulta el expediente con 'consultar_expediente' (expediente_id="{expediente_id}")
           - Extrae: tipo de expediente, datos del solicitante, estado

        2. Obtén la plantilla de Resolución con 'obtener_doc_documentacion':
           - tipo_expediente = <tipo obtenido>
           - tipo_documento = "plantilla_resolucion"

        3. Lista documentos con 'listar_documentos' (expediente_id="{expediente_id}")
           - Busca documento tipo "PROPUESTA_RESOLUCION"

        4. Lee la propuesta con 'obtener_texto_documento':
           - expediente_id="{expediente_id}"
           - documento_id = <id de la propuesta>

        5. Genera la Resolución:
           - Usa la plantilla del paso 2
           - Incorpora datos de la propuesta del paso 4
           - Rellena TODOS los campos {{campo}}

        6. Guarda con 'crear_documento_desde_markdown':
           - expediente_id="{expediente_id}"
           - nombre="resolucion.md"
           - tipo="RESOLUCION"
           - texto_markdown=<documento generado>

        7. Registra con 'añadir_anotacion':
           - expediente_id="{expediente_id}"
           - texto="Generada Resolución automática"

        Responde con JSON:
        {{
          "completado": true,
          "documento_id": "ID del documento",
          "tipo_resolucion": "aprobacion|denegacion",
          "resumen": "Breve descripción"
        }}

        {additional_goal}

      max_iterations: 15

    # Herramientas MCP
    tools:
      - consultar_expediente
      - listar_documentos
      - obtener_texto_documento
      - crear_documento_desde_markdown
      - añadir_anotacion
      - obtener_doc_documentacion

    required_permissions:
      - consulta
      - gestion
      - documentacion:leer

    timeout_seconds: 600
```

### Paso 4: Crear el agente RedactorResolucion

Crear `src/backoffice/agents/redactor_resolucion.py`:

```python
# backoffice/agents/redactor_resolucion.py

"""
Agente Redactor de Resolución - Genera Resoluciones usando LangGraph.

Lee la plantilla de Resolución, la Propuesta de Resolución existente y
los datos del expediente para generar el documento de Resolución final.

Este es el primer agente implementado con LangGraph (Paso 11).
"""

from .base_langgraph import AgentLangGraph


class RedactorResolucion(AgentLangGraph):
    """
    Agente que genera Resoluciones usando LangGraph + Anthropic.

    Flujo de ejecución:
    1. Usa 'consultar_expediente' para obtener tipo y datos
    2. Usa 'obtener_doc_documentacion' para obtener plantilla de Resolución
    3. Usa 'listar_documentos' para buscar la Propuesta de Resolución
    4. Usa 'obtener_texto_documento' para leer la propuesta
    5. LLM genera la Resolución rellenando la plantilla
    6. Usa 'crear_documento_desde_markdown' para guardar
    7. Usa 'añadir_anotacion' para registrar la acción

    La configuración se carga desde src/backoffice/config/agents.yaml

    Ejemplo de uso:
        agent = RedactorResolucion(
            expediente_id="EXP-2024-001",
            tarea_id="TASK-001",
            run_id="RUN-001",
            mcp_registry=registry,
            logger=logger
        )
        result = await agent.execute()
    """
    pass  # Toda la lógica está en AgentLangGraph + configuración YAML
```

### Paso 5: Actualizar Registry

Modificar `src/backoffice/agents/registry.py`:

```python
# Añadir importaciones condicionales para LangGraph
try:
    from .base_langgraph import AgentLangGraph
    from .redactor_resolucion import RedactorResolucion
    LANGGRAPH_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    AgentLangGraph = None
    RedactorResolucion = None
    LANGGRAPH_AVAILABLE = False

# Añadir agentes LangGraph al registry
if LANGGRAPH_AVAILABLE:
    if RedactorResolucion is not None:
        AGENT_REGISTRY["RedactorResolucion"] = RedactorResolucion

# Añadir función de listado
def list_langgraph_agents() -> list[str]:
    """Lista los nombres de agentes LangGraph."""
    if LANGGRAPH_AVAILABLE:
        return ["RedactorResolucion"]
    return []

def is_langgraph_available() -> bool:
    """Verifica si LangGraph está disponible."""
    return LANGGRAPH_AVAILABLE
```

### Paso 6: Actualizar __init__.py del módulo agents

```python
# En src/backoffice/agents/__init__.py

from .registry import (
    AGENT_REGISTRY,
    get_agent_class,
    list_available_agents,
    list_crewai_agents,
    list_langgraph_agents,
    is_crewai_available,
    is_langgraph_available,
)

# Exportar clases base si están disponibles
try:
    from .base_real import AgentReal
except ImportError:
    AgentReal = None

try:
    from .base_langgraph import AgentLangGraph
except ImportError:
    AgentLangGraph = None

__all__ = [
    "AGENT_REGISTRY",
    "get_agent_class",
    "list_available_agents",
    "list_crewai_agents",
    "list_langgraph_agents",
    "is_crewai_available",
    "is_langgraph_available",
    "AgentReal",
    "AgentLangGraph",
]
```

### Paso 7: Añadir dependencias

Actualizar `requirements.txt`:

```
# LangChain/LangGraph (Paso 11)
langchain>=0.3.0
langchain-anthropic>=0.3.0
langgraph>=0.2.0
```

### Paso 8: Crear plantilla de Resolución

Añadir en los datos de documentación (`src/mcp_mock/data/documentacion/`):

```yaml
# En el archivo del tipo de expediente correspondiente
plantilla_resolucion:
  tipo: plantilla
  nombre: "Plantilla de Resolución"
  contenido: |
    # RESOLUCIÓN

    ## DATOS DEL EXPEDIENTE
    - **Número de expediente:** {{expediente_id}}
    - **Tipo:** {{tipo_expediente}}
    - **Fecha de resolución:** {{fecha_resolucion}}

    ## ANTECEDENTES
    {{antecedentes}}

    ## FUNDAMENTOS JURÍDICOS
    {{fundamentos_juridicos}}

    ## RESOLUCIÓN

    {{#if es_aprobacion}}
    PRIMERO.- Se APRUEBA la solicitud presentada por {{solicitante_nombre}}
    con NIF {{solicitante_nif}}.

    {{#if importe}}
    SEGUNDO.- Se concede un importe de {{importe}} euros.
    {{/if}}
    {{/if}}

    {{#if es_denegacion}}
    PRIMERO.- Se DENIEGA la solicitud presentada por {{solicitante_nombre}}
    con NIF {{solicitante_nif}}.

    SEGUNDO.- Motivos de la denegación: {{motivos_denegacion}}
    {{/if}}

    ## RECURSOS
    Contra esta resolución cabe interponer recurso de alzada...

    ---
    Fecha: {{fecha_resolucion}}
    Firmado electrónicamente
```

---

## Tests

Crear `tests/test_backoffice/test_langgraph_agent.py`:

```python
"""Tests para agentes LangGraph."""

import pytest
from unittest.mock import MagicMock, patch

# Tests de configuración
class TestLangGraphConfig:
    def test_agent_definition_is_langgraph(self):
        """Verifica propiedad is_langgraph."""
        from backoffice.config.agent_config_loader import AgentConfigLoader
        loader = AgentConfigLoader()

        if loader.exists("RedactorResolucion"):
            config = loader.get("RedactorResolucion")
            assert config.is_langgraph
            assert config.type == "langgraph"

    def test_langgraph_config_has_prompts(self):
        """Verifica que la configuración tiene prompts."""
        from backoffice.config.agent_config_loader import AgentConfigLoader
        loader = AgentConfigLoader()

        if loader.exists("RedactorResolucion"):
            config = loader.get("RedactorResolucion")
            assert config.langgraph_config is not None
            assert config.langgraph_config.system_prompt
            assert config.langgraph_config.task_prompt


# Tests de registro
class TestLangGraphRegistry:
    def test_redactor_resolucion_in_registry(self):
        """Verifica que RedactorResolucion está registrado."""
        from backoffice.agents.registry import (
            AGENT_REGISTRY,
            is_langgraph_available
        )

        if is_langgraph_available():
            assert "RedactorResolucion" in AGENT_REGISTRY

    def test_list_langgraph_agents(self):
        """Verifica listado de agentes LangGraph."""
        from backoffice.agents.registry import (
            list_langgraph_agents,
            is_langgraph_available
        )

        agents = list_langgraph_agents()
        if is_langgraph_available():
            assert "RedactorResolucion" in agents
        else:
            assert agents == []
```

---

## Verificación

1. **Instalar dependencias:**
   ```bash
   pip install langchain langchain-anthropic langgraph
   ```

2. **Ejecutar tests:**
   ```bash
   pytest tests/test_backoffice/test_langgraph_agent.py -v
   ```

3. **Probar agente:**
   ```python
   from backoffice.agents import get_agent_class
   from backoffice.mcp.registry import MCPClientRegistry
   from backoffice.logging import AuditLogger

   agent_class = get_agent_class("RedactorResolucion")
   agent = agent_class(
       expediente_id="EXP-2024-001",
       tarea_id="TASK-001",
       run_id="RUN-001",
       mcp_registry=registry,
       logger=logger
   )
   result = await agent.execute()
   ```

---

## Ventajas de esta arquitectura

1. **Misma interfaz** - `execute() -> Dict` para ambos frameworks
2. **Configuración unificada** - Todo en agents.yaml
3. **Reutilización de tools** - Mismas herramientas MCP
4. **Logging consistente** - Usa AuditLogger con redacción PII
5. **Fácil de extender** - Añadir más agentes LangGraph es trivial

## Consideraciones

### CrewAI vs LangGraph

| Aspecto | CrewAI | LangGraph |
|---------|--------|-----------|
| Abstracción | Alta (Agent/Task/Crew) | Media (ReAct agent) |
| Flexibilidad | Menos flexible | Muy flexible |
| Multi-agente | Nativo | Requiere configuración |
| Debugging | Logs verbose | Trazabilidad de estados |
| Complejidad | Menor | Mayor |

### Cuándo usar cada uno

- **CrewAI**: Tareas bien definidas con flujo secuencial
- **LangGraph**: Flujos complejos con condicionales y loops

---

## Resultado Esperado

1. ✅ Nuevo tipo de agente `langgraph` en agents.yaml
2. ✅ Clase base `AgentLangGraph` con misma interfaz que `AgentReal`
3. ✅ Agente `RedactorResolucion` funcional
4. ✅ Registry actualizado con soporte dual
5. ✅ Tests de configuración y registro
6. ✅ Documentación de uso
