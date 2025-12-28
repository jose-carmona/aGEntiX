# backoffice/config.py

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración del back-office"""

    # JWT - Firma y algoritmo
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    # JWT - Validación de claims
    JWT_EXPECTED_ISSUER: str = "agentix-bpmn"
    JWT_EXPECTED_SUBJECT: str = "Automático"
    JWT_REQUIRED_AUDIENCE: str = "agentix-mcp-expedientes"

    # MCP Configuration
    MCP_CONFIG_PATH: str = str(Path(__file__).parent / "config" / "mcp_servers.yaml")

    # Agents Configuration (Paso 6)
    AGENTS_CONFIG_PATH: str = str(Path(__file__).parent / "config" / "agents.yaml")

    # Anthropic API (Paso 6 - Agentes IA)
    ANTHROPIC_API_KEY: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs/agent_runs"

    # API Configuration (Paso 2)
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    API_WORKERS: int = 4
    API_RELOAD: bool = False

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    # Admin Authentication (Paso 3 - Frontend Dashboard)
    API_ADMIN_TOKEN: str = "change-me-in-production"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignorar variables extra (ej: VITE_* para frontend)


# Instancia global de configuración
settings = Settings()


def get_settings() -> Settings:
    """Retorna la instancia de configuración."""
    return settings
