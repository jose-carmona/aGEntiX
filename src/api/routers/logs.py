"""
Router de logs del sistema.

Proporciona endpoints para consultar logs de ejecuciones de agentes.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field

from src.api.routers.auth import verify_admin_token
from src.backoffice.settings import settings


router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


# ============================================================================
# Modelos
# ============================================================================


class LogError(BaseModel):
    """Información de error en un log"""

    type: str
    message: str
    stacktrace: Optional[str] = None


class LogEntryResponse(BaseModel):
    """Entrada de log individual"""

    id: str
    timestamp: str
    level: str
    component: str = "AgentExecutor"  # Por defecto
    agent: Optional[str] = None
    expediente_id: Optional[str] = None
    message: str
    context: Optional[dict] = None
    user_id: Optional[str] = None
    agent_run_id: Optional[str] = None
    duration_ms: Optional[int] = None
    error: Optional[LogError] = None


class LogsResponse(BaseModel):
    """Respuesta paginada de logs"""

    logs: List[LogEntryResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================================================
# Servicio de Logs
# ============================================================================


def read_all_logs(log_dir: Path) -> List[dict]:
    """
    Lee todos los archivos de log del directorio de agent_runs.

    Args:
        log_dir: Directorio base de logs

    Returns:
        Lista de logs parseados
    """
    all_logs = []

    if not log_dir.exists():
        return all_logs

    # Recorrer todos los subdirectorios (expedientes) y archivos de log
    for expediente_dir in log_dir.iterdir():
        if not expediente_dir.is_dir():
            continue

        for log_file in expediente_dir.glob("*.log"):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            log_entry = json.loads(line)
                            # Añadir ID único basado en archivo y línea
                            log_entry["id"] = f"{log_file.stem}-{line_num}"
                            all_logs.append(log_entry)
                        except json.JSONDecodeError:
                            # Ignorar líneas mal formadas
                            continue
            except Exception:
                # Ignorar archivos que no se puedan leer
                continue

    return all_logs


def filter_logs(
    logs: List[dict],
    level: Optional[str] = None,
    component: Optional[str] = None,
    agent: Optional[str] = None,
    expediente_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
) -> List[dict]:
    """
    Filtra logs según criterios.

    Args:
        logs: Lista de logs a filtrar
        level: Niveles de log separados por comas (ej: "INFO,ERROR")
        component: Componentes separados por comas
        agent: Agentes separados por comas
        expediente_id: ID de expediente (búsqueda parcial)
        date_from: Fecha desde
        date_to: Fecha hasta
        search: Texto de búsqueda en mensaje y metadata

    Returns:
        Lista de logs filtrados
    """
    filtered = logs

    # Filtro por nivel
    if level:
        levels = [l.strip().upper() for l in level.split(",")]
        filtered = [log for log in filtered if log.get("level", "").upper() in levels]

    # Filtro por componente
    if component:
        components = [c.strip() for c in component.split(",")]
        filtered = [log for log in filtered if log.get("component", "AgentExecutor") in components]

    # Filtro por agente (puede venir en metadata)
    if agent:
        agents = [a.strip() for a in agent.split(",")]
        filtered = [
            log
            for log in filtered
            if log.get("agent") in agents
            or (log.get("metadata") and log["metadata"].get("agent") in agents)
        ]

    # Filtro por expediente_id (búsqueda parcial case-insensitive)
    if expediente_id:
        exp_lower = expediente_id.lower()
        filtered = [
            log
            for log in filtered
            if log.get("expediente_id")
            and exp_lower in log["expediente_id"].lower()
        ]

    # Filtro por rango de fechas
    if date_from:
        filtered = [
            log
            for log in filtered
            if datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00")) >= date_from
        ]

    if date_to:
        filtered = [
            log
            for log in filtered
            if datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00")) <= date_to
        ]

    # Búsqueda de texto completo
    if search:
        search_lower = search.lower()
        filtered = [
            log
            for log in filtered
            if (
                search_lower in log.get("mensaje", "").lower()
                or (
                    log.get("metadata")
                    and search_lower in json.dumps(log["metadata"]).lower()
                )
                or (log.get("error") and search_lower in str(log.get("error")).lower())
            )
        ]

    return filtered


def map_log_to_response(log: dict) -> LogEntryResponse:
    """
    Mapea un log del formato interno al formato de respuesta.

    Args:
        log: Log en formato interno (del archivo)

    Returns:
        Log en formato de respuesta API
    """
    # Extraer información de error si existe en metadata
    error = None
    if log.get("metadata") and log["metadata"].get("error"):
        error_data = log["metadata"]["error"]
        error = LogError(
            type=error_data.get("type", "UnknownError"),
            message=error_data.get("message", ""),
            stacktrace=error_data.get("stacktrace"),
        )

    # Mapear log
    return LogEntryResponse(
        id=log["id"],
        timestamp=log["timestamp"],
        level=log.get("level", "INFO"),
        component=log.get("component", "AgentExecutor"),
        agent=log.get("metadata", {}).get("agent") if log.get("metadata") else None,
        expediente_id=log.get("expediente_id"),
        message=log.get("mensaje", ""),
        context=log.get("metadata"),
        agent_run_id=log.get("agent_run_id"),
        duration_ms=log.get("metadata", {}).get("duration_ms") if log.get("metadata") else None,
        error=error,
    )


# ============================================================================
# Endpoints
# ============================================================================


@router.get("", response_model=LogsResponse, dependencies=[Depends(verify_admin_token)])
async def get_logs(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(50, ge=1, le=500, description="Tamaño de página"),
    level: Optional[str] = Query(None, description="Niveles de log (separados por comas)"),
    component: Optional[str] = Query(None, description="Componentes (separados por comas)"),
    agent: Optional[str] = Query(None, description="Agentes (separados por comas)"),
    expediente_id: Optional[str] = Query(None, description="ID de expediente (búsqueda parcial)"),
    date_from: Optional[datetime] = Query(None, description="Fecha desde (ISO 8601)"),
    date_to: Optional[datetime] = Query(None, description="Fecha hasta (ISO 8601)"),
    search: Optional[str] = Query(None, description="Búsqueda de texto completo"),
):
    """
    Obtiene logs del sistema con filtros y paginación.

    Requiere autenticación con token de administrador.

    **Filtros disponibles:**
    - `level`: Niveles de log (INFO, WARNING, ERROR, CRITICAL, DEBUG) separados por comas
    - `component`: Componentes del sistema separados por comas
    - `agent`: Tipos de agente separados por comas
    - `expediente_id`: Búsqueda parcial por ID de expediente
    - `date_from`, `date_to`: Rango de fechas en formato ISO 8601
    - `search`: Búsqueda de texto en mensaje y contexto

    **Ejemplo:**
    ```
    GET /api/v1/logs?level=ERROR,CRITICAL&expediente_id=EXP-2024-001&page=1&page_size=50
    ```

    Returns:
        Respuesta paginada con logs filtrados
    """
    # Leer todos los logs
    log_dir = Path(settings.LOG_DIR)
    all_logs = read_all_logs(log_dir)

    # Filtrar logs
    filtered_logs = filter_logs(
        all_logs,
        level=level,
        component=component,
        agent=agent,
        expediente_id=expediente_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )

    # Ordenar por timestamp descendente (más reciente primero)
    filtered_logs.sort(
        key=lambda x: x.get("timestamp", ""), reverse=True
    )

    # Paginación
    total = len(filtered_logs)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_logs = filtered_logs[start_idx:end_idx]

    # Mapear a formato de respuesta
    response_logs = [map_log_to_response(log) for log in paginated_logs]

    return LogsResponse(
        logs=response_logs,
        total=total,
        page=page,
        page_size=page_size,
        has_more=end_idx < total,
    )
