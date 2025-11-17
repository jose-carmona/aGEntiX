# Construcción de Servicios MCP Mock para aGEntiX

## Contexto

El proyecto se centra en la ejecución de agentes IA.

Los agentes interactúan con GEX mediante MCP (Model Context Protocol).

Para construir dichos agentes necesitamos servicios MCP.

Vamos a construir una serie de servicios mock en los que nos apoyaremos más adelante en la construcción de los agentes y en las pruebas.

## Tecnologías

Para la construcción de los servicios MCP mock nos vamos a basar en **Python**.

Simularemos los expedientes mediante **ficheros JSON**.

El MCP implementará el protocolo oficial usando el SDK de Python, con soporte para múltiples transportes (stdio y HTTP/SSE).

## Objetivos

Crear un servidor MCP mock que:

1. **Simule el acceso a GEX** sin necesidad de conectar con el sistema real
2. **Permita pruebas** de agentes IA durante el desarrollo
3. **Implemente el modelo de permisos** basado en JWT
4. **Proporcione herramientas (tools)** de lectura y escritura sobre expedientes
5. **Valide la propagación de permisos** según la arquitectura del sistema

## Alcance de la Simulación

### Posición en la Arquitectura Multi-MCP

Este servidor **MCP Mock de Expedientes** es uno de varios servidores MCP especializados que conformarán el sistema aGEntiX (ver sección "Arquitectura Multi-MCP" más adelante para detalles sobre otros MCP servers).

### Componentes Simulados

El servidor MCP Mock de Expedientes simula conjuntamente:
- **MCP Server**: Implementa el protocolo MCP para acceso a expedientes
- **API de GEX**: Capa de acceso específica de expedientes
- **Almacenamiento GEX**: Persistencia de expedientes en JSON

### Componentes NO Simulados (responsabilidad externa)

- **Motor BPMN**: El sistema de pruebas debe simular la invocación BPMN
- **Agente IA**: Los tests invocarán directamente las tools/resources del MCP
- **Otros MCP Servers**: Normativa, Documentos, etc. (serán implementados por separado)

### Flujo de Prueba

```
Test Script (simula BPMN) → [JWT] → MCP Mock Expedientes → JSON Storage
                                            ↓
                                Tools/Resources disponibles
                                            ↓
                                Test Agent (simula Agente IA)
                                            ↓
                            (Puede usar otros MCP Servers)
```

## Arquitectura

### Flujo Básico

```
BPMN (simulado) → Agente → MCP Mock → Datos JSON
```

El MCP Mock debe:
- Validar tokens JWT con claims completos (usuario "Automático", ID de expediente, contexto BPMN)
- Verificar permisos antes de cada operación
- Exponer resources y tools según la especificación MCP
- Mantener el estado en ficheros JSON

### Arquitectura Multi-MCP

El sistema aGEntiX contempla una arquitectura con **múltiples servidores MCP especializados** que proporcionan diferentes capacidades a los agentes IA.

```
                    ┌─────────────────┐
                    │  Motor BPMN     │
                    └────────┬────────┘
                             │ (JWT)
                    ┌────────▼────────┐
                    │  Agente IA      │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
    ┌───────▼──────┐  ┌──────▼──────┐  ┌─────▼──────┐
    │ MCP          │  │ MCP         │  │ MCP        │
    │ Expedientes  │  │ Normativa   │  │ Documentos │
    └───────┬──────┘  └──────┬──────┘  └─────┬──────┘
            │                │                │
    ┌───────▼──────┐  ┌──────▼──────┐  ┌─────▼──────┐
    │ JSON Store   │  │ JSON Store  │  │ Plantillas │
    └──────────────┘  └─────────────┘  └────────────┘
```

#### Otros Servidores MCP Previstos

**MCP de Normativa**
- **Propósito**: Acceso a normativa de referencia (BOE, BOJA, ordenanzas)
- **Resources**: `normativa://BOE/{año}/{numero}`, `normativa://BOJA/{año}/{numero}`, etc.
- **Tools**: `buscar_normativa`, `obtener_articulo`, `validar_vigencia`

**MCP de Generación de Documentos**
- **Propósito**: Generar documentos PDF desde plantillas
- **Resources**: `plantilla://{tipo_expediente}/{nombre_plantilla}`
- **Tools**: `listar_plantillas`, `generar_documento`, `previsualizar_documento`

#### Estrategia de Implementación

**Fase 1**: MCP de Expedientes (este documento)
**Fase 2**: MCP de Normativa
**Fase 3**: MCP de Generación de Documentos

Todos usarán persistencia en JSON para simplicidad, transparencia y facilidad de testing.

## Modelo de Datos

Cada expediente será un fichero JSON que contenga:

### Estructura Completa del Expediente

