#!/bin/bash
#
# Script de prueba rápida del servidor MCP Mock de Expedientes
#
# Este script demuestra el uso básico del servidor.
#

set -e

echo "========================================"
echo "MCP Mock de Expedientes - Prueba Rápida"
echo "========================================"
echo ""

# Configurar variables de entorno
export JWT_SECRET="test-secret-key"

# 1. Generar token JWT
echo "1. Generando token JWT para EXP-2024-001..."
TOKEN=$(python generate_token.py --exp-id EXP-2024-001 --formato raw)
echo "   ✓ Token generado"
echo ""

# 2. Mostrar información del token
echo "2. Información del token:"
python generate_token.py --decode "$TOKEN" | head -20
echo ""

# 3. Simular invocación BPMN
echo "3. Simulando invocación BPMN..."
python simulate_bpmn.py --exp-id EXP-2024-001 --prompt "Validar documentación del expediente"
echo ""

# 4. Instrucciones para ejecutar servidor
echo "========================================"
echo "Próximos pasos"
echo "========================================"
echo ""
echo "Para ejecutar el servidor en modo stdio:"
echo "  export MCP_JWT_TOKEN='$TOKEN'"
echo "  python server_stdio.py"
echo ""
echo "Para ejecutar el servidor HTTP:"
echo "  uvicorn server_http:app --reload --port 8000"
echo ""
echo "Para ejecutar los tests:"
echo "  pytest -v"
echo ""
