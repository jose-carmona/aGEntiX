#!/bin/bash
# =============================================================================
# test-mcp.sh - Demostración completa del MCP Mock Server
# =============================================================================
#
# Este script demuestra todas las características del servidor MCP:
#   1. Health check y server info
#   2. Generación de token JWT
#   3. Lista de tools disponibles (tools/list)
#   4. Lista de resources disponibles (resources/list)
#   5. Ejecutar tools de lectura (consultar_expediente, listar_documentos)
#   6. Leer resources (expediente, documentos, historial)
#   7. Ejecutar tools de escritura (añadir_anotacion)
#   8. Demostración de errores (401 sin token, token inválido)
#
# Uso:
#   ./test-mcp.sh                    # Usa valores por defecto
#   ./test-mcp.sh EXP-2024-002       # Especifica expediente_id
#
# Requisitos:
#   - MCP Server corriendo en http://localhost:8000 (usar ./run-mcp.sh)
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
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuración por defecto
MCP_URL="${MCP_URL:-http://localhost:8000}"
EXPEDIENTE_ID="${1:-EXP-2024-001}"
TAREA_ID="${2:-TAREA-TEST-001}"

# Variables globales
TOKEN=""

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

# Verificar que el servidor MCP está corriendo
check_server() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}0. Verificando Servidor MCP${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    RESPONSE=$(curl -s "${MCP_URL}/health" 2>/dev/null || echo "ERROR")

    if [ "$RESPONSE" = "ERROR" ]; then
        echo -e "${RED}Error: No se pudo conectar con el servidor MCP${NC}"
        echo -e "${YELLOW}Asegúrate de que el servidor está corriendo:${NC}"
        echo -e "  ./run-mcp.sh"
        echo ""
        exit 1
    fi

    echo -e "${GREEN}Servidor MCP disponible en ${MCP_URL}${NC}"
    echo ""
}

# 1. Health check
health_check() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}1. Health Check${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}GET ${MCP_URL}/health${NC}"
    echo ""

    RESPONSE=$(curl -s "${MCP_URL}/health")
    echo "$RESPONSE" | jq '.'
    echo ""
}

# 2. Server info
server_info() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}2. Información del Servidor${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}GET ${MCP_URL}/info${NC}"
    echo ""

    RESPONSE=$(curl -s "${MCP_URL}/info")
    echo "$RESPONSE" | jq '.'
    echo ""
}

# 3. Generar token JWT
generate_token() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}3. Generando Token JWT${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Usar el generador centralizado de JWT
    TOKEN=$(python3 -c "
import sys
sys.path.insert(0, 'src')
from backoffice.auth.jwt_generator import generate_jwt

result = generate_jwt(
    expediente_id='${EXPEDIENTE_ID}',
    tarea_id='${TAREA_ID}',
    permisos=['consulta', 'gestion']
)
print(result.token)
")

    if [ -z "$TOKEN" ]; then
        echo -e "${RED}Error generando token${NC}"
        exit 1
    fi

    echo -e "${GREEN}Token generado correctamente${NC}"
    echo -e "Expediente: ${YELLOW}${EXPEDIENTE_ID}${NC}"
    echo -e "Tarea: ${YELLOW}${TAREA_ID}${NC}"
    echo -e "Permisos: ${YELLOW}consulta, gestion${NC}"
    echo ""

    # Mostrar claims del token
    echo -e "${CYAN}Claims del token:${NC}"
    python3 -c "
import sys
sys.path.insert(0, 'src')
from backoffice.auth.jwt_generator import decode_jwt_unsafe
import json

claims = decode_jwt_unsafe('${TOKEN}')
# Mostrar solo claims relevantes
relevant = {k: v for k, v in claims.items() if k in ['iss', 'sub', 'aud', 'exp_id', 'permisos', 'exp', 'iat']}
print(json.dumps(relevant, indent=2, ensure_ascii=False))
"
    echo ""
}

# 4. Listar Tools
list_tools() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}4. Listando Tools Disponibles${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}POST ${MCP_URL}/rpc${NC}"
    echo -e "${MAGENTA}Method: tools/list${NC}"
    echo ""

    REQUEST_BODY='{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

    RESPONSE=$(curl -s -X POST "${MCP_URL}/rpc" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_BODY")

    echo -e "${CYAN}Tools disponibles:${NC}"
    echo "$RESPONSE" | jq '.result.tools[] | {name: .name, description: .description}'
    echo ""
}

