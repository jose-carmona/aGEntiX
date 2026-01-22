#!/bin/bash
# Script para lanzar el worker Celery de aGEntiX

# Configurar PYTHONPATH para imports desde src/
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH="${SCRIPT_DIR}/src:${PYTHONPATH}"

# Cargar variables de entorno
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Valores por defecto
CELERY_CONCURRENCY=${CELERY_CONCURRENCY:-2}
CELERY_LOGLEVEL=${CELERY_LOGLEVEL:-info}

echo "=========================================="
echo "🔄 Iniciando Celery Worker"
echo "=========================================="
echo "Concurrency: $CELERY_CONCURRENCY"
echo "Log Level:   $CELERY_LOGLEVEL"
echo "Broker:      ${CELERY_BROKER_URL:-redis://localhost:6379/0}"
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
echo "Iniciando worker..."
echo ""

celery -A backoffice.celery_app worker \
    --loglevel=${CELERY_LOGLEVEL} \
    --concurrency=${CELERY_CONCURRENCY}
