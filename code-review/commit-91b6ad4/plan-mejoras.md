# Plan de Mejoras - Commit 91b6ad4

## Estado de Implementación

| ID | Mejora | Estado | Prioridad |
|----|--------|--------|-----------|
| P1 | Descripciones dinámicas de tools | 🔜 Pendiente | Alta |
| P2 | Constante para regex sanitización | 🔜 Pendiente | Baja |
| P3 | Lista dinámica de agentes LangGraph | 🔜 Pendiente | Media |
| P4 | Externalizar prompts largos | 🔜 Pendiente | Baja |

---

## P1: Descripciones Dinámicas de Tools

**Problema actual:**
```python
# base_langgraph.py:246-260
descriptions = {
    "consultar_expediente": "Consulta los datos completos...",
    "listar_documentos": "Lista todos los documentos...",
    # ... hardcoded
}
```

**Solución propuesta:**
```python
def _get_tool_description(self, tool_name: str) -> str:
    """Obtiene descripción del MCP Registry."""
    # Intentar obtener del registry
    try:
        tool_info = self.mcp_registry.get_tool_info(tool_name)
        if tool_info and tool_info.get("description"):
            return tool_info["description"]
    except Exception:
        pass

    # Fallback a descripciones conocidas
    fallback_descriptions = {
        "consultar_expediente": "Consulta expediente...",
        # ...
    }
    return fallback_descriptions.get(tool_name, f"Tool MCP: {tool_name}")
```

**Beneficios:**
- Descripciones siempre sincronizadas con MCP
- Menos mantenimiento
- Nuevos tools funcionan automáticamente

**Esfuerzo:** Medio (requiere método en MCPClientRegistry)

---

## P2: Constante para Regex de Sanitización

**Problema actual:**
```python
# base_langgraph.py:187
sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', sanitized)
```

**Solución propuesta:**
```python
class AgentLangGraph(ABC):
    # Patrón de Anthropic para nombres de tools
    TOOL_NAME_PATTERN = re.compile(r'[^a-zA-Z0-9_-]')

    def _sanitize_tool_name(self, name: str) -> str:
        # ...
        sanitized = self.TOOL_NAME_PATTERN.sub('_', sanitized)
        # ...
```

**Beneficios:**
- Regex precompilado (micro-optimización)
- Documentación del patrón
- Fácil de encontrar y modificar

**Esfuerzo:** Bajo

---

## P3: Lista Dinámica de Agentes LangGraph

**Problema actual:**
```python
# registry.py:118-120
def list_langgraph_agents() -> list[str]:
    if LANGGRAPH_AVAILABLE:
        return ["RedactorResolucion"]  # Hardcoded
```

**Solución propuesta:**
```python
def list_langgraph_agents() -> list[str]:
    """Lista agentes LangGraph desde el registry."""
    if not LANGGRAPH_AVAILABLE:
        return []

    return [
        name for name, cls in AGENT_REGISTRY.items()
        if AgentLangGraph and isinstance(cls, type) and issubclass(cls, AgentLangGraph)
    ]
```

**Beneficios:**
- Nuevos agentes LangGraph registrados automáticamente
- Consistencia con `list_available_agents()`
- Menos código a mantener

**Esfuerzo:** Bajo

---

## P4: Externalizar Prompts Largos

**Problema actual:**
```yaml
# agents.yaml
langgraph_config:
  task_prompt: |
    Genera una Resolución para el expediente {expediente_id}.

    PASOS A SEGUIR:

    1. CONSULTAR EXPEDIENTE
       - Usa 'consultar_expediente'...
    # ... 30+ líneas
```

**Solución propuesta:**

Opción A: Archivos de prompts separados
```yaml
langgraph_config:
  system_prompt_file: "prompts/redactor_resolucion_system.md"
  task_prompt_file: "prompts/redactor_resolucion_task.md"
```

Opción B: Mantener inline para prompts cortos, externalizar largos
```python
def _load_prompt(self, prompt_or_path: str) -> str:
    """Carga prompt desde string o archivo."""
    if prompt_or_path.endswith('.md') or prompt_or_path.endswith('.txt'):
        path = Path(__file__).parent.parent / "config" / prompt_or_path
        return path.read_text()
    return prompt_or_path
```

**Beneficios:**
- YAML más legible
- Prompts editables sin tocar YAML
- Posible versionado independiente de prompts

**Esfuerzo:** Medio

---

## Priorización Recomendada

### Fase 1 (Inmediato)
- [ ] P3: Lista dinámica de agentes (5 min)

### Fase 2 (Próximo sprint)
- [ ] P1: Descripciones dinámicas de tools
- [ ] P2: Constante para regex

### Fase 3 (Cuando haya más prompts)
- [ ] P4: Externalizar prompts largos

---

## Notas Adicionales

### Mejoras No Prioritarias

1. **Type hints completos**: Añadir tipos de retorno faltantes
2. **Async nativo**: Migrar a `ainvoke()` cuando LangGraph lo soporte mejor
3. **Métricas**: Añadir instrumentación Prometheus para LangGraph
4. **Cache de tools**: Cachear `StructuredTool` creados

### Deuda Técnica Aceptable

- Descripciones hardcodeadas funcionan para el set actual de tools
- Lista hardcodeada es mantenible con pocos agentes LangGraph
- Prompts inline son legibles para tamaño actual
