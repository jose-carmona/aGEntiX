#!/bin/bash
# Script para lanzar Flower (UI de monitoreo de Celery)

# Configurar PYTHONPATH para imports desde src/
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH="${SCRIPT_DIR}/src:${PYTHONPATH}"

# Cargar variables de entorno
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Valores por defecto
FLOWER_PORT=${FLOWER_PORT:-5555}
FLOWER_USER=${FLOWER_USER:-admin}
FLOWER_PASSWORD=${FLOWER_PASSWORD:-admin}

echo "=========================================="
echo "🌸 Iniciando Flower (Celery Monitor)"
echo "=========================================="
echo "Port:   $FLOWER_PORT"
echo "User:   $FLOWER_USER"
echo "URL:    http://localhost:$FLOWER_PORT"
echo "Broker: ${CELERY_BROKER_URL:-redis://localhost:6379/0}"
echo "=========================================="
echo ""

# Verificar conexión a Redis
if command -v redis-cli &> /dev/null; then
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis disponible"
    else
        echo "❌ Redis no responde. ¿Está corriendo?"
        echo "   Ejecuta: redis-server --daemonize yes"
        exit 1
    fi
else
    echo "⚠️  redis-cli no disponible, continuando..."
fi

echo ""
echo "Iniciando Flower..."
echo ""

celery -A backoffice.celery_app flower \
    --port=${FLOWER_PORT} \
    --basic_auth=${FLOWER_USER}:${FLOWER_PASSWORD}
