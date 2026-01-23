#!/bin/bash
# ==============================================================================
# generate_secrets.sh - Genera secretos seguros para producción
#
# Uso:
#   ./scripts/generate_secrets.sh > .env.prod
#
# Genera valores seguros para:
#   - REDIS_PASSWORD
#   - FLOWER_PASSWORD
#   - JWT_SECRET
#   - API_ADMIN_TOKEN
#
# P3 - Ver code-review/commit-41f313a/plan-mejoras.md
# ==============================================================================

set -e

# Colores para output a stderr (no afecta el .env generado)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Función para generar secreto seguro
generate_secret() {
    openssl rand -base64 32 | tr -d '\n'
}

# Mensaje informativo a stderr
>&2 echo -e "${GREEN}Generando secretos seguros para producción...${NC}"
>&2 echo ""

# Generar y mostrar variables de entorno
cat << EOF
# ==============================================================================
# .env.prod - Configuración de producción para aGEntiX
# Generado el: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
#
# IMPORTANTE: Mantener este archivo seguro y nunca commitear a git
# ==============================================================================

# Redis
REDIS_PASSWORD=$(generate_secret)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Celery (usa Redis como broker)
CELERY_BROKER_URL=redis://:\${REDIS_PASSWORD}@redis:6379/0
CELERY_RESULT_BACKEND=redis://:\${REDIS_PASSWORD}@redis:6379/0
CELERY_TASK_TIME_LIMIT=3600
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_REPLICAS=2

# JWT
JWT_SECRET=$(generate_secret)
JWT_ALGORITHM=HS256
JWT_EXPECTED_ISSUER=agentix-bpmn
JWT_EXPECTED_SUBJECT=Automático
JWT_REQUIRED_AUDIENCE=agentix-mcp-expedientes

# Admin Authentication
API_ADMIN_TOKEN=$(generate_secret)

# Flower (Celery monitoring)
FLOWER_USER=admin
FLOWER_PASSWORD=$(generate_secret)
FLOWER_PORT=5555

# API
API_PORT=8080
API_WORKERS=4

# Logging
LOG_LEVEL=INFO

# Feature Flags
USE_CELERY=true

# Environment
ENVIRONMENT=production
EOF

# Mensaje final a stderr
>&2 echo ""
>&2 echo -e "${GREEN}✅ Secretos generados exitosamente${NC}"
>&2 echo ""
>&2 echo -e "${YELLOW}Próximos pasos:${NC}"
>&2 echo "  1. Guardar el output en .env.prod:"
>&2 echo "     ./scripts/generate_secrets.sh > .env.prod"
>&2 echo ""
>&2 echo "  2. Revisar y ajustar valores si es necesario"
>&2 echo ""
>&2 echo "  3. Iniciar con:"
>&2 echo "     docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d"
>&2 echo ""
>&2 echo -e "${RED}⚠️  NUNCA commitear .env.prod a git${NC}"
