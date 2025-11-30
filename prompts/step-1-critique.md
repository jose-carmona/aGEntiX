# Crítica: Paso 1 - Esqueleto Back-Office (Mock Funcional)

**Documento revisado:** `step-1-backoffice-skeleton.md`
**Fecha de revisión:** 2025-11-30
**Última actualización:** 2025-11-30
**Revisor:** Análisis de diseño de software

---

## 📝 Registro de Correcciones

| Fecha | Problema Corregido | Estado |
|-------|-------------------|--------|
| 2025-11-30 | CRÍTICO 1: Inconsistencia JWT claims | ✅ RESUELTO |
| 2025-11-30 | CRÍTICO 2: Arquitectura del Cliente MCP Subespecificada | ✅ RESUELTO |
| 2025-11-30 | CRÍTICO 3: Logging sin redacción PII | ✅ RESUELTO |

---

## Resumen Ejecutivo

**Puntuación General: 9.5/10** (actualizada tras corrección de todos los CRÍTICOS)

**Estado actual:**
- ✅ CRÍTICO 1 (JWT claims) - RESUELTO
- ✅ CRÍTICO 2 (Cliente MCP) - RESUELTO
- ✅ CRÍTICO 3 (Logging PII) - RESUELTO

El documento presenta una estrategia incremental sólida y un nivel de detalle apropiado. **TODOS los problemas críticos bloqueantes han sido resueltos**, eliminando la inconsistencia con el código existente del MCP mock, especificando completamente la arquitectura del cliente MCP, e implementando la redacción automática de PII para cumplimiento GDPR/LOPD/ENS.

**El documento está LISTO para implementación** de los requisitos críticos. Se recomienda considerar los problemas de prioridad ALTA para mejorar aún más la calidad.

---

## ✅ Fortalezas Identificadas

### 1. Estrategia Incremental Sólida

El enfoque de 4 pasos progresivos (mock → API → agentes reales → escalabilidad) es **excelente** y demuestra madurez en diseño de software.

**Beneficios:**
- Validación temprana de la arquitectura sin inversión en complejidad
- Detección de problemas de integración antes de implementar agentes reales
- Iteración rápida en interfaces y contratos
- Reducción de riesgo en cada fase

### 2. Alineación con MCP Mock Existente

El documento reconoce y reutiliza el servidor MCP ya implementado en `/mcp-mock/mcp-expedientes/`. Esto es pragmático y demuestra conocimiento del código existente.

### 3. Nivel de Detalle Apropiado

- ✅ Firmas de métodos con tipos Pydantic bien definidos
- ✅ Ejemplos de uso concretos y ejecutables
- ✅ Criterios de aceptación medibles
- ✅ Estructura de proyecto clara y organizada

### 4. Cobertura de Requisitos Funcionales Amplia

El documento cubre todos los aspectos clave:
- Validación JWT
- Cliente MCP
- Sistema de logging y auditoría
- Múltiples agentes mock
- Gestión de errores

---

## Problemas Críticos Identificados

### **✅ CRÍTICO 1: Inconsistencia entre Claims JWT en Documentación y Código** [RESUELTO]

**Severidad:** ~~🔴 BLOQUEANTE~~ → ✅ RESUELTO (2025-11-30)

**Estado de la corrección:**
- ✅ Sección "2. Validación JWT" actualizada con todos los claims obligatorios
- ✅ Ejemplo de uso actualizado con generación correcta de token
- ✅ Variable de entorno corregida: `JWT_SECRET` (era `JWT_SECRET_KEY`)
- ✅ Códigos de error actualizados a formato semántico
- ✅ Referencias al código MCP mock añadidas

---

**NOTA:** El resto de esta sección se mantiene como referencia histórica de qué se corrigió.

#### Descripción del Problema

El documento del Paso 1 especifica (líneas 100-102):

```python
# Claims documentados en step-1-backoffice-skeleton.md
- usuario: "Automático"
- expediente_id: "{ID del expediente}"
- exp: {timestamp de expiración}
```

Sin embargo, el código MCP mock ya implementado en `/mcp-mock/mcp-expedientes/auth.py` espera una estructura **completamente diferente**:

```python
# Claims reales esperados por auth.py (líneas 136, 140, etc.)
{
    "iss": "agentix-bpmn",              # Emisor (OBLIGATORIO, no mencionado)
    "sub": "Automático",                 # Subject (NO 'usuario')
    "aud": ["agentix-mcp-expedientes"],  # Audiencia (OBLIGATORIO, no mencionado)
    "exp": timestamp,                    # Expiración
    "iat": timestamp,                    # Issued at (no mencionado)
    "nbf": timestamp,                    # Not before (no mencionado)
    "jti": "unique-id",                  # JWT ID (no mencionado)
    "exp_id": "EXP-2024-001",           # ID expediente (NO 'expediente_id')
    "permisos": ["consulta", "gestion"]  # Permisos (no mencionado)
}
```

#### Evidencia del Código

**`auth.py:136`:**
```python
if claims.sub != "Automático":  # Usa 'sub', NO 'usuario'
    raise AuthError("Usuario no autorizado: solo se permite 'Automático'", 403)
```

**`auth.py:140`:**
```python
if claims.iss != "agentix-bpmn":  # Requiere 'iss' (no mencionado en documento)
    raise AuthError("Emisor de token no válido", 403)
```

**`auth.py:129`:**
```python
if not validate_audience(payload, server_id):  # Requiere 'aud'
    raise AuthError(f"Audiencia inválida...", 403)
```

**`auth.py:146`:**
```python
if exp_id != claims.exp_id:  # Usa 'exp_id', NO 'expediente_id'
    raise AuthError(f"Acceso no autorizado...", 403)
```

#### Impacto

- **CRÍTICO:** Un desarrollador siguiendo el documento implementará un sistema incompatible con el servidor MCP existente
- Pérdida significativa de tiempo al descubrir la incompatibilidad durante las pruebas de integración
- Necesidad de refactorización completa del sistema de autenticación

#### Solución Requerida

**Actualizar sección "2. Validación JWT" (líneas 94-106) con especificación correcta:**

```python
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

#### Validaciones a Realizar

1. **Firma JWT:** Validar con `JWT_SECRET` (misma clave que MCP mock)
2. **Emisor (iss):** Debe ser exactamente "agentix-bpmn"
3. **Subject (sub):** Debe ser exactamente "Automático"
4. **Audiencia (aud):** Debe incluir "agentix-mcp-expedientes"
5. **Expiración (exp):** Token no expirado (exp > now)
6. **Not Before (nbf):** Token ya válido (nbf <= now)
7. **Expediente (exp_id):** Debe coincidir con expediente de la request
8. **Permisos:** Debe contener los permisos necesarios para las herramientas solicitadas

#### Rechazo de Tokens Inválidos

- Token con claims faltantes → 401 AUTH_INVALID_TOKEN
- Token con emisor incorrecto → 403 AUTH_PERMISSION_DENIED
- Token con expediente diferente → 403 AUTH_PERMISSION_DENIED
- Token expirado → 401 AUTH_TOKEN_EXPIRED
- Permisos insuficientes → 403 AUTH_INSUFFICIENT_PERMISSIONS

#### Propagación del Token

El token completo debe propagarse sin modificaciones en todas las llamadas al servidor MCP.
```

**Actualizar ejemplo de uso (líneas 342-347):**

```python
# 1. Generar token JWT CON TODOS LOS CLAIMS
from mcp_expedientes.generate_token import generate_token

token = generate_token(
    usuario="Automático",
    expediente_id="EXP-2024-001",
    permisos=["consulta", "gestion"]
)
# Esto generará un JWT con todos los claims obligatorios:
# iss, sub, aud, exp, iat, nbf, jti, exp_id, permisos
```

#### Archivos a Referenciar

- Ver implementación de validación: `/mcp-mock/mcp-expedientes/auth.py`
- Ver generación de tokens: `/mcp-mock/mcp-expedientes/generate_token.py`
- Ver modelo de claims: `/mcp-mock/mcp-expedientes/models.py` (JWTClaims)

---

### **✅ CRÍTICO 2: Arquitectura del Cliente MCP Subespecificada** [RESUELTO]

**Severidad:** ~~🔴 BLOQUEANTE~~ → ✅ RESUELTO (2025-11-30)

**Estado de la corrección:**
- ✅ Sección "4. Cliente MCP" completamente reemplazada con especificación técnica completa
- ✅ Biblioteca especificada: SDK MCP + httpx (NO tenacity - error handling delegado a BPMN)
- ✅ Estructura JSON-RPC 2.0 completamente documentada
- ✅ Propagación JWT especificada con header Authorization
- ✅ Gestión de errores con excepciones estructuradas y clasificación para BPMN
- ✅ Implementación completa de MCPClient incluida (~590 líneas)
- ✅ Justificación clara de separación de responsabilidades (cliente detecta, BPMN decide)

---

**NOTA:** El resto de esta sección se mantiene como referencia histórica de qué se corrigió.

#### Descripción del Problema

El documento menciona vagamente (líneas 173-180):

