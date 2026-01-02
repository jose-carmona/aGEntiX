# Code Review: Acceso a Servidor MCP

**Fecha:** 2024-12-30
**Última actualización:** 2025-01-01
**Archivos analizados:**
- `src/backoffice/agents/mcp_tool_wrapper.py`
- `src/backoffice/mcp/client.py`
- `src/backoffice/mcp/registry.py`

**Calificación actual:** 5/5 ⭐⭐⭐⭐⭐ (post Fase 1+2+3+4)

## Estado de Implementación

| Fase | Descripción | Estado |
|------|-------------|--------|
| 1 | MCPClient dual (sync/async) | ✅ Implementada |
| 2 | Métodos públicos en Registry | ✅ Implementada |
| 3 | Wrapper con errores semánticos | ✅ Implementada |
| 4 | Discovery dinámico de schemas | ✅ Implementada |

### Fase 3: Mejoras Implementadas

El wrapper ahora preserva errores semánticos con información de retry:

```python
# Error response structure
{
    "error": "MCP_TIMEOUT",      # Código semántico
    "message": "Timeout en...",   # Mensaje descriptivo
    "type": "connection",         # Tipo: connection|auth|tool|internal
    "retriable": True             # ¿El agente puede reintentar?
}
```

| Tipo Error | Retriable | Ejemplo |
|------------|-----------|---------|
| MCPConnectionError | ✅ Sí | Timeout, servidor caído |
| MCPAuthError | ❌ No | Token inválido, permisos |
| MCPToolError (CONFLICT) | ✅ Sí | Modificación concurrente |
| MCPToolError (otros) | ❌ No | Tool no encontrada |
| Exception | ❌ No | Errores internos |

### Fase 4: Discovery Dinámico de Schemas

El sistema ahora obtiene schemas de argumentos dinámicamente del servidor MCP:

**Nuevo archivo: `backoffice/agents/schema_builder.py`**

```python
from backoffice.agents.schema_builder import build_pydantic_model, GenericMCPArgs

# Convertir JSON Schema a modelo Pydantic
json_schema = {
    "type": "object",
    "properties": {
        "expediente_id": {"type": "string", "description": "ID"},
        "campo": {"type": "string", "description": "Campo"}
    },
    "required": ["expediente_id"]
}

Model = build_pydantic_model("MiArgs", json_schema)
instance = Model(expediente_id="EXP-001", campo="test")
```

**Nuevo método en Registry: `get_tools_with_schemas()`**

```python
# Obtiene tools con sus schemas completos
tools = registry.get_tools_with_schemas()
# {
#     "consultar_expediente": {
#         "name": "consultar_expediente",
#         "description": "Consulta expediente...",
#         "inputSchema": {...},
#         "server_id": "expedientes"
#     }
# }
```

**MCPToolFactory con schemas dinámicos:**

```python
# Usa schemas del servidor (default)
tools = MCPToolFactory.create_tools(
    tool_names=["consultar_expediente"],
    mcp_registry=registry,
    logger=logger,
    use_dynamic_schemas=True  # Default
)

# Fallback a schemas estáticos
tools = MCPToolFactory.create_tools(
    tool_names=["consultar_expediente"],
    mcp_registry=registry,
    logger=logger,
    use_dynamic_schemas=False
)
```

**Beneficios:**
- Schemas siempre sincronizados con el servidor MCP
- No requiere actualizar código cuando cambian los argumentos de tools
- Fallback automático si el servidor no responde

---

## Resumen Ejecutivo

El sistema de acceso a servidores MCP funciona pero presenta varios problemas arquitectónicos que dificultan el mantenimiento y la extensibilidad. La principal deuda técnica es la **duplicación de la lógica HTTP** entre el cliente async y el wrapper síncrono de CrewAI.

---

## Problemas Identificados

### P1. Duplicación de Código HTTP (Crítico) 🔴

**Ubicación:** `mcp_tool_wrapper.py:168-220` vs `client.py:45-96`

El método `_run_async_safely()` reimplementa toda la lógica HTTP que ya existe en `MCPClient.call_tool()`:

```python
# mcp_tool_wrapper.py - DUPLICADO
with httpx.Client(...) as http_client:
    response = http_client.post(
        server_config.endpoint,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            ...
        }
    )

# client.py - ORIGINAL
response = await self.client.post(
    self.server_config.endpoint,
    json={
        "jsonrpc": "2.0",
        "id": self._next_request_id(),
        ...
    }
)
```

**Consecuencias:**
- Mantenimiento doble ante cambios en protocolo JSON-RPC
- El wrapper pierde el manejo de errores semántico de `MCPClient`
- Inconsistencia en generación de `request_id`

---

### P2. Violación de Encapsulamiento (Alto) 🟠

**Ubicación:** `mcp_tool_wrapper.py:179-190`

El wrapper accede directamente a atributos privados del registry:

```python
server_id = self.mcp_registry._tool_routing.get(tool_name)  # ❌ Privado
mcp_client = self.mcp_registry._clients.get(server_id)      # ❌ Privado
server_config = mcp_client.server_config
token = mcp_client.token
```

