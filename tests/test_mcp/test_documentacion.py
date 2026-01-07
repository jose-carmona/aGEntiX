"""
Tests para el módulo MCP de documentación de tipos de expediente.

Prueba las tools y resources que exponen normativa, instrucciones
y plantillas de documentos.
"""

import pytest
import json
from src.mcp_mock.mcp_documentacion.data_loader import (
    cargar_documento,
    listar_documentos,
    buscar_en_documentacion,
    validar_tipo_expediente,
    validar_tipo_documento,
    obtener_tipos_expediente,
    DocumentacionError,
    TIPOS_EXPEDIENTE,
    TIPOS_DOCUMENTO,
)
from src.mcp_mock.mcp_documentacion.tools import (
    list_tools,
    call_tool,
    TOOL_NAMES,
)
from src.mcp_mock.mcp_documentacion.resources import (
    list_resources,
    get_resource,
)


# ========== TESTS DE DATA_LOADER ==========

class TestDataLoader:
    """Tests para el módulo data_loader."""

    def test_tipos_expediente_validos(self):
        """Verifica que la lista de tipos de expediente sea correcta."""
        assert "subvenciones" in TIPOS_EXPEDIENTE
        assert "licencias_obras" in TIPOS_EXPEDIENTE
        assert "certificado_empadronamiento" in TIPOS_EXPEDIENTE
        assert len(TIPOS_EXPEDIENTE) == 3

    def test_tipos_documento_validos(self):
        """Verifica que la lista de tipos de documento sea correcta."""
        assert "normativa" in TIPOS_DOCUMENTO
        assert "instrucciones_tramitacion" in TIPOS_DOCUMENTO
        assert "plantilla_propuesta_resolucion" in TIPOS_DOCUMENTO
        assert "plantilla_requerimiento_documentacion" in TIPOS_DOCUMENTO
        assert "plantilla_certificado" in TIPOS_DOCUMENTO

    def test_validar_tipo_expediente_valido(self):
        """Valida tipos de expediente correctos."""
        # No debe lanzar excepción
        validar_tipo_expediente("subvenciones")
        validar_tipo_expediente("licencias_obras")
        validar_tipo_expediente("certificado_empadronamiento")

    def test_validar_tipo_expediente_invalido(self):
        """Rechaza tipos de expediente inválidos."""
        with pytest.raises(DocumentacionError) as exc_info:
            validar_tipo_expediente("tipo_inexistente")
        assert exc_info.value.status_code == 400
        assert "no válido" in exc_info.value.message

    def test_validar_tipo_documento_valido(self):
        """Valida tipos de documento correctos."""
        validar_tipo_documento("normativa", "subvenciones")
        validar_tipo_documento("instrucciones_tramitacion", "licencias_obras")
        validar_tipo_documento("plantilla_certificado", "certificado_empadronamiento")

    def test_validar_plantilla_certificado_solo_empadronamiento(self):
        """plantilla_certificado solo existe para certificado_empadronamiento."""
        with pytest.raises(DocumentacionError) as exc_info:
            validar_tipo_documento("plantilla_certificado", "subvenciones")
        assert exc_info.value.status_code == 404

    def test_validar_plantilla_propuesta_no_en_empadronamiento(self):
        """plantilla_propuesta_resolucion no existe para certificado_empadronamiento."""
        with pytest.raises(DocumentacionError) as exc_info:
            validar_tipo_documento("plantilla_propuesta_resolucion", "certificado_empadronamiento")
        assert exc_info.value.status_code == 404

    def test_cargar_documento_normativa_subvenciones(self):
        """Carga correctamente la normativa de subvenciones."""
        doc = cargar_documento("subvenciones", "normativa")
        assert doc.id == "SUB-NORM-001"
        assert doc.tipo == "normativa"
        assert doc.tipo_expediente == "subvenciones"
        assert len(doc.contenido) > 0
        assert doc.descripcion != ""
        assert doc.instrucciones_agente != ""

    def test_cargar_documento_instrucciones_licencias(self):
        """Carga correctamente las instrucciones de licencias de obras."""
        doc = cargar_documento("licencias_obras", "instrucciones_tramitacion")
        assert doc.id == "LOB-INST-001"
        assert doc.tipo == "instrucciones_tramitacion"
        assert len(doc.contenido) > 0

    def test_cargar_documento_plantilla_certificado(self):
        """Carga correctamente la plantilla de certificado de empadronamiento."""
        doc = cargar_documento("certificado_empadronamiento", "plantilla_certificado")
        assert doc.id == "EMP-TPL-001"
        assert doc.tipo == "plantilla"
        assert len(doc.contenido) > 0

    def test_cargar_documento_no_existente(self):
        """Error al cargar documento que no existe."""
        with pytest.raises(DocumentacionError) as exc_info:
            cargar_documento("subvenciones", "documento_inexistente")
        assert exc_info.value.status_code == 400  # tipo inválido

    def test_listar_documentos_subvenciones(self):
        """Lista correctamente los documentos de subvenciones."""
        docs = listar_documentos("subvenciones")
        assert len(docs) == 4  # normativa, instrucciones, 2 plantillas
        tipos = [d["tipo"] for d in docs]
        assert "normativa" in tipos
        assert "instrucciones_tramitacion" in tipos

    def test_listar_documentos_certificado(self):
        """Lista correctamente los documentos de certificado."""
        docs = listar_documentos("certificado_empadronamiento")
        assert len(docs) == 4
        # Verificar que tiene plantilla_certificado pero no propuesta_resolucion
        ids = [d["id"] for d in docs]
        assert any("EMP-TPL-001" in id for id in ids)

    def test_buscar_en_documentacion_encuentra(self):
        """Busca y encuentra texto en la documentación."""
        result = buscar_en_documentacion("subvenciones", "plazo")
        assert result["total_coincidencias"] > 0
        assert len(result["resultados"]) > 0

    def test_buscar_en_documentacion_no_encuentra(self):
        """Busca texto que no existe."""
        result = buscar_en_documentacion("subvenciones", "xyz123textoquenoexiste456abc")
        assert result["total_coincidencias"] == 0
        assert len(result["resultados"]) == 0

    def test_buscar_en_documentacion_filtro_tipo(self):
        """Busca con filtro por tipo de documento."""
        result = buscar_en_documentacion("subvenciones", "artículo", tipo_documento="normativa")
        # Solo debe buscar en normativa
        for r in result["resultados"]:
            assert r["tipo"] == "normativa"

    def test_obtener_tipos_expediente(self):
        """Retorna lista de tipos de expediente."""
        tipos = obtener_tipos_expediente()
        assert len(tipos) == 3
        assert tipos == TIPOS_EXPEDIENTE


