"""
Servidor MCP con transporte HTTP/SSE.

Este módulo implementa el transporte HTTP/SSE para el servidor MCP.
Usa Starlette como framework web y expone endpoints REST.

IMPORTANTE: El servidor valida el token JWT INMEDIATAMENTE al recibir
la request, antes de procesar cualquier operación MCP (fail-fast).

Uso:
    export JWT_SECRET="test-secret-key"
    uvicorn server_http:app --reload --host 0.0.0.0 --port 8000

Testing manual con curl:
    # Health check
    curl http://localhost:8000/health

    # Generar token
    TOKEN=$(python generate_token.py --exp-id EXP-2024-001 --formato raw)

    # Listar tools (con token válido)
    curl -X POST http://localhost:8000/sse \\
      -H "Authorization: Bearer $TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

    # Ejecutar tool
    curl -X POST http://localhost:8000/sse \\
      -H "Authorization: Bearer $TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
          "name": "consultar_expediente",
          "arguments": {"expediente_id": "EXP-2024-001"}
        }
      }'

    # Ejemplo de error 401 (sin token)
    curl -X POST http://localhost:8000/sse \\
      -H "Content-Type: application/json" \\
      -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
    # Respuesta: HTTP 401 {"error": "AUTH_INVALID_TOKEN", "message": "Se requiere token JWT..."}

    # Ejemplo de error 401 (token expirado)
    TOKEN_EXPIRADO=$(python generate_token.py --exp-id EXP-2024-001 --expired)
    curl -X POST http://localhost:8000/sse \\
      -H "Authorization: Bearer $TOKEN_EXPIRADO" \\
      -H "Content-Type: application/json" \\
      -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
    # Respuesta: HTTP 401 {"error": "AUTH_INVALID_TOKEN", "message": "Token expirado"}

    # Ejemplo de error 401 (token con firma inválida)
    curl -X POST http://localhost:8000/sse \\
      -H "Authorization: Bearer token-falso" \\
      -H "Content-Type: application/json" \\
      -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
    # Respuesta: HTTP 401 {"error": "AUTH_INVALID_TOKEN", "message": "Firma inválida"}
"""

import os
import logging
import json
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from mcp.server.sse import SseServerTransport
from .server import create_server, get_server_info
from .auth import validate_jwt, AuthError
from ..models import JWTClaims
from .tools import list_tools as list_exp_tools, call_tool as call_exp_tool
from .resources import list_resources as list_exp_resources, get_resource as get_exp_resource

# Importar módulo de documentación
from ..mcp_documentacion import (
    list_tools as list_doc_tools,
    call_tool as call_doc_tool,
    list_resources as list_doc_resources,
    get_resource as get_doc_resource,
)
from ..mcp_documentacion.tools import TOOL_NAMES as DOC_TOOL_NAMES
from ..mcp_documentacion.data_loader import DocumentacionError

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Logger específico para auditoría de llamadas a tools
tool_audit_logger = logging.getLogger("mcp.tool_audit")


def log_tool_call(
    tool_name: str,
    tool_args: dict,
    claims: "JWTClaims",
    request_id: any = None
) -> None:
    """
    Loguea una llamada a tool con información estructurada.

    Args:
        tool_name: Nombre de la tool invocada
        tool_args: Parámetros de la llamada
        claims: Claims del JWT validado
        request_id: ID de la request JSON-RPC
    """
    log_entry = {
        "event": "TOOL_CALL",
        "request_id": request_id,
        "tool": tool_name,
        "arguments": tool_args,
        "jwt_claims": {
            "sub": claims.sub,
            "iss": claims.iss,
            "aud": claims.aud,
            "exp_id": claims.exp_id,
            "exp_tipo": claims.exp_tipo,
            "tarea_id": claims.tarea_id,
            "tarea_nombre": claims.tarea_nombre,
            "permisos": claims.permisos,
            "jti": claims.jti,
        }
    }
    tool_audit_logger.info(f"🔧 Tool Call: {json.dumps(log_entry, ensure_ascii=False, default=str)}")

# Crear servidor MCP core
app_core, context = create_server()
info = get_server_info()

logger.info("=" * 60)
logger.info("MCP Mock Unificado - Expedientes + Documentación")
logger.info("=" * 60)
logger.info(f"Servidor: {info['name']} v{info['version']}")
logger.info(f"Protocolo MCP: {info['protocol_version']}")


# ========== FUNCIONES COMBINADAS PARA MÓDULOS ==========