**Consecuencias:**
- Acoplamiento fuerte entre wrapper y estructura interna del registry
- Cambios internos en `MCPClientRegistry` romperán el wrapper
- Viola el principio de ocultación de información

---

### P3. Schemas de Argumentos Hardcodeados (Medio) 🟡

**Ubicación:** `mcp_tool_wrapper.py:29-98`

Los schemas Pydantic están definidos manualmente y duplican información del servidor MCP:

```python
class ConsultarExpedienteArgs(BaseModel):
    expediente_id: str = Field(description="ID del expediente a consultar")
```

**Consecuencias:**
- Si el servidor MCP añade/modifica parámetros, hay que actualizar manualmente
- No hay validación de que los schemas coincidan con el servidor
- El servidor MCP ya define `inputSchema` en `tools/list`

---

### P4. Falta de Interfaz Síncrona en MCPClient (Medio) 🟡

**Ubicación:** `client.py`

`MCPClient` solo expone métodos async, forzando workarounds en contextos síncronos:

```python
async def call_tool(...) -> Dict[str, Any]  # Solo async
async def list_tools(...) -> Dict[str, Any]  # Solo async
```

**Consecuencias:**
- CrewAI (síncrono) no puede usar el cliente directamente
- Obliga a crear un cliente HTTP paralelo en el wrapper
- Potenciales problemas de event loop (ya experimentados)

---

### P5. Manejo de Errores Inconsistente (Medio) 🟡

**Ubicación:** `mcp_tool_wrapper.py:162-166` vs `client.py:98-166`

El wrapper tiene un manejo de errores simplificado que pierde información:

```python
# Wrapper - simplificado
except Exception as e:
    return json.dumps({"error": str(e)})

# Client - semántico
except httpx.TimeoutException:
    raise MCPConnectionError(codigo="MCP_TIMEOUT", ...)
except httpx.HTTPStatusError as e:
    if status == 401:
        raise MCPAuthError(codigo="AUTH_INVALID_TOKEN", ...)
```

**Consecuencias:**
- El agente CrewAI no distingue entre tipos de error
- No puede implementar estrategias de retry diferenciadas
- Se pierde contexto útil para debugging

---

### P6. Descripciones de Tools Duplicadas (Bajo) 🟢

**Ubicación:** `mcp_tool_wrapper.py:237-272`

Las descripciones de herramientas están hardcodeadas en el wrapper:

```python
TOOL_DESCRIPTIONS = {
    "consultar_expediente": "Consulta los datos completos...",
    ...
}
```

**Consecuencias:**
- Duplicación con las descripciones del servidor MCP
- Posible inconsistencia si el servidor cambia
- Mayor esfuerzo de mantenimiento

---

## Propuesta de Refactorización

### Fase 1: MCPClient con Interfaz Dual (sync + async)

Añadir un cliente síncrono que reutilice la lógica:

```python
# client.py

class MCPClient:
    def __init__(self, server_config: MCPServerConfig, token: str):
        self.server_config = server_config
        self.token = token
        self._request_id = 0

        # Cliente async para uso desde contextos async
        self._async_client: Optional[httpx.AsyncClient] = None

        # Cliente sync para uso desde contextos sync (CrewAI)
        self._sync_client: Optional[httpx.Client] = None

    def _get_sync_client(self) -> httpx.Client:
        """Lazy init del cliente síncrono."""
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                base_url=str(self.server_config.url),
                timeout=float(self.server_config.timeout),
                headers=self._headers
            )
        return self._sync_client

    def call_tool_sync(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Versión síncrona de call_tool para CrewAI."""
        client = self._get_sync_client()
        # ... misma lógica que call_tool pero síncrona
```

### Fase 2: Método Público en Registry

Exponer método público para obtener configuración de servidor:

```python
# registry.py

class MCPClientRegistry:
    def get_server_for_tool(self, tool_name: str) -> Optional[str]:
        """Retorna el server_id para una tool, o None si no existe."""
        return self._tool_routing.get(tool_name)

    def call_tool_sync(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Versión síncrona de call_tool para contextos no-async."""
        server_id = self.get_server_for_tool(tool_name)
        if not server_id:
            raise MCPToolError(...)

        client = self._clients[server_id]
        return client.call_tool_sync(tool_name, arguments)
```

### Fase 3: Wrapper Simplificado

Con la interfaz síncrona, el wrapper se simplifica drásticamente:

```python
# mcp_tool_wrapper.py

def _run(self, expediente_id: str = "", **kwargs) -> str:
    all_args = {"expediente_id": expediente_id, **kwargs}

    try:
        result = self.mcp_registry.call_tool_sync(self.name, all_args)
        # ... procesar resultado
    except MCPError as e:
        # Mantener errores semánticos
        return json.dumps({"error": e.codigo, "message": e.mensaje})
```

### Fase 4: Discovery Dinámico de Schemas

Obtener schemas del servidor MCP en lugar de hardcodearlos:

