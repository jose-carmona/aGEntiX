#!/bin/bash
set -e

echo "🚀 Configurando entorno de desarrollo aGEntiX..."

# Actualizar pip
echo "📦 Actualizando pip..."
python -m pip install --upgrade pip

# Instalar herramientas de desarrollo global
echo "🔧 Instalando herramientas de desarrollo..."
pip install --user black flake8 isort pytest pytest-asyncio mypy ruff

# Instalar dependencias del proyecto MCP Mock
if [ -f "src/mcp_mock/mcp_expedientes/requirements.txt" ]; then
    echo "📚 Instalando dependencias de mcp-expedientes..."
    pip install -r src/mcp_mock/mcp_expedientes/requirements.txt
fi

# Instalar MCP CLI tools (si están disponibles)
echo "🛠️ Instalando herramientas MCP..."
npm install -g @modelcontextprotocol/inspector || echo "⚠️ MCP Inspector no disponible, continuando..."

# Configurar git (si no está configurado)
if [ -z "$(git config user.name)" ]; then
    echo "⚙️ Configurando git..."
    git config --global --add safe.directory /workspaces/aGEntiX
fi

# Crear directorios necesarios si no existen
echo "📁 Verificando estructura de directorios..."
mkdir -p src/mcp_mock/mcp_expedientes/data/expedientes
mkdir -p src/mcp_mock/mcp_expedientes/data/documentos

# Hacer ejecutables los scripts
echo "🔐 Configurando permisos de scripts..."
chmod +x src/mcp_mock/mcp_expedientes/generate_token.py || true
chmod +x src/mcp_mock/mcp_expedientes/server_stdio.py || true
chmod +x src/mcp_mock/mcp_expedientes/simulate_bpmn.py || true

# Mensaje de éxito
echo ""
echo "✅ Entorno de desarrollo configurado correctamente!"
echo ""
echo "📋 Próximos pasos:"
echo "   1. Revisar la documentación en /doc/index.md"
echo "   2. Probar el servidor MCP: cd src/mcp_mock/mcp_expedientes"
echo "   3. Ejecutar tests: ./run-tests.sh"
echo ""
echo "🎉 ¡Listo para desarrollar!"
