# Cambios para Arquitectura Multi-MCP en Paso 1

**Decisión:** Implementar arquitectura multi-MCP plug-and-play desde el Paso 1, pero usando solo MCP Expedientes.

## Resumen de Cambios

### 1. Actualización del Objetivo

**ANTES:**
```markdown
Este mock funcional permitirá:
- Validar el diseño de la arquitectura
- Probar la integración con BPMN
- Verificar el flujo de permisos
- Establecer las interfaces que luego implementará el sistema real
```

**DESPUÉS:**
```markdown
Este mock funcional permitirá:
- Validar el diseño de la arquitectura
- Probar la integración con BPMN
- Verificar el flujo de permisos
- Establecer las interfaces que luego implementará el sistema real
- **Preparar arquitectura plug-and-play multi-MCP** (usaremos solo MCP Expedientes en este paso)
```

### 2. Actualización de Arquitectura del Sistema

**ANTES:**
```text
BPMN (GEX) → [API REST - Paso 2] → Back-Office (a crear) → MCP → API (futuro) → GEX
```

**DESPUÉS:**
```text
BPMN (GEX) → [API REST - Paso 2] → Back-Office (a crear) → MCP Registry → MCP Expedientes
                                    ├─ Validación JWT           │
                                    ├─ Configuración Agente     └─ (Futuros MCPs: Firma,
                                    ├─ Mock de Ejecución            Notificaciones, etc.)
                                    └─ Logging/Auditoría
```

**Nota arquitectónica a añadir:**
> Aunque en el Paso 1 solo usaremos el MCP de Expedientes, el sistema se diseñará con **arquitectura plug-and-play multi-MCP** para facilitar la adición de nuevos servidores MCP en el futuro (ej: MCP Firma, MCP Notificaciones, MCP Recaudación, etc.) mediante configuración, sin cambios en el código.

### 3. Nueva Sección: "3. Arquitectura Multi-MCP Plug-and-Play"

**Insertar después de la sección "2. Validación JWT" y antes de "3. Mock de Ejecución de Agente":**

```markdown
### 3. Arquitectura Multi-MCP Plug-and-Play

**Principio de diseño:**

El sistema debe estar preparado arquitectónicamente para soportar múltiples servidores MCP (Expedientes, Firma, Notificaciones, Recaudación, etc.) que se puedan añadir mediante **configuración**, sin cambios en el código.

**En el Paso 1:**
- Solo se usará el MCP de Expedientes
- Pero la arquitectura debe permitir añadir nuevos MCPs editando solo archivos de configuración

#### Catálogo de Servidores MCP Configurable

```yaml
# backoffice/config/mcp_servers.yaml

mcp_servers:
  - id: expedientes
    name: "MCP Expedientes"
    description: "Gestión de expedientes y documentos"
    url: http://localhost:8000
    type: http
    auth:
      type: jwt
      audience: agentix-mcp-expedientes
    timeout: 30
    enabled: true  # Solo este estará activo en Paso 1

  # Futuros MCPs (deshabilitados en Paso 1)
  - id: firma
    name: "MCP Firma Electrónica"
    description: "Firma y validación de documentos"
    url: http://mcp-firma:8001
    type: http
    auth:
      type: jwt
      audience: agentix-mcp-firma
    timeout: 60
    enabled: false  # Deshabilitado en Paso 1

  - id: notificaciones
    name: "MCP Notificaciones"
    description: "Envío de notificaciones electrónicas"
    url: http://mcp-notificaciones:8002
    type: http
    auth:
      type: jwt
      audience: agentix-mcp-notificaciones
    timeout: 30
    enabled: false  # Deshabilitado en Paso 1
```

**Nota:** En el Paso 1, solo el MCP `expedientes` tendrá `enabled: true`. Los demás son especificaciones para el futuro.

#### Componente MCPClientRegistry

**Responsabilidad central del sistema multi-MCP:**

```python
# backoffice/mcp/registry.py

class MCPClientRegistry:
    """
    Registro de clientes MCP con routing automático.

    Permite añadir nuevos MCPs mediante configuración sin cambiar código.
    """

    async def initialize(self):
        """
        Carga configuración de MCPs y crea clientes solo para MCPs habilitados.

        En Paso 1: solo crea cliente para 'expedientes'
        En futuro: creará clientes para todos los MCPs con enabled=true
        """
        pass

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """
        Ejecuta una tool con routing automático al MCP correcto.

        El registry descubre qué MCP tiene la tool solicitada.
        En Paso 1: todas las tools van al MCP expedientes.
        En futuro: routing automático entre múltiples MCPs.
        """
        pass
