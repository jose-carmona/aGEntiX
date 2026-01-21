FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Instalar Node.js LTS para MCP Inspector y frontend
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs

# Instalar redis-tools para debugging y jq para configuración
RUN apt-get update && apt-get install -y \
    redis-tools \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Configurar pip
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1

# Crear directorios para configuración de Claude Code
# Estos directorios serán sobrescritos por los mounts del host
RUN mkdir -p /home/vscode/.claude \
    && mkdir -p /home/vscode/.local/share/claude \
    && chown -R vscode:vscode /home/vscode/.claude \
    && chown -R vscode:vscode /home/vscode/.local
