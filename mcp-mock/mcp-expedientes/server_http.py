"""
Servidor MCP con transporte HTTP/SSE.

Este módulo implementa el transporte HTTP/SSE para el servidor MCP.
Usa Starlette como framework web y expone endpoints REST.

Uso:
    export JWT_SECRET="test-secret-key"
    uvicorn server_http:app --reload --host 0.0.0.0 --port 8000

Testing manual con curl:
    # Health check
    curl http://localhost:8000/health

    # Generar token
    TOKEN=$(python generate_token.py --exp-id EXP-2024-001 --formato raw)

    # Listar tools
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
"""

import logging
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from mcp.server.sse import SseServerTransport
from server import create_server, get_server_info

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

    El token JWT se extrae del header Authorization.
    El servidor procesa peticiones JSON-RPC y retorna respuestas vía SSE.

    Args:
        request: Petición HTTP

    Returns:
        Respuesta SSE
    """
    # Extraer token del header Authorization
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        context.set_token(token)
        logger.info(f"Token JWT recibido (primeros 20 chars): {token[:20]}...")
    else:
        logger.warning("No se recibió token JWT en el header Authorization")

    # Crear transporte SSE
    sse = SseServerTransport("/messages")

    # Conectar y ejecutar
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


# Crear aplicación Starlette
app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET", "POST"]),
        Route("/health", endpoint=health_check, methods=["GET"]),
        Route("/info", endpoint=server_info_endpoint, methods=["GET"])
    ]
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