```

**Flujo de routing:**

```
Agente.execute()
  └─> registry.call_tool("consultar_expediente", {...})
       └─> registry descubre que "consultar_expediente" está en MCP "expedientes"
            └─> client_expedientes.call_tool("consultar_expediente", {...})
                 └─> POST http://localhost:8000/sse con JSON-RPC 2.0
```

**Ventaja:** Cuando en el futuro se añada MCP Firma:
1. Editar `mcp_servers.yaml`: poner `enabled: true` en el servidor firma
2. El agente puede llamar `registry.call_tool("firmar_documento", {})` sin cambios
3. El registry automáticamente hace routing al nuevo MCP
```

### 4. Actualización en "Mock de Ejecución de Agente"

**CAMBIO:** Los agentes mock usan `MCPClientRegistry` en vez de `MCPClient` directo.

**ANTES:**
```python
async def mock_validador_documental(expediente_id: str, mcp_client: MCPClient, logger: Logger):
```

**DESPUÉS:**
```python
async def mock_validador_documental(
    expediente_id: str,
    mcp_registry: MCPClientRegistry,  # ⬅️ Usa registry en vez de client directo
    logger: AuditLogger
):
```

**Nota a añadir:**
> El agente usa `mcp_registry.call_tool()` en vez de llamar directamente a un cliente MCP específico. Esto prepara el código para multi-MCP futuro sin cambios.

### 5. Renombrar y Expandir Sección "Cliente MCP"

**La sección "4. Cliente MCP" se convierte en "5. Cliente MCP - Especificación Técnica"**

**Añadir subsección al inicio:**

```markdown
#### Arquitectura de Clientes MCP

El sistema tendrá dos niveles de abstracción:

1. **MCPClient**: Cliente para un servidor MCP específico (bajo nivel)
2. **MCPClientRegistry**: Registro que maneja múltiples MCPClients y hace routing (alto nivel)

```
AgentExecutor
  └─> MCPClientRegistry (maneja catálogo de MCPs)
       ├─> MCPClient(expedientes) → http://localhost:8000
       ├─> MCPClient(firma) → (deshabilitado en Paso 1)
       └─> MCPClient(notificaciones) → (deshabilitado en Paso 1)
```
```

**Añadir modelos de configuración:**

```markdown
#### Modelo de Configuración

```python
# backoffice/config/models.py

from pydantic import BaseModel, HttpUrl
from typing import List, Literal

class MCPAuthConfig(BaseModel):
    """Configuración de autenticación para un MCP"""
    type: Literal["jwt", "api_key", "none"] = "jwt"
    audience: str

class MCPServerConfig(BaseModel):
    """Configuración de un servidor MCP"""
    id: str
    name: str
    description: str
    url: HttpUrl
    type: Literal["http", "stdio"] = "http"
    auth: MCPAuthConfig
    timeout: int = 30
    enabled: bool = True  # Permite habilitar/deshabilitar MCPs

class MCPServersConfig(BaseModel):
    """Catálogo completo de servidores MCP"""
    mcp_servers: List[MCPServerConfig]

    @classmethod
    def load_from_file(cls, path: str) -> "MCPServersConfig":
        """Carga configuración desde archivo YAML"""
        import yaml
        from pathlib import Path

        config_path = Path(path)
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def get_enabled_servers(self) -> List[MCPServerConfig]:
        """Retorna solo los servidores MCP habilitados"""
        return [s for s in self.mcp_servers if s.enabled]
```
```

**Añadir dependencia pyyaml:**

```python
# requirements.txt
mcp>=1.0.0          # SDK oficial MCP (para tipos y protocolo)
httpx>=0.25.0       # Cliente HTTP asíncrono
pydantic>=2.0       # Validación de datos
pyyaml>=6.0         # Para leer mcp_servers.yaml  ⬅️ NUEVO
pyjwt>=2.8.0        # Validación JWT
python-dotenv>=1.0.0  # Variables de entorno
```

### 6. Actualización de MCPClient

**Cambio en el constructor:**

**ANTES:**
```python
def __init__(self, base_url: str, token: str):
```

**DESPUÉS:**
```python
def __init__(self, server_config: MCPServerConfig, token: str):
    """
    Inicializa el cliente MCP.

    Args:
        server_config: Configuración del servidor MCP
        token: Token JWT completo
    """
    self.server_config = server_config
    self.server_id = server_config.id
    self.token = token
    self._request_id = 0

    # Cliente HTTP con timeout configurado
    self.client = httpx.AsyncClient(
        base_url=str(server_config.url),
        timeout=float(server_config.timeout),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
```

**Mensajes de error actualizados para incluir server_id:**

```python
raise MCPConnectionError(
    codigo="MCP_TIMEOUT",
    mensaje=f"Timeout al ejecutar tool '{name}' en MCP '{self.server_id}' (>{self.server_config.timeout}s)",
    detalle=str(e)
)
```

