# backoffice/agents/redactor_propuesta_resolucion.py

"""
Agente Redactor de Propuesta de Resolución - Genera Propuestas de Resolución.

Lee la plantilla correspondiente al tipo de expediente, los datos del expediente
y el informe de situación previo para generar una Propuesta de Resolución formal.

Este es el tercer agente real implementado con CrewAI (Paso 9).
"""

from .base_real import AgentReal


class RedactorPropuestaResolucion(AgentReal):
    """
    Agente que genera Propuestas de Resolución usando CrewAI + Anthropic.

    Flujo de ejecución:
    1. Usa herramienta MCP 'consultar_expediente' para obtener datos y tipo
    2. Usa 'obtener_doc_documentacion' para obtener la plantilla del tipo
    3. Usa 'listar_documentos' para buscar el informe de situación
    4. Usa 'obtener_texto_documento' para leer el informe previo
    5. LLM genera la propuesta rellenando la plantilla
    6. Usa 'crear_documento_desde_markdown' para guardar la propuesta
    7. Usa 'añadir_anotacion' para registrar la acción

    La configuración (role, goal, backstory, task) se carga desde
    src/backoffice/config/agents.yaml

    Ejemplo de uso:
        agent = RedactorPropuestaResolucion(
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
        #         "completado": True,
        #         "documento_id": "DOC-123456",
        #         "tipo_expediente": "subvenciones",
        #         "tipo_resolucion": "aprobacion",
        #         "importe_concedido": 5000.00,
        #         "resumen": "Propuesta de resolución favorable...",
        #         "campos_rellenados": 18,
        #         "observaciones": null
        #     }
        # }
    """
    pass  # Toda la lógica está en AgentReal + configuración YAML
