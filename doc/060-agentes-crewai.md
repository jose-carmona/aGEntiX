# Agentes Reales con CrewAI

## Introducción

A partir del paso 6.1, el sistema soporta agentes reales usando CrewAI con Anthropic Claude como proveedor LLM.

## Acceso a Datos

Los agentes reales acceden a los datos del expediente mediante **herramientas MCP**, igual que los agentes mock. El LLM no tiene acceso directo a datos; debe usar las tools configuradas.

## Arquitectura

```text
AgentReal (base_real.py)
    |
    +-- MCPToolFactory --> MCPTool (wrapper sync→async)
    |                          |
    |                          v
    +-- CrewAI Agent --tools--> MCPClientRegistry --> MCP Server
```

## Componentes

### AgentReal (`base_real.py`)

Clase base para agentes reales. Implementa la misma interfaz que `AgentMock`:

- Constructor con los 5 parámetros requeridos
- Método `async execute()` que retorna `Dict[str, Any]`
- Métodos `_track_tool_use()` y `get_tools_used()`

### MCPToolWrapper (`mcp_tool_wrapper.py`)

Wrapper que convierte herramientas MCP async en Tools síncronas de CrewAI:

- `MCPTool`: Tool de CrewAI que ejecuta herramientas MCP
- `MCPToolFactory`: Factory para crear tools desde la configuración

### ClasificadorExpediente

Primer agente real. Clasifica expedientes según tipo y urgencia.

## Configuración YAML

Archivo: `src/backoffice/config/agents.yaml`

```yaml
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
      role: "Clasificador de Expedientes"
      goal: "Clasificar expediente {expediente_id}"
      backstory: "Experto en gestión documental..."
      verbose: true
      allow_delegation: false

    crewai_task:
      description: "Analiza el expediente {expediente_id}..."
      expected_output: "JSON con clasificación"

    tools:
      - consultar_expediente

    required_permissions:
      - expediente.lectura
    timeout_seconds: 300
```

## Variables de Entorno

```bash
# API Key de Anthropic (requerida para agentes CrewAI)
ANTHROPIC_API_KEY=sk-ant-...

# Ruta al archivo de configuración de agentes
AGENTS_CONFIG_PATH=src/backoffice/config/agents.yaml
```

## Uso

```python
from backoffice.agents import ClasificadorExpediente

# Crear agente
agent = ClasificadorExpediente(
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
#         "tipo_expediente": "subvención",
#         "urgencia": "media",
#         "justificacion": "..."
#     }
# }

# Herramientas usadas
tools = agent.get_tools_used()
# ["consultar_expediente"]
```

## Diferencias con AgentMock

| Aspecto | AgentMock | AgentReal |
|---------|-----------|-----------|
| LLM | Ninguno | Anthropic Claude |
| Razonamiento | Scripted | Dinámico |
| Configuración | Código | YAML |
| Herramientas | MCP directo | MCPTool wrapper |
| Tests | Unitarios | Unitarios + Integración |

## Compatibilidad

- `AgentReal` implementa la misma interfaz que `AgentMock`
- `AgentExecutor` funciona igual con ambos tipos
- Registry unificado: `AGENT_REGISTRY` contiene ambos tipos
- Importación condicional: Si CrewAI no está instalado, solo agentes mock disponibles

## Relaciones

- Ver: [Propuesta general](030-propuesta-agentes.md)
- Ver: [Configuración](031-configuracion-agente.md)
- Ver: [MCP Registry](mcp-registry.md)
