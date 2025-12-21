#!/bin/bash
#
# Script para ejecutar tests del proyecto aGEntiX
# Versión 2.0 - Configuración declarativa con soporte para selección múltiple
#
# Ejemplos de uso:
#   ./run-tests.sh                           # Ejecutar todos los tests
#   ./run-tests.sh --suites=api,contracts    # Solo API y Contracts
#   ./run-tests.sh --exclude=mcp             # Todo menos MCP
#   ./run-tests.sh --coverage                # Con coverage report
#   ./run-tests.sh --parallel                # Ejecución paralela (requiere pytest-xdist)
#   ./run-tests.sh --api-only -v             # Compatible con flags anteriores
#   ./run-tests.sh --help                    # Ver ayuda completa

# Nota: No usamos set -e aquí porque queremos continuar ejecutando suites
# incluso si una falla. Manejamos los errores explícitamente.

# ============================================================================
# COLORES PARA OUTPUT
# ============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# ============================================================================
# CONFIGURACIÓN DEL PROYECTO
# ============================================================================
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ============================================================================
# CONFIGURACIÓN DECLARATIVA DE SUITES DE TESTS
# ============================================================================
# Formato: suite_key="dir=<path>;name=<nombre>;emoji=<emoji>;timeout=<segundos>"
#
# Para agregar una nueva suite, solo agrega una línea aquí:
# TEST_SUITES[nueva]="dir=tests/test_nueva;name=Nueva Suite;emoji=🎯;timeout=60"
#
declare -A TEST_SUITES=(
    [api]="dir=tests/api;name=API REST;emoji=🌐;timeout=60"
    [mcp]="dir=tests/test_mcp;name=MCP Mock;emoji=🔌;timeout=90"
    [backoffice]="dir=tests/test_backoffice;name=Back-Office;emoji=⚙️;timeout=120"
    [contracts]="dir=tests/test_contracts;name=Contracts;emoji=📜;timeout=30"
    [error]="dir=tests/test_error_handling;name=Error Handling;emoji=🛡️;timeout=60"
)

# Orden de ejecución (si no se especifica --suites)
DEFAULT_SUITE_ORDER=("api" "mcp" "backoffice" "contracts" "error")

# ============================================================================
# FUNCIÓN PARA MOSTRAR AYUDA
# ============================================================================
show_help() {
    cat << EOF
${BLUE}═══════════════════════════════════════════════════════════════${NC}
${GREEN}Script de Tests - aGEntiX v2.0${NC}
${BLUE}═══════════════════════════════════════════════════════════════${NC}

${YELLOW}Uso:${NC}
    ./run-tests.sh [opciones] [argumentos_pytest]

${YELLOW}Opciones de selección de suites:${NC}
    --suites=SUITE1,SUITE2,...  Ejecutar solo las suites especificadas
    --exclude=SUITE1,SUITE2,... Excluir suites específicas
    --api-only                  Ejecutar solo tests de API (compatible)
    --mcp-only                  Ejecutar solo tests de MCP (compatible)
    --backoffice-only           Ejecutar solo tests de Back-Office (compatible)
    --contracts-only            Ejecutar solo tests de Contracts
    --error-only                Ejecutar solo tests de Error Handling

${YELLOW}Opciones de ejecución:${NC}
    --coverage                  Ejecutar con coverage report
    --parallel                  Ejecutar tests en paralelo (requiere pytest-xdist)
    --fail-fast                 Detener en el primer error de cualquier suite
    --quiet                     Output mínimo (solo resultados finales)
    --verbose                   Output detallado (equivale a -v para pytest)

${YELLOW}Opciones de pytest (se pasan directamente):${NC}
    -v, --verbose               Modo verbose de pytest
    -vv                         Modo muy verbose (muestra print statements)
    -k EXPRESION                Ejecutar solo tests que coincidan con la expresión
    -x, --exitfirst             Detener pytest en el primer fallo
    --failed                    Re-ejecutar solo los tests que fallaron
    --lf, --last-failed         Alias de --failed
    -m MARCA                    Ejecutar solo tests con marca específica
    --maxfail=N                 Detener después de N fallos

${YELLOW}Otras opciones:${NC}
    -h, --help                  Mostrar esta ayuda
    --list-suites               Listar suites disponibles y salir

${YELLOW}Ejemplos:${NC}
    ${GREEN}# Ejecutar todos los tests${NC}
    ./run-tests.sh

    ${GREEN}# Ejecutar solo API y Contracts${NC}
    ./run-tests.sh --suites=api,contracts

    ${GREEN}# Ejecutar todo excepto MCP${NC}
    ./run-tests.sh --exclude=mcp

    ${GREEN}# Tests con coverage en paralelo${NC}
    ./run-tests.sh --coverage --parallel

    ${GREEN}# Solo tests de autenticación con verbose${NC}
    ./run-tests.sh -k auth -v

    ${GREEN}# API tests con coverage y detener en primer error${NC}
    ./run-tests.sh --api-only --coverage -x

    ${GREEN}# Modo silencioso, solo API y Contracts${NC}
    ./run-tests.sh --quiet --suites=api,contracts

    ${GREEN}# Re-ejecutar solo tests fallidos con verbose${NC}
    ./run-tests.sh --failed -vv

${YELLOW}Suites disponibles:${NC}
EOF

    # Listar suites dinámicamente
    for suite_key in "${DEFAULT_SUITE_ORDER[@]}"; do
        if [[ -n "${TEST_SUITES[$suite_key]}" ]]; then
            local config="${TEST_SUITES[$suite_key]}"
            local suite_name suite_emoji suite_dir

            # Parsear configuración
            suite_dir=$(echo "$config" | grep -oP 'dir=\K[^;]+')
            suite_name=$(echo "$config" | grep -oP 'name=\K[^;]+')
            suite_emoji=$(echo "$config" | grep -oP 'emoji=\K[^;]+')

            echo -e "    ${suite_emoji}  ${CYAN}${suite_key}${NC} - ${suite_name} (${suite_dir})"
        fi
    done

    cat << EOF

${BLUE}═══════════════════════════════════════════════════════════════${NC}
EOF
}

