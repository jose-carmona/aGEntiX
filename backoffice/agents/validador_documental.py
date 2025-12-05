# backoffice/agents/validador_documental.py

from typing import Dict, Any
from .base import AgentMock


class ValidadorDocumental(AgentMock):
    """
    Agente mock que valida documentación de expedientes.

    Verifica que todos los documentos requeridos estén presentes.
    """

    async def execute(self) -> Dict[str, Any]:
        """
        Ejecuta la validación de documentos.

        Returns:
            Resultado de la validación
        """
        self.logger.log("Iniciando validación de documentos...")

        # 1. Consultar expediente (llamada real a MCP vía registry)
        self.logger.log(f"Consultando expediente {self.expediente_id}...")
        self._track_tool_use("consultar_expediente")

        result = await self.mcp_registry.call_tool("consultar_expediente", {
            "expediente_id": self.expediente_id
        })

        # Extraer contenido del resultado MCP
        expediente_data = result.get("content", [{}])[0].get("text", "{}")
        import json
        expediente = json.loads(expediente_data) if isinstance(expediente_data, str) else expediente_data

        # 2. Analizar documentos (lógica mock)
        documentos = expediente.get("documentos", [])
        self.logger.log(f"Documentos encontrados: {len(documentos)}")

        documentos_requeridos = ["SOLICITUD", "IDENTIFICACION", "BANCARIO"]
        documentos_presentes = [doc["tipo"] for doc in documentos]

        validacion_ok = all(doc_tipo in documentos_presentes for doc_tipo in documentos_requeridos)

        if validacion_ok:
            self.logger.log("Todos los documentos requeridos están presentes")
        else:
            faltantes = set(documentos_requeridos) - set(documentos_presentes)
            self.logger.log(f"Faltan documentos: {faltantes}")

        # 3. Actualizar expediente (llamada real a MCP vía registry)
        self.logger.log(f"Actualizando campo datos.documentacion_valida = {validacion_ok}")
        self._track_tool_use("actualizar_datos")

        await self.mcp_registry.call_tool("actualizar_datos", {
            "expediente_id": self.expediente_id,
            "campo": "datos.documentacion_valida",
            "valor": validacion_ok
        })

        # 4. Añadir anotación (llamada real a MCP vía registry)
        mensaje = "Documentación validada correctamente" if validacion_ok else "Documentación incompleta"
        self.logger.log(f"Añadiendo anotación al historial: {mensaje}")
        self._track_tool_use("añadir_anotacion")

        await self.mcp_registry.call_tool("añadir_anotacion", {
            "expediente_id": self.expediente_id,
            "texto": mensaje
        })

        return {
            "completado": True,
            "mensaje": mensaje,
            "datos_actualizados": {
                "datos.documentacion_valida": validacion_ok
            }
        }
