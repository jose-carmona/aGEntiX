# Arquitectura de Clientes MCP: Análisis y Propuesta

**Fecha:** 2025-12-04
**Contexto:** Discusión sobre si crear un "Paso 0" para cliente MCP antes del Paso 1
**Decisión:** Definir arquitectura multi-MCP antes de implementar

---

## 📋 Argumentación del Usuario

> - Lo que tengo en mente es que en el futuro aparezcan nuevos servidores MCP
> - Tendremos entonces pares Servidores MCP + su correspondiente cliente MCP
> - El sistema debe contemplar como requisito la facilidad para añadir nuevos clientes MCP (que usen sus correspondientes servidores MCP)
> - En la medida de lo posible el catálogo de MCP debe ser modificable por configuración

---

## ✅ Crítica de la Argumentación

### **EXCELENTE argumentación. Revela requisito arquitectónico crítico no documentado.**

**Puntos fuertes:**

1. **✅ Visión de escalabilidad correcta**
   - El sistema GEX integra con múltiples sistemas externos (doc/004-integraciones.md)
   - Cada integración podría tener su propio servidor MCP
   - Ejemplos futuros:
     - MCP de Firma Electrónica
     - MCP de Notificaciones
     - MCP de Recaudación
     - MCP de Contabilidad
     - MCP de Registro General

2. **✅ Requisito de configurabilidad bien identificado**
   - Añadir un nuevo MCP no debería requerir cambios en código
   - Despliegue de nuevos MCPs debe ser independiente del back-office
   - Alineado con principio "No Acoplamiento" (doc/040-criterios-diseño.md)

3. **✅ Arquitectura plug-and-play necesaria**
   - Los agentes deben poder usar diferentes MCPs según su tarea
   - Un agente podría necesitar múltiples MCPs en una ejecución
   - Ejemplo: Agente "GeneradorResolucion" podría necesitar:
     - MCP Expedientes (leer datos)
     - MCP Documentos (generar PDF)
     - MCP Firma (firmar documento)
     - MCP Notificaciones (notificar ciudadano)

### **Puntos que requieren clarificación:**

1. **🤔 ¿Catálogo centralizado o distribuido?**

   **Opción A: Catálogo centralizado en back-office**
   ```yaml
   # config/mcp_servers.yaml
   mcp_servers:
     - id: expedientes
       url: http://mcp-expedientes:8000
       type: http
       capabilities: [consulta_expediente, actualizar_datos, ...]

     - id: firma
       url: http://mcp-firma:8001
       type: http
       capabilities: [firmar_documento, validar_firma, ...]
   ```

   **Opción B: Discovery dinámico**
   ```yaml
   # Cada servidor MCP se anuncia en un registry
   # El back-office descubre MCPs disponibles en runtime
   mcp_registry_url: http://mcp-registry:9000
   ```

2. **🤔 ¿Qué tan genérico debe ser el cliente MCP?**

   **Opción A: Cliente MCP genérico único**
   - Todas las integraciones usan la misma clase `MCPClient`
   - Asume que todos los MCPs siguen protocolo estándar
   - Ventaja: Simplicidad
   - Riesgo: ¿Qué pasa si un MCP tiene peculiaridades?

   **Opción B: Cliente base + adaptadores específicos**
   - `MCPClientBase` con funcionalidad común
   - `MCPExpedientesClient`, `MCPFirmaClient`, etc. heredan y especializan
   - Ventaja: Flexibilidad para peculiaridades
   - Riesgo: Más complejidad

3. **🤔 ¿Cómo se configura qué MCP usa cada agente?**

   **Opción A: En configuración del agente**
   ```python
   AgentConfig(
       nombre="GeneradorResolucion",
       mcp_servers=["expedientes", "firma", "notificaciones"],
       herramientas=[
           {"mcp": "expedientes", "tool": "consultar_expediente"},
           {"mcp": "firma", "tool": "firmar_documento"},
           {"mcp": "notificaciones", "tool": "enviar_notificacion"}
       ]
   )
   ```

   **Opción B: Discovery automático por herramienta**
   ```python
   AgentConfig(
       nombre="GeneradorResolucion",
       herramientas=["consultar_expediente", "firmar_documento", "enviar_notificacion"]
   )
   # El sistema descubre automáticamente qué MCP proporciona cada tool
   ```

