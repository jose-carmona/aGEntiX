# Análisis Detallado - Commit 91b6ad4

## 1. Arquitectura

### Diagrama de Clases

```
┌─────────────────────────────────────────────────────────────────┐
│                        AgentConfigLoader                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   CrewAIConfig  │  │  LangGraphConfig │  │   LLMConfig     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       AgentDefinition                            │
│  - type: "crewai" | "langgraph" | "mock"                        │
│  - is_crewai: bool                                               │
│  - is_langgraph: bool                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│      AgentCrewAI          │     │     AgentLangGraph      │
│  (base_real.py)         │     │  (base_langgraph.py)    │
│  - CrewAI integration   │     │  - LangChain integration│
│  - MCPTool wrapper      │     │  - StructuredTool       │
│  - Crew.kickoff()       │     │  - create_react_agent() │
└─────────────────────────┘     └─────────────────────────┘
         │                               │
         ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│ ClasificadorExpediente  │     │   RedactorResolucion    │
│ RedactorSituacion       │     │                         │
│ RedactorPropuesta...    │     │                         │
└─────────────────────────┘     └─────────────────────────┘
```

### Flujo de Ejecución

```
1. AgentExecutor.execute()
         │
         ▼
2. get_agent_class("RedactorResolucion")
         │
         ▼
3. RedactorResolucion.__init__()
         │
         ├── _create_llm() → ChatAnthropic
         │
         └── _create_langchain_tools()
                  │
                  ├── _sanitize_tool_name() → "anadir_anotacion"
                  │
                  └── StructuredTool.from_function()
         │
         ▼
4. agent.execute()
         │
         ├── create_react_agent(model, tools)
         │
         └── agent.invoke(messages)
                  │
                  ├── LLM decide usar tool
                  │
                  └── tool_func(**kwargs)
                           │
                           ├── Extraer args de kwargs
                           │
                           └── mcp_registry.call_tool_sync()
         │
         ▼
5. Return {"completado": True, "mensaje": "...", "datos_actualizados": {...}}
```

## 2. Código Clave

### Sanitización de Nombres de Tools

```python
def _sanitize_tool_name(self, name: str) -> str:
    """
    Sanitiza el nombre de una herramienta para cumplir con el patrón
    de Anthropic: ^[a-zA-Z0-9_-]{1,128}$
    """
    # Reemplazar caracteres especiales comunes en español
    replacements = {
        'ñ': 'n', 'Ñ': 'N',
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ü': 'u', 'Ü': 'U',
    }
    sanitized = name
    for original, replacement in replacements.items():
        sanitized = sanitized.replace(original, replacement)

    # Eliminar cualquier caracter que no sea alfanumérico, guión o guión bajo
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', sanitized)

    # Truncar a 128 caracteres
    return sanitized[:128]
```

**¿Por qué es necesario?**
- La API de Anthropic requiere nombres de tools que coincidan con `^[a-zA-Z0-9_-]{1,128}$`
- El proyecto usa nombres en español como `añadir_anotacion`
- Sin sanitización: Error 400 - "invalid_request_error"

### Extracción de Argumentos

```python
def tool_func(**kwargs) -> str:
    # Extraer argumentos si vienen envueltos en 'kwargs'
    # (LangChain a veces envuelve los args así)
    if 'kwargs' in kwargs and len(kwargs) == 1:
        actual_args = kwargs['kwargs']
    else:
        actual_args = kwargs
```

**¿Por qué es necesario?**
- LangChain con `StructuredTool.from_function` a veces envía: `{"kwargs": {"expediente_id": "..."}}`
- El MCP espera: `{"expediente_id": "..."}`
- Sin este fix: `got an unexpected keyword argument 'kwargs'`

### Creación del Agente ReAct

