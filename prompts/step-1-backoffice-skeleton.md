# Paso 1: Crear Esqueleto de Back-Office (Mock Funcional)

## Objetivo

Crear un esqueleto de back-office que **simule** el comportamiento del sistema de agentes IA, cubriendo todos los requisitos funcionales y de arquitectura sin implementar aún la lógica real de agentes.

Este mock funcional permitirá:

- Validar el diseño de la arquitectura
- Probar la integración con BPMN
- Verificar el flujo de permisos
- Establecer las interfaces que luego implementará el sistema real

## Contexto del Sistema

### Componentes Existentes

Ya disponemos de:

- **MCP Mock Server** (`/mcp-mock/mcp-expedientes/`): Servidor MCP que expone:
  - **Resources**: Información de expedientes (lectura)
  - **Tools**: Acciones sobre expedientes (lectura/escritura)
  - **Autenticación JWT**: Validación de tokens con claims `usuario` y `expediente_id`
  - **Datos de prueba**: Expedientes de ejemplo en formato JSON

### Arquitectura del Sistema

```text
BPMN (GEX) → [API REST - Paso 2] → Back-Office (a crear) → MCP → API (futuro) → GEX
                                    ├─ Validación JWT
                                    ├─ Configuración Agente
                                    ├─ Mock de Ejecución
                                    └─ Logging/Auditoría
```

## Requisitos Funcionales

### 1. Interfaz Principal (Clase AgentExecutor)

El back-office debe proporcionar una clase `AgentExecutor` que exponga el método principal para ejecutar agentes.

**IMPORTANTE**: En este paso NO se crea ninguna API REST. Esto es solo lógica de negocio (clases y funciones Python) que en el Paso 2 será envuelta en una API FastAPI.

#### Método: `AgentExecutor.execute()`

Ejecuta una acción de agente para una tarea BPMN.

**Firma del método:**

```python
async def execute(
    self,
    token: str,
    expediente_id: str,
    tarea_id: str,
    agent_config: AgentConfig
) -> AgentExecutionResult
```

**Parámetros de entrada (AgentConfig):**

```python
@dataclass
class AgentConfig:
    nombre: str  # "ValidadorDocumental"
    system_prompt: str  # "Eres un validador..."
    modelo: str  # "claude-3-5-sonnet-20241022"
    prompt_tarea: str  # "Valida que todos los documentos..."
    herramientas: List[str]  # ["consultar_expediente", "actualizar_datos", ...]
```

**Resultado exitoso (AgentExecutionResult):**

```python
@dataclass
class AgentExecutionResult:
    success: bool
    agent_run_id: str
    resultado: Dict[str, Any]  # {"completado": True, "mensaje": "...", "datos_actualizados": {...}}
    log_auditoria: List[str]  # ["Iniciando validación...", "Consultando expediente..."]
    herramientas_usadas: List[str]  # ["consultar_expediente", "actualizar_datos"]
    error: Optional[AgentError] = None
```

**Resultado con error:**

```python
@dataclass
class AgentError:
    codigo: str  # "AUTH_INVALID_TOKEN"
    mensaje: str  # "Token JWT inválido o expirado"
```

### 2. Validación JWT

El sistema debe validar tokens JWT con la siguiente estructura completa de claims:

#### Claims Obligatorios

```json
{
  "iss": "agentix-bpmn",
  "sub": "Automático",
  "aud": ["agentix-mcp-expedientes"],
  "exp": 1234567890,
  "iat": 1234567890,
  "nbf": 1234567890,
  "jti": "unique-run-id-12345",
  "exp_id": "EXP-2024-001",
  "permisos": ["consulta", "gestion"]
}
```

**Descripción de cada claim:**

- **`iss` (issuer):** Emisor del token. Debe ser exactamente `"agentix-bpmn"`
- **`sub` (subject):** Usuario que ejecuta la acción. Debe ser exactamente `"Automático"`
- **`aud` (audience):** Audiencias autorizadas. Debe incluir `"agentix-mcp-expedientes"`
- **`exp` (expiration):** Timestamp de expiración. El token no debe estar expirado (exp > now)
- **`iat` (issued at):** Timestamp de emisión del token
- **`nbf` (not before):** Timestamp desde el cual el token es válido (nbf <= now)
- **`jti` (JWT ID):** Identificador único del token. Usado para revocación y auditoría
- **`exp_id`:** ID del expediente autorizado (ej: `"EXP-2024-001"`). **IMPORTANTE:** Es `exp_id`, NO `expediente_id`
- **`permisos`:** Array de permisos del agente. Valores posibles: `["consulta"]`, `["gestion"]`, o `["consulta", "gestion"]`

#### Validaciones a Realizar

El sistema debe validar cada uno de los siguientes aspectos:

1. **Firma JWT:** Validar con `JWT_SECRET` (misma clave que el servidor MCP mock)
2. **Emisor (iss):** Debe ser exactamente `"agentix-bpmn"`
3. **Subject (sub):** Debe ser exactamente `"Automático"`
4. **Audiencia (aud):** Debe incluir `"agentix-mcp-expedientes"` (puede ser string o array)
5. **Expiración (exp):** Token no expirado (exp > now)
6. **Not Before (nbf):** Token ya válido (nbf <= now)
7. **Expediente (exp_id):** Debe coincidir exactamente con el `expediente_id` de la request
8. **Permisos:** Debe contener los permisos necesarios para las herramientas solicitadas en `agent_config.herramientas`

#### Rechazo de Tokens Inválidos

El sistema debe rechazar tokens y devolver errores específicos según el problema:

- Token con claims faltantes → Error `AUTH_INVALID_TOKEN`
- Token con firma inválida → Error `AUTH_INVALID_TOKEN`
- Token con emisor incorrecto (`iss` != "agentix-bpmn") → Error `AUTH_PERMISSION_DENIED`
- Token con subject incorrecto (`sub` != "Automático") → Error `AUTH_PERMISSION_DENIED`
- Token sin audiencia correcta → Error `AUTH_PERMISSION_DENIED`
- Token con expediente diferente (`exp_id` != `expediente_id`) → Error `AUTH_EXPEDIENTE_MISMATCH`
- Token expirado (exp < now) → Error `AUTH_TOKEN_EXPIRED`
- Token aún no válido (nbf > now) → Error `AUTH_TOKEN_NOT_YET_VALID`
- Permisos insuficientes → Error `AUTH_INSUFFICIENT_PERMISSIONS`

#### Propagación del Token