> "El back-office debe incluir un cliente MCP que se conecte al servidor MCP (puede usar HTTP o stdio, preferir HTTP para simplicidad)"

Pero **no especifica** aspectos críticos de la implementación. A continuación, cada punto no especificado con su propuesta de solución:

---

#### 1. ¿Qué biblioteca usar?

**Problema:** No se especifica qué biblioteca usar para el cliente MCP.

**Opciones disponibles:**
- SDK oficial de MCP (`mcp` Python package)
- Cliente HTTP custom con `httpx`/`aiohttp`
- Mezcla: SDK MCP + cliente HTTP custom

**Propuesta específica:**

**Usar combinación de SDK MCP + httpx:**

```python
# requirements.txt
mcp>=1.0.0          # SDK oficial MCP (para tipos y protocolo)
httpx>=0.25.0       # Cliente HTTP asíncrono (más control)
tenacity>=8.2.0     # Gestión de reintentos
```

**Justificación:**
- ✅ SDK MCP oficial: proporciona tipos correctos (`types.Tool`, `types.TextContent`, etc.)
- ✅ httpx: control fino sobre headers, timeouts, reintentos
- ✅ Simplicidad: no requiere transporte complejo stdio
- ✅ Debugging: requests HTTP son fáciles de inspeccionar

**Alternativa descartada (solo SDK MCP):**
- ❌ El transporte HTTP del SDK MCP puede tener limitaciones para casos de uso específicos
- ❌ Menos control sobre reintentos y timeouts

**Alternativa descartada (solo httpx sin SDK):**
- ❌ Requiere reimplementar tipos y validaciones del protocolo MCP
- ❌ Riesgo de incompatibilidad con futuras versiones del protocolo

---

#### 2. ¿Cómo se estructura la request HTTP al servidor MCP?

**Problema:** No se especifica el formato de las requests al servidor.

**Opciones disponibles:**
- JSON-RPC 2.0 (estándar MCP)
- REST puro (no recomendado)
- Formato custom

**Propuesta específica:**

**Usar JSON-RPC 2.0 (protocolo estándar MCP):**

```python
# Estructura de request para call_tool
request_body = {
    "jsonrpc": "2.0",
    "id": unique_request_id,
    "method": "tools/call",
    "params": {
        "name": "consultar_expediente",
        "arguments": {
            "expediente_id": "EXP-2024-001"
        }
    }
}

# Endpoint HTTP
POST /sse
Headers:
  Authorization: Bearer <JWT>
  Content-Type: application/json
```

**Estructura de response esperada:**

```python
# Response exitosa
{
    "jsonrpc": "2.0",
    "id": unique_request_id,
    "result": {
        "content": [
            {
                "type": "text",
                "text": "{...json del expediente...}"
            }
        ]
    }
}

# Response con error
{
    "jsonrpc": "2.0",
    "id": unique_request_id,
    "error": {
        "code": -32600,
        "message": "Invalid Request",
        "data": {"detail": "..."}
    }
}
```

**Justificación:**
- ✅ Estándar del protocolo MCP
- ✅ Compatible con servidor MCP mock existente (`server_http.py`)
- ✅ Soporte para requests asíncronas con IDs
- ✅ Manejo de errores estandarizado

**Referencia:**
- Verificado en `/mcp-mock/mcp-expedientes/server_http.py` líneas 19-36 (ejemplos de uso)

---

#### 3. ¿Cómo se propaga el JWT exactamente?

**Problema:** El documento menciona header `Authorization` pero no especifica detalles de implementación.

**Opciones disponibles:**
- Header HTTP `Authorization: Bearer <token>`
- JWT en body del request JSON-RPC
- JWT como parámetro en URL (no recomendado por seguridad)

**Propuesta específica:**

**Usar header HTTP `Authorization: Bearer <token>`:**

```python
# En la inicialización del cliente httpx
client = httpx.AsyncClient(
    base_url="http://localhost:8000",
    timeout=30,
    headers={
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
)

# Todas las requests incluirán automáticamente este header
```

**Validación con código existente:**

El servidor MCP HTTP ya implementa esto correctamente:

```python
# /mcp-mock/mcp-expedientes/server_http.py líneas 79-82
auth_header = request.headers.get("Authorization", "")
if auth_header.startswith("Bearer "):
    token = auth_header[7:]
    context.set_token(token)
```

**Justificación:**
- ✅ **Verificado:** El servidor actual espera exactamente este formato
- ✅ Estándar HTTP para autenticación Bearer
- ✅ JWT no aparece en logs de URLs
- ✅ Compatible con proxies y balanceadores de carga

**Corrección necesaria en servidor:**
- ⚠️ El servidor actual NO valida el token inmediatamente (solo lo almacena)
- 🔧 Se requiere corrección (ver documento `/prompts/fix-mcp-http-jwt-validation.md`)

---

#### 4. ¿Gestión de errores de conexión?

**Problema:** No se especifica cómo manejar errores de conexión con el servidor MCP.

**Principio arquitectónico importante:**

⚠️ **El sistema BPMN ya tiene su propio sistema de gestión de errores y recuperación**. El back-office NO debe implementar lógica compleja de reintentos o recuperación.

**Responsabilidades por capa:**
- **Cliente MCP (back-office):** Detectar error, clasificarlo, propagarlo claramente
- **Sistema BPMN:** Decidir estrategia de recuperación (reintentar tarea, escalar a humano, etc.)

**Propuesta específica:**

**1. Timeouts básicos (responsabilidad del cliente)**

```python
import httpx

class MCPClient:
    """
    Cliente MCP simple que propaga errores al sistema BPMN.

    NO implementa reintentos complejos - esa responsabilidad es del BPMN.
    """

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token

        # Timeout único y generoso para todas las operaciones
        # El BPMN tiene sus propios timeouts de tarea más sofisticados
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=30.0,  # 30 segundos para cualquier operación MCP
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )

    async def call_tool(
        self,
        name: str,
        arguments: dict
    ) -> dict:
        """
        Ejecuta una tool y propaga errores al llamador.

        NO reintenta - el sistema BPMN maneja reintentos a nivel de tarea.
        """
        try:
            response = await self.client.post(
                "/sse",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": arguments}
                }
            )

            # Lanzar excepción si status code indica error
            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException as e:
            # Timeout - propagar con código específico
            raise MCPConnectionError(
                codigo="MCP_TIMEOUT",
                mensaje=f"Timeout al ejecutar tool '{name}' (>30s)",
                detalle=str(e)
            )

        except httpx.ConnectError as e:
            # No se puede conectar al servidor
            raise MCPConnectionError(
                codigo="MCP_CONNECTION_ERROR",
                mensaje=f"No se puede conectar al servidor MCP: {self.base_url}",
                detalle=str(e)
            )

        except httpx.HTTPStatusError as e:
            # Error HTTP - clasificar según código
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
                # Servidor MCP temporalmente no disponible
                raise MCPConnectionError(
                    codigo="MCP_SERVER_UNAVAILABLE",
                    mensaje=f"Servidor MCP no disponible (HTTP {status})",
                    detalle=e.response.text
                )

            else:
                # Otro error HTTP
                raise MCPToolError(
                    codigo="MCP_TOOL_ERROR",
                    mensaje=f"Error al ejecutar tool '{name}' (HTTP {status})",
                    detalle=e.response.text
                )

        except Exception as e:
            # Error inesperado
            raise MCPConnectionError(
                codigo="MCP_UNEXPECTED_ERROR",
                mensaje=f"Error inesperado al llamar a MCP: {type(e).__name__}",
                detalle=str(e)
            )

    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()
```

**2. Excepciones estructuradas para propagación clara**

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
    """Error de conexión con servidor MCP"""
    pass


@dataclass
class MCPToolError(MCPError):
    """Error al ejecutar una tool MCP"""
    pass


@dataclass
class MCPAuthError(MCPError):
    """Error de autenticación/autorización con MCP"""
    pass
```

**3. Propagación al AgentExecutor**

```python
# backoffice/executor.py

class AgentExecutor:
    async def execute(...) -> AgentExecutionResult:
        try:
            # Crear cliente MCP
            mcp_client = MCPClient(base_url=..., token=token)

            # Ejecutar agente (que usa mcp_client)
            resultado = await agent.execute()

            return AgentExecutionResult(success=True, ...)

        except MCPConnectionError as e:
            # Error de conexión - propagar al BPMN
            logger.error(f"Error de conexión MCP: {e}")
            return AgentExecutionResult(
                success=False,
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
                error=AgentError(
                    codigo=e.codigo,
                    mensaje=e.mensaje
                )
            )

        finally:
            await mcp_client.close()