```json
{
  "id": "EXP-2024-001",
  "tipo": "SUBVENCIONES",
  "estado": "EN_TRAMITE",
  "fecha_inicio": "2024-01-15T08:30:00Z",
  "datos": {
    "solicitante": {
      "nombre": "María García López",
      "nif": "12345678A",
      "direccion": "Calle Mayor 123, Córdoba",
      "email": "maria.garcia@example.com",
      "telefono": "+34 600123456"
    },
    "importe_solicitado": 5000.00,
    "concepto": "Ayuda para mejora de local comercial",
    "cuenta_bancaria": "ES79 2100 0813 4501 2345 6789",
    "documentacion_valida": null
  },
  "documentos": [
    {
      "id": "DOC-001",
      "nombre": "solicitud.pdf",
      "fecha": "2024-01-15T08:30:00Z",
      "tipo": "SOLICITUD",
      "ruta": "data/documentos/EXP-2024-001/solicitud.pdf",
      "hash_sha256": "abc123...",
      "tamano_bytes": 245678,
      "validado": null
    },
    {
      "id": "DOC-002",
      "nombre": "dni.pdf",
      "fecha": "2024-01-15T08:30:00Z",
      "tipo": "IDENTIFICACION",
      "ruta": "data/documentos/EXP-2024-001/dni.pdf",
      "hash_sha256": "def456...",
      "tamano_bytes": 123456,
      "validado": null
    },
    {
      "id": "DOC-003",
      "nombre": "justificante_bancario.pdf",
      "fecha": "2024-01-15T08:30:00Z",
      "tipo": "BANCARIO",
      "ruta": "data/documentos/EXP-2024-001/justificante.pdf",
      "hash_sha256": "ghi789...",
      "tamano_bytes": 98765,
      "validado": null
    }
  ],
  "historial": [
    {
      "id": "HIST-001",
      "fecha": "2024-01-15T08:30:00Z",
      "usuario": "Sistema",
      "tipo": "SISTEMA",
      "accion": "INICIAR_EXPEDIENTE",
      "detalles": "Expediente iniciado desde portal ciudadano"
    },
    {
      "id": "HIST-002",
      "fecha": "2024-01-15T10:30:00Z",
      "usuario": "Automático",
      "tipo": "AGENTE",
      "accion": "INICIAR_VALIDACION",
      "detalles": "Agente iniciado para validar documentación"
    }
  ],
  "metadatos": {
    "flujo_bpmn": {
      "id": "SUBVENCIONES_v1.2",
      "nombre": "Tramitación de Subvenciones",
      "version": "1.2",
      "fecha_inicio_flujo": "2024-01-15T08:30:00Z"
    },
    "tarea_actual": {
      "id": "TAREA-VALIDAR-DOC-001",
      "nombre": "VALIDAR_DOCUMENTACION",
      "tipo": "agent",
      "fecha_inicio": "2024-01-15T10:30:00Z",
      "fecha_limite": "2024-01-17T10:30:00Z",
      "estado": "EN_EJECUCION",
      "intentos": 1,
      "responsable": "Automático"
    },
    "tareas_completadas": [
      {
        "id": "TAREA-INICIO-001",
        "nombre": "INICIAR_EXPEDIENTE",
        "fecha_inicio": "2024-01-15T08:30:00Z",
        "fecha_fin": "2024-01-15T08:31:00Z",
        "responsable": "Sistema",
        "resultado": "COMPLETADO"
      }
    ],
    "siguiente_tarea": {
      "candidatos": [
        {
          "id": "TAREA-RESOLVER-001",
          "nombre": "RESOLVER_SUBVENCION",
          "condicion": "datos.documentacion_valida == true"
        },
        {
          "id": "TAREA-REQUERIR-DOC-001",
          "nombre": "REQUERIR_DOCUMENTACION",
          "condicion": "datos.documentacion_valida == false"
        }
      ]
    }
  }
}
```

### Campos Adicionales Explicados

**flujo_bpmn**: Información del proceso BPMN completo
- `id`: Identificador único del flujo
- `version`: Control de versiones del flujo

**tarea_actual**: Información detallada de la tarea en curso
- `fecha_limite`: Para simular timeouts
- `intentos`: Para simular reintentos
- `estado`: EN_EJECUCION | COMPLETADA | FALLIDA | TIMEOUT

**tareas_completadas**: Historial de tareas del flujo

**siguiente_tarea**: Define las posibles transiciones
- `candidatos`: Array de posibles siguientes tareas
- `condicion`: Expresión que determina la transición

## Diseño Conceptual: Resources vs Tools

### Resources (Recursos)

**Propósito**: Exponer información que el agente puede **leer pasivamente**.

**Características**:
- Operaciones idempotentes (sin efectos secundarios)
- El agente "pull" información cuando la necesita
- Formato URI estándar
- Cacheable

**Uso en el agente**:
El LLM puede pedir al runtime "dame el recurso X" para añadirlo a su contexto.

**Ejemplo**:
```
URI: expediente://EXP-2024-001
Retorna: JSON completo del expediente

URI: expediente://EXP-2024-001/documentos
Retorna: Lista de documentos

URI: expediente://EXP-2024-001/documento/DOC-001
Retorna: Metadata del documento DOC-001
```

### Tools (Herramientas)

**Propósito**: Exponer **acciones** que el agente puede ejecutar.

**Características**:
- Pueden tener efectos secundarios (escribir, modificar)
- El agente las invoca activamente con parámetros
- Definición de schema de entrada
- Respuesta estructurada

**Uso en el agente**:
El LLM decide "voy a ejecutar la tool X con parámetros Y".