El token JWT completo debe propagarse **sin modificaciones** en todas las llamadas al servidor MCP.

El servidor MCP realizará su propia validación independiente de los mismos claims.

#### Implementación de Referencia

Ver implementación existente en:

- **Validación de JWT:** `/mcp-mock/mcp-expedientes/auth.py` (función `validate_jwt()`)
- **Modelo de claims:** `/mcp-mock/mcp-expedientes/models.py` (clase `JWTClaims`)
- **Generación de tokens:** `/mcp-mock/mcp-expedientes/generate_token.py`

**IMPORTANTE:** El back-office debe usar **exactamente la misma estructura de claims** que el servidor MCP existente para garantizar compatibilidad.

### 3. Mock de Ejecución de Agente

Dado que en este paso **NO** implementamos agentes reales (LangGraph/CrewAI), el mock debe:

1. **Simular el comportamiento de un agente** siguiendo un script predefinido
2. Para cada tipo de agente (según `agent_config.nombre`), tener un **comportamiento hardcodeado**
3. **Llamar realmente al MCP** para leer/escribir datos (no mockear el MCP, ya existe)
4. **Registrar cada paso** en el log de auditoría

#### Ejemplo: Agente "ValidadorDocumental"

```python
async def mock_validador_documental(expediente_id: str, mcp_client: MCPClient, logger: Logger):
    """Mock del agente ValidadorDocumental"""

    logger.log("Iniciando validación de documentos...")

    # 1. Consultar expediente (llamada real a MCP)
    logger.log(f"Consultando expediente {expediente_id}...")
    expediente = await mcp_client.call_tool("consultar_expediente", {
        "expediente_id": expediente_id
    })

    # 2. Analizar documentos (lógica mock)
    logger.log(f"Documentos encontrados: {len(expediente['documentos'])}")

    documentos_requeridos = ["SOLICITUD", "IDENTIFICACION", "BANCARIO"]
    documentos_presentes = [doc["tipo"] for doc in expediente["documentos"]]

    validacion_ok = all(doc_tipo in documentos_presentes for doc_tipo in documentos_requeridos)

    if validacion_ok:
        logger.log("Todos los documentos requeridos están presentes")
    else:
        logger.log(f"Faltan documentos: {set(documentos_requeridos) - set(documentos_presentes)}")

    # 3. Actualizar expediente (llamada real a MCP)
    logger.log(f"Actualizando campo datos.documentacion_valida = {validacion_ok}")
    await mcp_client.call_tool("actualizar_datos", {
        "expediente_id": expediente_id,
        "campo": "datos.documentacion_valida",
        "valor": validacion_ok
    })

    # 4. Añadir anotación (llamada real a MCP)
    mensaje = "Documentación validada correctamente" if validacion_ok else "Documentación incompleta"
    logger.log(f"Añadiendo anotación al historial: {mensaje}")
    await mcp_client.call_tool("añadir_anotacion", {
        "expediente_id": expediente_id,
        "texto": mensaje
    })

    return {
        "completado": True,
        "mensaje": mensaje,
        "datos_actualizados": {
            "datos.documentacion_valida": validacion_ok
        }
    }
```

### 4. Cliente MCP - Especificación Técnica

El back-office debe incluir un cliente MCP HTTP que se comunique con el servidor MCP mock.

#### Principios de Diseño

**Separación de responsabilidades:**
- **Cliente MCP:** Detectar errores, clasificarlos, propagarlos claramente
- **Sistema BPMN:** Decidir estrategia de recuperación (reintentos, escalamiento)

⚠️ **El cliente NO debe implementar lógica de reintentos complejos**. El sistema BPMN ya cuenta con gestión de errores y recuperación a nivel de tarea.

#### Bibliotecas y Dependencias

```python
# requirements.txt
mcp>=1.0.0          # SDK oficial MCP (para tipos y protocolo)
httpx>=0.25.0       # Cliente HTTP asíncrono
pydantic>=2.0       # Validación de datos
```

**Justificación:**
- `mcp`: Proporciona tipos correctos (`types.Tool`, `types.TextContent`, etc.)
- `httpx`: Cliente HTTP asíncrono con control fino de timeouts y headers
- NO usar `tenacity` ni bibliotecas de reintentos (responsabilidad del BPMN)

#### Estructura de Requests (JSON-RPC 2.0)

El cliente debe usar el protocolo **JSON-RPC 2.0** estándar de MCP:

**Request para `call_tool`:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "consultar_expediente",
    "arguments": {
      "expediente_id": "EXP-2024-001"
    }
  }
}
```

**Endpoint HTTP:**
```
POST /sse
Headers:
  Authorization: Bearer <JWT>
  Content-Type: application/json
```

**Response exitosa:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{...json del expediente...}"
      }
    ]
  }
}
```

