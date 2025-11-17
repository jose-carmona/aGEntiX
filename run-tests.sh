#!/bin/bash
#
# Script para ejecutar tests del proyecto aGEntiX
#
# Uso:
#   ./run-tests.sh                    # Ejecutar todos los tests
#   ./run-tests.sh -v                 # Modo verbose
#   ./run-tests.sh -vv                # Modo muy verbose
#   ./run-tests.sh -k test_auth       # Ejecutar solo tests que contengan "test_auth"
#   ./run-tests.sh --help             # Ver ayuda

set -e  # Salir si hay error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directorio raíz del proyecto
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_DIR="${PROJECT_ROOT}/mcp-mock/mcp-expedientes"

# Función para mostrar ayuda
show_help() {
    cat << EOF
${BLUE}═══════════════════════════════════════════════════════════════${NC}
${GREEN}Script de Tests - aGEntiX${NC}
${BLUE}═══════════════════════════════════════════════════════════════${NC}

${YELLOW}Uso:${NC}
    ./run-tests.sh [argumentos_pytest]

${YELLOW}Opciones comunes:${NC}
    -h, --help          Mostrar esta ayuda
    -v, --verbose       Modo verbose
    -vv                 Modo muy verbose (muestra print statements)
    -k EXPRESION        Ejecutar solo tests que coincidan con la expresión
    --failed            Ejecutar solo los tests que fallaron la última vez
    -x, --exitfirst     Detener en el primer fallo

${YELLOW}Ejemplos:${NC}
    ${GREEN}# Ejecutar todos los tests${NC}
    ./run-tests.sh

    ${GREEN}# Ejecutar con output verbose${NC}
    ./run-tests.sh -v

    ${GREEN}# Ejecutar solo tests de autenticación${NC}
    ./run-tests.sh -k auth

    ${GREEN}# Ejecutar solo tests de tools con verbose${NC}
    ./run-tests.sh -v -k tools

    ${GREEN}# Detener en el primer error${NC}
    ./run-tests.sh -x

    ${GREEN}# Re-ejecutar solo los tests que fallaron${NC}
    ./run-tests.sh --failed

${BLUE}═══════════════════════════════════════════════════════════════${NC}
EOF
}

# Verificar si se pide ayuda
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# Banner
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Ejecutando Tests - aGEntiX MCP Mock${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Verificar que existe el directorio de tests
if [ ! -d "${MCP_DIR}/tests" ]; then
    echo -e "${RED}✗ Error: No se encuentra el directorio de tests${NC}"
    echo -e "  Esperado en: ${MCP_DIR}/tests"
    exit 1
fi

# Verificar que existe pytest
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}✗ Error: pytest no está instalado${NC}"
    echo -e "  Instalar con: pip install pytest pytest-asyncio"
    exit 1
fi

# Configurar PYTHONPATH
export PYTHONPATH="${MCP_DIR}/tests:${PYTHONPATH}"

# Cambiar al directorio del MCP
cd "${MCP_DIR}"

echo -e "${YELLOW}📂 Directorio:${NC} ${MCP_DIR}"
echo -e "${YELLOW}🐍 Python:${NC} $(python --version 2>&1)"
echo ""
echo -e "${BLUE}▶ Ejecutando tests...${NC}"
echo ""

# Ejecutar tests con todos los argumentos pasados
pytest "$@" tests/

RESULT=$?

# Resultado final
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
if [ $RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ TODOS LOS TESTS PASARON${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    exit 0
else
    echo -e "${RED}✗ ALGUNOS TESTS FALLARON (código: ${RESULT})${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    exit $RESULT
fi
