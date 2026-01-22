#!/bin/bash
# ==============================================================================
# start_flower.sh - Inicia Flower (UI de monitoreo de Celery)
#
# Uso:
#   ./scripts/start_flower.sh
#
# Variables de entorno opcionales:
#   FLOWER_PORT         - Puerto (default: 5555)
#   FLOWER_USER         - Usuario para autenticación (default: admin)
#   FLOWER_PASSWORD     - Contraseña (default: changeme)
#
# Acceso:
#   http://localhost:5555
#
# ==============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🌸 Iniciando Flower (Celery Monitor)...${NC}"

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
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  redis-cli no disponible, continuando...${NC}"
fi

# Configuración
PORT=${FLOWER_PORT:-5555}
USER=${FLOWER_USER:-admin}
PASSWORD=${FLOWER_PASSWORD:-changeme}

echo -e "${GREEN}📋 Configuración:${NC}"
echo "   - Puerto: ${PORT}"
echo "   - Usuario: ${USER}"
echo "   - URL: http://localhost:${PORT}"

# Añadir src al PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Iniciar Flower
echo -e "${GREEN}🔧 Iniciando Flower...${NC}"
celery -A backoffice.celery_app flower \
    --port=${PORT} \
    --basic_auth=${USER}:${PASSWORD} \
    --persistent=true \
    --db=/tmp/flower.db