# 5. Listar Resources
list_resources() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}5. Listando Resources Disponibles${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}POST ${MCP_URL}/rpc${NC}"
    echo -e "${MAGENTA}Method: resources/list${NC}"
    echo ""

    REQUEST_BODY='{"jsonrpc": "2.0", "id": 2, "method": "resources/list"}'

    RESPONSE=$(curl -s -X POST "${MCP_URL}/rpc" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_BODY")

    echo -e "${CYAN}Resources disponibles:${NC}"
    echo "$RESPONSE" | jq '.result.resources[] | {uri: .uri, name: .name}'
    echo ""
}

# 6. Consultar Expediente (tool de lectura)
consultar_expediente() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}6. Ejecutando Tool: consultar_expediente${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}POST ${MCP_URL}/rpc${NC}"
    echo -e "${MAGENTA}Method: tools/call${NC}"
    echo ""

    REQUEST_BODY=$(cat <<EOF
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "consultar_expediente",
    "arguments": {"expediente_id": "${EXPEDIENTE_ID}"}
  }
}
EOF
)

    echo -e "${CYAN}Request:${NC}"
    echo "$REQUEST_BODY" | jq '.params'
    echo ""

    RESPONSE=$(curl -s -X POST "${MCP_URL}/rpc" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_BODY")

    echo -e "${CYAN}Response (resumen):${NC}"
    # Parsear el contenido JSON dentro del texto
    echo "$RESPONSE" | jq -r '.result.content[0].text' | jq '{id, estado, tipo, fecha_creacion, solicitante: .datos.solicitante}'
    echo ""
}

# 7. Listar Documentos (tool de lectura)
listar_documentos() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}7. Ejecutando Tool: listar_documentos${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}POST ${MCP_URL}/rpc${NC}"
    echo -e "${MAGENTA}Method: tools/call${NC}"
    echo ""

    REQUEST_BODY=$(cat <<EOF
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "listar_documentos",
    "arguments": {"expediente_id": "${EXPEDIENTE_ID}"}
  }
}
EOF
)

    RESPONSE=$(curl -s -X POST "${MCP_URL}/rpc" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_BODY")

    echo -e "${CYAN}Documentos del expediente:${NC}"
    echo "$RESPONSE" | jq -r '.result.content[0].text' | jq '.[] | {id, nombre, tipo, validado}'
    echo ""
}

# 8. Leer Resource
read_resource() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}8. Leyendo Resource: historial${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}POST ${MCP_URL}/rpc${NC}"
    echo -e "${MAGENTA}Method: resources/read${NC}"
    echo ""

    REQUEST_BODY=$(cat <<EOF
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "resources/read",
  "params": {
    "uri": "expediente://${EXPEDIENTE_ID}/historial"
  }
}
EOF
)

    echo -e "${CYAN}URI: expediente://${EXPEDIENTE_ID}/historial${NC}"
    echo ""

    RESPONSE=$(curl -s -X POST "${MCP_URL}/rpc" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_BODY")

    echo -e "${CYAN}Historial del expediente:${NC}"
    echo "$RESPONSE" | jq -r '.result.contents[0].text' | jq '.[] | {id, fecha, tipo, accion, detalles}'
    echo ""
}

# 9. Añadir Anotación (tool de escritura)
añadir_anotacion() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}9. Ejecutando Tool: añadir_anotacion (ESCRITURA)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}POST ${MCP_URL}/rpc${NC}"
    echo -e "${MAGENTA}Method: tools/call${NC}"
    echo ""

    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    ANOTACION="[TEST] Anotación de prueba generada por test-mcp.sh - ${TIMESTAMP}"

    REQUEST_BODY=$(cat <<EOF
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "tools/call",
  "params": {
    "name": "añadir_anotacion",
    "arguments": {
      "expediente_id": "${EXPEDIENTE_ID}",
      "texto": "${ANOTACION}"
    }
  }
}
EOF
)

    echo -e "${CYAN}Anotación:${NC} ${ANOTACION}"
    echo ""

    RESPONSE=$(curl -s -X POST "${MCP_URL}/rpc" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_BODY")

    echo -e "${CYAN}Resultado:${NC}"
    echo "$RESPONSE" | jq -r '.result.content[0].text' | jq '.'
    echo ""
}