**Response con error:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": {"detail": "..."}
  }
}
```

#### Propagación del JWT

El token JWT debe pasarse en el **header HTTP `Authorization`**:

```python
client = httpx.AsyncClient(
    base_url="http://localhost:8000",
    timeout=30.0,
    headers={
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
)
```

**Validado con servidor existente:**

El servidor MCP HTTP (`/mcp-mock/mcp-expedientes/server_http.py`) ya espera este formato:

```python
# server_http.py líneas 79-82
auth_header = request.headers.get("Authorization", "")
if auth_header.startswith("Bearer "):
    token = auth_header[7:]
    context.set_token(token)
```

#### Implementación del Cliente

```python
# backoffice/mcp/client.py

import httpx
from typing import Dict, Any, List
from mcp import types

class MCPClient:
    """
    Cliente MCP HTTP simple que propaga errores al sistema BPMN.

    NO implementa reintentos complejos - esa responsabilidad es del BPMN.
    """

    def __init__(self, base_url: str, token: str):
        """
        Inicializa el cliente MCP.

        Args:
            base_url: URL base del servidor MCP (ej: http://localhost:8000)
            token: Token JWT completo
        """
        self.base_url = base_url
        self.token = token
        self._request_id = 0

        # Cliente HTTP con timeout único
        # El BPMN tiene timeouts de tarea más sofisticados
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=30.0,  # 30 segundos para cualquier operación
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )

    def _next_request_id(self) -> int:
        """Genera ID único para request JSON-RPC"""
        self._request_id += 1
        return self._request_id

    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> List[types.TextContent]:
        """
        Ejecuta una tool en el servidor MCP.

        NO reintenta - el sistema BPMN maneja reintentos a nivel de tarea.

        Args:
            name: Nombre de la tool (ej: "consultar_expediente")
            arguments: Argumentos de la tool

        Returns:
            Contenido de la respuesta

        Raises:
            MCPConnectionError: Error de conexión con servidor
            MCPAuthError: Error de autenticación/autorización
            MCPToolError: Error al ejecutar la tool
        """
        try:
            response = await self.client.post(
                "/sse",
                json={
                    "jsonrpc": "2.0",
                    "id": self._next_request_id(),
                    "method": "tools/call",
                    "params": {
                        "name": name,
                        "arguments": arguments
                    }
                }
            )

            # Lanzar excepción si status code indica error
            response.raise_for_status()

            # Parsear respuesta JSON-RPC
            data = response.json()

            # Verificar si hay error en respuesta JSON-RPC
            if "error" in data:
                raise MCPToolError(
                    codigo="MCP_TOOL_ERROR",
                    mensaje=f"Error en tool '{name}': {data['error']['message']}",
                    detalle=str(data['error'])
                )

            # Retornar result
            return data.get("result", {})

        except httpx.TimeoutException as e:
            raise MCPConnectionError(
                codigo="MCP_TIMEOUT",
                mensaje=f"Timeout al ejecutar tool '{name}' (>30s)",
                detalle=str(e)
            )

        except httpx.ConnectError as e:
            raise MCPConnectionError(
                codigo="MCP_CONNECTION_ERROR",
                mensaje=f"No se puede conectar al servidor MCP: {self.base_url}",
                detalle=str(e)
            )

        except httpx.HTTPStatusError as e:
            status = e.response.status_code

            if status == 401:
                raise MCPAuthError(
                    codigo="AUTH_INVALID_TOKEN",
                    mensaje="Token JWT inválido o expirado",
                    detalle=e.response.text
                )

            elif status == 403:
                raise MCPAuthError(
                    codigo="AUTH_PERMISSION_DENIED",
                    mensaje="Permisos insuficientes para ejecutar tool",
                    detalle=e.response.text
                )

            elif status == 404:
                raise MCPToolError(
                    codigo="MCP_TOOL_NOT_FOUND",
                    mensaje=f"Tool '{name}' no encontrada en servidor MCP",
                    detalle=e.response.text
                )

            elif status in [502, 503, 504]:
                raise MCPConnectionError(
                    codigo="MCP_SERVER_UNAVAILABLE",
                    mensaje=f"Servidor MCP no disponible (HTTP {status})",
                    detalle=e.response.text
                )

            else:
                raise MCPToolError(
                    codigo="MCP_TOOL_ERROR",
                    mensaje=f"Error al ejecutar tool '{name}' (HTTP {status})",
                    detalle=e.response.text
                )

        except MCPError:
            # Re-lanzar errores MCP ya clasificados
            raise

        except Exception as e:
            raise MCPConnectionError(
                codigo="MCP_UNEXPECTED_ERROR",
                mensaje=f"Error inesperado al llamar a MCP: {type(e).__name__}",
                detalle=str(e)
            )

    async def list_tools(self) -> List[types.Tool]:
        """
        Lista todas las tools disponibles en el servidor MCP.

        Returns:
            Lista de tools disponibles

        Raises:
            MCPConnectionError: Error de conexión
            MCPAuthError: Error de autenticación
        """
        try:
            response = await self.client.post(
                "/sse",
                json={
                    "jsonrpc": "2.0",
                    "id": self._next_request_id(),
                    "method": "tools/list"
                }
            )

            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise MCPToolError(
                    codigo="MCP_TOOL_ERROR",
                    mensaje=f"Error al listar tools: {data['error']['message']}",
                    detalle=str(data['error'])
                )

            return data.get("result", [])

        except httpx.HTTPError as e:
            # Reutilizar misma lógica de clasificación de errores
            # (simplificado para el ejemplo)
            raise MCPConnectionError(
                codigo="MCP_CONNECTION_ERROR",
                mensaje=f"Error al listar tools: {str(e)}",
                detalle=str(e)
            )

    async def read_resource(self, uri: str) -> str:
        """
        Lee un resource del servidor MCP.

        Args:
            uri: URI del resource (ej: "expediente://EXP-2024-001")

        Returns:
            Contenido del resource

        Raises:
            MCPConnectionError: Error de conexión
            MCPAuthError: Error de autenticación
        """
        try:
            response = await self.client.post(
                "/sse",
                json={
                    "jsonrpc": "2.0",
                    "id": self._next_request_id(),
                    "method": "resources/read",
                    "params": {"uri": uri}
                }
            )

            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise MCPToolError(
                    codigo="MCP_RESOURCE_ERROR",
                    mensaje=f"Error al leer resource '{uri}': {data['error']['message']}",
                    detalle=str(data['error'])
                )

            return data.get("result", "")

        except httpx.HTTPError as e:
            raise MCPConnectionError(
                codigo="MCP_CONNECTION_ERROR",
                mensaje=f"Error al leer resource: {str(e)}",
                detalle=str(e)
            )

    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()
```

#### Excepciones Estructuradas

```python
# backoffice/mcp/exceptions.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class MCPError(Exception):
    """Error base del cliente MCP"""
    codigo: str
    mensaje: str
    detalle: Optional[str] = None

    def __str__(self):
        return f"[{self.codigo}] {self.mensaje}"


@dataclass
class MCPConnectionError(MCPError):
    """
    Error de conexión con servidor MCP.

    Errores incluidos:
    - MCP_TIMEOUT: Timeout en la request
    - MCP_CONNECTION_ERROR: No se puede conectar
    - MCP_SERVER_UNAVAILABLE: Servidor retorna 502/503/504
    """
    pass


@dataclass
class MCPToolError(MCPError):
    """
    Error al ejecutar una tool MCP.

    Errores incluidos:
    - MCP_TOOL_ERROR: Error genérico en tool
    - MCP_TOOL_NOT_FOUND: Tool no existe (404)
    """
    pass


@dataclass
class MCPAuthError(MCPError):
    """
    Error de autenticación/autorización con MCP.

    Errores incluidos:
    - AUTH_INVALID_TOKEN: Token inválido (401)
    - AUTH_PERMISSION_DENIED: Permisos insuficientes (403)
    """
    pass
```

#### Propagación de Errores al AgentExecutor

El `AgentExecutor` debe capturar excepciones del cliente MCP y convertirlas en `AgentError`:

```python
# backoffice/executor.py