```

**4. El sistema BPMN decide la recuperación**

El BPMN puede configurar en cada tarea:

```yaml
# Ejemplo de configuración BPMN (no es responsabilidad del back-office)
tarea_validar_documentos:
  tipo: agente
  agente: ValidadorDocumental

  # Estrategia de recuperación (responsabilidad del BPMN)
  on_error:
    MCP_TIMEOUT:
      accion: reintentar
      max_reintentos: 3
      intervalo: 60s  # Esperar 1 minuto entre reintentos

    MCP_CONNECTION_ERROR:
      accion: reintentar
      max_reintentos: 2
      intervalo: 120s

    AUTH_INVALID_TOKEN:
      accion: escalar_humano  # No reintentar problemas de autenticación
      notificar: supervisor

    MCP_TOOL_ERROR:
      accion: marcar_para_revision
      notificar: administrador
```

**Justificación:**

**Por qué NO implementar reintentos en el cliente MCP:**
- ❌ **Duplicación de lógica:** El BPMN ya tiene sistema de reintentos a nivel de tarea
- ❌ **Menor control:** Reintentos en cliente son "ciegos", no conocen contexto del workflow
- ❌ **Complejidad innecesaria:** Añade dependencias (tenacity) y código complejo
- ❌ **Logs confusos:** Dificulta saber si error es por fallo real o reintento automático
- ❌ **Timeouts inconsistentes:** Timeout del cliente + timeout del BPMN = confusión

**Por qué SÍ propagar errores estructurados:**
- ✅ **Separación de responsabilidades:** Cliente detecta, BPMN decide
- ✅ **Flexibilidad:** BPMN puede tener diferentes estrategias por tipo de tarea
- ✅ **Simplicidad:** Código del cliente es simple y predecible
- ✅ **Trazabilidad:** Logs muestran claramente qué falló y cuándo
- ✅ **Control centralizado:** Toda la lógica de recuperación en un solo lugar (BPMN)

**Clasificación de errores para BPMN:**

| Código | Tipo | Sugerencia BPMN | Razón |
|--------|------|-----------------|-------|
| `MCP_TIMEOUT` | Temporal | Reintentar | Servidor lento, podría recuperarse |
| `MCP_CONNECTION_ERROR` | Temporal | Reintentar | Servidor caído, podría reiniciarse |
| `MCP_SERVER_UNAVAILABLE` | Temporal | Reintentar | 502/503/504, problema temporal |
| `AUTH_INVALID_TOKEN` | Permanente | Escalar a humano | Token inválido no se arregla solo |
| `AUTH_PERMISSION_DENIED` | Permanente | Escalar a humano | Permisos mal configurados |
| `MCP_TOOL_NOT_FOUND` | Permanente | Escalar a humano | Tool no existe, error de configuración |
| `MCP_TOOL_ERROR` | Depende | Analizar detalle | Puede ser temporal o permanente |

**Timeout único justificado:**

- Un solo timeout de 30s es suficiente para el Paso 1 (mock)
- Timeouts diferenciados por operación añaden complejidad sin beneficio claro
- El BPMN tiene timeouts de tarea más sofisticados (ej: timeout total de 5 minutos para toda la tarea)
- Simplicidad > Optimización prematura en esta fase

---

#### Impacto

- Desarrollador debe tomar decisiones arquitectónicas críticas durante implementación
- Riesgo de implementar cliente incompatible con servidor
- Falta de consistencia en manejo de errores de red

#### Solución Requerida

**Reemplazar sección "4. Cliente MCP" (líneas 169-184) con especificación completa:**

```markdown
### 4. Cliente MCP - Especificación Técnica

#### Biblioteca y Dependencias

```python
# requirements.txt
mcp>=1.0.0          # SDK oficial de Model Context Protocol
httpx>=0.25.0       # Cliente HTTP asíncrono
tenacity>=8.2.0     # Reintentos automáticos
```

#### Implementación del Cliente

```python
# backoffice/mcp/client.py

from typing import List, Dict, Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from mcp import types

class MCPClient:
    """
    Cliente para interactuar con servidor MCP vía HTTP.

    Implementa:
    - Propagación automática de JWT
    - Reintentos con exponential backoff
    - Timeout configurables
    - Logging de todas las operaciones
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.base_url = base_url
        self.token = token
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers={"Authorization": f"Bearer {token}"}
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> List[types.TextContent]:
        """
        Ejecuta una tool en el servidor MCP.

        Args:
            name: Nombre de la tool
            arguments: Argumentos de la tool

        Returns:
            Resultado de la tool

        Raises:
            MCPConnectionError: Si no se puede conectar al servidor
            MCPToolError: Si la tool falla
            MCPAuthError: Si hay error de autenticación
        """
        try:
            response = await self.client.post(
                "/tools/call",
                json={
                    "name": name,
                    "arguments": arguments
                }
            )
            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException as e:
            raise MCPConnectionError(f"Timeout al llamar tool '{name}': {e}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise MCPAuthError(f"Token JWT inválido: {e}")
            elif e.response.status_code == 403:
                raise MCPAuthError(f"Permisos insuficientes: {e}")
            else:
                raise MCPToolError(f"Error en tool '{name}': {e}")
        except httpx.RequestError as e:
            raise MCPConnectionError(f"Error de conexión con MCP: {e}")

    async def read_resource(self, uri: str) -> types.Resource:
        """Lee un resource del servidor MCP"""
        # Implementación similar a call_tool
        ...

    async def list_tools(self) -> List[types.Tool]:
        """Lista todas las tools disponibles"""
        # Implementación similar
        ...

    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()
```

#### Excepciones Específicas

```python
# backoffice/mcp/exceptions.py

class MCPError(Exception):
    """Error base del cliente MCP"""
    pass

class MCPConnectionError(MCPError):
    """Error de conexión con servidor MCP"""
    pass

class MCPToolError(MCPError):
    """Error al ejecutar una tool MCP"""
    pass

class MCPAuthError(MCPError):
    """Error de autenticación/autorización con MCP"""
    pass
```

#### Configuración

```python
# .env
MCP_SERVER_URL=http://localhost:8000
MCP_TIMEOUT=30  # segundos
MCP_MAX_RETRIES=3
```

#### Estrategia de Reintentos

- **Intentos:** 3 reintentos con exponential backoff
- **Backoff:** 1s, 2s, 4s entre intentos
- **Timeout:** 30 segundos por operación (configurable)
- **Errores retryables:** Timeout, ConnectionError, 502, 503, 504
- **Errores NO retryables:** 401, 403, 400, 404, 500

#### Logs de Auditoría

Cada operación del cliente MCP debe loguear:
- Timestamp de inicio y fin
- Tool/Resource solicitado
- Argumentos (sanitizados de PII)
- Resultado (success/error)
- Latencia de la operación

#### Tests del Cliente

Ver sección "Plan de Testing" → `test_mcp_client.py`
```

---

### **✅ CRÍTICO 3: Logging de Auditoría Insuficiente para Cumplimiento GDPR/LOPD** [RESUELTO]

**Severidad:** ~~🔴 BLOQUEANTE PARA PRODUCCIÓN~~ → ✅ RESUELTO (2025-11-30)

**Estado de la corrección:**
- ✅ Sección "5. Sistema de Logging y Auditoría" completamente reescrita (~420 líneas)
- ✅ Clase `PIIRedactor` implementada con 7 patrones (DNI, NIE, email, teléfono, IBAN, tarjeta, CCC)
- ✅ Clase `AuditLogger` con redacción automática antes de escribir a disco
- ✅ Tests obligatorios de redacción PII incluidos (7 tests completos)
- ✅ Control de acceso a logs especificado
- ✅ Retención de logs (365 días) y purga automática
- ✅ Integración con `AgentExecutor` documentada
- ✅ Cumplimiento GDPR Art. 32, LOPD, ENS
- ✅ Criterios de aceptación actualizados con verificación de PII

---

**NOTA:** El resto de esta sección se mantiene como referencia histórica de qué se corrigió.

#### Descripción del Problema

El documento especifica logging estructurado en JSON lines (líneas 186-205), pero **no aborda requisitos críticos** de protección de datos personales.

**Aspectos no considerados:**

1. **Redacción automática de PII (Personally Identifiable Information)**
   - Los logs contendrán datos personales: DNI, emails, direcciones, IBAN, teléfonos
   - Según GDPR Art. 32, los logs deben protegerse adecuadamente
   - Según `/doc/problemas/102-problema-permisos-seguridad.md` (líneas 126-130), esto es un **riesgo crítico**

2. **Control de acceso a logs**
   - ¿Quién puede leer `/logs/agent_runs/{expediente_id}/{agent_run_id}.log`?
   - ¿Se aplican los mismos permisos que al expediente?
   - ¿Hay segregación de logs por tipo de expediente?

3. **Retención de logs**
   - ¿Cuánto tiempo se conservan?
   - ¿Se eliminan automáticamente cuando el expediente se archiva/elimina?
   - ¿Hay proceso de purga periódica?

4. **Formato y estructura**
   - El ejemplo de log (líneas 200-205) **expone directamente** el `expediente_id` en cada línea
   - No hay indicación de que campos sensibles deban redactarse

#### Evidencia de la Problemática

**Documento `/doc/problemas/102-problema-permisos-seguridad.md` (líneas 123-131):**

> **3.1. Fuga en Logs y Trazas**:
> - Si logs son accesibles ampliamente, exposición masiva de datos personales
> - **Pregunta**: ¿Se sanitizan/redactan automáticamente DNIs, emails, números de cuenta?

**GDPR Art. 32 - Seguridad del tratamiento:**
> El responsable del tratamiento aplicará medidas técnicas y organizativas apropiadas para garantizar un nivel de seguridad adecuado al riesgo

**ENS (Esquema Nacional de Seguridad) - aplicable a administración pública española:**
> Requisito de registro de actividad con protección de datos personales

#### Impacto

- **CRÍTICO para producción:** Sistema no deployable en administración pública sin cumplimiento GDPR/LOPD
- **Riesgo legal:** Multas de hasta 4% de facturación anual (GDPR Art. 83)
- **Riesgo reputacional:** Filtración accidental de datos de ciudadanos

#### Solución Requerida

**Ampliar sección "5. Sistema de Logging y Auditoría" (líneas 186-205):**

```markdown
### 5. Sistema de Logging y Auditoría

