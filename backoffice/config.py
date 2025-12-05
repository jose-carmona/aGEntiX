# backoffice/config.py

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración del back-office"""

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    # MCP Configuration
    MCP_CONFIG_PATH: str = "backoffice/config/mcp_servers.yaml"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs/agent_runs"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()