---

## 🎯 Análisis de Impacto en el Paso 1

### **¿Cambia esto la necesidad de un "Paso 0"?**

**Respuesta: SÍ, pero no como "Paso 0" sino como REDISEÑO del Paso 1**

**Razones:**

1. **El Paso 1 actual asume un solo MCP hardcodeado**

   Evidencia en `step-1-backoffice-skeleton.md`:
   - Línea 1373: `MCP_SERVER_URL=http://localhost:8000` (URL única)
   - Línea 359-368: `MCPClient.__init__(base_url: str, token: str)` (un solo servidor)
   - Línea 670-673: `mcp_client = MCPClient(base_url=config.MCP_SERVER_URL, token=token)` (cliente único)

2. **El diseño actual NO soporta múltiples MCPs**

   Problemas identificados:
   - ❌ Un solo `MCP_SERVER_URL` en configuración
   - ❌ `AgentExecutor` crea un solo `MCPClient`
   - ❌ Agentes mock no especifican qué MCP usan
   - ❌ No hay concepto de "catálogo de MCPs"
   - ❌ JWT token asume audiencia única `["agentix-mcp-expedientes"]`

3. **Añadir multi-MCP después sería refactorización completa**

   Impacto:
   - 🔨 Cambiar `MCPClient` para aceptar múltiples servidores
   - 🔨 Cambiar `AgentConfig` para especificar MCPs por herramienta
   - 🔨 Cambiar JWT claims para múltiples audiencias
   - 🔨 Cambiar tests para múltiples servidores
   - 🔨 Cambiar ejemplos de uso

---

## 📐 Propuesta de Arquitectura Multi-MCP

### **Principios de Diseño**

1. **Catálogo de MCPs configurable**
   - Lista de MCPs disponibles se carga desde archivo de configuración
   - Añadir nuevo MCP = editar config + reiniciar servicio (sin código)

2. **Cliente MCP genérico con routing**
   - Un solo `MCPClient` que maneja múltiples servidores
   - Routing automático: herramienta → servidor MCP correcto

3. **Propagación de JWT por audiencia**
   - JWT con múltiples audiencias según MCPs usados
   - Cada MCP valida que está en la lista de audiencias

4. **Discovery de capabilities**
   - Cada MCP expone sus tools vía `tools/list`
   - Back-office cachea catálogo de tools disponibles

### **Arquitectura Propuesta**

```
┌─────────────────────────────────────────────────────────────┐
│                      AgentExecutor                          │
│  - Valida JWT                                               │
│  - Crea MCPClientRegistry                                   │
│  - Ejecuta agente mock                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  MCPClientRegistry                          │
│  - Carga catálogo de MCPs desde config                     │
│  - Crea MCPClient por cada MCP configurado                 │
│  - Routing: tool_name → MCPClient correcto                 │
│  - Cachea capabilities de cada MCP                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────┴───────────┬───────────────────┐
         ▼                       ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  MCPClient      │  │  MCPClient      │  │  MCPClient      │
│  (Expedientes)  │  │  (Firma)        │  │  (Notificaciones)│
│                 │  │                 │  │                 │
│ - call_tool()   │  │ - call_tool()   │  │ - call_tool()   │
│ - list_tools()  │  │ - list_tools()  │  │ - list_tools()  │
│ - read_resource()│  │ - read_resource()│  │ - read_resource()│
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                     │
         ▼                    ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ MCP Server      │  │ MCP Server      │  │ MCP Server      │
│ Expedientes     │  │ Firma           │  │ Notificaciones  │
│ :8000           │  │ :8001           │  │ :8002           │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## 🔧 Implementación Propuesta

### **1. Catálogo de MCPs Configurable**

```yaml
# backoffice/config/mcp_servers.yaml