class AgentExecutor:
    async def execute(
        self,
        token: str,
        expediente_id: str,
        tarea_id: str,
        agent_config: AgentConfig
    ) -> AgentExecutionResult:
        """Ejecuta un agente y maneja errores del cliente MCP"""

        mcp_client = None

        try:
            # Crear cliente MCP
            mcp_client = MCPClient(
                base_url=config.MCP_SERVER_URL,
                token=token
            )

            # Crear y ejecutar agente mock
            agent = self._create_agent(
                agent_config=agent_config,
                expediente_id=expediente_id,
                tarea_id=tarea_id,
                mcp_client=mcp_client
            )

            resultado = await agent.execute()

            return AgentExecutionResult(
                success=True,
                agent_run_id=agent.run_id,
                resultado=resultado,
                log_auditoria=agent.logger.get_log_entries(),
                herramientas_usadas=agent.get_tools_used()
            )

        except MCPConnectionError as e:
            # Error de conexión - propagar al BPMN
            logger.error(f"Error de conexión MCP: {e}")
            return AgentExecutionResult(
                success=False,
                agent_run_id=agent.run_id if agent else "ERROR",
                resultado={},
                log_auditoria=agent.logger.get_log_entries() if agent else [],
                herramientas_usadas=[],
                error=AgentError(
                    codigo=e.codigo,  # "MCP_TIMEOUT", "MCP_CONNECTION_ERROR", etc.
                    mensaje=e.mensaje
                )
            )

        except MCPAuthError as e:
            # Error de autenticación - propagar al BPMN
            logger.error(f"Error de autenticación MCP: {e}")
            return AgentExecutionResult(
                success=False,
                agent_run_id=agent.run_id if agent else "ERROR",
                resultado={},
                log_auditoria=agent.logger.get_log_entries() if agent else [],
                herramientas_usadas=[],
                error=AgentError(
                    codigo=e.codigo,
                    mensaje=e.mensaje
                )
            )

        except MCPToolError as e:
            # Error en tool - propagar al BPMN
            logger.error(f"Error en tool MCP: {e}")
            return AgentExecutionResult(
                success=False,
                agent_run_id=agent.run_id if agent else "ERROR",
                resultado={},
                log_auditoria=agent.logger.get_log_entries() if agent else [],
                herramientas_usadas=[],
                error=AgentError(
                    codigo=e.codigo,
                    mensaje=e.mensaje
                )
            )

        finally:
            # Cerrar cliente MCP
            if mcp_client:
                await mcp_client.close()
```

#### Gestión de Errores: Responsabilidad del BPMN

**Clasificación de errores para que el BPMN decida:**

| Código | Tipo | Sugerencia BPMN | Razón |
|--------|------|-----------------|-------|
| `MCP_TIMEOUT` | Temporal | Reintentar | Servidor lento, podría recuperarse |
| `MCP_CONNECTION_ERROR` | Temporal | Reintentar | Servidor caído, podría reiniciarse |
| `MCP_SERVER_UNAVAILABLE` | Temporal | Reintentar | 502/503/504, problema temporal |
| `AUTH_INVALID_TOKEN` | Permanente | Escalar a humano | Token inválido no se arregla solo |
| `AUTH_PERMISSION_DENIED` | Permanente | Escalar a humano | Permisos mal configurados |
| `MCP_TOOL_NOT_FOUND` | Permanente | Escalar a humano | Tool no existe, error de configuración |
| `MCP_TOOL_ERROR` | Depende | Analizar detalle | Puede ser temporal o permanente |

**Ejemplo de configuración BPMN (fuera del alcance del back-office):**

```yaml
# El BPMN decide la estrategia de recuperación por cada tarea
tarea_validar_documentos:
  tipo: agente
  agente: ValidadorDocumental

  on_error:
    MCP_TIMEOUT:
      accion: reintentar
      max_reintentos: 3
      intervalo: 60s

    AUTH_INVALID_TOKEN:
      accion: escalar_humano
      notificar: supervisor
```

#### Por Qué NO Reintentos en el Cliente

**Razones para delegar reintentos al BPMN:**

- ❌ **Duplicación:** El BPMN ya tiene sistema de reintentos a nivel de tarea
- ❌ **Falta de contexto:** Reintentos en cliente son "ciegos", no conocen el workflow
- ❌ **Complejidad innecesaria:** Añade dependencias y código complejo
- ❌ **Logs confusos:** Dificulta distinguir fallos reales de reintentos
- ❌ **Timeouts inconsistentes:** Timeout del cliente + timeout del BPMN = confusión

**Beneficios de propagar errores estructurados:**

- ✅ **Separación de responsabilidades:** Cliente detecta, BPMN decide
- ✅ **Flexibilidad:** BPMN puede tener estrategias diferentes por tarea
- ✅ **Simplicidad:** Código del cliente limpio y predecible
- ✅ **Trazabilidad:** Logs claros de qué falló y cuándo
- ✅ **Control centralizado:** Lógica de recuperación en un solo lugar

#### Referencias

- **Especificación MCP:** https://modelcontextprotocol.io/
- **Servidor HTTP existente:** `/mcp-mock/mcp-expedientes/server_http.py`
- **Autenticación JWT:** `/mcp-mock/mcp-expedientes/auth.py`
- **Modelos de datos:** `/mcp-mock/mcp-expedientes/models.py`

### 5. Sistema de Logging y Auditoría con Protección de Datos Personales

#### Obligación de Logging

El sistema debe registrar **todos los pasos** del agente según requisito `/doc/033-auditoria-agente.md`.

#### Estructura de Logs

Cada entrada debe tener:

- **Timestamp** (ISO 8601 con timezone UTC)
- **Nivel** (INFO, WARNING, ERROR)
- **Mensaje descriptivo**
- **Contexto** (expediente_id, tarea_id, agent_run_id)
- **Metadata adicional** según tipo de evento (opcional)

Los logs deben:

- Guardarse en fichero: `/logs/agent_runs/{expediente_id}/{agent_run_id}.log`
- Devolverse en la response para que BPMN los registre
- Formato estructurado (JSON lines) para facilitar análisis
- **CRÍTICO:** Redactar automáticamente PII antes de escribirse a disco

#### Redacción Automática de PII (Cumplimiento GDPR/LOPD)

**CRÍTICO para cumplimiento normativo:**

Los logs deben sanitizar automáticamente **información personal identificable (PII)** antes de escribirse a disco para cumplir con:

- **GDPR Art. 32** (Seguridad del tratamiento)
- **LOPD** (Ley Orgánica de Protección de Datos española)
- **ENS** (Esquema Nacional de Seguridad) para administración pública

**Implementación del redactor de PII:**

```python
# backoffice/logging/pii_redactor.py

