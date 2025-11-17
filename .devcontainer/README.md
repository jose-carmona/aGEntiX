# Dev Container - aGEntiX

Este proyecto está configurado para usar **Dev Containers** de VS Code, proporcionando un entorno de desarrollo consistente y completamente configurado.

## Requisitos Previos

1. **Docker Desktop** instalado y ejecutándose
   - [Descargar para macOS](https://www.docker.com/products/docker-desktop/)
   - [Descargar para Windows](https://www.docker.com/products/docker-desktop/)
   - [Descargar para Linux](https://docs.docker.com/desktop/install/linux-install/)

2. **Visual Studio Code** con la extensión **Dev Containers**
   - Instalar VS Code: https://code.visualstudio.com/
   - Instalar extensión: https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers

## Inicio Rápido

### Opción 1: Abrir en Dev Container (Recomendado)

1. Abre el proyecto en VS Code
2. VS Code detectará la configuración de Dev Container
3. Haz clic en el botón **"Reopen in Container"** que aparece en la notificación
4. Espera a que el container se construya e inicialice (primera vez ~5-10 min)
5. ¡Listo! El entorno estará completamente configurado

### Opción 2: Comando Manual

1. Abre VS Code
2. Presiona `Cmd+Shift+P` (macOS) o `Ctrl+Shift+P` (Windows/Linux)
3. Escribe: `Dev Containers: Reopen in Container`
4. Selecciona la opción y presiona Enter

### Opción 3: Desde Terminal

```bash
# Desde el directorio del proyecto
code .
# Luego usa el Command Palette para abrir en container
```

## ¿Qué se Instala Automáticamente?

El Dev Container incluye:

### Entorno Base
- **Python 3.11** (con pip, venv)
- **Node.js LTS** (para herramientas MCP)
- **Git** (configuración automática)
- **Zsh + Oh My Zsh** (shell mejorada)

### Herramientas Python
- `black` - Formateador de código
- `flake8` - Linter
- `isort` - Organizador de imports
- `pytest` - Framework de testing
- `mypy` - Type checker
- `ruff` - Linter moderno ultra-rápido

### Dependencias del Proyecto
- SDK MCP oficial (`mcp`)
- JWT handling (`pyjwt`)
- Web framework (`starlette`, `uvicorn`)
- Testing (`pytest-asyncio`)
- Todas las dependencias de `mcp-mock/mcp-expedientes/requirements.txt`

### Herramientas MCP
- `@modelcontextprotocol/inspector` - Inspector web para servidores MCP

### Extensiones VS Code

**Python Development:**
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Black Formatter (ms-python.black-formatter)
- isort (ms-python.isort)
- Flake8 (ms-python.flake8)
- Ruff (charliermarsh.ruff)

**Git & Version Control:**
- GitLens (eamodio.gitlens)
- Git History (donjayamanne.githistory)
- GitHub Pull Requests (github.vscode-pull-request-github)

**Editing:**
- Markdown All in One (yzhang.markdown-all-in-one)
- Markdown Lint (davidanson.vscode-markdownlint)
- YAML (redhat.vscode-yaml)
- TOML (tamasfe.even-better-toml)
- Prettier (esbenp.prettier-vscode)

## Configuración Automática

El script `post-create.sh` se ejecuta automáticamente después de crear el container:

1. ✅ Actualiza pip
2. ✅ Instala herramientas de desarrollo
3. ✅ Instala dependencias del proyecto
4. ✅ Instala MCP Inspector
5. ✅ Configura Git
6. ✅ Crea directorios necesarios
7. ✅ Configura permisos de scripts

## Puertos Expuestos

El Dev Container expone automáticamente estos puertos:

- **8000**: Servidor HTTP MCP Mock
- **8080**: Servidor auxiliar
- **5173**: MCP Inspector (abre navegador automáticamente)

## Verificar Instalación

Una vez dentro del Dev Container, ejecuta:

```bash
# Verificar Python
python --version
# Debería mostrar: Python 3.11.x

# Verificar Node
node --version
# Debería mostrar: v20.x.x (LTS)

# Verificar dependencias MCP
python -c "import mcp; print('MCP instalado correctamente')"

# Ejecutar tests
cd mcp-mock/mcp-expedientes
pytest
```

## Quick Start - Probar el MCP Mock

```bash
# Ir al directorio del servidor
cd mcp-mock/mcp-expedientes

# Ejecutar test rápido
./quick_test.sh

# O ejecutar tests completos
pytest -v

# O iniciar servidor HTTP
python -m uvicorn server_http:app --reload --port 8000
```

## Workspace Settings

El Dev Container configura automáticamente VS Code con:

- **Formateo automático** al guardar (Black)
- **Organización de imports** al guardar (isort)
- **Linting en tiempo real** (Flake8 + Ruff)
- **Testing con pytest** integrado
- **Type checking** con Pylance

## Persistencia de Datos

- El código fuente está montado desde tu sistema local
- Los cambios se sincronizan automáticamente
- La configuración de Git se preserva
- Los archivos `.git` se mantienen enlazados

## Troubleshooting

### El container no inicia
```bash
# Reconstruir el container
Cmd+Shift+P → "Dev Containers: Rebuild Container"
```

### Dependencias no instaladas
```bash
# Re-ejecutar script de post-creación
.devcontainer/post-create.sh
```

### Permisos de scripts
```bash
# Hacer ejecutables manualmente
chmod +x mcp-mock/mcp-expedientes/*.py
chmod +x mcp-mock/mcp-expedientes/*.sh
```

### Docker Desktop no responde
```bash
# Reiniciar Docker Desktop y volver a abrir en container
```

## Personalización

Puedes personalizar el Dev Container editando:

- `.devcontainer/devcontainer.json` - Configuración principal
- `.devcontainer/post-create.sh` - Script de inicialización

Después de modificar, reconstruye el container:
```
Cmd+Shift+P → "Dev Containers: Rebuild Container"
```

## Recursos Adicionales

- [Documentación oficial Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)
- [Especificación Dev Container](https://containers.dev/)
- [Dev Container Features](https://containers.dev/features)

## Soporte

Si encuentras problemas con el Dev Container:

1. Revisa los logs: `View → Output → Dev Containers`
2. Reconstruye el container
3. Verifica que Docker Desktop esté ejecutándose
4. Consulta la documentación en `/doc/index.md`
