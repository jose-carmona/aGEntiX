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

import logging
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.exceptions import HTTPException
from mcp.server.sse import SseServerTransport
from .server import create_server, get_server_info
from .auth import validate_jwt, AuthError

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear servidor MCP core
app_core, context = create_server()
info = get_server_info()

logger.info("=" * 60)
logger.info("MCP Mock de Expedientes - Transporte HTTP/SSE")
logger.info("=" * 60)
logger.info(f"Servidor: {info['name']} v{info['version']}")
logger.info(f"Protocolo MCP: {info['protocol_version']}")


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
        Route("/health", endpoint=health_check, methods=["GET"]),
        Route("/info", endpoint=server_info_endpoint, methods=["GET"])
    ],
    exception_handlers={
        HTTPException: http_exception_handler
    }
)


@app.on_event("startup")
async def startup():
    """Handler de inicio del servidor"""
    logger.info("Servidor HTTP/SSE iniciado")
    logger.info("Endpoints disponibles:")
    logger.info("  GET  /health  - Health check")
    logger.info("  GET  /info    - Información del servidor")
    logger.info("  POST /sse     - Endpoint MCP (requiere token JWT)")


@app.on_event("shutdown")
async def shutdown():
    """Handler de cierre del servidor"""
    logger.info("Servidor HTTP/SSE detenido")


# Punto de entrada para uvicorn
# uvicorn server_http:app --reload --host 0.0.0.0 --port 8000