**Ejemplo**:
```
Tool: añadir_documento
Input: {expediente_id, nombre, tipo, contenido}
Output: {success: true, documento_id: "DOC-004"}

Tool: actualizar_datos
Input: {expediente_id, campo, valor}
Output: {success: true, valor_anterior: "..."}
```

### Decisión de Diseño

**Para este mock**:

- **Resources**: Información completa del expediente (para contexto del LLM)
- **Tools**: Todas las operaciones (lectura y escritura)

**Justificación**:
- Resources permiten al agente obtener contexto completo
- Tools proporcionan control fino sobre permisos
- Separación clara: contexto vs acciones

### Mapeo

| Concepto | Implementación |
|----------|----------------|
| Consultar expediente completo | Resource: `expediente://{id}` |
| Leer historial | Resource: `expediente://{id}/historial` |
| Listar documentos | Tool: `listar_documentos` |
| Obtener documento específico | Tool: `obtener_documento` |
| Añadir documento | Tool: `añadir_documento` |
| Actualizar datos | Tool: `actualizar_datos` |
| Añadir anotación | Tool: `añadir_anotacion` |

**Nota**: `listar_documentos` y `obtener_documento` son Tools (no Resources) para aplicar validación de permisos explícita.

## Recursos MCP (Resources)

El servidor MCP debe exponer:

1. **expediente://{id}** - Información completa del expediente
2. **expediente://{id}/documentos** - Lista de documentos
3. **expediente://{id}/documento/{doc_id}** - Documento específico
4. **expediente://{id}/historial** - Historial de acciones

## Herramientas MCP (Tools)

### Herramientas de Lectura

1. **consultar_expediente(expediente_id)**
   - Retorna toda la información del expediente
   - Requiere: permiso de consulta

2. **obtener_documento(expediente_id, documento_id)**
   - Retorna un documento específico
   - Requiere: permiso de consulta

3. **listar_documentos(expediente_id)**
   - Lista todos los documentos del expediente
   - Requiere: permiso de consulta

### Herramientas de Escritura

1. **añadir_documento(expediente_id, nombre, tipo, contenido)**
   - Añade un nuevo documento al expediente
   - Requiere: permiso de gestión
   - Registra en historial

2. **actualizar_datos(expediente_id, campo, valor)**
   - Actualiza un campo de datos del expediente
   - Requiere: permiso de gestión
   - Registra en historial

3. **añadir_anotacion(expediente_id, texto)**
   - Añade una anotación al historial
   - Requiere: permiso de gestión
   - Registra en historial

## Sistema de Permisos

### JWT Claims Requeridos

**Claims completos**:

```json
{
  "sub": "Automático",
  "iat": 1700000000,
  "exp": 1700003600,
  "nbf": 1700000000,
  "iss": "agentix-bpmn",
  "aud": ["agentix-mcp-expedientes", "agentix-mcp-normativa"],
  "jti": "uuid-v4-token-id",
  "exp_id": "EXP-2024-001",
  "exp_tipo": "SUBVENCIONES",
  "tarea_id": "TAREA-VALIDAR-DOC-001",
  "tarea_nombre": "VALIDAR_DOCUMENTACION",
  "permisos": ["consulta", "gestion"]
}
```

**Nota**: En este ejemplo, el token autoriza al agente a usar tanto el MCP de Expedientes como el de Normativa.

**Claims customizados**:
- `exp_id`: ID del expediente autorizado
- `exp_tipo`: Tipo de expediente (para validaciones adicionales)
- `tarea_id`: ID de la tarea BPMN actual
- `tarea_nombre`: Nombre legible de la tarea
- `permisos`: Array de permisos (`["consulta"]` o `["consulta", "gestion"]`)

**Claims estándar JWT**:
- `sub`: Usuario "Automático"
- `iat`: Timestamp de emisión
- `exp`: Timestamp de expiración (sugerido: 1 hora)
- `nbf`: Not Before timestamp
- `iss`: Emisor del token (BPMN engine)
- `aud`: Audiencia (puede ser un array para múltiples MCP servers)
- `jti`: ID único del token (para revocación)

**Nota sobre Multi-MCP**: En un entorno con múltiples servidores MCP, el claim `aud` puede ser un array que liste todos los MCP servers a los que el agente tiene acceso. Cada servidor MCP validará que su identificador está presente en el array.

### Validación

El servidor MCP de Expedientes debe validar:

1. **Firma JWT**: Token firmado correctamente con la clave secreta
2. **Expiración**: `exp` > tiempo actual
3. **Not Before**: `nbf` <= tiempo actual
4. **Audiencia**: `"agentix-mcp-expedientes"` está presente en el array `aud`
5. **Subject**: `sub` == "Automático"
6. **Expediente**: Recurso solicitado coincide con `exp_id`
7. **Permisos**: Operación requerida está en array `permisos`

**Ejemplo de validación de audiencia en Python**:

```python
def validate_audience(token_payload: dict, server_id: str = "agentix-mcp-expedientes") -> bool:
    """
    Valida que el servidor esté autorizado en el token.
    Soporta tanto string como array en el claim 'aud'.
    """
    aud = token_payload.get("aud")

    if isinstance(aud, str):
        return aud == server_id
    elif isinstance(aud, list):
        return server_id in aud
    else:
        return False
```

