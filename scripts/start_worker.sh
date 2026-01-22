#!/bin/bash
# ==============================================================================
# start_worker.sh - Inicia un worker de Celery
#
# Uso:
#   ./scripts/start_worker.sh
#
# Variables de entorno opcionales:
#   CELERY_CONCURRENCY  - Número de procesos concurrentes (default: 4)
#   CELERY_LOGLEVEL     - Nivel de log (default: info)
#   CELERY_MAX_TASKS    - Máximo de tareas por worker hijo (default: 100)
#
# ==============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Iniciando Celery Worker...${NC}"

# Verificar que estamos en el directorio correcto
if [ ! -f "src/backoffice/celery_app.py" ]; then
    echo -e "${RED}❌ Error: Ejecutar desde el directorio raíz del proyecto${NC}"
    exit 1
fi

# Verificar conexión a Redis
echo -e "${YELLOW}🔍 Verificando conexión a Redis...${NC}"
if command -v redis-cli &> /dev/null; then
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis disponible${NC}"
    else
        echo -e "${RED}❌ Redis no responde. ¿Está corriendo?${NC}"
        echo -e "${YELLOW}   Intenta: redis-server --daemonize yes${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  redis-cli no disponible, continuando...${NC}"
fi

# Configuración
CONCURRENCY=${CELERY_CONCURRENCY:-4}
LOGLEVEL=${CELERY_LOGLEVEL:-info}
MAX_TASKS=${CELERY_MAX_TASKS:-100}

echo -e "${GREEN}📋 Configuración:${NC}"
echo "   - Concurrency: ${CONCURRENCY}"
echo "   - Log Level: ${LOGLEVEL}"
echo "   - Max Tasks per Child: ${MAX_TASKS}"

# Añadir src al PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Iniciar worker
echo -e "${GREEN}🔧 Iniciando worker...${NC}"
celery -A backoffice.celery_app worker \
    --loglevel=${LOGLEVEL} \
    --concurrency=${CONCURRENCY} \
    --max-tasks-per-child=${MAX_TASKS} \
    --time-limit=3600 \
    --soft-time-limit=3540