async def list_all_tools():
    """Combina tools de todos los módulos."""
    exp_tools = await list_exp_tools()
    doc_tools = await list_doc_tools()
    return exp_tools + doc_tools


async def list_all_resources():
    """Combina resources de todos los módulos."""
    exp_resources = await list_exp_resources()
    doc_resources = await list_doc_resources()
    return exp_resources + doc_resources


async def call_tool(name: str, arguments: dict):
    """Dispatch al módulo correcto según el nombre de la tool."""
    if name in DOC_TOOL_NAMES:
        return await call_doc_tool(name, arguments)
    # Default: tools de expedientes
    return await call_exp_tool(name, arguments)


async def get_resource(uri: str):
    """Dispatch al módulo correcto según el esquema de la URI."""
    if uri.startswith("documentacion://"):
        return await get_doc_resource(uri)
    # Default: resources de expedientes
    return await get_exp_resource(uri)


async def handle_sse(request: Request) -> Response:
    """
    Endpoint SSE para comunicación MCP.

    El token JWT se extrae del header Authorization y se valida
    INMEDIATAMENTE antes de procesar cualquier request MCP.

    Args:
        request: Petición HTTP

    Returns:
        Respuesta SSE o error 401/403

    Raises:
        HTTPException: Si el token es inválido o no está presente
    """
    # 1. Extraer token del header Authorization
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        logger.warning("Request sin token JWT en header Authorization")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "AUTH_INVALID_TOKEN",
                "message": "Se requiere token JWT en header Authorization: Bearer <token>"
            }
        )

    token = auth_header[7:]  # Extraer token (quitar "Bearer ")

    # 2. VALIDAR TOKEN INMEDIATAMENTE (CAMBIO PRINCIPAL)
    try:
        # Validación básica del token (firma, expiración, claims obligatorios)
        # No validamos expediente_id ni tool específica aquí, eso se hace en cada handler
        await validate_jwt(token, server_id=context.server_id)

        logger.info(f"✅ Token JWT válido recibido (primeros 20 chars): {token[:20]}...")

    except AuthError as e:
        logger.warning(f"❌ Token JWT inválido: {e.message}")
        raise HTTPException(
            status_code=e.status_code,  # 401 o 403 según el error
            detail={
                "error": "AUTH_INVALID_TOKEN" if e.status_code == 401 else "AUTH_PERMISSION_DENIED",
                "message": e.message
            }
        )
    except Exception as e:
        logger.error(f"Error inesperado al validar token: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "Error interno al validar token JWT"
            }
        )

    # 3. Almacenar token en contexto (solo si es válido)
    context.set_token(token)

    # 4. Procesar request MCP (solo si token es válido)
    sse = SseServerTransport("/messages")

    async with sse.connect_sse(
        request.scope,
        request.receive,
        request._send
    ) as streams:
        await app_core.run(
            streams[0],
            streams[1],
            app_core.create_initialization_options()
        )

    return Response()


