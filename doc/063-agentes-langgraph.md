# Agentes Reales con LangGraph

## Introducción

A partir del paso 11, el sistema soporta agentes usando LangChain/LangGraph como alternativa a CrewAI. Esto proporciona flexibilidad en la elección del framework de orquestación de agentes.

## Acceso a Datos

Los agentes LangGraph acceden a los datos del expediente mediante **herramientas MCP**, igual que los agentes CrewAI. El LLM razona sobre los datos obtenidos a través de las tools configuradas.

## Arquitectura

```text
AgentLangGraph (base_langgraph.py)
    |
    +-- ChatAnthropic (LLM)
    |
    +-- StructuredTool --> MCPClientRegistry --> MCP Server
    |
    +-- create_react_agent() --> ReAct Agent
```

## Componentes

### AgentLangGraph (`base_langgraph.py`)

Clase base para agentes LangGraph. Implementa la misma interfaz que `AgentCrewAI`:

- Constructor con los 5 parámetros requeridos
- Método `async execute()` que retorna `Dict[str, Any]`
- Métodos `_track_tool_use()` y `get_tools_used()`

### Características

- **Sanitización de nombres**: Convierte caracteres españoles (ñ→n, á→a) para compatibilidad con API Anthropic
- **Descripciones dinámicas**: Obtiene descripciones de tools desde MCP Registry
- **Parseo de JSON**: Extrae automáticamente JSON de las respuestas del agente

### RedactorResolucion

Primer agente LangGraph. Genera resoluciones formales basadas en el expediente.

## Configuración YAML

Archivo: `src/backoffice/config/agents.yaml`

```yaml
agents:
  RedactorResolucion:
    type: langgraph
    enabled: true
    description: "Genera Resoluciones usando LangGraph"

    llm:
      provider: anthropic
      model: claude-sonnet-4-5-20250929
      max_tokens: 4096
      temperature: 0.1

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

    required_permissions:
      - expediente.lectura
      - expediente.escritura
    timeout_seconds: 300
```

## Diferencias con CrewAI

| Aspecto | AgentCrewAI | AgentLangGraph |
|---------|-------------|----------------|
| Framework | CrewAI | LangChain/LangGraph |
| Tipo agente | Agent + Crew | ReAct Agent |
| Tools | MCPTool (BaseTool) | StructuredTool |
| Ejecución | crew.kickoff() | agent.invoke() |
| Config YAML | crewai_agent, crewai_task | langgraph_config |
| Prompts | role, goal, backstory | system_prompt, task_prompt |

## Uso

```python
from backoffice.agents import RedactorResolucion

# Crear agente
agent = RedactorResolucion(
    expediente_id="EXP-2024-001",
    tarea_id="TASK-001",
    run_id="RUN-001",
    mcp_registry=mcp_registry,
    logger=audit_logger
)

# Ejecutar
result = await agent.execute()

# Resultado
# {
#     "completado": True,
#     "mensaje": "...",
#     "datos_actualizados": {
#         "documento_id": "DOC-123456",
#         "tipo_resolucion": "aprobacion"
#     }
# }
```

## Compatibilidad

- `AgentLangGraph` implementa la misma interfaz que `AgentCrewAI`
- `AgentExecutor` funciona igual con ambos tipos
- Registry unificado: `AGENT_REGISTRY` contiene ambos tipos
- Importación condicional: Si LangGraph no está instalado, solo agentes CrewAI disponibles

## Dependencias

```bash
pip install langchain langchain-anthropic langgraph
```

## Relaciones

- Ver: [Agentes CrewAI](060-agentes-crewai.md)
- Ver: [Propuesta general](030-propuesta-agentes.md)
- Ver: [Configuración](031-configuracion-agente.md)