mcp_servers:
  - id: expedientes
    name: "MCP Expedientes"
    description: "Gestión de expedientes y documentos"
    url: http://mcp-expedientes:8000
    type: http
    auth:
      type: jwt
      audience: agentix-mcp-expedientes
    timeout: 30
    max_retries: 3
    capabilities:
      # Descubiertas automáticamente vía tools/list, pero documentadas aquí
      tools:
        - consultar_expediente
        - actualizar_datos
        - añadir_anotacion
        - añadir_documento
      resources:
        - expediente://{expediente_id}
        - documento://{expediente_id}/{documento_id}

  - id: firma
    name: "MCP Firma Electrónica"
    description: "Firma y validación de documentos"
    url: http://mcp-firma:8001
    type: http
    auth:
      type: jwt
      audience: agentix-mcp-firma
    timeout: 60  # Firma puede tardar más
    max_retries: 2
    capabilities:
      tools:
        - firmar_documento
        - validar_firma
        - verificar_certificado

  - id: notificaciones
    name: "MCP Notificaciones"
    description: "Envío de notificaciones electrónicas"
    url: http://mcp-notificaciones:8002
    type: http
    auth:
      type: jwt
      audience: agentix-mcp-notificaciones
    timeout: 30
    max_retries: 3
    capabilities:
      tools:
        - enviar_notificacion
        - consultar_estado_notificacion
```

### **2. Modelo de Configuración**

```python
# backoffice/config/models.py

from pydantic import BaseModel, HttpUrl
from typing import List, Literal, Dict, Any

class MCPAuthConfig(BaseModel):
    """Configuración de autenticación para un MCP"""
    type: Literal["jwt", "api_key", "none"] = "jwt"
    audience: str | None = None  # Para JWT
    api_key_header: str | None = None  # Para API Key

class MCPCapabilities(BaseModel):
    """Capabilities expuestas por un MCP"""
    tools: List[str] = []
    resources: List[str] = []

class MCPServerConfig(BaseModel):
    """Configuración de un servidor MCP"""
    id: str
    name: str
    description: str
    url: HttpUrl
    type: Literal["http", "stdio"] = "http"
    auth: MCPAuthConfig
    timeout: int = 30
    max_retries: int = 3
    capabilities: MCPCapabilities

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
```

### **3. MCPClient (sin cambios, sigue siendo para un solo servidor)**

```python
# backoffice/mcp/client.py

import httpx
from typing import Dict, Any, List
from mcp import types

class MCPClient:
    """
    Cliente para interactuar con UN servidor MCP específico.

    NO cambia respecto a la especificación del Paso 1.
    El routing multi-MCP lo maneja MCPClientRegistry.
    """

    def __init__(
        self,
        server_config: MCPServerConfig,
        token: str
    ):
        """
        Inicializa el cliente MCP.

        Args:
            server_config: Configuración del servidor MCP
            token: Token JWT completo
        """
        self.server_config = server_config
        self.token = token
        self._request_id = 0

        self.client = httpx.AsyncClient(
            base_url=str(server_config.url),
            timeout=float(server_config.timeout),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )

    # ... resto de métodos igual que en step-1-backoffice-skeleton.md
    # call_tool(), list_tools(), read_resource(), close()
```

### **4. MCPClientRegistry (NUEVO componente clave)**

```python
# backoffice/mcp/registry.py

from typing import Dict, List, Optional
from .client import MCPClient
from .exceptions import MCPError, MCPToolError
from backoffice.config.models import MCPServersConfig, MCPServerConfig
import asyncio

