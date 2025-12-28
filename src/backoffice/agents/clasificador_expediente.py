# backoffice/agents/clasificador_expediente.py

"""
Primer agente real: Clasificador de Expedientes.

Clasifica un expediente según su tipo y urgencia usando IA,
accediendo a los datos reales del expediente mediante MCP.

Este es el agente más simple implementado con CrewAI (Paso 6.1).
"""

from .base_real import AgentReal


class ClasificadorExpediente(AgentReal):
    """
    Agente que clasifica expedientes usando CrewAI + Anthropic.

    Flujo de ejecución:
    1. Usa herramienta MCP 'consultar_expediente' para obtener datos
    2. LLM analiza los datos y determina clasificación
    3. Retorna clasificación con justificación

    La configuración (role, goal, backstory, task) se carga desde
    src/backoffice/config/agents.yaml

    Ejemplo de uso:
        agent = ClasificadorExpediente(
            expediente_id="EXP-2024-001",
            tarea_id="TASK-001",
            run_id="RUN-001",
            mcp_registry=registry,
            logger=logger
        )
        result = await agent.execute()
        # result = {
        #     "completado": True,
        #     "mensaje": "...",
        #     "datos_actualizados": {
        #         "tipo_expediente": "subvención",
        #         "urgencia": "media",
        #         "justificacion": "..."
        #     }
        # }
    """
    pass  # Toda la lógica está en AgentReal + configuración YAML
