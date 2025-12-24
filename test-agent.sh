#!/bin/bash
# =============================================================================
# test-agent.sh - Script de ejemplo para ejecutar agentes
# =============================================================================
#
# Este script demuestra cómo usar el API simplificado de aGEntiX:
#   1. Genera un token JWT válido
#   2. Lista los agentes disponibles
#   3. Ejecuta un agente sin callback
#   4. Consulta el estado de la ejecución
#
# Uso:
#   ./test-agent.sh                    # Usa valores por defecto
#   ./test-agent.sh EXP-2024-002       # Especifica expediente_id
#   ./test-agent.sh EXP-2024-002 AnalizadorSubvencion  # Especifica agente
#
# Requisitos:
#   - API corriendo en http://localhost:8080
#   - curl y jq instalados
#
# =============================================================================

set -e

# Cargar variables de entorno desde .env si existe
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuración por defecto
API_URL="${API_URL:-http://localhost:8080}"
EXPEDIENTE_ID="${1:-EXP-2024-001}"
AGENT_NAME="${2:-ValidadorDocumental}"
TAREA_ID="${3:-TAREA-TEST-001}"

# Verificar dependencias
check_dependencies() {
    local missing=0

    if ! command -v curl &> /dev/null; then
        echo -e "${RED}Error: curl no está instalado${NC}"
        missing=1
    fi

    if ! command -v jq &> /dev/null; then
        echo -e "${RED}Error: jq no está instalado${NC}"
        echo -e "${YELLOW}Instalar con: apt-get install jq${NC}"
        missing=1
    fi

    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: python3 no está instalado${NC}"
        missing=1
    fi

    if [ $missing -eq 1 ]; then
        exit 1
    fi
}

# Generar token JWT
generate_token() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}1. Generando Token JWT${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    TOKEN=$(python3 -c "
import sys
sys.path.insert(0, 'src')
from mcp_mock.mcp_expedientes.generate_token import generate_test_token

token = generate_test_token(
    exp_id='${EXPEDIENTE_ID}',
    tarea_id='${TAREA_ID}',
    permisos=['consulta', 'gestion']
)
print(token)
")

    if [ -z "$TOKEN" ]; then
        echo -e "${RED}Error generando token${NC}"
        exit 1
    fi

    echo -e "${GREEN}Token generado correctamente${NC}"
    echo -e "Expediente: ${YELLOW}${EXPEDIENTE_ID}${NC}"
    echo -e "Tarea: ${YELLOW}${TAREA_ID}${NC}"
    echo ""
}

# Listar agentes disponibles
list_agents() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}2. Listando Agentes Disponibles${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}GET ${API_URL}/api/v1/agent/agents${NC}"
    echo ""

    RESPONSE=$(curl -s "${API_URL}/api/v1/agent/agents")

    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: No se pudo conectar con la API${NC}"
        echo -e "${YELLOW}Asegúrate de que el servidor está corriendo:${NC}"
        echo -e "  python -m uvicorn src.api.main:app --reload --port 8080"
        exit 1
    fi

    echo "$RESPONSE" | jq '.'
    echo ""
}

# Ejecutar agente
execute_agent() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}3. Ejecutando Agente: ${AGENT_NAME}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}POST ${API_URL}/api/v1/agent/execute${NC}"
    echo ""

    # Request body (formato simplificado)
    REQUEST_BODY=$(cat <<EOF
{
  "agent": "${AGENT_NAME}",
  "prompt": "Valida los documentos del expediente ${EXPEDIENTE_ID} y verifica que toda la documentación esté completa",
  "context": {
    "expediente_id": "${EXPEDIENTE_ID}",
    "tarea_id": "${TAREA_ID}"
  }
}
EOF
)

    echo -e "${CYAN}Request Body:${NC}"
    echo "$REQUEST_BODY" | jq '.'
    echo ""

    RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/agent/execute" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_BODY")

    echo -e "${CYAN}Response:${NC}"
    echo "$RESPONSE" | jq '.'
    echo ""

    # Extraer agent_run_id para consultar estado
    AGENT_RUN_ID=$(echo "$RESPONSE" | jq -r '.agent_run_id // empty')

    if [ -z "$AGENT_RUN_ID" ]; then
        echo -e "${RED}Error: No se recibió agent_run_id${NC}"
        echo "$RESPONSE" | jq '.'
        exit 1
    fi

    echo -e "${GREEN}Ejecución iniciada: ${AGENT_RUN_ID}${NC}"
    echo ""
}

# Consultar estado
check_status() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}4. Consultando Estado${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}GET ${API_URL}/api/v1/agent/status/${AGENT_RUN_ID}${NC}"
    echo ""

    # Esperar un momento para que el agente procese
    sleep 1

    RESPONSE=$(curl -s "${API_URL}/api/v1/agent/status/${AGENT_RUN_ID}")

    echo -e "${CYAN}Status:${NC}"
    echo "$RESPONSE" | jq '.'
    echo ""

    STATUS=$(echo "$RESPONSE" | jq -r '.status // empty')
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // empty')

    if [ "$STATUS" = "completed" ]; then
        if [ "$SUCCESS" = "true" ]; then
            echo -e "${GREEN}✓ Agente completado exitosamente${NC}"
        else
            echo -e "${RED}✗ Agente completó con errores${NC}"
        fi
    elif [ "$STATUS" = "running" ] || [ "$STATUS" = "pending" ]; then
        echo -e "${YELLOW}⏳ Agente en ejecución (status: ${STATUS})${NC}"
        echo -e "Puedes consultar el estado nuevamente con:"
        echo -e "  curl ${API_URL}/api/v1/agent/status/${AGENT_RUN_ID}"
    else
        echo -e "${RED}Estado desconocido: ${STATUS}${NC}"
    fi
}

# Mostrar resumen
show_summary() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}Resumen${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "Expediente:    ${YELLOW}${EXPEDIENTE_ID}${NC}"
    echo -e "Agente:        ${YELLOW}${AGENT_NAME}${NC}"
    echo -e "Tarea:         ${YELLOW}${TAREA_ID}${NC}"
    echo -e "Run ID:        ${YELLOW}${AGENT_RUN_ID}${NC}"
    echo ""
    echo -e "${CYAN}Comandos útiles:${NC}"
    echo -e "  # Consultar estado"
    echo -e "  curl ${API_URL}/api/v1/agent/status/${AGENT_RUN_ID}"
    echo ""
    echo -e "  # Listar agentes"
    echo -e "  curl ${API_URL}/api/v1/agent/agents"
    echo ""
}

# Main
main() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║            aGEntiX - Test de Ejecución de Agente          ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""

    check_dependencies
    generate_token
    list_agents
    execute_agent
    check_status
    show_summary
}

main
