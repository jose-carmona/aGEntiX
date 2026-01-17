# backoffice/agents/agente_test_simple.py

"""
Agente de prueba E2E extremadamente simple.

Solo responde "OK" para verificar que todo el pipeline funciona:
- API REST
- Carga de agentes
- Invocación CrewAI
- Respuesta del agente

No usa herramientas MCP ni requiere permisos especiales.
"""

from .base_real import AgentCrewAI


class AgenteTestSimple(AgentCrewAI):
    """
    Agente de prueba que solo responde "OK".

    Útil para:
    - Pruebas de despliegue
    - Verificación de conectividad
    - Validación del pipeline completo
    - Health check avanzado
    - Debugging de infraestructura

    La configuración se carga desde src/backoffice/config/agents.yaml
    """
    pass  # Toda la lógica está en AgentCrewAI + configuración YAML
