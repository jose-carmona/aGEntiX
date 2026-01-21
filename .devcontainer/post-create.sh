#!/bin/bash
set -e

echo "🚀 Instalando Claude Code"
curl -fsSL https://claude.ai/install.sh | bash

echo "🚀 Configurando entorno de desarrollo aGEntiX..."

# Actualizar pip
echo "📦 Actualizando pip..."
python -m pip install --upgrade pip

# Instalar herramientas de desarrollo global
echo "🔧 Instalando herramientas de desarrollo..."
pip install --user black flake8 isort pytest pytest-asyncio mypy ruff

# Instalar dependencias principales del proyecto
echo "📚 Instalando dependencias del proyecto..."
pip install -r requirements.txt

# Instalar dependencias del proyecto MCP Mock
if [ -f "src/mcp_mock/mcp_expedientes/requirements.txt" ]; then
    echo "📚 Instalando dependencias de mcp-expedientes..."
    pip install -r src/mcp_mock/mcp_expedientes/requirements.txt
fi

# Configurar git (si no está configurado)
if [ -z "$(git config user.name)" ]; then
    echo "⚙️ Configurando git..."
    git config --global --add safe.directory /workspaces/aGEntiX
fi

# Instalar dependencias de Celery y Redis (Paso 12)
echo "📦 Instalando dependencias de Celery/Redis..."
pip install celery[redis]>=5.3.4 redis>=5.0.1 flower>=2.0.1

# Verificar conexión a Redis
echo "🔍 Verificando conexión a Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis conectado correctamente"
else
    echo "⚠️ Redis no disponible - se iniciará con docker-compose"
fi

# Mensaje de éxito
echo ""
echo "✅ Entorno de desarrollo configurado correctamente!"
echo ""
echo "🔧 Comandos Celery (Paso 12):"
echo "   - Worker: celery -A backoffice.celery_app worker --loglevel=info"
echo "   - Flower: celery -A backoffice.celery_app flower --port=5555"
echo "   - Redis CLI: redis-cli"
echo ""
echo "🎉 ¡Listo para desarrollar!"
