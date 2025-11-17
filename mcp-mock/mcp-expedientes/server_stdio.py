#!/usr/bin/env python3
"""
Servidor MCP con transporte stdio.

Este módulo implementa el transporte stdio para el servidor MCP.
Se comunica mediante stdin/stdout usando JSON-RPC.

Uso:
    export MCP_JWT_TOKEN="<token>"
    export JWT_SECRET="test-secret-key"
    python server_stdio.py

Configuración para Claude Desktop:
    {
      "mcpServers": {
        "gex-expedientes": {
          "command": "python",
          "args": ["/ruta/a/server_stdio.py"],
          "env": {
            "MCP_JWT_TOKEN": "eyJhbGc...",
            "JWT_SECRET": "test-secret-key"
          }
        }
      }
    }
"""

import asyncio
import logging
import sys
from mcp.server.stdio import stdio_server
from server import create_server, get_server_info

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # Log a stderr para no interferir con stdio
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """
    Ejecuta el servidor MCP con transporte stdio.

    Lee peticiones JSON-RPC desde stdin y escribe respuestas a stdout.
    El token JWT se obtiene de la variable de entorno MCP_JWT_TOKEN.
    """
    logger.info("=" * 60)
    logger.info("MCP Mock de Expedientes - Transporte stdio")
    logger.info("=" * 60)

    # Crear servidor
    app, context = create_server()
    info = get_server_info()

    logger.info(f"Servidor: {info['name']} v{info['version']}")
    logger.info(f"Protocolo MCP: {info['protocol_version']}")
    logger.info(f"Capabilities: {info['capabilities']}")
    logger.info("Esperando peticiones en stdin...")

    # Ejecutar servidor stdio
    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    except KeyboardInterrupt:
        logger.info("Servidor detenido por usuario")
    except Exception as e:
        logger.error(f"Error fatal en servidor: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Servidor terminado")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}")
        sys.exit(1)
