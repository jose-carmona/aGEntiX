# backoffice/agents/redactor_resolucion.py

"""
Agente LangGraph para redactar Resoluciones.

Genera documentos de resolución administrativa usando LangGraph ReAct,
accediendo a los datos del expediente mediante MCP.

Este es el primer agente implementado con LangGraph (Paso 11).
"""

from .base_langgraph import AgentLangGraph


class RedactorResolucion(AgentLangGraph):
    """
    Agente que genera Resoluciones usando LangGraph + Anthropic.

    Flujo de ejecución:
    1. Usa herramienta MCP 'consultar_expediente' para obtener datos
    2. Usa 'listar_documentos' para encontrar propuesta de resolución
    3. Usa 'obtener_texto_documento' para leer documentos relevantes
    4. LLM genera resolución formal basada en datos y propuesta
    5. Usa 'crear_documento_desde_markdown' para guardar la resolución
    6. Usa 'añadir_anotacion' para registrar la acción

    La configuración (system_prompt, task_prompt, tools) se carga desde
    src/backoffice/config/agents.yaml

    Ejemplo de uso:
        agent = RedactorResolucion(
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
        #         "documento_id": "...",
        #         "tipo_resolucion": "aprobacion",
        #         "resumen": "..."
        #     }
        # }
    """
    pass  # Toda la lógica está en AgentLangGraph + configuración YAML