```python
# mcp_tool_wrapper.py

class MCPToolFactory:
    @classmethod
    def create_tools(cls, tool_names: List[str], mcp_registry: MCPClientRegistry, ...):
        # Obtener schemas del servidor
        available_tools = mcp_registry.get_available_tools_with_schemas()

        for name in tool_names:
            tool_info = available_tools.get(name)
            if tool_info:
                # Generar schema Pydantic dinámicamente desde inputSchema
                args_schema = cls._build_schema_from_mcp(tool_info["inputSchema"])
            else:
                args_schema = GenericMCPArgs  # Fallback
```

---

## Plan de Implementación

| Fase | Descripción | Esfuerzo | Impacto |
|------|-------------|----------|---------|
| 1 | MCPClient dual (sync/async) | Medio | Alto |
| 2 | Métodos públicos en Registry | Bajo | Alto |
| 3 | Simplificar wrapper | Bajo | Medio |
| 4 | Discovery dinámico de schemas | Alto | Medio |

**Recomendación:** Implementar Fases 1-3 primero (quick wins), dejar Fase 4 para después.

---

## Diagrama de Dependencias Actual vs Propuesto

### Actual (Problemático)

```
┌─────────────────┐
│   MCPTool       │
│   (wrapper)     │
└────────┬────────┘
         │ accede a atributos privados
         │ duplica lógica HTTP
         ▼
┌─────────────────┐      ┌─────────────────┐
│ MCPClientRegistry│◄────│   MCPClient     │
│ (_tool_routing) │      │ (solo async)    │
│ (_clients)      │      └─────────────────┘
└─────────────────┘
```

### Propuesto

```
┌─────────────────┐
│   MCPTool       │
│   (wrapper)     │
└────────┬────────┘
         │ usa API pública
         │ call_tool_sync()
         ▼
┌─────────────────┐      ┌─────────────────┐
│ MCPClientRegistry│◄────│   MCPClient     │
│ +call_tool_sync │      │ +call_tool_sync │
│ +get_server_for │      │ +call_tool      │
└─────────────────┘      └─────────────────┘
```

---

## Métricas de Mejora Esperadas

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Líneas duplicadas | ~50 | 0 |
| Accesos a privados | 4 | 0 |
| Schemas hardcodeados | 9 | 0 (dinámicos) |
| Tipos de error distinguibles | 1 | 6+ |

---

## Conclusión

El código funciona pero tiene deuda técnica significativa. Las Fases 1-3 pueden implementarse en una sesión de trabajo y resolverían los problemas P1, P2, P4 y P5. La Fase 4 (schemas dinámicos) requiere más análisis pero eliminaría P3 y P6.

**Calificación post-refactor estimada:** 4.5/5 ⭐⭐⭐⭐⭐

---

## API Pública Actual (Post Fase 1+2+3+4)

### MCPClientRegistry

```python
# Métodos de ejecución
async call_tool(tool_name, arguments)     # Async
call_tool_sync(tool_name, arguments)      # Sync (CrewAI)

# Discovery
get_available_tools() -> Dict[str, str]   # {tool_name: server_id}
get_tool_names() -> List[str]             # Solo nombres
is_tool_available(tool_name) -> bool      # Verificación rápida
list_tools_sync(server_id=None) -> Dict   # Discovery sync
get_tools_with_schemas() -> Dict          # Tools con inputSchema (Fase 4)

# Servidor
get_server_for_tool(tool_name) -> Optional[str]
get_enabled_server_ids() -> List[str]
get_server_config(server_id) -> Optional[MCPServerConfig]

# Estado
is_initialized -> bool                    # Property

# Lifecycle
async initialize()
async close()
close_sync()
```

### schema_builder (Fase 4)

```python
build_pydantic_model(name, json_schema) -> Type[BaseModel]
build_models_from_tools(tools_with_schemas) -> Dict[str, Type[BaseModel]]
GenericMCPArgs  # Modelo genérico con extra="allow"
```

### MCPClient

```python
# Async
async call_tool(name, arguments)
async list_tools()
async read_resource(uri)
async close()

# Sync (para CrewAI)
call_tool_sync(name, arguments)
list_tools_sync()
close_sync()
async close_all()
```

---

## Problemas Resueltos

| Problema | Estado | Fase |
|----------|--------|------|
| P1. Duplicación HTTP | ✅ Resuelto | 1 |
| P2. Violación encapsulamiento | ✅ Resuelto | 1+2 |
| P3. Schemas hardcodeados | ✅ Resuelto | 4 |
| P4. Sin interfaz sync | ✅ Resuelto | 1 |
| P5. Errores inconsistentes | ✅ Resuelto | 1+3 |
| P6. Descripciones duplicadas | ✅ Resuelto | 4 |

## Tests

- **test_mcp_integration.py**: 22 tests (MCPClient + MCPClientRegistry)
- **test_mcp_tool_wrapper.py**: 17 tests (errores semánticos + factory + dynamic schemas)
- **test_schema_builder.py**: 16 tests (JSON Schema → Pydantic)
- **Total backoffice**: 154 tests PASS