async def handle_rpc(request: Request) -> JSONResponse:
    """
    Endpoint HTTP simple para JSON-RPC (sin SSE).

    Este endpoint permite comunicación request-response directa,
    sin necesidad de establecer una conexión SSE.

    Métodos soportados:
    - tools/list: Lista las tools disponibles
    - tools/call: Ejecuta una tool
    - resources/list: Lista los resources disponibles
    - resources/read: Lee un resource

    Args:
        request: Petición HTTP con body JSON-RPC

    Returns:
        Respuesta JSON-RPC
    """
    # 1. Extraer y validar token JWT
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        logger.warning("Request /rpc sin token JWT")
        return JSONResponse(
            status_code=401,
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32001,
                    "message": "Se requiere token JWT en header Authorization: Bearer <token>"
                }
            }
        )

    token = auth_header[7:]

    try:
        await validate_jwt(token, server_id=context.server_id)
        logger.info(f"✅ Token JWT válido en /rpc (primeros 20 chars): {token[:20]}...")
    except AuthError as e:
        logger.warning(f"❌ Token JWT inválido en /rpc: {e.message}")
        return JSONResponse(
            status_code=e.status_code,
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32001,
                    "message": e.message
                }
            }
        )

    # 2. Parsear body JSON-RPC
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Error parseando JSON: {e}")
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error: JSON inválido"
                }
            }
        )

    # Validar estructura JSON-RPC
    if not isinstance(body, dict):
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: se esperaba objeto JSON"
                }
            }
        )

    request_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {})

    logger.info(f"📥 RPC Request: method={method}, id={request_id}")

    # 3. Almacenar token en contexto para las operaciones
    context.set_token(token)

    # 4. Ejecutar método
    try:
        if method == "tools/list":
            tools = await list_all_tools()
            result = {
                "tools": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "inputSchema": t.inputSchema
                    }
                    for t in tools
                ]
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            if not tool_name:
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": "Invalid params: falta 'name' de la tool"
                        }
                    }
                )

            # Validar permisos para la tool específica
            claims = await validate_jwt(
                token,
                tool_name=tool_name,
                tool_args=tool_args,
                server_id=context.server_id
            )

            # Loguear la llamada con tool, parámetros y claims JWT
            log_tool_call(tool_name, tool_args, claims, request_id)

            tool_result = await call_tool(tool_name, tool_args)
            result = {
                "content": [
                    {"type": item.type, "text": item.text}
                    for item in tool_result
                ]
            }

        elif method == "resources/list":
            resources = await list_all_resources()
            result = {
                "resources": [
                    {
                        "uri": str(r.uri),
                        "name": r.name,
                        "description": r.description,
                        "mimeType": r.mimeType
                    }
                    for r in resources
                ]
            }

        elif method == "resources/read":
            uri = params.get("uri")

            if not uri:
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": "Invalid params: falta 'uri' del resource"
                        }
                    }
                )

            # Validar permisos para el resource
            await validate_jwt(
                token,
                resource_uri=uri,
                server_id=context.server_id
            )

            content = await get_resource(uri)
            result = {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": content
                    }
                ]
            }

        else:
            logger.warning(f"Método no soportado: {method}")
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            )

        logger.info(f"📤 RPC Response: method={method}, success=true")

        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        })

    except AuthError as e:
        logger.warning(f"❌ Error de autorización en {method}: {e.message}")
        return JSONResponse(
            status_code=e.status_code,
            content={
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32001,
                    "message": e.message
                }
            }
        )

    except DocumentacionError as e:
        logger.warning(f"❌ Error de documentación en {method}: {e.message}")
        return JSONResponse(
            status_code=e.status_code,
            content={
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32002,
                    "message": e.message
                }
            }
        )

    except Exception as e:
        logger.error(f"❌ Error interno en {method}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
        )


async def health_check(request: Request) -> JSONResponse:
    """
    Endpoint de health check.

    Retorna información básica sobre el estado del servidor.

    Returns:
        JSON con información del servidor
    """
    return JSONResponse({
        "status": "ok",
        "service": info["name"],
        "version": info["version"],
        "protocol": info["protocol_version"],
        "capabilities": info["capabilities"]
    })


async def server_info_endpoint(request: Request) -> JSONResponse:
    """
    Endpoint con información detallada del servidor.

    Returns:
        JSON con información completa del servidor
    """
    return JSONResponse(info)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handler para convertir HTTPException en respuesta JSON.

    Args:
        request: Request HTTP
        exc: Excepción HTTP

    Returns:
        Respuesta JSON con el error
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )


# Crear aplicación Starlette
app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET", "POST"]),
        Route("/rpc", endpoint=handle_rpc, methods=["POST"]),
        Route("/health", endpoint=health_check, methods=["GET"]),
        Route("/info", endpoint=server_info_endpoint, methods=["GET"])
    ],
    exception_handlers={
        HTTPException: http_exception_handler
    }
)

# Configurar CORS para permitir acceso desde el frontend
# Los orígenes se pueden configurar via variable de entorno MCP_CORS_ORIGINS
cors_origins = os.environ.get(
    "MCP_CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.on_event("startup")
async def startup():
    """Handler de inicio del servidor"""
    logger.info("Servidor HTTP/SSE iniciado")
    logger.info("Endpoints disponibles:")
    logger.info("  GET  /health  - Health check")
    logger.info("  GET  /info    - Información del servidor")
    logger.info("  POST /sse     - Endpoint MCP SSE (requiere token JWT)")
    logger.info("  POST /rpc     - Endpoint MCP HTTP simple (requiere token JWT)")
    logger.info(f"CORS habilitado para: {cors_origins}")


@app.on_event("shutdown")
async def shutdown():
    """Handler de cierre del servidor"""
    logger.info("Servidor HTTP/SSE detenido")


# Punto de entrada para uvicorn
# uvicorn server_http:app --reload --host 0.0.0.0 --port 8000