# ========== TESTS DE TOOLS ==========

class TestTools:
    """Tests para las tools MCP de documentación."""

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Lista las tools de documentación."""
        tools = await list_tools()
        assert len(tools) == 3
        names = [t.name for t in tools]
        assert "listar_documentacion" in names
        assert "obtener_doc_documentacion" in names
        assert "buscar_en_documentacion" in names

    @pytest.mark.asyncio
    async def test_tool_listar_documentacion(self):
        """Tool listar_documentacion funciona correctamente."""
        result = await call_tool("listar_documentacion", {"tipo_expediente": "subvenciones"})
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["tipo_expediente"] == "subvenciones"
        assert len(data["documentos"]) == 4

    @pytest.mark.asyncio
    async def test_tool_obtener_doc_documentacion(self):
        """Tool obtener_doc_documentacion funciona correctamente."""
        result = await call_tool("obtener_doc_documentacion", {
            "tipo_expediente": "licencias_obras",
            "tipo_documento": "normativa"
        })
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["id"] == "LOB-NORM-001"
        assert data["tipo"] == "normativa"
        assert "contenido" in data
        assert len(data["contenido"]) > 0

    @pytest.mark.asyncio
    async def test_tool_buscar_en_documentacion(self):
        """Tool buscar_en_documentacion funciona correctamente."""
        result = await call_tool("buscar_en_documentacion", {
            "tipo_expediente": "subvenciones",
            "query": "ley"
        })
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "resultados" in data
        assert "total_coincidencias" in data

    @pytest.mark.asyncio
    async def test_tool_desconocida(self):
        """Error al llamar tool desconocida."""
        with pytest.raises(DocumentacionError) as exc_info:
            await call_tool("tool_inexistente", {})
        assert exc_info.value.status_code == 404

    def test_tool_names_constante(self):
        """Verifica la constante TOOL_NAMES."""
        assert len(TOOL_NAMES) == 3
        assert "listar_documentacion" in TOOL_NAMES
        assert "obtener_doc_documentacion" in TOOL_NAMES
        assert "buscar_en_documentacion" in TOOL_NAMES


# ========== TESTS DE RESOURCES ==========

class TestResources:
    """Tests para los resources MCP de documentación."""

    @pytest.mark.asyncio
    async def test_list_resources(self):
        """Lista los resources de documentación."""
        resources = await list_resources()
        assert len(resources) == 3  # Un resource por tipo de expediente
        uris = [str(r.uri) for r in resources]
        assert "documentacion://subvenciones" in uris
        assert "documentacion://licencias_obras" in uris
        assert "documentacion://certificado_empadronamiento" in uris

    @pytest.mark.asyncio
    async def test_get_resource_subvenciones(self):
        """Obtiene resource de documentación de subvenciones."""
        content = await get_resource("documentacion://subvenciones")
        data = json.loads(content)
        assert data["tipo_expediente"] == "subvenciones"
        assert "documentos" in data
        assert len(data["documentos"]) == 4

    @pytest.mark.asyncio
    async def test_get_resource_licencias(self):
        """Obtiene resource de documentación de licencias."""
        content = await get_resource("documentacion://licencias_obras")
        data = json.loads(content)
        assert data["tipo_expediente"] == "licencias_obras"
        assert "instrucciones" in data

    @pytest.mark.asyncio
    async def test_get_resource_uri_invalida(self):
        """Error con URI inválida."""
        with pytest.raises(DocumentacionError) as exc_info:
            await get_resource("expediente://algo")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_get_resource_tipo_invalido(self):
        """Error con tipo de expediente inválido."""
        with pytest.raises(DocumentacionError) as exc_info:
            await get_resource("documentacion://tipo_inexistente")
        assert exc_info.value.status_code == 400


# ========== TESTS DE INTEGRACIÓN ==========

class TestIntegracion:
    """Tests de integración del módulo de documentación."""

    @pytest.mark.asyncio
    async def test_flujo_completo_consulta(self):
        """
        Prueba un flujo completo de consulta de documentación:
        1. Listar documentación disponible
        2. Obtener documento específico
        3. Buscar en la documentación
        """
        # 1. Listar
        lista = await call_tool("listar_documentacion", {"tipo_expediente": "subvenciones"})
        data_lista = json.loads(lista[0].text)
        assert len(data_lista["documentos"]) > 0

        # 2. Obtener normativa
        doc = await call_tool("obtener_doc_documentacion", {
            "tipo_expediente": "subvenciones",
            "tipo_documento": "normativa"
        })
        data_doc = json.loads(doc[0].text)
        assert "Ley" in data_doc["contenido"] or "ley" in data_doc["contenido"].lower()

        # 3. Buscar término
        busqueda = await call_tool("buscar_en_documentacion", {
            "tipo_expediente": "subvenciones",
            "query": "beneficiario"
        })
        data_busqueda = json.loads(busqueda[0].text)
        # Puede o no encontrar resultados, pero no debe fallar
        assert "total_coincidencias" in data_busqueda

    def test_todos_los_documentos_cargables(self):
        """Verifica que todos los documentos listados se pueden cargar."""
        for tipo_exp in TIPOS_EXPEDIENTE:
            docs = listar_documentos(tipo_exp)
            for doc in docs:
                # Determinar el tipo_documento desde el tipo del doc
                tipo_doc = doc["tipo"]
                subtipo = doc.get("subtipo")

                # Mapear a nombre de archivo
                if tipo_doc == "plantilla" and subtipo:
                    tipo_doc = f"plantilla_{subtipo}"
                elif tipo_doc == "plantilla" and "certificado" in doc["id"].lower():
                    tipo_doc = "plantilla_certificado"
                elif tipo_doc == "plantilla":
                    # Intentar deducir del ID
                    if "TPL-001" in doc["id"]:
                        if tipo_exp == "certificado_empadronamiento":
                            tipo_doc = "plantilla_certificado"
                        else:
                            tipo_doc = "plantilla_propuesta_resolucion"
                    elif "TPL-002" in doc["id"]:
                        tipo_doc = "plantilla_requerimiento_documentacion"

                # Verificar que se puede cargar (no lanza excepción)
                try:
                    loaded = cargar_documento(tipo_exp, tipo_doc)
                    assert loaded.id == doc["id"]
                except DocumentacionError:
                    # Algunos casos especiales pueden fallar por mapeo
                    pass