### Respuestas de Error

- **401**: Token inválido o expirado
- **403**: Permiso insuficiente
- **404**: Expediente o documento no encontrado
- **422**: Operación no válida en el estado actual

## Implementación del Protocolo MCP

### Librería Oficial

Usar el SDK oficial de Anthropic:

```bash
pip install mcp
```

Repositorio: https://github.com/modelcontextprotocol/python-sdk

### Versión del Protocolo

Implementar **MCP 1.0** (versión estable actual)

### Opciones de Transporte

El protocolo MCP soporta múltiples transportes. A continuación se analizan las alternativas disponibles:

#### Opción 1: stdio (Standard Input/Output)

**Cómo funciona**: El servidor se ejecuta como proceso hijo y comunica vía stdin/stdout usando JSON-RPC.

**Ventajas**:
- ✅ Implementación más simple
- ✅ Compatible nativamente con Claude Desktop
- ✅ No requiere gestión de puertos/red
- ✅ Aislamiento de procesos (cada sesión = 1 proceso)
- ✅ SDK de Python tiene soporte completo

**Desventajas**:
- ❌ Un proceso por sesión (no escala para múltiples clientes simultáneos)
- ❌ No accesible vía HTTP/REST (requiere lanzar el proceso)
- ❌ Difícil de probar manualmente (no puedes usar curl/Postman)
- ❌ Menos familiar para desarrolladores web

**Cuándo usar**:
- Tests unitarios y de integración
- Desarrollo con Claude Desktop
- Mocks de un solo usuario

#### Opción 2: SSE (Server-Sent Events) sobre HTTP

**Cómo funciona**: El servidor expone endpoints HTTP. El cliente hace POST para peticiones y recibe respuestas vía SSE.

**Ventajas**:
- ✅ Accesible vía HTTP (curl, Postman)
- ✅ Múltiples clientes simultáneos
- ✅ Compatible con el estándar MCP
- ✅ Familiar para desarrolladores web
- ✅ Fácil de desplegar (cualquier servidor web)

**Desventajas**:
- ❌ Más complejo de implementar
- ❌ Requiere gestión de puertos
- ❌ Soporte del SDK menos maduro que stdio

**Cuándo usar**:
- Producción con múltiples clientes
- Testing manual con herramientas HTTP
- Servicios desplegados en la nube

#### Comparativa de Transportes

| Característica | stdio | SSE/HTTP |
|---------------|-------|----------|
| **Compatibilidad MCP** | ✅ Total | ✅ Total |
| **Múltiples clientes** | ❌ No | ✅ Sí |
| **Testing manual** | ❌ Difícil | ✅ Fácil |
| **Complejidad impl.** | ✅ Baja | ⚠️ Media |
| **Claude Desktop** | ✅ Sí | ✅ Sí |
| **Familiaridad web** | ❌ Baja | ✅ Alta |

### Recomendación: Implementación Híbrida (stdio + HTTP/SSE)

**Para maximizar flexibilidad, implementar AMBOS transportes compartiendo la lógica core.**

#### Estructura del Proyecto

```
mcp-expedientes/
├── server.py           # Lógica core del servidor (agnóstica del transporte)
├── server_stdio.py     # Wrapper para transporte stdio
├── server_http.py      # Wrapper para transporte HTTP/SSE
├── auth.py             # Validación JWT
├── tools.py            # Implementación de tools
├── resources.py        # Implementación de resources
├── models.py           # Modelos de datos
└── data/
    └── expedientes/
```

#### Implementación: Servidor Core (server.py)

```python
"""
Servidor MCP core - Lógica agnóstica del transporte
"""
import os
from mcp.server import Server
from mcp import types

# Importar handlers
from auth import validate_jwt
from resources import list_resources, get_resource
from tools import list_tools, call_tool

def create_server(name: str = "gex-expedientes-mock") -> Server:
    """
    Crea el servidor MCP core que puede usarse con cualquier transporte.

    Esta función encapsula toda la lógica del servidor independientemente
    de cómo se comunique (stdio, HTTP, etc.)
    """
    app = Server(name)

    # Obtener token JWT del entorno (para stdio) o de contexto (para HTTP)
    def get_token() -> str:
        # Para stdio: variable de entorno
        token = os.environ.get("MCP_JWT_TOKEN")
        # Para HTTP: se pasará en el contexto de la petición
        # (implementación específica del transporte)
        return token

    @app.list_resources()
    async def handle_list_resources() -> list[types.Resource]:
        """Lista todos los resources disponibles"""
        token = get_token()
        await validate_jwt(token)
        return await list_resources()

    @app.read_resource()
    async def handle_read_resource(uri: str) -> str:
        """Lee un resource específico"""
        token = get_token()
        await validate_jwt(token, resource_uri=uri)
        return await get_resource(uri)

    @app.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """Lista todas las tools disponibles"""
        token = get_token()
        await validate_jwt(token)
        return await list_tools()

    @app.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        """Ejecuta una tool"""
        token = get_token()
        await validate_jwt(token, tool_name=name, tool_args=arguments)
        return await call_tool(name, arguments)

    return app
```

