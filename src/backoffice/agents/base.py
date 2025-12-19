# backoffice/agents/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from ..mcp.registry import MCPClientRegistry
from ..logging.audit_logger import AuditLogger


class AgentMock(ABC):
    """
    Clase base para agentes mock.

    Los agentes mock simulan el comportamiento de agentes reales
    siguiendo un script predefinido.
    """

    def __init__(
        self,
        expediente_id: str,
        tarea_id: str,
        run_id: str,
        mcp_registry: MCPClientRegistry,
        logger: AuditLogger
    ):
        """
        Inicializa el agente mock.

        Args:
            expediente_id: ID del expediente a procesar
            tarea_id: ID de la tarea BPMN
            run_id: ID único de esta ejecución
            mcp_registry: Registry de clientes MCP para routing
            logger: Logger de auditoría
        """
        self.expediente_id = expediente_id
        self.tarea_id = tarea_id
        self.run_id = run_id
        self.mcp_registry = mcp_registry
        self.logger = logger
        self._tools_used: List[str] = []

    @abstractmethod
    async def execute(self) -> Dict[str, Any]:
        """
        Ejecuta el comportamiento del agente mock.

        Returns:
            Diccionario con el resultado de la ejecución
        """
        pass

    def _track_tool_use(self, tool_name: str):
        """Registra el uso de una herramienta"""
        if tool_name not in self._tools_used:
            self._tools_used.append(tool_name)

    def get_tools_used(self) -> List[str]:
        """Retorna lista de herramientas usadas"""
        return self._tools_used.copy()
