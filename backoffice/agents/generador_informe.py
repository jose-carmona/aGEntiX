# backoffice/agents/generador_informe.py

from typing import Dict, Any
from .base import AgentMock
import json


class GeneradorInforme(AgentMock):
    """
    Agente mock que genera informes resumiendo el estado del expediente.

    Crea un informe estructurado con la información relevante.
    """

    async def execute(self) -> Dict[str, Any]:
        """
        Ejecuta la generación del informe.

        Returns:
            Resultado con el informe generado
        """
        self.logger.log("Iniciando generación de informe...")

        # 1. Consultar expediente
        self.logger.log(f"Consultando expediente {self.expediente_id}...")
        self._track_tool_use("consultar_expediente")

        result = await self.mcp_registry.call_tool("consultar_expediente", {
            "expediente_id": self.expediente_id
        })

        # Extraer contenido
        expediente_data = result.get("content", [{}])[0].get("text", "{}")
        expediente = json.loads(expediente_data) if isinstance(expediente_data, str) else expediente_data

        # 2. Extraer información relevante
        self.logger.log("Extrayendo información relevante...")

        solicitante = expediente.get("solicitante", {})
        datos = expediente.get("datos", {})
        documentos = expediente.get("documentos", [])
        historial = expediente.get("historial", [])

        # 3. Generar informe estructurado (mock)
        informe = {
            "expediente_id": self.expediente_id,
            "fecha_generacion": "2024-01-15",  # Mock
            "resumen": {
                "solicitante": solicitante.get("nombre", "N/A"),
                "estado": expediente.get("estado", "N/A"),
                "documentos_totales": len(documentos),
                "documentacion_valida": datos.get("documentacion_valida", False),
                "analisis_aprobado": datos.get("analisis_aprobado", False)
            },
            "documentos": [
                {
                    "tipo": doc.get("tipo", "N/A"),
                    "fecha_subida": doc.get("fecha_subida", "N/A")
                }
                for doc in documentos
            ],
            "eventos_recientes": len(historial)
        }

        self.logger.log(f"Informe generado con {len(informe['documentos'])} documentos")

        # 4. Guardar informe en datos del expediente
        self.logger.log("Guardando informe en expediente...")
        self._track_tool_use("actualizar_datos")

        await self.mcp_registry.call_tool("actualizar_datos", {
            "expediente_id": self.expediente_id,
            "campo": "datos.ultimo_informe",
            "valor": informe
        })

        # 5. Añadir anotación
        mensaje = f"Informe generado exitosamente con {len(documentos)} documentos analizados"
        self.logger.log(f"Añadiendo anotación: {mensaje}")
        self._track_tool_use("añadir_anotacion")

        await self.mcp_registry.call_tool("añadir_anotacion", {
            "expediente_id": self.expediente_id,
            "texto": mensaje
        })

        return {
            "completado": True,
            "mensaje": mensaje,
            "informe": informe,
            "datos_actualizados": {
                "datos.ultimo_informe": informe
            }
        }