#### Implementación: Transporte stdio (server_stdio.py)

```python
"""
Servidor MCP con transporte stdio
Uso: python server_stdio.py
"""
import asyncio
from mcp.server.stdio import stdio_server
from server import create_server

async def main():
    """Ejecuta el servidor MCP con transporte stdio"""
    app = create_server()

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

**Configuración para Claude Desktop**:

```json
{
  "mcpServers": {
    "gex-expedientes": {
      "command": "python",
      "args": ["/path/to/mcp-expedientes/server_stdio.py"],
      "env": {
        "MCP_JWT_TOKEN": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "JWT_SECRET": "test-secret-key"
      }
    }
  }
}
```

#### Implementación: Transporte HTTP/SSE (server_http.py)

```python
"""
Servidor MCP con transporte HTTP/SSE
Uso: uvicorn server_http:app --reload --port 8000
"""
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse
from mcp.server.sse import sse_server
from server import create_server
import os

# Crear servidor MCP core
app_core = create_server()

async def handle_sse(request: Request):
    """
    Endpoint SSE para comunicación MCP.
    El token JWT se extrae de los headers.
    """
    # Extraer token del header Authorization
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        # Inyectar token en el entorno para que lo use el servidor core
        os.environ["MCP_JWT_TOKEN"] = token

    # Delegar al handler SSE del SDK
    return await sse_server(app_core)(request)

async def health_check(request: Request):
    """Endpoint de health check"""
    return JSONResponse({"status": "ok", "service": "gex-expedientes-mock"})

# Crear aplicación Starlette
app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["POST"]),
        Route("/health", endpoint=health_check, methods=["GET"])
    ]
)

# Para ejecutar:
# uvicorn server_http:app --reload --host 0.0.0.0 --port 8000
```

**Testing manual con curl**:

```bash
# Health check
curl http://localhost:8000/health

# Llamar a una tool
curl -X POST http://localhost:8000/sse \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "consultar_expediente",
      "arguments": {
        "expediente_id": "EXP-2024-001"
      }
    }
  }'
```

### Decisión para el Mock

**Implementar ambos transportes** (stdio + HTTP/SSE):

**stdio** para:
- ✅ Desarrollo con Claude Desktop
- ✅ Tests unitarios rápidos
- ✅ Integración con herramientas MCP estándar

**HTTP/SSE** para:
- ✅ Testing manual con curl/Postman
- ✅ Debugging más sencillo
- ✅ Demos y documentación
- ✅ Preparación para escalado futuro

**Lógica compartida** mediante `create_server()`:
- ✅ Sin duplicación de código
- ✅ Consistencia entre transportes
- ✅ Fácil añadir nuevos transportes

### Dependencias Actualizadas

```txt
# requirements.txt
mcp>=1.0.0              # SDK oficial MCP
pyjwt>=2.8.0            # Validación JWT
pytest>=7.4.0           # Testing
pytest-asyncio>=0.21.0  # Testing async

# Para transporte HTTP/SSE
starlette>=0.27.0       # Framework ASGI
uvicorn>=0.23.0         # Servidor ASGI
```

### Testing con MCP Inspector

El SDK proporciona una herramienta de inspección:

```bash
# Inspeccionar servidor stdio
npx @modelcontextprotocol/inspector python server_stdio.py

# Esto abre una UI web en http://localhost:5173 para interactuar con el servidor
```

### Ejemplo de Uso Completo

#### 1. Desarrollo local con stdio

```bash
# Terminal 1: Ejecutar servidor
export MCP_JWT_TOKEN="$(python generate_token.py --exp-id EXP-2024-001)"
export JWT_SECRET="test-secret-key"
python server_stdio.py
```

#### 2. Testing manual con HTTP

```bash
# Terminal 1: Ejecutar servidor HTTP
uvicorn server_http:app --reload --port 8000

# Terminal 2: Generar token
TOKEN=$(python generate_token.py --exp-id EXP-2024-001 --formato raw)

# Terminal 3: Probar endpoint
curl -X POST http://localhost:8000/sse \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

#### 3. Integración con Claude Desktop

Añadir a `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gex-expedientes": {
      "command": "python",
      "args": ["/Users/jose/wrk/github/aGEntiX/mcp-mock/mcp-expedientes/server_stdio.py"],
      "env": {
        "MCP_JWT_TOKEN": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "JWT_SECRET": "test-secret-key"
      }
    }
  }
}
```

## Generación de Tokens de Prueba

Crear un script `generate_token.py` con funcionalidad completa:

```python
import jwt
import uuid
from datetime import datetime, timedelta

def generate_test_token(
    exp_id: str,
    exp_tipo: str,
    tarea_id: str,
    tarea_nombre: str,
    permisos: list[str],
    mcp_servers: list[str] = None,
    secret: str = "test-secret-key",
    exp_hours: int = 1
) -> str:
    """
    Genera un JWT de prueba válido para testing.

    Args:
        exp_id: ID del expediente (ej: "EXP-2024-001")
        exp_tipo: Tipo de expediente (ej: "SUBVENCIONES")
        tarea_id: ID de la tarea BPMN
        tarea_nombre: Nombre de la tarea
        permisos: Lista de permisos (ej: ["consulta"] o ["consulta", "gestion"])
        mcp_servers: Lista de MCP servers autorizados (default: solo expedientes)
        secret: Clave secreta para firma (default: test-secret-key)
        exp_hours: Horas hasta expiración (default: 1)

    Returns:
        Token JWT firmado
    """
    if mcp_servers is None:
        mcp_servers = ["agentix-mcp-expedientes"]

    now = datetime.utcnow()
    payload = {
        "sub": "Automático",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=exp_hours)).timestamp()),
        "nbf": int(now.timestamp()),
        "iss": "agentix-bpmn",
        "aud": mcp_servers,
        "jti": str(uuid.uuid4()),
        "exp_id": exp_id,
        "exp_tipo": exp_tipo,
        "tarea_id": tarea_id,
        "tarea_nombre": tarea_nombre,
        "permisos": permisos
    }
    return jwt.encode(payload, secret, algorithm="HS256")
```

**Ejemplo de uso**:

```python
# Token solo para MCP de Expedientes
token_solo_exp = generate_test_token(
    exp_id="EXP-2024-001",
    exp_tipo="SUBVENCIONES",
    tarea_id="TAREA-VALIDAR-DOC-001",
    tarea_nombre="VALIDAR_DOCUMENTACION",
    permisos=["consulta", "gestion"]
)

# Token para múltiples MCP servers
token_multi = generate_test_token(
    exp_id="EXP-2024-001",
    exp_tipo="SUBVENCIONES",
    tarea_id="TAREA-GENERAR-RESOLUCION-001",
    tarea_nombre="GENERAR_RESOLUCION",
    permisos=["consulta", "gestion"],
    mcp_servers=["agentix-mcp-expedientes", "agentix-mcp-normativa", "agentix-mcp-documentos"]
)
```

## Simulación del Iniciador BPMN

Crear un script `simulate_bpmn.py` que simule la invocación desde el motor BPMN:

```python
"""
Simulador de invocación BPMN para testing del MCP Mock.

Este script simula el comportamiento del motor BPMN al invocar un agente:
1. Lee un expediente
2. Genera un JWT válido para la tarea
3. Configura el entorno para el MCP server
4. Invoca el MCP server (vía stdio)
5. Simula interacción del agente
6. Muestra resultados
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional
from generate_token import generate_test_token

class BPMNSimulator:
    def __init__(self, data_dir: Path, server_script: Path):
        self.data_dir = data_dir
        self.server_script = server_script

    def load_expediente(self, exp_id: str) -> dict:
        """Carga un expediente desde JSON"""
        exp_file = self.data_dir / "expedientes" / f"{exp_id}.json"
        with open(exp_file) as f:
            return json.load(f)

    def generate_context_token(self, expediente: dict, tarea: dict, permisos: list[str]) -> str:
        """Genera JWT para el contexto de la tarea"""
        return generate_test_token(
            exp_id=expediente["id"],
            exp_tipo=expediente["tipo"],
            tarea_id=tarea["id"],
            tarea_nombre=tarea["nombre"],
            permisos=permisos
        )

    def invoke_agent(self, token: str, task_prompt: str) -> dict:
        """
        Invoca el MCP server simulando un agente.

        En un sistema real, aquí iríamos al endpoint del agente.
        Para el mock, invocamos directamente el MCP server.
        """
        env = os.environ.copy()
        env["MCP_JWT_TOKEN"] = token
        env["JWT_SECRET"] = "test-secret-key"

        # Por ahora, solo iniciamos el servidor
        # TODO: Implementar cliente MCP que interactúe
        print(f"[BPMN] Iniciando MCP server con token para tarea...")
        print(f"[BPMN] Token (primeros 50 chars): {token[:50]}...")

        # Aquí iría la lógica de invocar al agente real
        # que a su vez invocaría al MCP server

        return {
            "status": "simulated",
            "message": "En implementación real, aquí se invocaría al agente"
        }

    def simulate_task(
        self,
        exp_id: str,
        tarea_id: str,
        permisos: list[str],
        task_prompt: str
    ):
        """
        Simula la ejecución de una tarea BPMN.

        Args:
            exp_id: ID del expediente
            tarea_id: ID de la tarea a ejecutar
            permisos: Lista de permisos para el agente
            task_prompt: Prompt específico de la tarea
        """
        print(f"\n{'='*60}")
        print(f"SIMULACIÓN BPMN - Inicio de Tarea")
        print(f"{'='*60}\n")

        # 1. Cargar expediente
        print(f"[BPMN] Cargando expediente {exp_id}...")
        expediente = self.load_expediente(exp_id)
        print(f"[BPMN] Expediente cargado: {expediente['tipo']} - {expediente['estado']}")

        # 2. Obtener información de la tarea
        tarea = expediente["metadatos"]["tarea_actual"]
        if tarea["id"] != tarea_id:
            print(f"[ERROR] La tarea actual no coincide: esperado {tarea_id}, actual {tarea['id']}")
            return

        print(f"[BPMN] Tarea actual: {tarea['nombre']}")
        print(f"[BPMN] Responsable: {tarea['responsable']}")

        # 3. Generar token JWT
        print(f"\n[BPMN] Generando token JWT...")
        token = self.generate_context_token(expediente, tarea, permisos)
        print(f"[BPMN] Token generado con permisos: {permisos}")

        # 4. Invocar agente
        print(f"\n[BPMN] Invocando agente...")
        print(f"[BPMN] Prompt de tarea: {task_prompt[:100]}...")

        result = self.invoke_agent(token, task_prompt)

        # 5. Mostrar resultado
        print(f"\n{'='*60}")
        print(f"RESULTADO")
        print(f"{'='*60}")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print()

def main():
    # Configuración
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data"
    server_script = base_dir / "server.py"

    simulator = BPMNSimulator(data_dir, server_script)

    # Ejemplo: Simular tarea de validación de documentación
    simulator.simulate_task(
        exp_id="EXP-2024-001",
        tarea_id="TAREA-VALIDAR-DOC-001",
        permisos=["consulta", "gestion"],
        task_prompt="""
        Valida la documentación del expediente de subvenciones.

        Verifica que estén presentes:
        - Solicitud firmada
        - DNI del solicitante
        - Justificante bancario

        Actualiza el campo 'documentacion_valida' según el resultado.
        """
    )

if __name__ == "__main__":
    main()
```