### 7. Añadir Implementación Completa de MCPClientRegistry

**Nueva subsección en "5. Cliente MCP":**

```markdown
#### Implementación de MCPClientRegistry (alto nivel)

**Maneja múltiples MCPClients y hace routing:**

```python
# backoffice/mcp/registry.py

from typing import Dict, List, Any
from .client import MCPClient
from .exceptions import MCPError, MCPToolError
from backoffice.config.models import MCPServersConfig
import asyncio

class MCPClientRegistry:
    """
    Registro de clientes MCP con routing automático.

    Permite arquitectura plug-and-play: añadir MCPs mediante configuración.
    """

    def __init__(self, config: MCPServersConfig, token: str):
        """
        Inicializa el registro de clientes MCP.

        Args:
            config: Configuración de servidores MCP
            token: Token JWT con audiencias para los MCPs
        """
        self.config = config
        self.token = token

        # MCPClient por ID de servidor
        self._clients: Dict[str, MCPClient] = {}

        # Cache: tool_name → server_id
        self._tool_routing: Dict[str, str] = {}

        # Flag de inicialización
        self._initialized = False

    async def initialize(self):
        """
        Inicializa clientes MCP para servidores habilitados y descubre tools.

        En Paso 1: solo crea cliente para MCP Expedientes.
        En futuro: creará clientes para todos los MCPs con enabled=true.
        """
        if not self._initialized:
            # 1. Crear cliente solo para MCPs habilitados
            enabled_servers = self.config.get_enabled_servers()

            for server_config in enabled_servers:
                client = MCPClient(
                    server_config=server_config,
                    token=self.token
                )
                self._clients[server_config.id] = client

            # 2. Descubrir tools de cada MCP (en paralelo)
            tasks = [
                self._discover_tools(server_id)
                for server_id in self._clients.keys()
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

            self._initialized = True

    async def _discover_tools(self, server_id: str):
        """Descubre las tools disponibles en un servidor MCP."""
        client = self._clients[server_id]

        try:
            tools_response = await client.list_tools()
            tools = tools_response.get("tools", [])
            tool_names = [tool["name"] for tool in tools]

            # Actualizar routing: cada tool → su servidor
            for tool_name in tool_names:
                self._tool_routing[tool_name] = server_id

        except Exception as e:
            print(f"⚠️ Warning: No se pudieron descubrir tools de MCP '{server_id}': {e}")

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta una tool con routing automático al MCP correcto.
        """
        if not self._initialized:
            await self.initialize()

        # Routing: buscar qué servidor tiene esta tool
        server_id = self._tool_routing.get(tool_name)

        if not server_id:
            available_tools = list(self._tool_routing.keys())
            raise MCPToolError(
                codigo="MCP_TOOL_NOT_FOUND",
                mensaje=f"Tool '{tool_name}' no encontrada en ningún servidor MCP configurado",
                detalle=f"Tools disponibles: {available_tools}"
            )

        # Delegar al cliente correcto
        client = self._clients[server_id]
        return await client.call_tool(tool_name, arguments)

    def get_available_tools(self) -> Dict[str, str]:
        """Retorna mapping de tools disponibles por servidor."""
        return self._tool_routing.copy()

    async def close(self):
        """Cierra todos los clientes HTTP"""
        tasks = [client.close() for client in self._clients.values()]
        await asyncio.gather(*tasks)
```
```

### 8. Actualización de AgentExecutor

**ANTES:**
```python
mcp_client = MCPClient(
    base_url=config.MCP_SERVER_URL,
    token=token
)
```

**DESPUÉS:**
```python
# 1. Cargar configuración de MCPs
mcp_config = MCPServersConfig.load_from_file(self.mcp_config_path)

# 2. Crear registry de clientes MCP
mcp_registry = MCPClientRegistry(
    config=mcp_config,
    token=token
)

# 3. Inicializar (crea clientes para MCPs habilitados y descubre tools)
await mcp_registry.initialize()

# 4. Crear logger
logger.log(f"Iniciando ejecución de agente {agent_config.nombre}")

# Logear qué MCPs están disponibles
enabled_mcps = [s.id for s in mcp_config.get_enabled_servers()]
logger.log(f"MCPs habilitados: {enabled_mcps}")

# 5. Crear y ejecutar agente mock
agent = self._create_agent(
    agent_config=agent_config,
    expediente_id=expediente_id,
    tarea_id=tarea_id,
    mcp_registry=mcp_registry,  # ⬅️ Pasa registry, no client directo
    logger=logger
)
```

### 9. Actualización de Estructura de Proyecto

**AÑADIR:**

```text
/backoffice/
├── config/
│   ├── __init__.py
│   ├── models.py               # Modelos de configuración MCP  ⬅️ NUEVO
│   └── mcp_servers.yaml        # Catálogo de servidores MCP   ⬅️ NUEVO
├── mcp/
│   ├── __init__.py
│   ├── client.py               # Cliente MCP HTTP (bajo nivel)
│   ├── registry.py             # MCPClientRegistry (alto nivel, routing)  ⬅️ NUEVO
│   └── exceptions.py           # Excepciones del cliente MCP
```

### 10. Actualización de Variables de Entorno

**ANTES:**
```bash
# MCP Server
MCP_SERVER_URL=http://localhost:8000
MCP_SERVER_TYPE=http  # http o stdio
```

**DESPUÉS:**
```bash
# MCP Configuration
MCP_CONFIG_PATH=backoffice/config/mcp_servers.yaml
```

### 11. Actualización de Criterios de Aceptación

**AÑADIR:**

```markdown
✅ **Arquitectura multi-MCP plug-and-play implementada:**
  - Catálogo de MCPs configurable en YAML
  - `MCPClientRegistry` con routing automático
  - Añadir nuevo MCP requiere solo editar configuración
✅ Agentes usan `MCPClientRegistry` (no cliente directo)
✅ Tests de `MCPClientRegistry` verifican routing correcto
✅ Documentación README con:
  - Cómo configurar nuevos MCPs (editar mcp_servers.yaml)
  - Arquitectura plug-and-play multi-MCP
```

### 12. Actualización de Ejemplo de Uso

**AÑADIR nueva subsección "3. Añadir un Nuevo MCP (Ejemplo Futuro)":**

```markdown
### 3. Añadir un Nuevo MCP (Ejemplo Futuro)

**Para añadir MCP de Firma en el futuro:**

1. Editar `backoffice/config/mcp_servers.yaml`:

```yaml
  - id: firma
    name: "MCP Firma Electrónica"
    description: "Firma y validación de documentos"
    url: http://mcp-firma:8001
    type: http
    auth:
      type: jwt
      audience: agentix-mcp-firma
    timeout: 60
    enabled: true  # ⬅️ Cambiar a true cuando esté disponible
```

2. Reiniciar el servicio (NO cambios en código)

3. El agente puede ahora usar tools de firma:

```python
await mcp_registry.call_tool("firmar_documento", {...})
# El registry automáticamente hace routing al MCP firma
```
```

**ACTUALIZAR "4. Verificar Resultado":**

**AÑADIR:**
```markdown
- Logs muestran "MCPs habilitados: ['expedientes']"
```

### 13. Actualización de "Notas Importantes"

**AÑADIR nuevo principio:**

```markdown
5. **Arquitectura Plug-and-Play**:
   - Nuevos MCPs se añaden mediante configuración
   - NO cambiar código para añadir integraciones
```

**AÑADIR nueva subsección:**

```markdown
### Alcance del Paso 1 vs. Futuro

**En el Paso 1:**
- Solo MCP Expedientes habilitado (`enabled: true`)
- MCPs de Firma y Notificaciones especificados pero deshabilitados (`enabled: false`)
- Arquitectura multi-MCP completamente funcional
- Routing automático implementado

**En el futuro:**
- Habilitar MCPs adicionales editando solo `mcp_servers.yaml`
- Sin cambios en código del back-office
- Agentes pueden usar tools de múltiples MCPs transparentemente
```

### 14. Actualización de Referencias

**AÑADIR:**
```markdown
- Análisis arquitectura multi-MCP: `/prompts/mcp-client-architecture.md`
```

### 15. Actualización de "Próximos Pasos"

**En Paso 3, añadir:**
```markdown
- Los agentes reales seguirán usando `MCPClientRegistry` para multi-MCP
```

---

## Resumen de Archivos Nuevos a Crear

1. `backoffice/config/models.py` - Modelos Pydantic de configuración MCP
2. `backoffice/config/mcp_servers.yaml` - Catálogo de MCPs (solo expedientes enabled)
3. `backoffice/mcp/registry.py` - MCPClientRegistry con routing automático
4. `backoffice/tests/test_mcp_registry.py` - Tests del registry

## Resumen de Archivos a Modificar

1. `backoffice/mcp/client.py` - Constructor acepta `MCPServerConfig`
2. `backoffice/executor.py` - Usa `MCPClientRegistry` en vez de `MCPClient` directo
3. `backoffice/agents/*.py` - Reciben `mcp_registry` en vez de `mcp_client`
4. `requirements.txt` - Añadir `pyyaml>=6.0`
5. `.env` - Cambiar `MCP_SERVER_URL` por `MCP_CONFIG_PATH`

---

**FIN DEL RESUMEN DE CAMBIOS**
