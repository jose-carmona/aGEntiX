# backoffice/agents/analizador_subvencion.py

from typing import Dict, Any
from .base import AgentMock
import json


class AnalizadorSubvencion(AgentMock):
    """
    Agente mock que analiza solicitudes de subvención.

    Simula análisis de requisitos (mock: siempre aprueba).
    """

    async def execute(self) -> Dict[str, Any]:
        """
        Ejecuta el análisis de subvención.

        Returns:
            Resultado del análisis
        """
        self.logger.log("Iniciando análisis de subvención...")

        # 1. Consultar expediente
        self.logger.log(f"Consultando expediente {self.expediente_id}...")
        self._track_tool_use("consultar_expediente")

        result = await self.mcp_registry.call_tool("consultar_expediente", {
            "expediente_id": self.expediente_id
        })

        # Extraer contenido
        expediente_data = result.get("content", [{}])[0].get("text", "{}")
        expediente = json.loads(expediente_data) if isinstance(expediente_data, str) else expediente_data

        # 2. Analizar requisitos (lógica mock - siempre aprueba)
        solicitante = expediente.get("solicitante", {})
        self.logger.log(f"Analizando requisitos para solicitante {solicitante.get('nombre', 'Desconocido')}")

        # Mock: criterios simples
        criterios_cumplidos = {
            "documentacion_completa": expediente.get("datos", {}).get("documentacion_valida", False),
            "datos_correctos": True,  # Mock: siempre True
            "elegibilidad": True  # Mock: siempre True
        }

        aprobado = all(criterios_cumplidos.values())

        self.logger.log(f"Criterios evaluados: {criterios_cumplidos}")
        self.logger.log(f"Resultado del análisis: {'APROBADO' if aprobado else 'RECHAZADO'}")

        # 3. Actualizar estado
        self.logger.log(f"Actualizando campo datos.analisis_aprobado = {aprobado}")
        self._track_tool_use("actualizar_datos")

        await self.mcp_registry.call_tool("actualizar_datos", {
            "expediente_id": self.expediente_id,
            "campo": "datos.analisis_aprobado",
            "valor": aprobado
        })

        # 4. Añadir anotación
        mensaje = f"Análisis completado: {'APROBADO' if aprobado else 'RECHAZADO'}"
        self.logger.log(f"Añadiendo anotación: {mensaje}")
        self._track_tool_use("añadir_anotacion")

        await self.mcp_registry.call_tool("añadir_anotacion", {
            "expediente_id": self.expediente_id,
            "texto": mensaje
        })

        return {
            "completado": True,
            "mensaje": mensaje,
            "aprobado": aprobado,
            "criterios": criterios_cumplidos,
            "datos_actualizados": {
                "datos.analisis_aprobado": aprobado
            }
        }