import re
from typing import Dict, Pattern

class PIIRedactor:
    """
    Redacta automáticamente información personal identificable (PII).

    Cumplimiento: GDPR Art. 32, LOPD, ENS
    """

    # Patrones de redacción
    PATTERNS: Dict[str, Pattern] = {
        "dni": re.compile(r'\b\d{8}[A-Z]\b'),
        "nie": re.compile(r'\b[XYZ]\d{7}[A-Z]\b'),
        "email": re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'),
        "telefono": re.compile(r'\b[6-9]\d{8}\b'),
        "iban": re.compile(r'\bES\d{22}\b'),
        "tarjeta": re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
        "ccc": re.compile(r'\b\d{20}\b'),  # Código Cuenta Cliente
    }

    @classmethod
    def redact(cls, text: str) -> str:
        """
        Redacta todos los patrones de PII en el texto.

        Args:
            text: Texto que puede contener PII

        Returns:
            Texto con PII redactada

        Examples:
            >>> PIIRedactor.redact("DNI: 12345678A")
            'DNI: [DNI-REDACTED]'
            >>> PIIRedactor.redact("Email: juan@example.com")
            'Email: [EMAIL-REDACTED]'
        """
        redacted = text
        for pii_type, pattern in cls.PATTERNS.items():
            redacted = pattern.sub(f'[{pii_type.upper()}-REDACTED]', redacted)
        return redacted
```

**Implementación del logger de auditoría:**

```python
# backoffice/logging/audit_logger.py

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from .pii_redactor import PIIRedactor

