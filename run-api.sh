#!/bin/bash
# Script para lanzar la API de aGEntiX

# Configurar PYTHONPATH para imports desde src/
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH="${SCRIPT_DIR}/src:${PYTHONPATH}"

# Cargar variables de entorno
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Valores por defecto
API_HOST=${API_HOST:-0.0.0.0}
API_PORT=${API_PORT:-8080}
API_WORKERS=${API_WORKERS:-4}
API_RELOAD=${API_RELOAD:-false}

echo "=========================================="
echo "🚀 Iniciando aGEntiX API"
echo "=========================================="
echo "Host:    $API_HOST"
echo "Port:    $API_PORT"
echo "Workers: $API_WORKERS"
echo "Reload:  $API_RELOAD"
echo "=========================================="
echo ""

if [ "$API_RELOAD" = "true" ]; then
    # Modo desarrollo (con auto-reload)
    echo "Modo: DESARROLLO (auto-reload activado)"
    uvicorn api.main:app --host $API_HOST --port $API_PORT --reload
else
    # Modo producción (con múltiples workers)
    echo "Modo: PRODUCCIÓN ($API_WORKERS workers)"
    uvicorn api.main:app --host $API_HOST --port $API_PORT --workers $API_WORKERS
fi
