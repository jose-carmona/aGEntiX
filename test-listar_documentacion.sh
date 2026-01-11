#!/bin/bash
# =============================================================================
# test-listar_documentacion.sh - Script para probar la tool listar_documentacion
# =============================================================================
#
# Este script prueba directamente la tool MCP `listar_documentacion`:
#   1. Genera un token JWT con permiso 'documentacion:leer'
#   2. Llama directamente al servidor MCP via JSON-RPC
#   3. Muestra la documentación disponible para el tipo de expediente
#
# Uso:
#   ./test-listar_documentacion.sh                    # Usa 'subvenciones' por defecto
#   ./test-listar_documentacion.sh licencias_obras    # Especifica tipo de expediente
#   ./test-listar_documentacion.sh certificado_empadronamiento
#
# Tipos de expediente válidos:
#   - subvenciones
#   - licencias_obras
#   - certificado_empadronamiento
#
# Requisitos:
#   - Servidor MCP corriendo en http://localhost:8000
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
MCP_URL="${MCP_URL:-http://localhost:8000}"
TIPO_EXPEDIENTE="${1:-subvenciones}"
EXPEDIENTE_ID="${2:-EXP-2026-004}"

# Tipos válidos para referencia
TIPOS_VALIDOS="subvenciones, licencias_obras, certificado_empadronamiento"

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

# Verificar tipo de expediente válido
validate_tipo_expediente() {
    case "$TIPO_EXPEDIENTE" in
        subvenciones|licencias_obras|certificado_empadronamiento)
            return 0
            ;;
        *)
            echo -e "${RED}Error: Tipo de expediente no válido: '${TIPO_EXPEDIENTE}'${NC}"
            echo -e "${YELLOW}Tipos válidos: ${TIPOS_VALIDOS}${NC}"
            exit 1
            ;;
    esac
}

# Verificar que el servidor MCP está corriendo
check_mcp_server() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}1. Verificando Servidor MCP${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}GET ${MCP_URL}/health${NC}"
    echo ""

    RESPONSE=$(curl -s "${MCP_URL}/health" 2>/dev/null || echo "ERROR")

    if [ "$RESPONSE" = "ERROR" ] || [ -z "$RESPONSE" ]; then
        echo -e "${RED}Error: No se pudo conectar con el servidor MCP${NC}"
        echo -e "${YELLOW}Asegúrate de que el servidor está corriendo:${NC}"
        echo -e "  cd src/mcp_mock/mcp_expedientes"
        echo -e "  python -m uvicorn server_http:app --reload --port 8000"
        exit 1
    fi

    echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
    echo -e "${GREEN}✓ Servidor MCP disponible${NC}"
    echo ""
}

# Generar token JWT con permiso documentacion:leer
generate_token() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}2. Generando Token JWT (con permiso documentacion:leer)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Generar token con permiso 'documentacion:leer' necesario para listar_documentacion
    TOKEN=$(python3 -c "
import sys
sys.path.insert(0, 'src')
from backoffice.auth.jwt_generator import generate_jwt

result = generate_jwt(
    expediente_id='${EXPEDIENTE_ID}',
    tarea_id='TAREA-DOC-TEST',
    permisos=['consulta', 'gestion', 'documentacion:leer', 'documentacion:buscar']
)
print(result.token)
")

    if [ -z "$TOKEN" ]; then
        echo -e "${RED}Error generando token${NC}"
        exit 1
    fi

    echo -e "${GREEN}Token generado correctamente${NC}"
    echo -e "Permisos: ${YELLOW}consulta, gestion, documentacion:leer, documentacion:buscar${NC}"
    echo ""
}

# Listar tools disponibles (opcional, para verificar)
list_tools() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}3. Listando Tools Disponibles${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}POST ${MCP_URL}/rpc (tools/list)${NC}"
    echo ""

    RESPONSE=$(curl -s -X POST "${MCP_URL}/rpc" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}')

    # Mostrar solo las tools de documentación
    echo -e "${CYAN}Tools de documentación disponibles:${NC}"
    echo "$RESPONSE" | jq '.result.tools[] | select(.name | startswith("listar_doc") or startswith("obtener_doc") or startswith("buscar_en"))' 2>/dev/null || echo "$RESPONSE"
    echo ""
}

# Ejecutar listar_documentacion
call_listar_documentacion() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}4. Ejecutando listar_documentacion${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}POST ${MCP_URL}/rpc (tools/call)${NC}"
    echo ""

    # Request body JSON-RPC
    REQUEST_BODY=$(cat <<EOF
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "listar_documentacion",
    "arguments": {
      "tipo_expediente": "${TIPO_EXPEDIENTE}"
    }
  }
}
EOF
)

    echo -e "${CYAN}Request:${NC}"
    echo "$REQUEST_BODY" | jq '.'
    echo ""

    RESPONSE=$(curl -s -X POST "${MCP_URL}/rpc" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_BODY")

    HTTP_CODE=$(echo "$RESPONSE" | jq -r '.error.code // empty')

    if [ -n "$HTTP_CODE" ]; then
        echo -e "${RED}Error en la respuesta:${NC}"
        echo "$RESPONSE" | jq '.'
        echo ""

        ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error.message // empty')
        echo -e "${RED}✗ Error: ${ERROR_MSG}${NC}"

        if [[ "$ERROR_MSG" == *"documentacion:leer"* ]]; then
            echo -e "${YELLOW}→ El token no tiene el permiso 'documentacion:leer' requerido${NC}"
        fi
        return 1
    fi

    echo -e "${CYAN}Response:${NC}"
    # Extraer y formatear el contenido de la respuesta
    CONTENT=$(echo "$RESPONSE" | jq -r '.result.content[0].text // empty')

    if [ -n "$CONTENT" ]; then
        echo "$CONTENT" | jq '.'
        echo ""
        echo -e "${GREEN}✓ listar_documentacion ejecutado correctamente${NC}"

        # Contar documentos
        NUM_DOCS=$(echo "$CONTENT" | jq '.documentos | length')
        echo -e "${GREEN}  Documentos encontrados: ${NUM_DOCS}${NC}"
    else
        echo "$RESPONSE" | jq '.'
    fi
}

# Mostrar resumen
show_summary() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}Resumen${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "Tipo expediente: ${YELLOW}${TIPO_EXPEDIENTE}${NC}"
    echo -e "Servidor MCP:    ${YELLOW}${MCP_URL}${NC}"
    echo ""
    echo -e "${CYAN}Otros comandos útiles:${NC}"
    echo ""
    echo -e "  # Probar otros tipos de expediente:"
    echo -e "  ./test-listar_documentacion.sh licencias_obras"
    echo -e "  ./test-listar_documentacion.sh certificado_empadronamiento"
    echo ""
    echo -e "  # Probar otras tools de documentación:"
    echo -e "  # obtener_doc_documentacion (requiere tipo_expediente + tipo_documento)"
    echo -e "  # buscar_en_documentacion (requiere tipo_expediente + query)"
    echo ""
}

# Main
main() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     aGEntiX - Test de Tool listar_documentacion           ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""

    check_dependencies
    validate_tipo_expediente
    check_mcp_server
    generate_token
    list_tools
    call_listar_documentacion
    show_summary
}

main