## Datos de Prueba

Crear al menos 3 expedientes de ejemplo:

1. **EXP-2024-001**: Expediente de subvenciones (estado: en trámite)
2. **EXP-2024-002**: Expediente de licencia (estado: pendiente documentación)
3. **EXP-2024-003**: Expediente completado (estado: archivado)

Cada uno con:
- Datos completos (según el modelo enriquecido con metadatos BPMN)
- Al menos 3 documentos
- Historial de acciones con tipos (SISTEMA, AGENTE, HUMANO)
- Diferentes tipos de datos para probar extracción
- Metadatos completos de flujo BPMN y tareas

## Suite de Tests Funcionales

### Organización de Tests

```
tests/
├── test_auth.py              # Tests de autenticación/autorización
├── test_resources.py         # Tests de resources MCP
├── test_tools_read.py        # Tests de tools de lectura
├── test_tools_write.py       # Tests de tools de escritura
├── test_permissions.py       # Tests de validación de permisos
├── test_data_persistence.py  # Tests de persistencia
└── fixtures/
    ├── tokens.py             # Fixtures de tokens JWT
    └── expedientes.py        # Fixtures de expedientes
```

### Test Cases Obligatorios

#### TC-AUTH-001: Token Válido con Permisos Consulta

```python
def test_valid_token_consulta():
    """
    Given: Un token JWT válido con permisos de consulta para EXP-2024-001
    When: Se invoca la tool consultar_expediente("EXP-2024-001")
    Then: Se retorna el expediente completo sin error
    """
```

#### TC-AUTH-002: Token Válido con Permisos Gestión

```python
def test_valid_token_gestion():
    """
    Given: Un token JWT válido con permisos de gestión para EXP-2024-001
    When: Se invoca la tool añadir_documento(...)
    Then: El documento se añade y se retorna success=true
    """
```

#### TC-AUTH-003: Token Expirado

```python
def test_expired_token():
    """
    Given: Un token JWT expirado (exp < now)
    When: Se invoca cualquier tool
    Then: Se retorna error 401 "Token expirado"
    """
```

#### TC-AUTH-004: Token con Firma Inválida

```python
def test_invalid_signature():
    """
    Given: Un token JWT con firma incorrecta
    When: Se invoca cualquier tool
    Then: Se retorna error 401 "Firma inválida"
    """
```

#### TC-AUTH-005: Acceso a Expediente No Autorizado

```python
def test_unauthorized_expediente():
    """
    Given: Un token JWT válido para EXP-2024-001
    When: Se invoca consultar_expediente("EXP-2024-002")
    Then: Se retorna error 403 "Acceso no autorizado al expediente"
    """
```

#### TC-AUTH-006: Usuario No Automático

```python
def test_invalid_user():
    """
    Given: Un token JWT con sub="Usuario Humano"
    When: Se invoca cualquier tool
    Then: Se retorna error 403 "Usuario no autorizado"
    """
```

#### TC-PERM-001: Escritura sin Permiso Gestión

```python
def test_write_without_gestion():
    """
    Given: Un token JWT válido con solo permisos=["consulta"]
    When: Se invoca añadir_documento(...)
    Then: Se retorna error 403 "Permiso insuficiente: se requiere gestión"
    """
```

#### TC-PERM-002: Lectura con Solo Permiso Consulta

```python
def test_read_with_consulta():
    """
    Given: Un token JWT válido con permisos=["consulta"]
    When: Se invoca consultar_expediente(...)
    Then: Se retorna el expediente correctamente
    """
```

#### TC-RES-001: Resource Expediente Completo

```python
def test_resource_expediente():
    """
    Given: Un token JWT válido
    When: Se lee el resource "expediente://EXP-2024-001"
    Then: Se retorna el JSON completo del expediente
    """
```

#### TC-RES-002: Resource Documentos

