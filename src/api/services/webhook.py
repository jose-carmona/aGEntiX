# api/services/webhook.py

"""
Servicio para envío de webhooks al BPMN.

Envía el resultado de la ejecución del agente al callback URL
proporcionado por el BPMN engine.
"""

import httpx
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


async def send_webhook(
    webhook_url: str,
    agent_run_id: str,
    result=None,
    error: Optional[Dict[str, str]] = None
) -> bool:
    """
    Envía resultado al webhook del BPMN.

    Args:
        webhook_url: URL del callback
        agent_run_id: ID de la ejecución
        result: AgentExecutionResult (si éxito)
        error: Dict con error (si fallo)

    Returns:
        True si envío exitoso, False si falló
    """

    # Construir payload
    payload = {
        "agent_run_id": agent_run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if error:
        # Caso de error
        payload["status"] = "failed"
        payload["success"] = False
        payload["error"] = error
    else:
        # Caso de éxito
        payload["status"] = "completed"
        payload["success"] = result.success

        if result.success:
            payload["resultado"] = result.resultado
            payload["herramientas_usadas"] = result.herramientas_usadas
        else:
            # Agente completó pero con error
            payload["error"] = {
                "codigo": result.error.codigo if result.error else "UNKNOWN",
                "mensaje": result.error.mensaje if result.error else "Error desconocido",
                "detalle": result.error.detalle if result.error else ""
            }

    # Enviar webhook
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Enviando webhook a {webhook_url} para {agent_run_id}")
            response = await client.post(
                webhook_url,
                json=payload,
                timeout=10.0,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            logger.info(
                f"Webhook enviado exitosamente: {agent_run_id} -> "
                f"{webhook_url} (status={response.status_code})"
            )
            return True

        except httpx.TimeoutException:
            logger.error(
                f"Timeout enviando webhook: {agent_run_id} -> {webhook_url}"
            )
            return False

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Error HTTP enviando webhook: {agent_run_id} -> {webhook_url} "
                f"(status={e.response.status_code})"
            )
            return False

        except Exception as e:
            logger.error(
                f"Error inesperado enviando webhook: {agent_run_id} -> {webhook_url} "
                f"({type(e).__name__}: {str(e)})"
            )
            return False


async def send_webhook_with_retry(
    webhook_url: str,
    agent_run_id: str,
    result=None,
    error: Optional[Dict[str, str]] = None,
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> Dict[str, Any]:
    """
    Envía webhook con exponential backoff retry.

    Args:
        webhook_url: URL del callback
        agent_run_id: ID de la ejecución
        result: AgentExecutionResult (si éxito)
        error: Dict con error (si fallo)
        max_retries: Número máximo de reintentos (default: 3)
        backoff_factor: Factor de backoff exponencial (default: 2.0)

    Returns:
        {
            "success": bool,
            "attempts": int,
            "final_status_code": Optional[int],
            "error": Optional[str]
        }

    Examples:
        >>> # Ejemplo con fallo y retry exitoso
        >>> result = await send_webhook_with_retry(
        ...     "https://example.com/callback",
        ...     "run-123",
        ...     result=execution_result
        ... )
        >>> print(result)
        {"success": True, "attempts": 2, "final_status_code": 200, "error": None}
    """
    import asyncio

    attempt_count = 0

    for attempt in range(max_retries):
        attempt_count = attempt + 1

        # Intentar enviar webhook
        success = await send_webhook(webhook_url, agent_run_id, result, error)

        if success:
            logger.info(
                f"Webhook enviado exitosamente después de {attempt_count} intento(s): "
                f"{agent_run_id} -> {webhook_url}"
            )
            return {
                "success": True,
                "attempts": attempt_count,
                "final_status_code": 200,
                "error": None
            }

        # Si no es el último intento, hacer backoff
        if attempt < max_retries - 1:
            delay = backoff_factor ** attempt
            logger.warning(
                f"Webhook falló (intento {attempt_count}/{max_retries}). "
                f"Reintentando en {delay}s..."
            )
            await asyncio.sleep(delay)

    # Todos los intentos fallaron
    logger.error(
        f"Webhook falló después de {max_retries} intentos: "
        f"{agent_run_id} -> {webhook_url}"
    )
    return {
        "success": False,
        "attempts": attempt_count,
        "final_status_code": None,
        "error": "Max retries exceeded"
    }