class AuditLogger:
    """
    Logger de auditoría con redacción automática de PII.

    Todos los mensajes y metadata se redactan automáticamente antes
    de escribirse a disco para cumplir con GDPR/LOPD/ENS.
    """

    def __init__(self, expediente_id: str, agent_run_id: str, log_dir: Path):
        """
        Inicializa el logger de auditoría.

        Args:
            expediente_id: ID del expediente
            agent_run_id: ID único de esta ejecución del agente
            log_dir: Directorio base para logs
        """
        self.expediente_id = expediente_id
        self.agent_run_id = agent_run_id
        self.log_dir = log_dir
        self.log_file = log_dir / expediente_id / f"{agent_run_id}.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._entries = []

    def log(
        self,
        mensaje: str,
        nivel: str = "INFO",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Registra una entrada en el log CON REDACCIÓN AUTOMÁTICA DE PII.

        IMPORTANTE: Este método redacta automáticamente DNIs, emails,
        IBANs, teléfonos, etc. antes de escribir a disco.

        Args:
            mensaje: Mensaje a logear (será redactado automáticamente)
            nivel: Nivel de log (INFO, WARNING, ERROR)
            metadata: Metadata adicional (también será redactada)

        Examples:
            >>> logger.log("Usuario con DNI 12345678A solicita expediente")
            # Escribe: "Usuario con DNI [DNI-REDACTED] solicita expediente"

            >>> logger.log("Contacto", metadata={"email": "juan@example.com"})
            # Escribe metadata con email redactado
        """
        # REDACTAR PII antes de logear
        mensaje_redactado = PIIRedactor.redact(mensaje)

        entrada = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": nivel,
            "agent_run_id": self.agent_run_id,
            "expediente_id": self.expediente_id,
            "mensaje": mensaje_redactado
        }

        if metadata:
            # Redactar también la metadata
            metadata_str = json.dumps(metadata, ensure_ascii=False)
            metadata_redacted_str = PIIRedactor.redact(metadata_str)
            entrada["metadata"] = json.loads(metadata_redacted_str)

        # Escribir a archivo (JSON lines)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False) + "\n")

        # Guardar en memoria para devolución en resultado
        self._entries.append(mensaje_redactado)

    def get_log_entries(self) -> list[str]:
        """
        Retorna todas las entradas logeadas.

        Returns:
            Lista de mensajes redactados
        """
        return self._entries.copy()
```

#### Control de Acceso a Logs

**Permisos de archivos:**

```bash
# Los logs deben ser accesibles solo por el sistema
chmod 600 /logs/agent_runs/{expediente_id}/{agent_run_id}.log
chown agentix-service:agentix-service /logs/agent_runs/**/*.log
```

**Acceso programático:**

- Solo usuarios con permisos de "Gestión" sobre el tipo de expediente pueden leer logs
- Logs se acceden mediante API autenticada (en Paso 2)
- Auditoría de acceso a logs (quién lee qué log y cuándo)

#### Retención de Logs

```python
# config.py
LOG_RETENTION_DAYS = 365  # 1 año según normativa

# Proceso de purga automática (cron job)
# backoffice/scripts/purge_old_logs.py
from datetime import datetime, timedelta

async def purge_old_logs():
    """
    Elimina logs más antiguos que LOG_RETENTION_DAYS.

    Cumplimiento: GDPR Art. 5.1.e (limitación del plazo de conservación)
    """
    cutoff_date = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)
    # ... implementación de purga ...
```

#### Formato de Log

**Ejemplo de log CON datos sensibles (ANTES de redacción - SOLO en memoria):**

```python
# En el código del agente:
logger.log("Solicitante Juan Pérez con DNI 12345678A y email juan@example.com")
```

**Ejemplo de log DESPUÉS de redacción (lo que se escribe a disco):**

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "agent_run_id": "RUN-001",
  "expediente_id": "EXP-2024-001",
  "mensaje": "Solicitante Juan Pérez con DNI [DNI-REDACTED] y email [EMAIL-REDACTED]"
}
```

**Ejemplos adicionales de redacción:**

```json
{"timestamp": "2024-01-15T10:30:01Z", "level": "INFO", "agent_run_id": "RUN-001", "expediente_id": "EXP-2024-001", "mensaje": "Consultando expediente EXP-2024-001", "tool": "consultar_expediente"}
{"timestamp": "2024-01-15T10:30:02Z", "level": "INFO", "agent_run_id": "RUN-001", "expediente_id": "EXP-2024-001", "mensaje": "Documentos encontrados: 3"}
{"timestamp": "2024-01-15T10:30:03Z", "level": "INFO", "agent_run_id": "RUN-001", "expediente_id": "EXP-2024-001", "mensaje": "Contacto bancario: IBAN [IBAN-REDACTED]"}
```

#### Ubicación de Logs

```
/logs/agent_runs/{expediente_id}/{agent_run_id}.log
```

**Estructura de directorios:**

```
/logs/
  agent_runs/
    EXP-2024-001/
      RUN-20240115-103000.log
      RUN-20240116-141500.log
    EXP-2024-002/
      RUN-20240115-120000.log
```

#### Tests de Redacción de PII

**OBLIGATORIO:** Incluir tests que verifiquen que PII se redacta correctamente.

```python
# backoffice/tests/test_logging.py

import pytest
from pathlib import Path
from backoffice.logging.pii_redactor import PIIRedactor
from backoffice.logging.audit_logger import AuditLogger

def test_pii_redactor_dni():
    """Verifica que DNIs se redactan automáticamente"""
    mensaje = "Solicitante con DNI 12345678A"
    redacted = PIIRedactor.redact(mensaje)
    assert "12345678A" not in redacted
    assert "[DNI-REDACTED]" in redacted

def test_pii_redactor_email():
    """Verifica que emails se redactan automáticamente"""
    mensaje = "Contacto: juan.perez@example.com"
    redacted = PIIRedactor.redact(mensaje)
    assert "juan.perez@example.com" not in redacted
    assert "[EMAIL-REDACTED]" in redacted

def test_pii_redactor_iban():
    """Verifica que IBANs se redactan automáticamente"""
    mensaje = "Cuenta bancaria: ES1234567890123456789012"
    redacted = PIIRedactor.redact(mensaje)
    assert "ES1234567890123456789012" not in redacted
    assert "[IBAN-REDACTED]" in redacted

def test_pii_redactor_telefono():
    """Verifica que teléfonos se redactan automáticamente"""
    mensaje = "Teléfono de contacto: 612345678"
    redacted = PIIRedactor.redact(mensaje)
    assert "612345678" not in redacted
    assert "[TELEFONO-REDACTED]" in redacted

def test_pii_redactor_nie():
    """Verifica que NIEs se redactan automáticamente"""
    mensaje = "Extranjero con NIE X1234567Z"
    redacted = PIIRedactor.redact(mensaje)
    assert "X1234567Z" not in redacted
    assert "[NIE-REDACTED]" in redacted

def test_audit_logger_escribe_logs_redactados(tmp_path):
    """Verifica que el logger escribe logs con PII redactada automáticamente"""
    logger = AuditLogger("EXP-001", "RUN-001", tmp_path)
    logger.log("Usuario con DNI 12345678Z solicita expediente")

    # Leer el archivo de log
    log_file = tmp_path / "EXP-001" / "RUN-001.log"
    content = log_file.read_text()

    # Verificar que NO contiene el DNI original
    assert "12345678Z" not in content
    # Verificar que SÍ contiene la redacción
    assert "[DNI-REDACTED]" in content

def test_audit_logger_redacta_metadata(tmp_path):
    """Verifica que el logger redacta también la metadata"""
    logger = AuditLogger("EXP-001", "RUN-001", tmp_path)
    logger.log(
        "Consultando expediente",
        metadata={"solicitante_email": "juan@example.com", "telefono": "612345678"}
    )

    log_file = tmp_path / "EXP-001" / "RUN-001.log"
    content = log_file.read_text()

    # No debe contener datos originales
    assert "juan@example.com" not in content
    assert "612345678" not in content
    # Debe contener redacciones
    assert "[EMAIL-REDACTED]" in content
    assert "[TELEFONO-REDACTED]" in content

def test_audit_logger_multiples_pii_en_mismo_mensaje(tmp_path):
    """Verifica que múltiples PII en el mismo mensaje se redactan"""
    logger = AuditLogger("EXP-001", "RUN-001", tmp_path)
    logger.log(
        "Solicitante Juan Pérez, DNI 12345678A, email juan@example.com, "
        "teléfono 612345678, IBAN ES1234567890123456789012"
    )

    log_file = tmp_path / "EXP-001" / "RUN-001.log"
    content = log_file.read_text()

    # No debe contener ningún dato original
    assert "12345678A" not in content
    assert "juan@example.com" not in content
    assert "612345678" not in content
    assert "ES1234567890123456789012" not in content

    # Debe contener todas las redacciones
    assert "[DNI-REDACTED]" in content
    assert "[EMAIL-REDACTED]" in content
    assert "[TELEFONO-REDACTED]" in content
    assert "[IBAN-REDACTED]" in content
```

#### Integración con AgentExecutor

El `AgentExecutor` debe usar el `AuditLogger` con redacción automática:

```python
# backoffice/executor.py

from backoffice.logging.audit_logger import AuditLogger
from pathlib import Path

class AgentExecutor:
    async def execute(
        self,
        token: str,
        expediente_id: str,
        tarea_id: str,
        agent_config: AgentConfig
    ) -> AgentExecutionResult:
        """Ejecuta un agente con logging seguro (PII redactada)"""

        # Crear logger con redacción automática de PII
        agent_run_id = f"RUN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        logger = AuditLogger(
            expediente_id=expediente_id,
            agent_run_id=agent_run_id,
            log_dir=Path(config.LOG_DIR)
        )

        logger.log(f"Iniciando ejecución de agente {agent_config.nombre}")
        logger.log(f"Tarea: {tarea_id}")

        try:
            # ... resto de la lógica ...

            # Los mensajes con PII se redactan automáticamente:
            logger.log(f"Procesando datos del solicitante")  # OK
            # Si el agente intenta logear PII, se redacta:
            # logger.log("DNI: 12345678A") -> escribe "DNI: [DNI-REDACTED]"

        except Exception as e:
            logger.log(f"Error: {str(e)}", nivel="ERROR")
            # ...
```

#### Notas Importantes sobre Protección de Datos

1. **La redacción es automática e inevitable**: Los desarrolladores de agentes no necesitan preocuparse por redactar PII manualmente - el sistema lo hace automáticamente.

2. **Patrones extensibles**: Si se identifican nuevos tipos de PII, se pueden añadir fácilmente al diccionario `PATTERNS` en `PIIRedactor`.

3. **Balance entre utilidad y privacidad**: Los logs redactados siguen siendo útiles para debugging (se ve el contexto), pero no exponen datos personales.

4. **Cumplimiento normativo**: Este sistema es **obligatorio** para despliegue en administración pública española.

5. **Auditoría de auditoría**: El acceso a logs (incluso redactados) debe auditarse también (quién lee logs de qué expedientes).

### 6. Configuración de Agentes Mock

Crear al menos 2-3 agentes mock predefinidos, por ejemplo:

1. **ValidadorDocumental**: Valida que todos los documentos requeridos estén presentes
2. **AnalizadorSubvencion**: Analiza si el solicitante cumple requisitos (mock: siempre aprueba)
3. **GeneradorInforme**: Genera un informe resumiendo el estado del expediente

Cada uno debe:

- Tener su propia función `mock_<nombre_agente>()`
- Usar diferentes herramientas MCP
- Simular diferentes flujos de trabajo
- Registrar pasos en el log

### 7. Gestión de Errores

El sistema debe manejar errores usando códigos semánticos (no HTTP), ya que el Paso 1 es solo lógica Python sin API REST.

#### Catálogo de Códigos de Error

```python
# backoffice/models.py

ERROR_CODES = {
    # Errores de autenticación y autorización
    "AUTH_INVALID_TOKEN": "Token JWT inválido o mal formado",
    "AUTH_TOKEN_EXPIRED": "Token JWT expirado",
    "AUTH_TOKEN_NOT_YET_VALID": "Token JWT aún no válido (nbf)",
    "AUTH_PERMISSION_DENIED": "Permisos insuficientes",
    "AUTH_EXPEDIENTE_MISMATCH": "Token no autorizado para este expediente",
    "AUTH_INSUFFICIENT_PERMISSIONS": "Permisos insuficientes para la operación solicitada",

    # Errores de recursos
    "EXPEDIENTE_NOT_FOUND": "Expediente no encontrado",
    "DOCUMENTO_NOT_FOUND": "Documento no encontrado",

    # Errores de configuración
    "AGENT_NOT_CONFIGURED": "Tipo de agente no configurado",
    "AGENT_CONFIG_INVALID": "Configuración de agente inválida",

    # Errores de MCP
    "MCP_CONNECTION_ERROR": "Error al conectar con servidor MCP",
    "MCP_TIMEOUT": "Timeout en llamada a servidor MCP",
    "MCP_TOOL_ERROR": "Error al ejecutar tool MCP",
    "MCP_AUTH_ERROR": "Error de autenticación con servidor MCP",

    # Errores de validación
    "OUTPUT_VALIDATION_ERROR": "Output del agente no válido",
    "INPUT_VALIDATION_ERROR": "Parámetros de entrada inválidos",

    # Errores internos
    "INTERNAL_ERROR": "Error interno del sistema"
}
```

#### Mapeo a HTTP (Referencia para Paso 2)

**Nota:** En el Paso 2 (API REST), estos códigos se mapearán a códigos HTTP:

```python
# Solo referencia para el futuro (Paso 2)
HTTP_STATUS_MAPPING = {
    "AUTH_INVALID_TOKEN": 401,
    "AUTH_TOKEN_EXPIRED": 401,
    "AUTH_TOKEN_NOT_YET_VALID": 401,
    "AUTH_PERMISSION_DENIED": 403,
    "AUTH_EXPEDIENTE_MISMATCH": 403,
    "AUTH_INSUFFICIENT_PERMISSIONS": 403,
    "EXPEDIENTE_NOT_FOUND": 404,
    "DOCUMENTO_NOT_FOUND": 404,
    "AGENT_NOT_CONFIGURED": 400,
    "AGENT_CONFIG_INVALID": 400,
    "MCP_CONNECTION_ERROR": 502,
    "MCP_TIMEOUT": 504,
    "MCP_TOOL_ERROR": 502,
    "MCP_AUTH_ERROR": 502,
    "OUTPUT_VALIDATION_ERROR": 400,
    "INPUT_VALIDATION_ERROR": 400,
    "INTERNAL_ERROR": 500
}
```

#### Requisitos de Manejo de Errores

Todos los errores deben:

- **Logearse** con nivel ERROR antes de devolverse
- **Devolverse** con formato consistente usando `AgentError`
- **Incluir mensaje descriptivo** que ayude a diagnosticar el problema
- **Preservar el contexto** (expediente_id, tarea_id, agent_run_id) en los logs

## Requisitos No Funcionales

### Tecnologías

- **Lenguaje**: Python 3.11+
- **Modelos de datos**: Pydantic (dataclasses)
- **Cliente MCP**: Implementación custom o usar SDK de MCP si existe
- **JWT**: PyJWT
- **Config**: python-dotenv, pydantic-settings
- **Testing**: pytest
- **Async**: asyncio (toda la lógica debe ser asíncrona)

**NOTA**: FastAPI se añadirá en el Paso 2 para envolver esta lógica en una API REST.

### Estructura de Proyecto

```text
/backoffice/
├── __init__.py
├── executor.py                 # Clase AgentExecutor (punto de entrada principal)
├── models.py                   # Modelos Pydantic (AgentConfig, AgentExecutionResult, etc.)
├── auth/
│   ├── __init__.py
│   └── jwt_validator.py        # Validación de JWT
├── agents/
│   ├── __init__.py
│   ├── base.py                 # Clase base AgentMock
│   ├── registry.py             # Registro de agentes disponibles
│   ├── validador_documental.py
│   ├── analizador_subvencion.py
│   └── generador_informe.py
├── mcp/
│   ├── __init__.py
│   ├── client.py               # Cliente MCP HTTP
│   └── exceptions.py           # Excepciones del cliente MCP
├── logging/
│   ├── __init__.py
│   ├── pii_redactor.py         # Redactor de PII (GDPR/LOPD)
│   └── audit_logger.py         # Logger de auditoría con redacción PII
├── config.py                   # Configuración (carga .env)
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_executor.py        # Tests del AgentExecutor
    ├── test_auth.py
    ├── test_agents.py
    ├── test_mcp_client.py
    └── test_logging.py         # Tests de redacción PII (OBLIGATORIO)

/.env                           # Variables de entorno
/requirements.txt               # Dependencias
/README.md                      # Documentación
```

### Variables de Entorno (.env)

```bash
# JWT (IMPORTANTE: usar mismo nombre que el servidor MCP mock)
JWT_SECRET=tu-clave-secreta-super-segura
JWT_ALGORITHM=HS256

# MCP Server
MCP_SERVER_URL=http://localhost:8000
MCP_SERVER_TYPE=http  # http o stdio

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs/agent_runs
```

**Nota importante:** La variable de entorno debe llamarse `JWT_SECRET` (no `JWT_SECRET_KEY`) para mantener consistencia con el servidor MCP mock existente en `/mcp-mock/mcp-expedientes/`.

## Criterios de Aceptación

Para considerar completado el Paso 1, el sistema debe:

✅ Clase `AgentExecutor` funcional con método `execute()`
✅ Validar JWT con claims correctos (10 claims obligatorios: iss, sub, aud, exp, iat, nbf, jti, exp_id, permisos)
✅ Conectarse al MCP mock server vía HTTP con JSON-RPC 2.0
✅ Cliente MCP con propagación de errores estructurados (NO reintentos)
✅ Ejecutar al menos 2 agentes mock diferentes
✅ Realizar llamadas reales al MCP (leer/escribir expedientes)
✅ Registrar todos los pasos en logs estructurados (JSON lines)
✅ **CRÍTICO:** Redacción automática de PII en logs (DNI, email, IBAN, teléfono, NIE, tarjeta, CCC)
✅ Tests de redacción PII verifican que datos personales NO aparecen en logs
✅ Devolver logs de auditoría en el resultado (ya redactados)
✅ Manejar errores con excepciones apropiadas y códigos semánticos
✅ Incluir tests automatizados (>80% cobertura)
✅ Tests obligatorios de `test_logging.py` pasando
✅ Documentación README con:
  - Cómo importar y usar la clase AgentExecutor
  - Cómo ejecutar tests
  - Estructura del proyecto
  - Cumplimiento GDPR/LOPD/ENS
  - Próximos pasos (Paso 2: envolver en API REST)

## Ejemplo de Uso

### 1. Iniciar MCP Mock Server

```bash
cd mcp-mock/mcp-expedientes
python -m mcp_expedientes.server_http
# Escucha en http://localhost:8000
```

### 2. Usar el Back-Office desde Python

```python
import asyncio
from backoffice.executor import AgentExecutor
from backoffice.models import AgentConfig
from mcp_expedientes.generate_token import generate_token

async def main():
    # 1. Generar token JWT con todos los claims obligatorios
    token = generate_token(
        usuario="Automático",
        expediente_id="EXP-2024-001",
        permisos=["consulta", "gestion"]
    )
    # Esto generará un JWT con todos los claims obligatorios:
    # iss, sub, aud, exp, iat, nbf, jti, exp_id, permisos

    # 2. Configurar el agente
    agent_config = AgentConfig(
        nombre="ValidadorDocumental",
        system_prompt="Eres un validador de documentación",
        modelo="claude-3-5-sonnet-20241022",
        prompt_tarea="Valida que todos los documentos estén presentes",
        herramientas=["consultar_expediente", "actualizar_datos", "añadir_anotacion"]
    )

    # 3. Crear executor y ejecutar agente
    executor = AgentExecutor()
    resultado = await executor.execute(
        token=token,
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-VALIDAR-DOC-001",
        agent_config=agent_config
    )

    # 4. Verificar resultado
    if resultado.success:
        print(f"✅ Agente ejecutado: {resultado.agent_run_id}")
        print(f"   Mensaje: {resultado.resultado['mensaje']}")
        print(f"   Herramientas usadas: {resultado.herramientas_usadas}")
        print("\n📋 Log de auditoría:")
        for log in resultado.log_auditoria:
            print(f"   - {log}")
    else:
        print(f"❌ Error: {resultado.error.codigo}")
        print(f"   {resultado.error.mensaje}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Verificar Resultado

Comprobar que:

- `resultado.success == True`
- Logs de auditoría muestran cada paso
- El expediente se actualizó en `/mcp-mock/mcp-expedientes/data/expedientes/EXP-2024-001.json`
- El historial del expediente tiene nueva entrada

### 4. Ejecutar Tests

```bash
cd backoffice
pytest tests/ -v --cov=. --cov-report=term-missing
```

## Notas Importantes

### Principios Arquitectónicos a Seguir

1. **No Acoplamiento** (`/doc/040-criterios-diseño.md`):
   - El back-office debe ser independiente de GEX
   - Toda comunicación con GEX es vía MCP (simulado por el mock)

2. **Mínimo Privilegio** (`/doc/050-permisos-agente.md`):
   - Validar que el JWT contenga el expediente solicitado
   - Solo pasar al MCP las herramientas configuradas en `agent_config.herramientas`

3. **Auditoría Completa** (`/doc/033-auditoria-agente.md`):
   - Logear TODO: entrada, cada paso, llamadas MCP, resultado, errores

4. **Propagación de Permisos** (`/doc/052-propagacion-permisos.md`):
   - El JWT recibido de BPMN debe pasarse sin modificar al MCP
   - El MCP lo validará y aplicará permisos

### Limitaciones del Mock

En este paso, el agente **NO**:

- Usa LLMs reales (comportamiento hardcodeado)
- Razona dinámicamente (sigue script predefinido)
- Aprende o se adapta
- Usa LangGraph/CrewAI (eso es el Paso 3)

El agente **SÍ**:

- Valida JWT
- Llama al MCP real
- Modifica datos reales (en el mock MCP)
- Registra auditoría completa
- Simula diferentes comportamientos según tipo de agente

## Referencias

- Documentación del proyecto: `/doc/index.md`
- Servidor MCP Mock: `/mcp-mock/mcp-expedientes/`
- Modelo de datos de expedientes: `/mcp-mock/mcp-expedientes/models.py`
- Tools MCP disponibles: `/mcp-mock/mcp-expedientes/tools.py`
- Autenticación JWT: `/mcp-mock/mcp-expedientes/auth.py`

## Próximos Pasos (Preview)

Una vez completado el Paso 1, el **Paso 2** envolverá esta lógica en una API REST:

- API FastAPI que expone la clase `AgentExecutor` vía HTTP
- Endpoint `POST /api/v1/agent/execute` que llama a `AgentExecutor.execute()`
- Más endpoints: `GET /api/v1/agent/{run_id}/status`, `DELETE /api/v1/agent/{run_id}`, etc.
- Gestión de trabajos asíncronos (background tasks)
- Webhooks para notificar a BPMN cuando el agente termine
- Métricas y monitorización (Prometheus)
- Documentación OpenAPI automática

El **Paso 3** reemplazará los agentes mock por agentes reales:

- Integración con LangGraph/CrewAI
- LLMs reales (Anthropic Claude)
- Razonamiento dinámico basado en los prompts de configuración
- Sistema de agentes multi-paso
- La interfaz `AgentExecutor` se mantiene sin cambios (solo cambia la implementación interna)

El **Paso 4** añadirá escalabilidad horizontal:

- Celery para ejecutar agentes en workers distribuidos
- Redis como message broker y backend de resultados
- Múltiples workers procesando agentes en paralelo
- Load balancing automático