# ============================================================================
# FUNCIÓN PARA LISTAR SUITES
# ============================================================================
list_suites() {
    echo -e "${BLUE}Suites disponibles:${NC}"
    for suite_key in "${DEFAULT_SUITE_ORDER[@]}"; do
        if [[ -n "${TEST_SUITES[$suite_key]}" ]]; then
            local config="${TEST_SUITES[$suite_key]}"
            local suite_name suite_emoji

            suite_name=$(echo "$config" | grep -oP 'name=\K[^;]+')
            suite_emoji=$(echo "$config" | grep -oP 'emoji=\K[^;]+')

            echo -e "  ${suite_emoji}  ${CYAN}${suite_key}${NC} - ${suite_name}"
        fi
    done
}

# ============================================================================
# FUNCIÓN PARA EJECUTAR UNA SUITE DE TESTS
# ============================================================================
run_test_suite() {
    local suite_key="$1"
    shift  # Remover suite_key de $@

    local config="${TEST_SUITES[$suite_key]}"

    if [[ -z "$config" ]]; then
        echo -e "${RED}✗ Error: Suite desconocida '${suite_key}'${NC}"
        return 1
    fi

    # Parsear configuración de la suite
    local suite_dir suite_name suite_emoji suite_timeout
    suite_dir=$(echo "$config" | grep -oP 'dir=\K[^;]+')
    suite_name=$(echo "$config" | grep -oP 'name=\K[^;]+')
    suite_emoji=$(echo "$config" | grep -oP 'emoji=\K[^;]+')
    suite_timeout=$(echo "$config" | grep -oP 'timeout=\K[^;]+')

    local full_path="${PROJECT_ROOT}/${suite_dir}"

    # Verificar que existe el directorio
    if [ ! -d "$full_path" ]; then
        if [ "$QUIET_MODE" = false ]; then
            echo -e "${YELLOW}⚠️  Saltando ${suite_name}: directorio no existe${NC}"
            echo -e "    ${CYAN}Esperado en:${NC} ${full_path}"
            echo ""
        fi
        return 0  # No es error, solo skip
    fi

    # Header (solo si no está en quiet mode)
    if [ "$QUIET_MODE" = false ]; then
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}${suite_emoji}  Tests de ${suite_name}${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}📂 Directorio:${NC} ${suite_dir}"
        if [ "$TIMEOUT_AVAILABLE" = true ]; then
            echo -e "${YELLOW}⏱️  Timeout:${NC} ${suite_timeout}s por test"
        fi
        echo ""
    else
        echo -e "${CYAN}${suite_emoji} ${suite_name}...${NC}"
    fi

    # Configurar PYTHONPATH
    export PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH}"

    # Construir comando pytest
    local pytest_cmd="pytest"

    # Timeout por test (solo si pytest-timeout está disponible)
    if [ "$TIMEOUT_AVAILABLE" = true ]; then
        pytest_cmd+=" --timeout=${suite_timeout}"
    fi

    # Coverage (si está habilitado globalmente)
    if [ "$ENABLE_COVERAGE" = true ]; then
        pytest_cmd+=" --cov=src --cov-append --cov-report=term-missing:skip-covered"
    fi

    # Parallel (si está habilitado globalmente)
    if [ "$ENABLE_PARALLEL" = true ]; then
        pytest_cmd+=" -n auto"
    fi

    # Fail fast (si está habilitado globalmente)
    if [ "$FAIL_FAST" = true ]; then
        pytest_cmd+=" -x"
    fi

    # Quiet mode para pytest
    if [ "$QUIET_MODE" = true ]; then
        pytest_cmd+=" -q"
    fi

    # Argumentos adicionales de pytest
    if [ ${#PYTEST_ARGS[@]} -gt 0 ]; then
        pytest_cmd+=" ${PYTEST_ARGS[@]}"
    fi

    # Directorio de tests
    pytest_cmd+=" ${full_path}/"

    # Ejecutar tests
    cd "${PROJECT_ROOT}"

    local result=0

    if [ "$QUIET_MODE" = false ]; then
        # Modo normal: mostrar todo el output
        eval "$pytest_cmd" || result=$?
        echo ""
    else
        # Quiet mode: capturar output y solo mostrar si hay error
        local temp_log="/tmp/pytest_output_${suite_key}_$$.log"

        if eval "$pytest_cmd" > "$temp_log" 2>&1; then
            echo -e "${GREEN}✓${NC}"
            result=0
        else
            result=$?
            echo -e "${RED}✗${NC}"
            cat "$temp_log"
        fi

        rm -f "$temp_log"
    fi

    return $result
}

# ============================================================================
# PARSEO DE ARGUMENTOS
# ============================================================================
SELECTED_SUITES=()
EXCLUDED_SUITES=()
PYTEST_ARGS=()
ENABLE_COVERAGE=false
ENABLE_PARALLEL=false
FAIL_FAST=false
QUIET_MODE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        --list-suites)
            list_suites
            exit 0
            ;;
        --suites=*)
            IFS=',' read -ra SELECTED_SUITES <<< "${1#--suites=}"
            shift
            ;;
        --exclude=*)
            IFS=',' read -ra EXCLUDED_SUITES <<< "${1#--exclude=}"
            shift
            ;;
        --api-only)
            SELECTED_SUITES=("api")
            shift
            ;;
        --mcp-only)
            SELECTED_SUITES=("mcp")
            shift
            ;;
        --backoffice-only)
            SELECTED_SUITES=("backoffice")
            shift
            ;;
        --contracts-only)
            SELECTED_SUITES=("contracts")
            shift
            ;;
        --error-only)
            SELECTED_SUITES=("error")
            shift
            ;;
        --coverage)
            ENABLE_COVERAGE=true
            shift
            ;;
        --parallel)
            ENABLE_PARALLEL=true
            shift
            ;;
        --fail-fast)
            FAIL_FAST=true
            shift
            ;;
        --quiet)
            QUIET_MODE=true
            shift
            ;;
        --verbose)
            PYTEST_ARGS+=("-v")
            shift
            ;;
        *)
            # Todos los demás argumentos se pasan a pytest
            PYTEST_ARGS+=("$1")
            shift
            ;;
    esac