#### Obligación de Logging

Registrar **todos los pasos** del agente según requisito `/doc/033-auditoria-agente.md`.

#### Estructura de Logs

Cada entrada debe tener:
- Timestamp (ISO 8601 con timezone UTC)
- Nivel (INFO, WARNING, ERROR)
- Mensaje descriptivo
- Contexto (expediente_id, tarea_id, agent_run_id)
- Metadata adicional según tipo de evento

#### Redacción Automática de PII

**CRÍTICO para cumplimiento GDPR/LOPD:**

Los logs deben sanitizar automáticamente información personal identificable antes de escribirse a disco:

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
        """
        redacted = text
        for pii_type, pattern in cls.PATTERNS.items():
            redacted = pattern.sub(f'[{pii_type.upper()}-REDACTED]', redacted)
        return redacted
```

```python
# backoffice/logging/audit_logger.py

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from .pii_redactor import PIIRedactor

class AuditLogger:
    """
    Logger de auditoría con redacción automática de PII.
    """

    def __init__(self, expediente_id: str, agent_run_id: str, log_dir: Path):
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
        metadata: Dict[str, Any] = None
    ):
        """
        Registra una entrada en el log CON REDACCIÓN DE PII.

        Args:
            mensaje: Mensaje a logear (será redactado automáticamente)
            nivel: Nivel de log (INFO, WARNING, ERROR)
            metadata: Metadata adicional (también será redactada)
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
        """Retorna todas las entradas logeadas"""
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
async def purge_old_logs():
    """
    Elimina logs más antiguos que LOG_RETENTION_DAYS.

    Cumplimiento: GDPR Art. 5.1.e (limitación del plazo de conservación)
    """
    cutoff_date = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)
    # ... implementación de purga ...
```

#### Formato de Log (Actualizado con Redacción)

**Ejemplo de log CON datos sensibles (ANTES de redacción):**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "agent_run_id": "RUN-001",
  "expediente_id": "EXP-2024-001",
  "mensaje": "Solicitante Juan Pérez con DNI 12345678A y email juan@example.com"
}
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

#### Tests de Redacción

**OBLIGATORIO:** Incluir tests que verifiquen que PII se redacta correctamente.

```python
# backoffice/tests/test_logging.py

def test_pii_redaction_dni():
    """Verifica que DNIs se redactan automáticamente"""
    mensaje = "Solicitante con DNI 12345678A"
    redacted = PIIRedactor.redact(mensaje)
    assert "12345678A" not in redacted
    assert "[DNI-REDACTED]" in redacted

def test_pii_redaction_email():
    """Verifica que emails se redactan automáticamente"""
    mensaje = "Contacto: juan.perez@example.com"
    redacted = PIIRedactor.redact(mensaje)
    assert "juan.perez@example.com" not in redacted
    assert "[EMAIL-REDACTED]" in redacted

def test_audit_logger_writes_redacted_logs(tmp_path):
    """Verifica que el logger escribe logs con PII redactada"""
    logger = AuditLogger("EXP-001", "RUN-001", tmp_path)
    logger.log("Usuario con DNI 12345678Z solicita expediente")

    # Leer el archivo de log
    log_file = tmp_path / "EXP-001" / "RUN-001.log"
    content = log_file.read_text()

    # Verificar que NO contiene el DNI original
    assert "12345678Z" not in content
    # Verificar que SÍ contiene la redacción
    assert "[DNI-REDACTED]" in content
```
```

---

## ⚠️ Problemas Importantes (No Críticos)

### **IMPORTANTE 4: Validación de Salida (Output Validation) Ausente**

**Severidad:** 🟡 ALTA

#### Descripción del Problema

El documento especifica extensamente permisos de **entrada** (qué puede leer/escribir el agente), pero **no menciona validación de salida** (qué puede generar/exponer).

**Escenarios problemáticos no contemplados:**

1. **Agente genera documento de tipo no esperado**
   - Mock "ValidadorDocumental" configurado para crear "INFORME_VALIDACION"
   - Pero podría intentar crear documento tipo "RESOLUCION" (no autorizado)

2. **Agente escribe cantidad excesiva de datos**
   - Mock podría añadir 1000 anotaciones al historial (DoS)
   - Sin límite en cantidad de documentos creados

3. **Agente modifica campos fuera de scope**
   - Mock configurado para actualizar `datos.documentacion_valida`
   - Podría intentar actualizar `estado` o `tipo` (cambios no autorizados)

#### Evidencia de la Problemática

**Documento `/doc/problemas/102-problema-permisos-seguridad.md` (líneas 115-161):**

> **3. Validación de Salida No Especificada (SIN RESOLVER)**
>
> **3.4. Generación de Documentos No Autorizados**:
> - Agente con permiso de "Gestión" podría:
>   - Crear documento de tipo no esperado
>   - Generar documento con contenido malicioso
>   - Crear número excesivo de documentos (DoS)

#### Por Qué es Importante en el Mock

Podría argumentarse que "es solo un mock, no importa". **Sin embargo:**

- El propósito del Paso 1 es **validar la arquitectura**
- Si el mock no simula las restricciones del sistema real, la validación es incompleta
- Es más fácil diseñar estas validaciones ahora que refactorizar después

#### Solución Requerida

**Añadir nueva sección después de "6. Configuración de Agentes Mock":**

```markdown
### 7. Validación de Salida (Output Validation)

#### Principio

Cada agente mock debe validar sus outputs **antes** de llamar a herramientas MCP de escritura.

Esto simula las restricciones que tendrá el sistema real y valida que la arquitectura soporta control fino de acceso.

#### Constraints por Agente

Cada tipo de agente debe declarar sus constraints de salida:

```python
# backoffice/agents/validador_documental.py

class ValidadorDocumentalMock(AgentMock):
    """
    Mock del agente ValidadorDocumental.

    Simula validación de documentación con constraints de salida.
    """

    # Constraints de salida
    ALLOWED_DOCUMENT_TYPES = ["INFORME_VALIDACION"]
    MAX_DOCUMENTS_PER_RUN = 1
    ALLOWED_FIELDS_TO_UPDATE = [
        "datos.documentacion_valida",
        "datos.documentos_faltantes"
    ]
    MAX_ANNOTATIONS_PER_RUN = 3

    def __init__(self, ...):
        super().__init__(...)
        self._documents_created = 0
        self._annotations_added = 0

    async def _create_document(
        self,
        tipo: str,
        nombre: str,
        contenido: str
    ):
        """
        Crea un documento validando constraints de salida.
        """
        # VALIDAR: Tipo de documento autorizado
        if tipo not in self.ALLOWED_DOCUMENT_TYPES:
            raise OutputValidationError(
                f"Tipo de documento '{tipo}' no autorizado. "
                f"Permitidos: {self.ALLOWED_DOCUMENT_TYPES}"
            )

        # VALIDAR: No exceder límite de documentos
        if self._documents_created >= self.MAX_DOCUMENTS_PER_RUN:
            raise OutputValidationError(
                f"Límite de documentos alcanzado: {self.MAX_DOCUMENTS_PER_RUN}"
            )

        # Llamar a MCP tool
        result = await self.mcp_client.call_tool("añadir_documento", {
            "expediente_id": self.expediente_id,
            "nombre": nombre,
            "tipo": tipo,
            "contenido": contenido
        })

        self._documents_created += 1
        self.logger.log(f"Documento creado: {nombre} (tipo: {tipo})")

        return result

    async def _update_field(self, campo: str, valor: Any):
        """
        Actualiza un campo validando constraints de salida.
        """
        # VALIDAR: Campo autorizado
        if campo not in self.ALLOWED_FIELDS_TO_UPDATE:
            raise OutputValidationError(
                f"Campo '{campo}' no autorizado para actualización. "
                f"Permitidos: {self.ALLOWED_FIELDS_TO_UPDATE}"
            )

        # Llamar a MCP tool
        result = await self.mcp_client.call_tool("actualizar_datos", {
            "expediente_id": self.expediente_id,
            "campo": campo,
            "valor": valor
        })

        self.logger.log(f"Campo actualizado: {campo} = {valor}")

        return result

    async def _add_annotation(self, texto: str):
        """
        Añade anotación validando constraints de salida.
        """
        # VALIDAR: No exceder límite de anotaciones
        if self._annotations_added >= self.MAX_ANNOTATIONS_PER_RUN:
            raise OutputValidationError(
                f"Límite de anotaciones alcanzado: {self.MAX_ANNOTATIONS_PER_RUN}"
            )

        # Llamar a MCP tool
        result = await self.mcp_client.call_tool("añadir_anotacion", {
            "expediente_id": self.expediente_id,
            "texto": texto
        })

        self._annotations_added += 1
        self.logger.log(f"Anotación añadida")

        return result