class MCPClientRegistry:
    """
    Registro de clientes MCP que maneja routing automático.

    Responsabilidades:
    - Cargar catálogo de MCPs desde configuración
    - Crear MCPClient por cada MCP configurado
    - Descubrir capabilities de cada MCP (cache)
    - Routing: tool_name → MCPClient correcto
    - Gestión del ciclo de vida de clientes
    """

    def __init__(
        self,
        config: MCPServersConfig,
        token: str
    ):
        """
        Inicializa el registro de clientes MCP.

        Args:
            config: Configuración de servidores MCP
            token: Token JWT con múltiples audiencias
        """
        self.config = config
        self.token = token

        # MCPClient por ID de servidor
        self._clients: Dict[str, MCPClient] = {}

        # Cache: tool_name → server_id
        self._tool_routing: Dict[str, str] = {}

        # Cache: server_id → List[tool_name]
        self._server_tools: Dict[str, List[str]] = {}

        # Flag de inicialización
        self._initialized = False

    async def initialize(self):
        """
        Inicializa todos los clientes MCP y descubre capabilities.

        Se ejecuta una vez al crear el registry.
        """
        if self._initialized:
            return

        # 1. Crear cliente por cada MCP configurado
        for server_config in self.config.mcp_servers:
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
        await asyncio.gather(*tasks)

        self._initialized = True

    async def _discover_tools(self, server_id: str):
        """
        Descubre las tools disponibles en un servidor MCP.

        Args:
            server_id: ID del servidor MCP
        """
        client = self._clients[server_id]

        try:
            tools_response = await client.list_tools()

            # Parsear tools (depende de formato MCP)
            # Asumiendo que retorna {"result": {"tools": [{"name": "..."}, ...]}}
            tools = tools_response.get("result", {}).get("tools", [])
            tool_names = [tool["name"] for tool in tools]

            # Cachear
            self._server_tools[server_id] = tool_names

            # Actualizar routing
            for tool_name in tool_names:
                self._tool_routing[tool_name] = server_id

        except Exception as e:
            # Log error pero no fallar
            # Permitir que el sistema funcione aunque un MCP esté caído
            print(f"⚠️ Warning: No se pudieron descubrir tools de MCP '{server_id}': {e}")
            self._server_tools[server_id] = []

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta una tool, haciendo routing automático al MCP correcto.

        Args:
            tool_name: Nombre de la tool (ej: "consultar_expediente")
            arguments: Argumentos de la tool

        Returns:
            Resultado de la tool

        Raises:
            MCPToolError: Si la tool no existe en ningún MCP
            MCPError: Otros errores de ejecución
        """
        if not self._initialized:
            await self.initialize()

        # Routing: buscar qué servidor tiene esta tool
        server_id = self._tool_routing.get(tool_name)

        if not server_id:
            # Tool no encontrada en ningún MCP
            available_tools = list(self._tool_routing.keys())
            raise MCPToolError(
                codigo="MCP_TOOL_NOT_FOUND",
                mensaje=f"Tool '{tool_name}' no encontrada en ningún servidor MCP configurado",
                detalle=f"Tools disponibles: {available_tools}"
            )

        # Delegar al cliente correcto
        client = self._clients[server_id]
        return await client.call_tool(tool_name, arguments)

    async def read_resource(
        self,
        uri: str
    ) -> str:
        """
        Lee un resource, haciendo routing automático al MCP correcto.

        Args:
            uri: URI del resource (ej: "expediente://EXP-2024-001")

        Returns:
            Contenido del resource

        Raises:
            MCPError: Si no se puede leer el resource
        """
        if not self._initialized:
            await self.initialize()

        # Routing por prefijo de URI
        # ej: "expediente://..." → servidor "expedientes"
        # ej: "firma://..." → servidor "firma"

        uri_prefix = uri.split("://")[0] if "://" in uri else ""

        # Buscar servidor que maneje este prefijo
        # (se podría configurar en mcp_servers.yaml)
        server_id = self._find_server_for_resource(uri_prefix)

        if not server_id:
            raise MCPError(
                codigo="MCP_RESOURCE_NOT_FOUND",
                mensaje=f"No hay servidor MCP configurado para resources con prefijo '{uri_prefix}://'"
            )

        client = self._clients[server_id]
        return await client.read_resource(uri)

    def _find_server_for_resource(self, uri_prefix: str) -> Optional[str]:
        """
        Encuentra qué servidor MCP maneja un tipo de resource.

        Args:
            uri_prefix: Prefijo del URI (ej: "expediente", "firma")

        Returns:
            ID del servidor, o None si no se encuentra
        """
        # Mapeo simple: prefijo → server_id
        # Podría ser configurable en mcp_servers.yaml
        mapping = {
            "expediente": "expedientes",
            "documento": "expedientes",
            "firma": "firma",
            "notificacion": "notificaciones"
        }
        return mapping.get(uri_prefix)

    async def get_available_tools(self) -> Dict[str, List[str]]:
        """
        Retorna todas las tools disponibles por servidor.

        Returns:
            Diccionario: server_id → list of tool names
        """
        if not self._initialized:
            await self.initialize()

        return self._server_tools.copy()

    async def close(self):
        """Cierra todos los clientes HTTP"""
        tasks = [client.close() for client in self._clients.values()]
        await asyncio.gather(*tasks)
```

### **5. Actualización de AgentExecutor**

```python
# backoffice/executor.py

from backoffice.mcp.registry import MCPClientRegistry
from backoffice.config.models import MCPServersConfig

class AgentExecutor:
    def __init__(self, mcp_config_path: str = "backoffice/config/mcp_servers.yaml"):
        """
        Inicializa el executor de agentes.

        Args:
            mcp_config_path: Ruta al archivo de configuración de MCPs
        """
        self.mcp_config_path = mcp_config_path

    async def execute(
        self,
        token: str,
        expediente_id: str,
        tarea_id: str,
        agent_config: AgentConfig
    ) -> AgentExecutionResult:
        """Ejecuta un agente con soporte multi-MCP"""

        mcp_registry = None

        try:
            # 1. Cargar configuración de MCPs
            mcp_config = MCPServersConfig.load_from_file(self.mcp_config_path)

            # 2. Crear registry de clientes MCP
            mcp_registry = MCPClientRegistry(
                config=mcp_config,
                token=token
            )

            # 3. Inicializar (discovery de tools)
            await mcp_registry.initialize()

            # 4. Crear logger
            agent_run_id = f"RUN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            logger = AuditLogger(
                expediente_id=expediente_id,
                agent_run_id=agent_run_id,
                log_dir=Path(config.LOG_DIR)
            )

            logger.log(f"Iniciando ejecución de agente {agent_config.nombre}")
            logger.log(f"MCPs disponibles: {list(mcp_registry._clients.keys())}")

            # 5. Crear y ejecutar agente mock
            agent = self._create_agent(
                agent_config=agent_config,
                expediente_id=expediente_id,
                tarea_id=tarea_id,
                mcp_registry=mcp_registry,  # ⬅️ Ahora recibe registry, no client
                logger=logger
            )

            resultado = await agent.execute()

            return AgentExecutionResult(
                success=True,
                agent_run_id=agent_run_id,
                resultado=resultado,
                log_auditoria=logger.get_log_entries(),
                herramientas_usadas=agent.get_tools_used()
            )

        except MCPConnectionError as e:
            # ... manejo de errores igual ...

        finally:
            if mcp_registry:
                await mcp_registry.close()
```

### **6. Actualización de Agentes Mock**

```python
# backoffice/agents/validador_documental.py

from backoffice.mcp.registry import MCPClientRegistry

class ValidadorDocumentalMock(AgentMock):
    def __init__(
        self,
        expediente_id: str,
        tarea_id: str,
        mcp_registry: MCPClientRegistry,  # ⬅️ Ahora recibe registry
        logger: AuditLogger
    ):
        self.expediente_id = expediente_id
        self.tarea_id = tarea_id
        self.mcp_registry = mcp_registry  # ⬅️ Guarda registry
        self.logger = logger

    async def execute(self):
        """Mock del agente ValidadorDocumental con multi-MCP"""

        self.logger.log("Iniciando validación de documentos...")

        # 1. Consultar expediente (routing automático a MCP expedientes)
        self.logger.log(f"Consultando expediente {self.expediente_id}...")
        expediente_result = await self.mcp_registry.call_tool(
            "consultar_expediente",  # ⬅️ Registry hace routing automático
            {"expediente_id": self.expediente_id}
        )

        # Parsear resultado (depende de formato MCP)
        expediente = self._parse_tool_result(expediente_result)

        # 2. Analizar documentos (lógica mock)
        self.logger.log(f"Documentos encontrados: {len(expediente['documentos'])}")

        documentos_requeridos = ["SOLICITUD", "IDENTIFICACION", "BANCARIO"]
        documentos_presentes = [doc["tipo"] for doc in expediente["documentos"]]

        validacion_ok = all(
            doc_tipo in documentos_presentes
            for doc_tipo in documentos_requeridos
        )

        if validacion_ok:
            self.logger.log("Todos los documentos requeridos están presentes")
        else:
            faltantes = set(documentos_requeridos) - set(documentos_presentes)
            self.logger.log(f"Faltan documentos: {faltantes}")

        # 3. Actualizar expediente (routing automático)
        self.logger.log(f"Actualizando campo datos.documentacion_valida = {validacion_ok}")
        await self.mcp_registry.call_tool(
            "actualizar_datos",
            {
                "expediente_id": self.expediente_id,
                "campo": "datos.documentacion_valida",
                "valor": validacion_ok
            }
        )

        # 4. Añadir anotación (routing automático)
        mensaje = "Documentación validada correctamente" if validacion_ok else "Documentación incompleta"
        self.logger.log(f"Añadiendo anotación al historial: {mensaje}")
        await self.mcp_registry.call_tool(
            "añadir_anotacion",
            {
                "expediente_id": self.expediente_id,
                "texto": mensaje
            }
        )

        return {
            "completado": True,
            "mensaje": mensaje,
            "datos_actualizados": {
                "datos.documentacion_valida": validacion_ok
            }
        }
```

### **7. Actualización de JWT Claims**

```python
# mcp-mock/mcp-expedientes/models.py

@dataclass
class JWTClaims:
    """Claims del token JWT (actualizado para multi-MCP)"""
    iss: str  # "agentix-bpmn"
    sub: str  # "Automático"
    aud: List[str]  # ⬅️ AHORA ES LISTA: ["agentix-mcp-expedientes", "agentix-mcp-firma", ...]
    exp: int
    iat: int
    nbf: int
    jti: str
    exp_id: str
    permisos: List[str]
```

```python
# mcp-mock/mcp-expedientes/generate_token.py

def generate_token(
    usuario: str,
    expediente_id: str,
    permisos: List[str],
    audiences: List[str] | None = None  # ⬅️ NUEVO parámetro
) -> str:
    """
    Genera un token JWT con múltiples audiencias.

    Args:
        usuario: Nombre del usuario (debe ser "Automático")
        expediente_id: ID del expediente autorizado
        permisos: Lista de permisos (["consulta"], ["gestion"], etc.)
        audiences: Lista de MCPs autorizados.
                   Si None, solo ["agentix-mcp-expedientes"]

    Returns:
        Token JWT firmado
    """
    if audiences is None:
        audiences = ["agentix-mcp-expedientes"]

    now = int(time.time())

    claims = {
        "iss": "agentix-bpmn",
        "sub": usuario,
        "aud": audiences,  # ⬅️ Lista de audiencias
        "exp": now + 3600,
        "iat": now,
        "nbf": now,
        "jti": f"jwt-{uuid.uuid4()}",
        "exp_id": expediente_id,
        "permisos": permisos
    }

    return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALGORITHM)
```

### **8. Ejemplo de Uso Actualizado**

```python
# example_multi_mcp.py

import asyncio
from backoffice.executor import AgentExecutor
from backoffice.models import AgentConfig
from mcp_expedientes.generate_token import generate_token

async def main():
    # 1. Generar token JWT con MÚLTIPLES AUDIENCIAS
    token = generate_token(
        usuario="Automático",
        expediente_id="EXP-2024-001",
        permisos=["consulta", "gestion"],
        audiences=[
            "agentix-mcp-expedientes",  # ⬅️ Múltiples MCPs
            "agentix-mcp-firma",
            "agentix-mcp-notificaciones"
        ]
    )

    # 2. Configurar el agente
    agent_config = AgentConfig(
        nombre="GeneradorResolucion",
        system_prompt="Eres un generador de resoluciones administrativas",
        modelo="claude-3-5-sonnet-20241022",
        prompt_tarea="Genera resolución de aprobación de subvención",
        herramientas=[
            "consultar_expediente",     # Del MCP expedientes
            "firmar_documento",          # Del MCP firma
            "enviar_notificacion"        # Del MCP notificaciones
        ]
    )

    # 3. Crear executor (carga config de MCPs automáticamente)
    executor = AgentExecutor()

    # 4. Ejecutar agente (routing automático multi-MCP)
    resultado = await executor.execute(
        token=token,
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-GENERAR-RESOLUCION-001",
        agent_config=agent_config
    )

    # 5. Verificar resultado
    if resultado.success:
        print(f"✅ Agente ejecutado: {resultado.agent_run_id}")
        print(f"   Usó {len(resultado.herramientas_usadas)} herramientas de diferentes MCPs")
        print(f"   Herramientas: {resultado.herramientas_usadas}")
    else:
        print(f"❌ Error: {resultado.error.codigo}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📊 Comparación: Antes vs. Después

### **Paso 1 Original (mono-MCP)**

```
AgentExecutor
  └─ MCPClient (un solo servidor hardcodeado)
       └─ http://localhost:8000
```

**Limitaciones:**
- ❌ Solo un MCP
- ❌ URL hardcodeada en config
- ❌ Añadir nuevo MCP = cambiar código
- ❌ No escalable

### **Paso 1 Rediseñado (multi-MCP)**

```
AgentExecutor
  └─ MCPClientRegistry (catálogo configurable)
       ├─ MCPClient (expedientes) → http://mcp-expedientes:8000
       ├─ MCPClient (firma) → http://mcp-firma:8001
       └─ MCPClient (notificaciones) → http://mcp-notificaciones:8002
```

**Ventajas:**
- ✅ Múltiples MCPs
- ✅ Catálogo en YAML (sin cambiar código)
- ✅ Routing automático tool → MCP
- ✅ Discovery de capabilities
- ✅ Escalable a N servidores

---

## 🎯 Líneas de Acción Propuestas

### **Opción A: Implementar Multi-MCP desde el Paso 1** ⭐ **RECOMENDADO**

**Justificación:**
- Evita refactorización completa después
- La complejidad adicional es manejable (~300 líneas más)
- Valida arquitectura real desde el principio
- Añadir segundo MCP será trivial (solo config)

**Esfuerzo adicional estimado:**
- Implementar `MCPClientRegistry`: ~3 horas
- Actualizar `AgentExecutor`: ~1 hora
- Actualizar modelos de config: ~1 hora
- Actualizar tests: ~2 horas
- Actualizar documentación: ~1 hora
- **Total: ~8 horas adicionales** sobre el Paso 1 original

**Entregables del Paso 1 actualizado:**
1. ✅ `backoffice/config/mcp_servers.yaml` (catálogo de MCPs)
2. ✅ `backoffice/config/models.py` (modelos Pydantic de config)
3. ✅ `backoffice/mcp/registry.py` (MCPClientRegistry)
4. ✅ `backoffice/mcp/client.py` (MCPClient sin cambios)
5. ✅ `backoffice/executor.py` (usa registry en vez de client único)
6. ✅ Tests de multi-MCP
7. ✅ Ejemplo de uso con 2-3 MCPs mock

**Criterio de aceptación adicional:**
- ✅ Añadir un nuevo MCP requiere SOLO editar `mcp_servers.yaml` (sin tocar código)
- ✅ Agente puede usar herramientas de 2+ MCPs diferentes en una ejecución
- ✅ Routing automático funciona correctamente
- ✅ Errores de un MCP no afectan a otros MCPs

### **Opción B: Paso 1 mono-MCP + Paso 1.5 para multi-MCP**

**Justificación:**
- Validar primero arquitectura básica
- Añadir multi-MCP como mejora incremental
- Menor riesgo de sobre-ingeniería

**Fases:**
1. **Paso 1 (original):** Back-office con un solo MCP
2. **Paso 1.5 (nuevo):** Refactorizar para multi-MCP
3. **Paso 2:** API REST (usa multi-MCP)

**Desventajas:**
- ⚠️ Refactorización entre Paso 1 y 1.5 (cambios en interfaces)
- ⚠️ Tests del Paso 1 hay que reescribirlos
- ⚠️ Riesgo de postponer indefinidamente el Paso 1.5

### **Opción C: Paso 1 mono-MCP + Documentar requisito multi-MCP para el futuro**

**Justificación:**
- YAGNI (You Aren't Gonna Need It): implementar solo cuando se necesite
- El segundo MCP no existe todavía
- Optimizar para aprender rápido

**Desventajas:**
- ❌ **PELIGRO: Deuda técnica alta**
- ❌ Cuando llegue el segundo MCP, refactorización completa
- ❌ No valida arquitectura real
- ❌ Riesgo de descubrir problemas tarde

---

## 🏆 Recomendación Final

### **Implementar Multi-MCP desde el Paso 1 (Opción A)**

**Razones:**

1. **Tu argumentación revela requisito real del sistema**
   - GEX integra con múltiples sistemas (doc/004-integraciones.md)
   - Cada integración merece su propio MCP
   - El segundo MCP llegará pronto (firma, notificaciones, etc.)

2. **Esfuerzo adicional es razonable**
   - ~8 horas adicionales es aceptable
   - Evita semanas de refactorización después
   - Complejidad conceptual es manejable

3. **Valida arquitectura plug-and-play desde el inicio**
   - Criterio de aceptación: "Añadir MCP = editar YAML"
   - Si esto no funciona en el Paso 1, no funcionará después

4. **Alineado con principios del proyecto**
   - Modularidad (doc/040-criterios-diseño.md)
   - No acoplamiento (doc/040-criterios-diseño.md)
   - Acceso vía MCP (doc/042-acceso-mcp.md)

5. **El mock perfecto para validar esto**
   - Paso 1 es un mock, ideal para experimentar
   - Podemos crear 2-3 MCPs mock triviales para validar routing
   - Bajo riesgo, alto aprendizaje

### **Plan de Implementación Actualizado**

```
Paso 1 Rediseñado: Back-Office Mock con Multi-MCP
├─ Día 1-2: Configuración y modelos
│   ├─ mcp_servers.yaml
│   ├─ config/models.py
│   └─ Tests de carga de config
│
├─ Día 3-4: MCPClientRegistry
│   ├─ registry.py
│   ├─ Discovery de tools
│   ├─ Routing automático
│   └─ Tests de registry
│
├─ Día 5: Actualizar MCPClient
│   ├─ Recibe MCPServerConfig en vez de URL
│   └─ Tests (sin cambios mayores)
│
├─ Día 6: Actualizar AgentExecutor
│   ├─ Usa MCPClientRegistry
│   └─ Tests de integración
│
├─ Día 7-8: Crear MCPs mock adicionales
│   ├─ MCP Firma mock (solo 1-2 tools)
│   ├─ MCP Notificaciones mock (solo 1-2 tools)
│   └─ Tests end-to-end multi-MCP
│
├─ Día 9: Actualizar agentes mock
│   ├─ Agente que usa múltiples MCPs
│   └─ Tests
│
└─ Día 10: Documentación y cierre
    ├─ README actualizado
    ├─ Ejemplo de uso multi-MCP
    └─ Criterios de aceptación validados
```

**Duración total:** ~10 días (vs. ~7 días del Paso 1 original)

### **Siguiente Paso Inmediato**

1. **Actualizar documento `step-1-backoffice-skeleton.md`** con arquitectura multi-MCP:
   - Añadir sección "Arquitectura Multi-MCP"
   - Actualizar requisitos funcionales
   - Actualizar estructura de proyecto
   - Actualizar criterios de aceptación
   - Actualizar ejemplos de uso

2. **Crear `step-1-mcp-servers-example.yaml`** con 2-3 MCPs mock:
   - expedientes (ya existe)
   - firma (crear mock trivial)
   - notificaciones (crear mock trivial)

3. **Actualizar `step-1-critique.md`** con nueva evaluación:
   - Marcar el problema de "mono-MCP" como identificado
   - Documentar decisión de multi-MCP desde Paso 1
   - Actualizar estimaciones de esfuerzo

---

## 📋 Checklist de Decisión

Antes de proceder, confirmar:

- [ ] **¿Realmente necesitarás múltiples MCPs en los próximos 6 meses?**
  - Si SÍ → Implementar multi-MCP ahora (Opción A)
  - Si NO → Postergar a Paso 1.5 (Opción B)

- [ ] **¿El equipo tiene capacidad para 8 horas adicionales en Paso 1?**
  - Si SÍ → Opción A viable
  - Si NO → Opción B o C

- [ ] **¿Es crítico validar arquitectura plug-and-play desde el inicio?**
  - Si SÍ → Opción A
  - Si NO → Opción B aceptable

- [ ] **¿Hay claridad sobre qué otros MCPs se necesitan?**
  - Si SÍ (firma, notificaciones, etc.) → Opción A
  - Si NO (muy incierto) → Opción B o C

**Mi recomendación basada en tu argumentación:**
- ✅ Implementar multi-MCP ahora (Opción A)
- ✅ Crear 2-3 MCPs mock triviales para validar
- ✅ Actualizar Paso 1 con arquitectura multi-MCP

---

## 🔗 Referencias

- Especificación Paso 1: `/prompts/step-1-backoffice-skeleton.md`
- Crítica Paso 1: `/prompts/step-1-critique.md`
- Integraciones GEX: `/doc/004-integraciones.md`
- Criterios de diseño: `/doc/040-criterios-diseño.md`
- Acceso MCP: `/doc/042-acceso-mcp.md`

---

**Fin del documento de análisis**
