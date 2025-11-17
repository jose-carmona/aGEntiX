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
if [ -f "mcp-mock/mcp-expedientes/requirements.txt" ]; then
    echo "📚 Instalando dependencias de mcp-expedientes..."
    pip install -r mcp-mock/mcp-expedientes/requirements.txt
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
mkdir -p mcp-mock/mcp-expedientes/data/expedientes
mkdir -p mcp-mock/mcp-expedientes/data/documentos

# Hacer ejecutables los scripts
echo "🔐 Configurando permisos de scripts..."
chmod +x mcp-mock/mcp-expedientes/generate_token.py || true
chmod +x mcp-mock/mcp-expedientes/server_stdio.py || true
chmod +x mcp-mock/mcp-expedientes/simulate_bpmn.py || true
chmod +x mcp-mock/mcp-expedientes/quick_test.sh || true

# Mensaje de éxito
echo ""
echo "✅ Entorno de desarrollo configurado correctamente!"
echo ""
echo "📋 Próximos pasos:"
echo "   1. Revisar la documentación en /doc/index.md"
echo "   2. Probar el servidor MCP: cd mcp-mock/mcp-expedientes && ./quick_test.sh"
echo "   3. Ejecutar tests: cd mcp-mock/mcp-expedientes && pytest"
echo ""
echo "🎉 ¡Listo para desarrollar!"
