#!/bin/bash

# Script de setup para el frontend de aGEntiX

echo "=========================================="
echo "  aGEntiX Dashboard - Setup Frontend"
echo "=========================================="
echo ""

# Verificar si Node.js está instalado
if ! command -v node &> /dev/null
then
    echo "❌ Error: Node.js no está instalado"
    echo "Por favor instala Node.js >= 18.x desde https://nodejs.org/"
    exit 1
fi

# Verificar versión de Node.js
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Error: Node.js versión $NODE_VERSION detectada"
    echo "Se requiere Node.js >= 18.x"
    exit 1
fi

echo "✅ Node.js $(node -v) detectado"
echo "✅ npm $(npm -v) detectado"
echo ""

# Instalar dependencias
echo "📦 Instalando dependencias..."
npm install

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Dependencias instaladas correctamente"
    echo ""
    echo "=========================================="
    echo "  Setup completado exitosamente"
    echo "=========================================="
    echo ""
    echo "Para iniciar el servidor de desarrollo:"
    echo "  npm run dev"
    echo ""
    echo "La aplicación estará disponible en:"
    echo "  http://localhost:5173"
    echo ""
else
    echo ""
    echo "❌ Error al instalar dependencias"
    exit 1
fi
