# api/main.py

"""
Aplicación principal de la API REST de aGEntiX.

FastAPI app que expone endpoints para:
- Ejecución asíncrona de agentes
- Consulta de estado
- Health check
- Métricas Prometheus
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from .routers import agent, health
from backoffice.settings import settings

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación.

    Startup: Inicialización y configuración
    Shutdown: Limpieza de recursos
    """
    # Startup
    logger.info("=" * 60)
    logger.info("aGEntiX API iniciando...")
    logger.info(f"Versión: 1.0.0")
    logger.info(f"MCP Config: {settings.MCP_CONFIG_PATH}")
    logger.info(f"Log Level: {settings.LOG_LEVEL}")
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("aGEntiX API cerrando...")


# Crear app FastAPI
app = FastAPI(
    title="aGEntiX API",
    description="API REST para ejecución de agentes IA en GEX",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configurar CORS
cors_origins = settings.CORS_ORIGINS.split(",")
logger.info(f"Configurando CORS para orígenes: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(
    agent.router,
    prefix="/api/v1/agent",
    tags=["Agent"]
)

app.include_router(
    health.router,
    tags=["Health"]
)

# Configurar Prometheus
logger.info("Configurando métricas Prometheus")
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get(
    "/",
    tags=["Root"],
    summary="Información de la API",
    description="Retorna información básica de la API"
)
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "name": "aGEntiX API",
        "version": "1.0.0",
        "description": "API REST para ejecución de agentes IA en GEX",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
        "endpoints": {
            "execute_agent": "POST /api/v1/agent/execute",
            "agent_status": "GET /api/v1/agent/status/{agent_run_id}"
        }
    }