```

#### Excepciones de Validación

```python
# backoffice/models.py

class OutputValidationError(Exception):
    """
    Error lanzado cuando un agente intenta generar output no autorizado.
    """
    pass
```

#### Configuración de Constraints

Los constraints también pueden cargarse desde configuración:

```yaml
# backoffice/config/agents/validador_documental.yaml
name: "ValidadorDocumental"
constraints:
  documents:
    allowed_types: ["INFORME_VALIDACION"]
    max_per_run: 1
  fields:
    allowed_to_update:
      - "datos.documentacion_valida"
      - "datos.documentos_faltantes"
  annotations:
    max_per_run: 3
```

#### Tests de Validación de Salida

**OBLIGATORIO:** Tests que verifiquen que las validaciones funcionan.

```python
# backoffice/tests/test_agents.py

@pytest.mark.asyncio
async def test_validador_rechaza_tipo_documento_no_autorizado(mcp_server):
    """Verifica que el agente rechaza crear documento de tipo no autorizado"""
    agent = ValidadorDocumentalMock(...)

    with pytest.raises(OutputValidationError, match="no autorizado"):
        await agent._create_document(
            tipo="RESOLUCION",  # Tipo NO autorizado
            nombre="resolucion.pdf",
            contenido="..."
        )

@pytest.mark.asyncio
async def test_validador_rechaza_campo_no_autorizado(mcp_server):
    """Verifica que el agente rechaza actualizar campo no autorizado"""
    agent = ValidadorDocumentalMock(...)

    with pytest.raises(OutputValidationError, match="no autorizado"):
        await agent._update_field(
            campo="estado",  # Campo NO autorizado
            valor="APROBADO"
        )

@pytest.mark.asyncio
async def test_validador_respeta_limite_documentos(mcp_server):
    """Verifica que el agente respeta límite de documentos por ejecución"""
    agent = ValidadorDocumentalMock(...)

    # Primer documento: OK
    await agent._create_document("INFORME_VALIDACION", "doc1.pdf", "...")

    # Segundo documento: Debe fallar (límite = 1)
    with pytest.raises(OutputValidationError, match="Límite de documentos"):
        await agent._create_document("INFORME_VALIDACION", "doc2.pdf", "...")
```

#### Criterios de Aceptación Actualizados

Añadir:

✅ Agentes mock implementan validación de salida (output validation)
✅ Tests verifican que constraints se respetan
✅ OutputValidationError se captura y logea apropiadamente
✅ Documentación incluye constraints por cada tipo de agente
```

---

### **IMPORTANTE 5: Gestión de Errores - Inconsistencia HTTP vs Semántico**

**Severidad:** 🟡 MEDIA

#### Descripción del Problema

La sección "7. Gestión de Errores" (líneas 223-236) menciona códigos HTTP (401, 404, 400, 502, 500), pero el Paso 1 es **solo lógica Python**, no API REST.

**Inconsistencias detectadas:**

1. El documento dice: "Token JWT inválido/expirado → 401"
2. Pero el modelo `AgentError` usa `codigo: str` (no `int`):
   ```python
   @dataclass
   class AgentError:
       codigo: str  # "AUTH_INVALID_TOKEN"
       mensaje: str
   ```

3. **¿Entonces `codigo` debe ser `"401"` o `"AUTH_INVALID_TOKEN"`?**

#### Por Qué Importa

- El Paso 1 es **solo clases Python** (sin API REST)
- Los códigos HTTP son para el Paso 2 (FastAPI)
- Mezclar niveles de abstracción genera confusión

#### Solución Requerida

**Aclarar sección "7. Gestión de Errores" (líneas 223-236):**

```markdown
### 7. Gestión de Errores

#### Códigos de Error del Back-Office (Paso 1)

El sistema usa códigos de error **semánticos** (no HTTP), ya que es lógica Python pura.

```python
# backoffice/models.py

@dataclass
class AgentError:
    """
    Error del sistema de agentes.

    En Paso 2 (API REST), estos se mapearán a códigos HTTP.
    """
    codigo: str      # Código semántico (ej: "AUTH_INVALID_TOKEN")
    mensaje: str     # Mensaje descriptivo
    details: Optional[Dict[str, Any]] = None  # Detalles adicionales

