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
BACKOFFICE_DIR="${PROJECT_ROOT}/backoffice"

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
    --mcp-only          Ejecutar solo tests de MCP
    --backoffice-only   Ejecutar solo tests de Back-Office

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

    ${GREEN}# Ejecutar solo tests de MCP${NC}
    ./run-tests.sh --mcp-only

    ${GREEN}# Ejecutar solo tests de Back-Office${NC}
    ./run-tests.sh --backoffice-only

${BLUE}═══════════════════════════════════════════════════════════════${NC}
EOF
}

# Verificar si se pide ayuda
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# Detectar qué tests ejecutar
RUN_MCP=true
RUN_BACKOFFICE=true

if [[ "$1" == "--mcp-only" ]]; then
    RUN_BACKOFFICE=false
    shift
elif [[ "$1" == "--backoffice-only" ]]; then
    RUN_MCP=false
    shift
fi

# Banner
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Ejecutando Tests - aGEntiX${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Verificar que existen los directorios de tests
if [ "$RUN_MCP" = true ] && [ ! -d "${MCP_DIR}/tests" ]; then
    echo -e "${RED}✗ Error: No se encuentra el directorio de tests de MCP${NC}"
    echo -e "  Esperado en: ${MCP_DIR}/tests"
    exit 1
fi

if [ "$RUN_BACKOFFICE" = true ] && [ ! -d "${BACKOFFICE_DIR}/tests" ]; then
    echo -e "${RED}✗ Error: No se encuentra el directorio de tests de Back-Office${NC}"
    echo -e "  Esperado en: ${BACKOFFICE_DIR}/tests"
    exit 1
fi

# Verificar que existe pytest
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}✗ Error: pytest no está instalado${NC}"
    echo -e "  Instalar con: pip install pytest pytest-asyncio"
    exit 1
fi

echo -e "${YELLOW}🐍 Python:${NC} $(python --version 2>&1)"
echo ""

OVERALL_RESULT=0

# Ejecutar tests de MCP si está habilitado
if [ "$RUN_MCP" = true ]; then
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}📦 Tests de MCP Mock${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}📂 Directorio:${NC} ${MCP_DIR}"
    echo ""

    # Configurar PYTHONPATH
    export PYTHONPATH="${MCP_DIR}/tests:${PYTHONPATH}"

    # Cambiar al directorio del MCP y ejecutar tests
    cd "${MCP_DIR}"
    pytest "$@" tests/
    MCP_RESULT=$?

    if [ $MCP_RESULT -ne 0 ]; then
        OVERALL_RESULT=$MCP_RESULT
    fi

    echo ""
fi

# Ejecutar tests de Back-Office si está habilitado
if [ "$RUN_BACKOFFICE" = true ]; then
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}📦 Tests de Back-Office${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}📂 Directorio:${NC} ${BACKOFFICE_DIR}"
    echo ""

    # Cambiar al directorio del proyecto raíz para mantener imports relativos
    cd "${PROJECT_ROOT}"

    # Ejecutar tests del back-office desde el directorio raíz
    pytest "$@" backoffice/tests/
    BACKOFFICE_RESULT=$?

    if [ $BACKOFFICE_RESULT -ne 0 ]; then
        OVERALL_RESULT=$BACKOFFICE_RESULT
    fi

    echo ""
fi

# Resultado final
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
if [ $OVERALL_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ TODOS LOS TESTS PASARON${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    exit 0
else
    echo -e "${RED}✗ ALGUNOS TESTS FALLARON (código: ${OVERALL_RESULT})${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    exit $OVERALL_RESULT
fi
