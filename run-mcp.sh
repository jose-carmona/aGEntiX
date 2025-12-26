#!/bin/bash
# Script para lanzar el servidor MCP Mock de aGEntiX

# Configurar PYTHONPATH para imports desde src/
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH="${SCRIPT_DIR}/src:${PYTHONPATH}"

# Cargar variables de entorno
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Valores por defecto
MCP_HOST=${MCP_HOST:-0.0.0.0}
MCP_PORT=${MCP_PORT:-8000}
MCP_RELOAD=${MCP_RELOAD:-true}

echo "=========================================="
echo "🔌 Iniciando MCP Mock Server (Expedientes)"
echo "=========================================="
echo "Host:   $MCP_HOST"
echo "Port:   $MCP_PORT"
echo "Reload: $MCP_RELOAD"
echo "=========================================="
echo ""

cd "${SCRIPT_DIR}/src/mcp_mock/mcp_expedientes"

if [ "$MCP_RELOAD" = "true" ]; then
    echo "Modo: DESARROLLO (auto-reload activado)"
    uvicorn server_http:app --host $MCP_HOST --port $MCP_PORT --reload
else
    echo "Modo: PRODUCCIÓN"
    uvicorn server_http:app --host $MCP_HOST --port $MCP_PORT
fi