# Catálogo de códigos de error
ERROR_CODES = {
    # Errores de autenticación
    "AUTH_INVALID_TOKEN": "Token JWT inválido o mal formado",
    "AUTH_TOKEN_EXPIRED": "Token JWT expirado",
    "AUTH_PERMISSION_DENIED": "Permisos insuficientes",
    "AUTH_EXPEDIENTE_MISMATCH": "Token no autorizado para este expediente",

    # Errores de recursos
    "EXPEDIENTE_NOT_FOUND": "Expediente no encontrado",
    "DOCUMENTO_NOT_FOUND": "Documento no encontrado",

    # Errores de configuración
    "AGENT_NOT_CONFIGURED": "Tipo de agente no configurado",
    "AGENT_CONFIG_INVALID": "Configuración de agente inválida",

    # Errores de MCP
    "MCP_CONNECTION_ERROR": "Error al conectar con servidor MCP",
    "MCP_TIMEOUT": "Timeout en llamada a MCP",
    "MCP_TOOL_ERROR": "Error al ejecutar tool MCP",
    "MCP_AUTH_ERROR": "Error de autenticación con MCP",

    # Errores de validación
    "OUTPUT_VALIDATION_ERROR": "Output del agente no válido",
    "INPUT_VALIDATION_ERROR": "Parámetros de entrada inválidos",

    # Errores internos
    "INTERNAL_ERROR": "Error interno del sistema"
}
```

#### Mapeo a HTTP (Referencia para Paso 2)

Cuando en el Paso 2 se envuelva esto en una API REST, el mapeo será:

```python
# API FastAPI (Paso 2) - Solo referencia
HTTP_STATUS_MAPPING = {
    "AUTH_INVALID_TOKEN": 401,
    "AUTH_TOKEN_EXPIRED": 401,
    "AUTH_PERMISSION_DENIED": 403,
    "AUTH_EXPEDIENTE_MISMATCH": 403,
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

#### Manejo de Errores en AgentExecutor

```python
# backoffice/executor.py

class AgentExecutor:
    async def execute(...) -> AgentExecutionResult:
        try:
            # ... lógica de ejecución ...

        except JWTValidationError as e:
            return AgentExecutionResult(
                success=False,
                agent_run_id=run_id,
                resultado={},
                log_auditoria=logger.get_log_entries(),
                herramientas_usadas=[],
                error=AgentError(
                    codigo="AUTH_INVALID_TOKEN",
                    mensaje=str(e)
                )
            )

        except MCPConnectionError as e:
            return AgentExecutionResult(
                success=False,
                agent_run_id=run_id,
                resultado={},
                log_auditoria=logger.get_log_entries(),
                herramientas_usadas=[],
                error=AgentError(
                    codigo="MCP_CONNECTION_ERROR",
                    mensaje=str(e)
                )
            )

        except OutputValidationError as e:
            return AgentExecutionResult(
                success=False,
                agent_run_id=run_id,
                resultado={},
                log_auditoria=logger.get_log_entries(),
                herramientas_usadas=[],
                error=AgentError(
                    codigo="OUTPUT_VALIDATION_ERROR",
                    mensaje=str(e)
                )
            )

        except Exception as e:
            # Error inesperado
            logger.log(f"Error inesperado: {e}", nivel="ERROR")
            return AgentExecutionResult(
                success=False,
                agent_run_id=run_id,
                resultado={},
                log_auditoria=logger.get_log_entries(),
                herramientas_usadas=[],
                error=AgentError(
                    codigo="INTERNAL_ERROR",
                    mensaje=f"Error inesperado: {str(e)}"
                )
            )
```

#### Logging de Errores

Todos los errores deben logearse con nivel ERROR antes de devolverse:

```python
logger.log(f"Error: {error.codigo} - {error.mensaje}", nivel="ERROR")
```
```

---

### **IMPORTANTE 6: Plan de Testing Insuficiente**

**Severidad:** 🟡 MEDIA

#### Descripción del Problema

El documento especifica (línea 318):
> "✅ Incluir tests automatizados (>80% cobertura)"

**Excelente objetivo**, pero **falta**:

1. **Casos de prueba específicos**
   - ¿Qué escenarios debe cubrir `test_executor.py`?
   - ¿Qué edge cases probar en `test_auth.py`?

2. **Estrategia de testing con MCP**
   - ¿Los tests arrancan el servidor MCP real?
   - ¿O se mockea el MCP (mock de un mock)?
   - ¿Cómo se gestionan fixtures de expedientes?

3. **Tests de integración**
   - ¿Hay tests end-to-end que validen todo el flujo?

#### Impacto

- Sin casos de prueba especificados, cada desarrollador interpretará diferente
- Riesgo de baja cobertura de edge cases
- Tests inconsistentes entre diferentes módulos

#### Solución Requerida

**Añadir nueva sección al final del documento:**

```markdown
## Plan de Testing

### Objetivo de Cobertura

- **Mínimo:** 80% de cobertura de código
- **Recomendado:** 90% para módulos críticos (auth, executor)

### Estrategia de Testing con MCP

Los tests deben ejecutarse contra el **servidor MCP mock real** (no un mock del mock).

**Setup de tests:**

```python
# backoffice/tests/conftest.py

import pytest
import asyncio
from pathlib import Path
import subprocess
import time
import httpx

@pytest.fixture(scope="session")
def mcp_server():
    """
    Arranca el servidor MCP mock para tests.

    Se ejecuta una vez por sesión de tests.
    """
    # Arrancar servidor MCP HTTP en puerto de test
    server_process = subprocess.Popen(
        ["python", "-m", "mcp_expedientes.server_http"],
        env={"MCP_PORT": "8001", "JWT_SECRET": "test-secret-key"},
        cwd=Path(__file__).parent.parent.parent / "mcp-mock" / "mcp-expedientes"
    )

    # Esperar a que el servidor esté listo
    time.sleep(2)

    # Verificar que el servidor responde
    for _ in range(10):
        try:
            response = httpx.get("http://localhost:8001/health")
            if response.status_code == 200:
                break
        except:
            time.sleep(0.5)

    yield "http://localhost:8001"

    # Limpiar: matar servidor
    server_process.terminate()
    server_process.wait()

@pytest.fixture
def test_token():
    """Genera un token JWT válido para tests"""
    from mcp_expedientes.generate_token import generate_token
    return generate_token(
        usuario="Automático",
        expediente_id="EXP-2024-001",
        permisos=["consulta", "gestion"]
    )

@pytest.fixture
def clean_expediente():
    """Resetea el expediente de prueba a su estado inicial"""
    # Implementar lógica de reset de fixtures
    pass
```

### Casos de Prueba Obligatorios

#### test_auth.py - Validación JWT

```python
@pytest.mark.asyncio
async def test_token_valido_pasa_validacion(test_token):
    """Token válido con todos los claims debe pasar validación"""
    from backoffice.auth.jwt_validator import JWTValidator

    claims = await JWTValidator.validate(
        token=test_token,
        expediente_id="EXP-2024-001"
    )

    assert claims.sub == "Automático"
    assert claims.exp_id == "EXP-2024-001"
    assert "consulta" in claims.permisos

@pytest.mark.asyncio
async def test_token_sin_exp_id_rechazado():
    """Token sin claim exp_id debe ser rechazado"""
    # Generar token malformado sin exp_id
    token = jwt.encode(
        {"sub": "Automático", "exp": time.time() + 3600},
        "test-secret-key",
        algorithm="HS256"
    )

    with pytest.raises(AuthError, match="exp_id"):
        await JWTValidator.validate(token, "EXP-2024-001")

@pytest.mark.asyncio
async def test_token_expediente_diferente_rechazado(test_token):
    """Token para expediente A no debe permitir acceso a expediente B"""
    with pytest.raises(AuthError, match="no autorizado"):
        await JWTValidator.validate(
            token=test_token,  # Token para EXP-2024-001
            expediente_id="EXP-2024-002"  # Intentar acceder a otro
        )

@pytest.mark.asyncio
async def test_token_expirado_rechazado():
    """Token expirado debe ser rechazado"""
    # Generar token expirado
    token = jwt.encode(
        {
            "sub": "Automático",
            "exp_id": "EXP-2024-001",
            "exp": time.time() - 3600,  # Expirado hace 1 hora
            "permisos": ["consulta"]
        },
        "test-secret-key",
        algorithm="HS256"
    )

    with pytest.raises(AuthError, match="expirado"):
        await JWTValidator.validate(token, "EXP-2024-001")

@pytest.mark.asyncio
async def test_token_permisos_insuficientes_rechazado():
    """Token sin permiso 'gestion' no debe poder ejecutar tools de escritura"""
    # Token solo con permiso 'consulta'
    token = generate_token(
        usuario="Automático",
        expediente_id="EXP-2024-001",
        permisos=["consulta"]  # Sin 'gestion'
    )

    with pytest.raises(AuthError, match="Permiso insuficiente"):
        await JWTValidator.validate_permission(
            token,
            required_permission="gestion"
        )
```

#### test_mcp_client.py - Cliente MCP

```python
@pytest.mark.asyncio
async def test_mcp_client_call_tool_exitoso(mcp_server, test_token):
    """Llamada exitosa a tool MCP debe retornar resultado"""
    from backoffice.mcp.client import MCPClient

    client = MCPClient(base_url=mcp_server, token=test_token)

    result = await client.call_tool(
        "consultar_expediente",
        {"expediente_id": "EXP-2024-001"}
    )

    assert result is not None
    assert "id" in result
    assert result["id"] == "EXP-2024-001"

    await client.close()

@pytest.mark.asyncio
async def test_mcp_client_token_invalido_lanza_excepcion(mcp_server):
    """Llamada con token inválido debe lanzar MCPAuthError"""
    from backoffice.mcp.client import MCPClient, MCPAuthError

    client = MCPClient(base_url=mcp_server, token="token-invalido")

    with pytest.raises(MCPAuthError):
        await client.call_tool(
            "consultar_expediente",
            {"expediente_id": "EXP-2024-001"}
        )

    await client.close()

@pytest.mark.asyncio
async def test_mcp_client_servidor_caido_reintenta():
    """Cliente debe reintentar automáticamente si servidor está caído"""
    from backoffice.mcp.client import MCPClient, MCPConnectionError

    # URL a servidor inexistente
    client = MCPClient(
        base_url="http://localhost:9999",
        token="any-token",
        max_retries=3
    )

    start_time = time.time()

    with pytest.raises(MCPConnectionError):
        await client.call_tool("consultar_expediente", {"expediente_id": "EXP-001"})

    elapsed = time.time() - start_time

    # Debe haber reintentos (1s + 2s + 4s ≈ 7s de backoff)
    assert elapsed >= 6  # Al menos 3 reintentos con backoff

    await client.close()

@pytest.mark.asyncio
async def test_mcp_client_timeout_configurable(mcp_server, test_token):
    """Cliente debe respetar timeout configurado"""
    from backoffice.mcp.client import MCPClient, MCPConnectionError

    # Cliente con timeout muy corto
    client = MCPClient(
        base_url=mcp_server,
        token=test_token,
        timeout=0.001  # 1ms - casi imposible de cumplir
    )

    with pytest.raises(MCPConnectionError, match="Timeout"):
        await client.call_tool("consultar_expediente", {"expediente_id": "EXP-001"})

    await client.close()
```

#### test_executor.py - AgentExecutor

```python
@pytest.mark.asyncio
async def test_executor_ejecuta_agente_exitosamente(mcp_server, test_token, clean_expediente):
    """Ejecución exitosa de agente debe retornar success=True"""
    from backoffice.executor import AgentExecutor
    from backoffice.models import AgentConfig

    executor = AgentExecutor(mcp_url=mcp_server)

    config = AgentConfig(
        nombre="ValidadorDocumental",
        system_prompt="Eres un validador de documentación",
        modelo="mock",
        prompt_tarea="Valida que todos los documentos estén presentes",
        herramientas=["consultar_expediente", "actualizar_datos", "añadir_anotacion"]
    )

    resultado = await executor.execute(
        token=test_token,
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=config
    )

    assert resultado.success is True
    assert resultado.agent_run_id is not None
    assert len(resultado.log_auditoria) > 0
    assert len(resultado.herramientas_usadas) > 0
    assert resultado.error is None

@pytest.mark.asyncio
async def test_executor_token_invalido_retorna_error(mcp_server):
    """Ejecución con token inválido debe retornar error AUTH_INVALID_TOKEN"""
    from backoffice.executor import AgentExecutor
    from backoffice.models import AgentConfig

    executor = AgentExecutor(mcp_url=mcp_server)

    config = AgentConfig(
        nombre="ValidadorDocumental",
        system_prompt="...",
        modelo="mock",
        prompt_tarea="...",
        herramientas=["consultar_expediente"]
    )

    resultado = await executor.execute(
        token="token-invalido",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=config
    )

    assert resultado.success is False
    assert resultado.error is not None
    assert resultado.error.codigo == "AUTH_INVALID_TOKEN"

@pytest.mark.asyncio
async def test_executor_agente_no_configurado_retorna_error(mcp_server, test_token):
    """Ejecución de agente no configurado debe retornar error AGENT_NOT_CONFIGURED"""
    from backoffice.executor import AgentExecutor
    from backoffice.models import AgentConfig

    executor = AgentExecutor(mcp_url=mcp_server)

    config = AgentConfig(
        nombre="AgenteInexistente",  # Agente no implementado
        system_prompt="...",
        modelo="mock",
        prompt_tarea="...",
        herramientas=[]
    )

    resultado = await executor.execute(
        token=test_token,
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=config
    )

    assert resultado.success is False
    assert resultado.error is not None
    assert resultado.error.codigo == "AGENT_NOT_CONFIGURED"

@pytest.mark.asyncio
async def test_executor_error_mcp_registra_logs_completos(mcp_server, test_token):
    """Error en MCP debe registrarse completamente en logs de auditoría"""
    # Implementar test que provoque error en MCP y verifique logs
    pass
```

#### test_agents.py - Agentes Mock

```python
@pytest.mark.asyncio
async def test_validador_documental_documentos_completos(mcp_server, test_token, clean_expediente):
    """ValidadorDocumental con documentos completos debe marcar validacion_ok=True"""
    from backoffice.agents.validador_documental import ValidadorDocumentalMock
    from backoffice.mcp.client import MCPClient
    from backoffice.logging.audit_logger import AuditLogger

    client = MCPClient(base_url=mcp_server, token=test_token)
    logger = AuditLogger("EXP-2024-001", "RUN-001", Path("/tmp/logs"))

    agent = ValidadorDocumentalMock(
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        mcp_client=client,
        logger=logger
    )

    resultado = await agent.execute()

    assert resultado["completado"] is True
    assert resultado["datos_actualizados"]["datos.documentacion_valida"] is True

    await client.close()

@pytest.mark.asyncio
async def test_validador_documental_documentos_faltantes(mcp_server, test_token):
    """ValidadorDocumental con documentos faltantes debe marcar validacion_ok=False"""
    # Preparar expediente con documentos incompletos
    # Ejecutar agente
    # Verificar que validacion_ok=False
    pass

@pytest.mark.asyncio
async def test_validador_logs_registran_todos_pasos(mcp_server, test_token, clean_expediente):
    """Logs de auditoría deben registrar todos los pasos del agente"""
    # Ejecutar agente
    # Verificar que logs incluyen:
    #   - Iniciando validación
    #   - Consultando expediente
    #   - Documentos encontrados: N
    #   - Actualizando campo datos.documentacion_valida
    #   - Añadiendo anotación
    pass

@pytest.mark.asyncio
async def test_validador_historial_expediente_actualizado(mcp_server, test_token, clean_expediente):
    """Historial del expediente debe tener nueva entrada tras ejecución"""
    # Consultar historial inicial
    # Ejecutar agente
    # Consultar historial final
    # Verificar que tiene nueva entrada con tipo="ANOTACION"
    pass

@pytest.mark.asyncio
async def test_validador_respeta_output_validation(mcp_server, test_token):
    """Agente debe respetar constraints de output validation"""
    # Ver tests en sección "Output Validation"
    pass
```

#### test_logging.py - Sistema de Logging y Redacción PII

```python
def test_pii_redactor_dni():
    """Redactor debe reemplazar DNIs con [DNI-REDACTED]"""
    from backoffice.logging.pii_redactor import PIIRedactor

    mensaje = "Solicitante Juan Pérez con DNI 12345678A"
    redacted = PIIRedactor.redact(mensaje)

    assert "12345678A" not in redacted
    assert "[DNI-REDACTED]" in redacted

def test_pii_redactor_email():
    """Redactor debe reemplazar emails con [EMAIL-REDACTED]"""
    from backoffice.logging.pii_redactor import PIIRedactor

    mensaje = "Contacto: juan.perez@example.com"
    redacted = PIIRedactor.redact(mensaje)

    assert "juan.perez@example.com" not in redacted
    assert "[EMAIL-REDACTED]" in redacted

def test_pii_redactor_iban():
    """Redactor debe reemplazar IBANs con [IBAN-REDACTED]"""
    from backoffice.logging.pii_redactor import PIIRedactor

    mensaje = "Cuenta bancaria: ES1234567890123456789012"
    redacted = PIIRedactor.redact(mensaje)

    assert "ES1234567890123456789012" not in redacted
    assert "[IBAN-REDACTED]" in redacted

def test_audit_logger_escribe_logs_redactados(tmp_path):
    """Logger debe escribir logs con PII redactada automáticamente"""
    from backoffice.logging.audit_logger import AuditLogger

    logger = AuditLogger("EXP-001", "RUN-001", tmp_path)
    logger.log("Usuario con DNI 12345678Z solicita expediente")

    log_file = tmp_path / "EXP-001" / "RUN-001.log"
    content = log_file.read_text()

    # NO debe contener DNI original
    assert "12345678Z" not in content
    # SÍ debe contener redacción
    assert "[DNI-REDACTED]" in content

def test_audit_logger_redacta_metadata(tmp_path):
    """Logger debe redactar también la metadata"""
    from backoffice.logging.audit_logger import AuditLogger

    logger = AuditLogger("EXP-001", "RUN-001", tmp_path)
    logger.log(
        "Consultando expediente",
        metadata={"solicitante_email": "juan@example.com"}
    )

    log_file = tmp_path / "EXP-001" / "RUN-001.log"
    content = log_file.read_text()

    assert "juan@example.com" not in content
    assert "[EMAIL-REDACTED]" in content
```

### Ejecución de Tests

```bash
# Ejecutar todos los tests con cobertura
cd backoffice
pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

# Ejecutar solo tests de autenticación
pytest tests/test_auth.py -v

# Ejecutar con logs visibles (útil para debugging)
pytest tests/ -v -s

# Ejecutar en modo watch (re-ejecuta al cambiar archivos)
pytest-watch tests/
```

### Objetivo de Cobertura por Módulo

| Módulo | Cobertura Mínima | Justificación |
|--------|------------------|---------------|
| `auth/` | 95% | Crítico para seguridad |
| `executor.py` | 90% | Punto de entrada principal |
| `mcp/client.py` | 90% | Integración crítica |
| `logging/` | 90% | Cumplimiento GDPR |
| `agents/` | 85% | Lógica de negocio |
| `models.py` | 80% | Modelos de datos |

### Criterios de Aceptación Actualizados

Añadir:

✅ Tests cubren >80% del código (verificado con `pytest --cov`)
✅ Todos los tests de los casos obligatorios pasan
✅ Tests se ejecutan contra servidor MCP real (no mock del mock)
✅ Tests incluyen verificación de redacción de PII
✅ Tests de output validation funcionan correctamente
✅ Fixtures de expedientes se resetean entre tests
✅ Tests documentan edge cases específicos
```

---

### **IMPORTANTE 7: Falta Consideración de Problemas Documentados**

**Severidad:** 🟡 MEDIA

#### Descripción del Problema

El proyecto tiene análisis críticos detallados en:
- `/doc/problemas/101-problema-arquitectura-mcp.md`
- `/doc/problemas/102-problema-permisos-seguridad.md`

Sin embargo, el documento del Paso 1 **no menciona ni aborda** varios problemas identificados.

**Aspectos ignorados:**

1. **Latencia no considerada** (problemas/101 líneas 30-39)
   - No hay requisitos de rendimiento especificados
   - ¿Cuánto debe tardar un agente mock?
   - ¿Se medirá latencia de llamadas MCP?

2. **Versionado de MCP no definido** (problemas/101 líneas 56-65)
   - ¿Qué pasa si el servidor MCP cambia su interfaz?
   - ¿El cliente declara versión MCP soportada?

3. **Estrategia de resiliencia ausente** (problemas/101 líneas 42-53)
   - ¿Circuit breaker en cliente MCP?
   - ¿Fallback si MCP está caído?

#### Impacto

- El mock no valida aspectos no funcionales importantes
- Problemas de rendimiento/resiliencia se descubrirán tarde

#### Solución Requerida

**Añadir nueva sección "Requisitos No Funcionales":**

```markdown
## Requisitos No Funcionales

### Performance

#### Latencia Objetivo

- **Agente mock completo:** < 5 segundos
- **Llamada individual a MCP:** < 500ms (P95)
- **Validación JWT:** < 50ms

#### Métricas a Recopilar

Cada ejecución debe registrar:
- Tiempo total de ejecución
- Latencia por tool MCP (min, max, avg)
- Número de llamadas a MCP
- Tamaño de payloads (request/response)

```python
# backoffice/executor.py

class AgentExecutor:
    async def execute(...) -> AgentExecutionResult:
        start_time = time.time()

        # ... ejecución del agente ...

        execution_time = time.time() - start_time

        logger.log(f"Ejecución completada en {execution_time:.2f}s")

        # Verificar que no excede límite
        if execution_time > 5.0:
            logger.log(
                f"⚠️ Ejecución lenta: {execution_time:.2f}s (límite: 5.0s)",
                nivel="WARNING"
            )
```

### Resiliencia

#### Estrategia de Reintentos

Ver especificación en sección "4. Cliente MCP".

- Reintentos automáticos: 3 intentos
- Exponential backoff: 1s, 2s, 4s
- Timeout: 30s por operación

#### Circuit Breaker (Opcional para Paso 1)

**Nota:** No es crítico implementarlo en el mock, pero el diseño debe contemplarlo.

```python
# Referencia para futuro (Paso 3-4)
# backoffice/mcp/circuit_breaker.py

class CircuitBreaker:
    """
    Circuit breaker para proteger contra fallos cascada del servidor MCP.

    Estados:
    - CLOSED: Funcionamiento normal
    - OPEN: Servidor considerado caído, rechazar requests
    - HALF_OPEN: Probar si servidor se recuperó
    """
    pass
```

#### Fallback Strategy

Si el servidor MCP está completamente inaccesible tras reintentos:

```python
# En AgentExecutor
if mcp_connection_failed_after_retries:
    return AgentExecutionResult(
        success=False,
        agent_run_id=run_id,
        resultado={},
        log_auditoria=logger.get_log_entries(),
        herramientas_usadas=[],
        error=AgentError(
            codigo="MCP_CONNECTION_ERROR",
            mensaje="Servidor MCP no disponible tras 3 reintentos"
        )
    )
```

**Importante:** El sistema BPMN debe manejar este error apropiadamente (ej: marcar tarea para revisión manual).

### Observabilidad

#### Métricas Recomendadas (para Paso 2-3)

Aunque en Paso 1 no se implementará Prometheus, el diseño debe contemplar:

```python
# Métricas a exponer en futuro:
# - agent_executions_total{agent_type, status}
# - agent_execution_duration_seconds{agent_type}
# - mcp_tool_calls_total{tool_name, status}
# - mcp_tool_call_duration_seconds{tool_name}
# - jwt_validation_errors_total{error_code}
```

Por ahora, incluir esta información en los logs estructurados.

### Versionado

#### Versión del Back-Office

```python
# backoffice/__init__.py
__version__ = "0.1.0"  # Paso 1: Mock funcional
```

#### Compatibilidad con MCP

El cliente MCP debe declarar qué versión del protocolo soporta:

```python
# backoffice/mcp/client.py

class MCPClient:
    MCP_VERSION = "1.0.0"

    async def list_tools(self):
        # Incluir versión en headers/request
        ...
```

**Nota:** En Paso 1, como el servidor MCP mock es nuestro, no hay problema de incompatibilidad. Pero el diseño debe contemplar versionado para el futuro.
```

---

## 📋 Resumen de Recomendaciones

### Prioridad CRÍTICA (Bloqueantes para Implementación)

| # | Problema | Acción Requerida | Estado | Estimación |
|---|----------|------------------|--------|------------|
| 1 | JWT claims inconsistentes | Actualizar sección 2 con claims completos según código existente | ✅ COMPLETADO | ~~30 min~~ |
| 2 | Cliente MCP subespecificado | Reemplazar sección 4 con especificación técnica completa | ✅ COMPLETADO | ~~1 hora~~ |
| 3 | Logging sin redacción PII | Ampliar sección 5 con PIIRedactor y tests | ✅ COMPLETADO | ~~2 horas~~ |

**Subtotal CRÍTICO:** ✅ **COMPLETADO** (3 de 3)

### Prioridad ALTA (Importantes para Calidad)

| # | Problema | Acción Requerida | Estado | Estimación |
|---|----------|------------------|--------|------------|
| 4 | Output validation ausente | Añadir nueva sección 7 con validación de salida | 🟡 PENDIENTE | 1.5 horas |
| 5 | Códigos de error inconsistentes | Aclarar sección 7 con catálogo semántico | ✅ COMPLETADO | ~~30 min~~ |
| 6 | Plan de testing insuficiente | Añadir nueva sección con casos de prueba concretos | 🟡 PENDIENTE | 1 hora |

**Subtotal ALTA:** 2.5 horas restantes (1 de 3 completado)

### Prioridad MEDIA (Mejoras Progresivas)

| # | Problema | Acción Requerida | Estado | Estimación |
|---|----------|------------------|--------|------------|
| 7 | Requisitos no funcionales no considerados | Añadir sección de performance/resiliencia | 🟡 PENDIENTE | 45 min |

**Subtotal MEDIA:** 45 min restantes

---

**Tiempo total original:** ~7.5 horas
**Tiempo completado (CRÍTICOS):** ~3.5 horas (47%)
**Tiempo restante (ALTA+MEDIA):** ~4 horas

---

## 🎯 Conclusión y Siguiente Paso

### Valoración Final (Actualizada)

El documento del Paso 1 es un **muy buen punto de partida** que demuestra:
- Comprensión clara de la arquitectura general
- Enfoque incremental apropiado
- Nivel de detalle generalmente adecuado

**Progreso actual (2025-11-30):**
- ✅ 4 de 7 problemas resueltos (57%)
- ✅ **TODOS los problemas CRÍTICOS resueltos (3/3 = 100%)**
  - CRÍTICO 1 (JWT claims) - completamente corregido
  - CRÍTICO 2 (Cliente MCP) - completamente especificado
  - CRÍTICO 3 (Logging PII) - completamente implementado
- ✅ ALTA 5 (códigos de error) - corregido como parte del CRÍTICO 1
- 🟡 2 problemas ALTA restantes (recomendados)
- 🟡 1 problema MEDIA restante (opcional)

**El documento está LISTO para implementación:**
- ~~Inconsistencias críticas con código existente (JWT)~~ ✅ RESUELTO
- ~~Subespecificación de componentes clave (cliente MCP)~~ ✅ RESUELTO
- ~~Omisiones en aspectos de seguridad y cumplimiento (PII redaction)~~ ✅ RESUELTO

**Todos los bloqueantes eliminados.** Los problemas ALTA y MEDIA son mejoras de calidad recomendadas pero no bloqueantes.

### Siguiente Acción Recomendada

**El documento está listo para comenzar implementación:**

1. ✅ ~~**Resolver CRÍTICO 1 (JWT claims)**~~ → COMPLETADO (2025-11-30)

2. ✅ ~~**Resolver CRÍTICO 2 (Cliente MCP)**~~ → COMPLETADO (2025-11-30)

3. ✅ ~~**Resolver CRÍTICO 3 (Logging sin redacción PII)**~~ → COMPLETADO (2025-11-30)

4. **✅ TODOS LOS PROBLEMAS BLOQUEANTES RESUELTOS**

### Opciones Ahora

**Opción A: Comenzar Implementación Inmediatamente** (RECOMENDADO)
- Todos los requisitos críticos están especificados
- El documento es suficientemente completo para un Paso 1 (mock)
- Los problemas restantes son mejoras de calidad, no bloqueantes
- Ventaja: Empezar a validar arquitectura cuanto antes

**Opción B: Resolver Problemas ALTA antes de implementar**
- IMPORTANTE 4: Validación de salida (output validation) → ~1.5 horas
- IMPORTANTE 6: Plan de testing más detallado → ~1 hora
- Ventaja: Mayor calidad desde el inicio
- Desventaja: Retrasa validación de arquitectura

**Opción C: Revisar con stakeholders antes de implementar**
- ✅ ~~Confirmar estructura de JWT con equipo GEX/BPMN~~ (ya validado con código existente)
- ✅ ~~Confirmar arquitectura cliente MCP~~ (especificación completa incorporada)
- ✅ ~~Confirmar requisitos de redacción PII~~ (GDPR/LOPD/ENS implementado)
- Acordar SLAs de performance con equipo de operaciones (opcional para Paso 1)

### Recomendación Final

**Comenzar implementación del Paso 1 ahora.** El documento está suficientemente completo:

- ✅ Todos los aspectos críticos resueltos
- ✅ Especificación técnica completa
- ✅ Cumplimiento normativo garantizado
- 🟡 Mejoras de calidad pueden incorporarse durante implementación o en revisión posterior

### Beneficios de Corregir Antes

- ✅ Evita descubrir inconsistencias durante integración
- ✅ Reduce riesgo de refactorizaciones grandes
- ✅ Asegura cumplimiento normativo desde el inicio
- ✅ Facilita onboarding de nuevos desarrolladores
- ✅ Mejora estimaciones de esfuerzo (más precisas)

---

## 📊 Estado del Documento

**Última actualización:** 2025-11-30

**Progreso de correcciones:**
- ✅ Completadas: 4/7 (57%)
- ✅ **Críticas completadas: 3/3 (100%) - TODOS RESUELTOS**
- 🟡 Altas pendientes: 2/3 (recomendadas, no bloqueantes)
- 🟡 Medias pendientes: 1/1 (opcional)

**Estado del documento:**
- ✅ **LISTO PARA IMPLEMENTACIÓN** (todos los bloqueantes resueltos)

**Próximos pasos opcionales (mejoras de calidad):**
1. OPCIONAL: Resolver problemas ALTA (4, 6) para mayor calidad → ~2.5 horas
2. OPCIONAL: Resolver problema MEDIA (7) → ~45 min
3. **RECOMENDADO: Comenzar implementación del Paso 1**

---

**Fin del documento de crítica (versión actualizada)**