```python
def test_resource_documentos():
    """
    Given: Un token JWT válido
    When: Se lee el resource "expediente://EXP-2024-001/documentos"
    Then: Se retorna un array con todos los documentos
    """
```

#### TC-RES-003: Resource Historial

```python
def test_resource_historial():
    """
    Given: Un token JWT válido
    When: Se lee el resource "expediente://EXP-2024-001/historial"
    Then: Se retorna un array con el historial de acciones
    """
```

#### TC-TOOL-001: Consultar Expediente

```python
def test_tool_consultar_expediente():
    """
    Given: Un token JWT válido con permisos de consulta
    When: Se ejecuta consultar_expediente("EXP-2024-001")
    Then: Se retorna el expediente con todos sus campos
    """
```

#### TC-TOOL-002: Listar Documentos

```python
def test_tool_listar_documentos():
    """
    Given: Un token JWT válido con permisos de consulta
    When: Se ejecuta listar_documentos("EXP-2024-001")
    Then: Se retorna lista de 3 documentos con metadata
    """
```

#### TC-TOOL-003: Obtener Documento Específico

```python
def test_tool_obtener_documento():
    """
    Given: Un token JWT válido con permisos de consulta
    When: Se ejecuta obtener_documento("EXP-2024-001", "DOC-001")
    Then: Se retorna la metadata del documento DOC-001
    """
```

#### TC-TOOL-004: Obtener Documento Inexistente

```python
def test_tool_obtener_documento_not_found():
    """
    Given: Un token JWT válido
    When: Se ejecuta obtener_documento("EXP-2024-001", "DOC-999")
    Then: Se retorna error 404 "Documento no encontrado"
    """
```

#### TC-TOOL-005: Añadir Documento

```python
def test_tool_añadir_documento():
    """
    Given: Un token JWT válido con permisos de gestión
    When: Se ejecuta añadir_documento(exp_id, nombre, tipo, contenido)
    Then:
      - Se crea nuevo documento con ID único
      - Se añade al array de documentos
      - Se registra en historial
      - Se retorna success=true con documento_id
    """
```

#### TC-TOOL-006: Actualizar Datos

```python
def test_tool_actualizar_datos():
    """
    Given: Un token JWT válido con permisos de gestión
    When: Se ejecuta actualizar_datos("EXP-2024-001", "datos.documentacion_valida", true)
    Then:
      - El campo se actualiza en el expediente
      - Se registra en historial
      - Se retorna success=true con valor_anterior
    """
```

#### TC-TOOL-007: Añadir Anotación

```python
def test_tool_añadir_anotacion():
    """
    Given: Un token JWT válido con permisos de gestión
    When: Se ejecuta añadir_anotacion("EXP-2024-001", "Documentación verificada correctamente")
    Then:
      - Se añade entrada al historial
      - Tipo = "ANOTACION"
      - Usuario = "Automático"
      - Se retorna success=true
    """
```

#### TC-PERSIST-001: Cambios Persisten Entre Invocaciones

```python
def test_persistence():
    """
    Given: Un expediente EXP-2024-001 en estado inicial
    When:
      1. Se añade un documento
      2. Se reinicia el servidor
      3. Se consulta el expediente
    Then: El documento añadido está presente
    """
```

#### TC-PERSIST-002: Historial Completo

```python
def test_historial_registro():
    """
    Given: Un expediente EXP-2024-001
    When: Se ejecutan en orden:
      1. añadir_documento(...)
      2. actualizar_datos(...)
      3. añadir_anotacion(...)
    Then: El historial contiene 3 nuevas entradas en orden cronológico
    """
```

### Tests de Integración

Incluir al menos un test que ejecute el flujo completo:

```python
def test_flujo_completo_validacion():
    """
    Test de integración: Flujo completo de validación de documentación

    Simula:
    1. BPMN genera token para tarea VALIDAR_DOCUMENTACION
    2. Agente consulta expediente
    3. Agente lista documentos
    4. Agente obtiene cada documento
    5. Agente actualiza campo documentacion_valida
    6. Agente añade anotación con resultado
    7. Verificar historial completo
    """
```

## Criterios de Aceptación

El MCP mock debe:

- [ ] Implementar la especificación MCP correctamente
- [ ] Soportar transportes stdio y HTTP/SSE
- [ ] Validar tokens JWT en cada petición (con claims completos)
- [ ] Exponer todos los resources definidos
- [ ] Implementar todas las tools (lectura y escritura)
- [ ] Rechazar accesos a expedientes no autorizados
- [ ] Validar audiencia en tokens para soporte multi-MCP
- [ ] Registrar todas las acciones en el historial
- [ ] Incluir tests funcionales completos
- [ ] Proporcionar documentación de uso
- [ ] Incluir script de generación de tokens
- [ ] Incluir script de simulación BPMN
- [ ] Mantener persistencia en JSON entre reinicios
- [ ] Soportar modelo de datos enriquecido con contexto BPMN

## Referencias

- [Especificación MCP](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Acceso vía MCP](../doc/042-acceso-mcp.md)
- [Permisos de agente](../doc/050-permisos-agente.md)
- [Propagación de permisos](../doc/052-propagacion-permisos.md)
- [Contexto del agente](../doc/032-contexto-agente.md)
