# backoffice/agents/redactor_situacion.py

"""
Agente Redactor de Situación - Genera Informes de Situación.

Analiza todos los documentos de un expediente y genera un informe
estructurado con el resumen de situación actual del expediente.

Este es el segundo agente real implementado con CrewAI (Paso 6.2).
"""

from .base_crewai import AgentCrewAI


class RedactorSituacion(AgentCrewAI):
    """
    Agente que genera Informes de Situación usando CrewAI + Anthropic.

    Flujo de ejecución:
    1. Usa herramienta MCP 'consultar_expediente' para obtener datos generales
    2. Usa 'listar_documentos' para obtener lista de documentos
    3. Usa 'obtener_texto_documento' para leer cada documento
    4. Analiza el historial del expediente
    5. LLM genera el informe en formato Markdown
    6. Usa 'crear_documento_desde_markdown' para guardar el informe

    La configuración (role, goal, backstory, task) se carga desde
    src/backoffice/config/agents.yaml

    Ejemplo de uso:
        agent = RedactorSituacion(
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
        #         "documento_id": "doc_informe_001",
        #         "resumen": "Informe generado con 3 documentos...",
        #         "documentos_analizados": 3,
        #         "eventos_historial": 5
        #     }
        # }
    """
    pass  # Toda la lógica está en AgentCrewAI + configuración YAML