done

# ============================================================================
# DETERMINAR QUÉ SUITES EJECUTAR
# ============================================================================

# Si no hay selección, ejecutar todas en orden por defecto
if [ ${#SELECTED_SUITES[@]} -eq 0 ]; then
    SELECTED_SUITES=("${DEFAULT_SUITE_ORDER[@]}")
fi

# Validar que todas las suites seleccionadas existen
for suite in "${SELECTED_SUITES[@]}"; do
    if [[ -z "${TEST_SUITES[$suite]}" ]]; then
        echo -e "${RED}✗ Error: Suite desconocida '${suite}'${NC}"
        echo ""
        echo "Suites disponibles:"
        list_suites
        exit 1
    fi
done

# Aplicar exclusiones
if [ ${#EXCLUDED_SUITES[@]} -gt 0 ]; then
    FILTERED_SUITES=()
    for suite in "${SELECTED_SUITES[@]}"; do
        excluded=false
        for exclude in "${EXCLUDED_SUITES[@]}"; do
            if [[ "$suite" == "$exclude" ]]; then
                excluded=true
                break
            fi
        done
        if [ "$excluded" = false ]; then
            FILTERED_SUITES+=("$suite")
        fi
    done
    SELECTED_SUITES=("${FILTERED_SUITES[@]}")
fi

# Verificar que quedó al menos una suite para ejecutar
if [ ${#SELECTED_SUITES[@]} -eq 0 ]; then
    echo -e "${RED}✗ Error: No hay suites para ejecutar después de aplicar exclusiones${NC}"
    exit 1
fi

# ============================================================================
# VALIDACIONES PREVIAS
# ============================================================================

# Banner inicial (solo si no está en quiet mode)
if [ "$QUIET_MODE" = false ]; then
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Ejecutando Tests - aGEntiX${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
fi

# Verificar que existe pytest
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}✗ Error: pytest no está instalado${NC}"
    echo -e "  ${YELLOW}Instalar con:${NC} pip install pytest pytest-asyncio"
    exit 1
fi

# Verificar pytest-xdist si se pidió parallel
if [ "$ENABLE_PARALLEL" = true ] && ! python -c "import xdist" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: pytest-xdist no está instalado, --parallel será ignorado${NC}"
    echo -e "  ${CYAN}Instalar con:${NC} pip install pytest-xdist"
    ENABLE_PARALLEL=false
fi

# Verificar pytest-cov si se pidió coverage
if [ "$ENABLE_COVERAGE" = true ] && ! python -c "import pytest_cov" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: pytest-cov no está instalado, --coverage será ignorado${NC}"
    echo -e "  ${CYAN}Instalar con:${NC} pip install pytest-cov"
    ENABLE_COVERAGE=false
fi

# Verificar pytest-timeout (para timeouts por test)
TIMEOUT_AVAILABLE=false
if python -c "import pytest_timeout" &> /dev/null; then
    TIMEOUT_AVAILABLE=true
fi

# Mostrar información del sistema (solo si no está en quiet mode)
if [ "$QUIET_MODE" = false ]; then
    echo -e "${YELLOW}🐍 Python:${NC} $(python --version 2>&1)"
    echo -e "${YELLOW}📦 pytest:${NC} $(pytest --version 2>&1 | head -1)"

    if [ "$ENABLE_COVERAGE" = true ]; then
        echo -e "${YELLOW}📊 Coverage:${NC} Habilitado"
    fi

    if [ "$ENABLE_PARALLEL" = true ]; then
        echo -e "${YELLOW}⚡ Parallel:${NC} Habilitado (pytest-xdist)"
    fi

    echo ""
    echo -e "${CYAN}Suites a ejecutar:${NC} ${SELECTED_SUITES[*]}"

    if [ ${#EXCLUDED_SUITES[@]} -gt 0 ]; then
        echo -e "${CYAN}Suites excluidas:${NC} ${EXCLUDED_SUITES[*]}"
    fi

    echo ""
fi

# ============================================================================
# EJECUTAR SUITES SELECCIONADAS
# ============================================================================
OVERALL_RESULT=0
SUITES_PASSED=0
SUITES_FAILED=0
declare -A SUITE_RESULTS

for suite_key in "${SELECTED_SUITES[@]}"; do
    if run_test_suite "$suite_key" "${PYTEST_ARGS[@]}"; then
        SUITE_RESULTS[$suite_key]="PASS"
        ((SUITES_PASSED++))
    else
        SUITE_RESULTS[$suite_key]="FAIL"
        ((SUITES_FAILED++))
        OVERALL_RESULT=1

        # Si fail-fast está habilitado, detener aquí
        if [ "$FAIL_FAST" = true ]; then
            echo -e "${RED}⚠️  Fail-fast habilitado: deteniendo ejecución${NC}"
            break
        fi
    fi
done

# ============================================================================
# RESUMEN FINAL
# ============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

if [ $OVERALL_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ TODOS LOS TESTS PASARON${NC}"
else
    echo -e "${RED}✗ ALGUNOS TESTS FALLARON${NC}"
fi

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

# Resumen por suite (solo si no está en quiet mode)
if [ "$QUIET_MODE" = false ]; then
    echo ""
    echo -e "${YELLOW}Resumen por suite:${NC}"

    for suite_key in "${SELECTED_SUITES[@]}"; do
        result="${SUITE_RESULTS[$suite_key]}"
        config="${TEST_SUITES[$suite_key]}"

        suite_name=$(echo "$config" | grep -oP 'name=\K[^;]+')
        suite_emoji=$(echo "$config" | grep -oP 'emoji=\K[^;]+')

        if [[ "$result" == "PASS" ]]; then
            echo -e "  ${GREEN}✓${NC} ${suite_emoji}  ${suite_name}"
        elif [[ "$result" == "FAIL" ]]; then
            echo -e "  ${RED}✗${NC} ${suite_emoji}  ${suite_name}"
        else
            echo -e "  ${YELLOW}⊘${NC} ${suite_emoji}  ${suite_name} (skipped)"
        fi
    done

    echo ""
    echo -e "${CYAN}Total:${NC} ${SUITES_PASSED} passed, ${SUITES_FAILED} failed"
fi

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

exit $OVERALL_RESULT