```python
async def execute(self) -> Dict[str, Any]:
    # Crear el agente ReAct de LangGraph
    agent = create_react_agent(
        model=self.llm,
        tools=self.tools
    )

    # Preparar mensajes
    system_content = lg_cfg.system_prompt
    task_content = self._format_template(lg_cfg.task_prompt)

    # Ejecutar agente
    def run_agent():
        return agent.invoke({
            "messages": [
                ("system", system_content),
                ("human", task_content)
            ]
        })

    result = await loop.run_in_executor(None, run_agent)
```

**Patrón usado:**
- `create_react_agent`: Agente ReAct preconfigurado de LangGraph
- `run_in_executor`: Ejecutar código síncrono en thread pool (async wrapper)
- Mensajes como tuplas: `("role", "content")`

## 3. Configuración YAML

```yaml
RedactorResolucion:
    type: langgraph
    enabled: true
    description: "Genera Resoluciones usando LangGraph ReAct agent"

    llm:
      provider: anthropic
      model: claude-sonnet-4-5-20250929
      max_tokens: 4096
      temperature: 0.1
      num_retries: 5
      request_timeout: 180

    langgraph_config:
      system_prompt: |
        Eres un experto jurídico-administrativo...
      task_prompt: |
        Genera una Resolución para el expediente {expediente_id}...
      max_iterations: 15

    tools:
      - consultar_expediente
      - listar_documentos
      - obtener_texto_documento
      - crear_documento_desde_markdown
      - añadir_anotacion
```

**Diferencias con CrewAI:**

| Aspecto | CrewAI | LangGraph |
|---------|--------|-----------|
| Config | `crewai_agent` + `crewai_task` | `langgraph_config` |
| Prompts | `role`, `goal`, `backstory` | `system_prompt`, `task_prompt` |
| Iteraciones | `max_iterations` en código | `max_iterations` en config |
| Tools | `MCPTool` wrapper | `StructuredTool` nativo |

## 4. Tests Implementados

### Test de Sanitización

```python
def test_sanitize_tool_name_with_spanish_chars(self, ...):
    result = agent._sanitize_tool_name("añadir_anotación")
    assert result == "anadir_anotacion"
    assert "ñ" not in result
    assert "ó" not in result
```

### Test de Parseo de JSON

```python
def test_parse_result_json_in_text(self, ...):
    text = 'Aquí está el resultado: {"status": "success"} fin.'
    result = agent._parse_result(text)
    assert result["status"] == "success"
```

### Test de Tracking de Tools

```python
def test_track_tool_use(self, ...):
    agent._track_tool_use("consultar_expediente")
    agent._track_tool_use("listar_documentos")
    agent._track_tool_use("consultar_expediente")  # Duplicado

    tools = agent.get_tools_used()
    assert len(tools) == 2  # Sin duplicados
```

## 5. Comparación: CrewAI vs LangGraph

| Característica | AgentCrewAI (CrewAI) | AgentLangGraph |
|----------------|-------------------|----------------|
| Framework | CrewAI | LangChain/LangGraph |
| Tipo agente | Agent + Crew | ReAct Agent |
| Tools | MCPTool (BaseTool) | StructuredTool |
| Ejecución | crew.kickoff() | agent.invoke() |
| Logs | output_log_file | Reutiliza CrewAI logs |
| Async | Wrapper con executor | Wrapper con executor |
| Config YAML | crewai_agent, crewai_task | langgraph_config |

## 6. Dependencias Añadidas

```python
# Nuevas dependencias (importación condicional)
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent
```

**Instalación:**
```bash
pip install langchain langchain-anthropic langgraph
```

## 7. Compatibilidad

### ✅ Backward Compatible

- No modifica comportamiento de agentes CrewAI existentes
- Registry soporta ambos tipos de agentes
- AgentExecutor funciona con ambos

### ✅ Graceful Degradation

```python
try:
    from langchain_anthropic import ChatAnthropic
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
```

- Si LangGraph no está instalado, solo agentes CrewAI disponibles
- Tests se saltan automáticamente si LangGraph no está