# 10. Error sin token (401)
error_sin_token() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}10. Demostración Error 401: Sin Token${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}POST ${MCP_URL}/rpc (sin Authorization header)${NC}"
    echo ""

    REQUEST_BODY='{"jsonrpc": "2.0", "id": 99, "method": "tools/list"}'

    # Capturar código HTTP
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${MCP_URL}/rpc" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_BODY")

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    echo -e "${RED}HTTP Status: ${HTTP_CODE}${NC}"
    echo -e "${CYAN}Response:${NC}"
    echo "$BODY" | jq '.'
    echo ""
}

# 11. Error con token inválido
error_token_invalido() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}11. Demostración Error 401: Token Inválido${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}POST ${MCP_URL}/rpc (con token falso)${NC}"
    echo ""

    REQUEST_BODY='{"jsonrpc": "2.0", "id": 100, "method": "tools/list"}'
    FAKE_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${MCP_URL}/rpc" \
        -H "Authorization: Bearer ${FAKE_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_BODY")

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    echo -e "${RED}HTTP Status: ${HTTP_CODE}${NC}"
    echo -e "${CYAN}Response:${NC}"
    echo "$BODY" | jq '.'
    echo ""
}

# Mostrar resumen
show_summary() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}Resumen - Características Demostradas${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${GREEN}Endpoints:${NC}"
    echo -e "  GET  /health  - Health check (sin autenticación)"
    echo -e "  GET  /info    - Información del servidor"
    echo -e "  POST /rpc     - JSON-RPC 2.0 (requiere JWT)"
    echo -e "  POST /sse     - Server-Sent Events (requiere JWT)"
    echo ""
    echo -e "${GREEN}Tools MCP (6 disponibles):${NC}"
    echo -e "  ${CYAN}Lectura:${NC}"
    echo -e "    - consultar_expediente  Obtiene info completa del expediente"
    echo -e "    - listar_documentos     Lista documentos del expediente"
    echo -e "    - obtener_documento     Obtiene un documento específico"
    echo -e "  ${YELLOW}Escritura:${NC}"
    echo -e "    - añadir_documento      Añade documento al expediente"
    echo -e "    - actualizar_datos      Modifica campos del expediente"
    echo -e "    - añadir_anotacion      Añade nota al historial"
    echo ""
    echo -e "${GREEN}Resources MCP (por expediente):${NC}"
    echo -e "  - expediente://{id}           Info completa"
    echo -e "  - expediente://{id}/documentos Lista de documentos"
    echo -e "  - expediente://{id}/historial  Historial de acciones"
    echo ""
    echo -e "${GREEN}Seguridad:${NC}"
    echo -e "  - Validación JWT obligatoria (10 claims)"
    echo -e "  - Permisos: consulta, gestion"
    echo -e "  - Validación de expediente_id en token vs request"
    echo ""
    echo -e "${CYAN}Comandos útiles:${NC}"
    echo -e "  # Iniciar servidor MCP"
    echo -e "  ./run-mcp.sh"
    echo ""
    echo -e "  # Test con otro expediente"
    echo -e "  ./test-mcp.sh EXP-2024-002"
    echo ""
    echo -e "  # Consulta manual"
    echo -e "  curl -X POST ${MCP_URL}/rpc \\"
    echo -e "    -H 'Authorization: Bearer \$TOKEN' \\"
    echo -e "    -H 'Content-Type: application/json' \\"
    echo -e "    -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}'"
    echo ""
}

# Main
main() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║        aGEntiX - Test del MCP Mock Server                 ║${NC}"
    echo -e "${GREEN}║        Demostración de todas las características          ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""

    check_dependencies
    check_server
    health_check
    server_info
    generate_token
    list_tools
    list_resources
    consultar_expediente
    listar_documentos
    read_resource
    añadir_anotacion
    error_sin_token
    error_token_invalido
    show_summary
}

main
