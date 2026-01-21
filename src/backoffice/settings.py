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

    # Redis Configuration (Paso 12 - Escalado Horizontal)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # Celery Configuration (Paso 12 - Escalado Horizontal)
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_TIME_LIMIT: int = 3600  # 1 hora max por tarea
    CELERY_TASK_TRACK_STARTED: bool = True

    # Feature Flags
    USE_CELERY: bool = False  # False = BackgroundTasks, True = Celery

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignorar variables extra (ej: VITE_* para frontend)


# Instancia global de configuración
settings = Settings()


def get_settings() -> Settings:
    """Retorna la instancia de configuración."""
    return settings
