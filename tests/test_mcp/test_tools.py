"""
Tests de tools MCP y permisos.

Casos de prueba:
- TC-PERM-001: Escritura sin Permiso Gestión
- TC-PERM-002: Lectura con Solo Permiso Consulta
- TC-TOOL-001: Consultar Expediente
- TC-TOOL-002: Listar Documentos
- TC-TOOL-003: Obtener Documento Específico
- TC-TOOL-004: Obtener Documento Inexistente
- TC-TOOL-005: Añadir Documento
- TC-TOOL-006: Actualizar Datos
- TC-TOOL-007: Añadir Anotación
"""

import json
import pytest

# JWT_SECRET ya configurado por fixture autouse en conftest.py global

from mcp_mock.mcp_expedientes.auth import validate_jwt, AuthError
from mcp_mock.mcp_expedientes.tools import call_tool
from fixtures.tokens import token_consulta, token_gestion


@pytest.mark.asyncio
async def test_tc_perm_001_escritura_sin_gestion(exp_id_subvenciones):
    """
    TC-PERM-001: Escritura sin Permiso Gestión

    Given: Un token JWT válido con solo permisos=["consulta"]
    When: Se intenta añadir documento
    Then: Se retorna error 403 "Permiso insuficiente: se requiere gestión"
    """
    token = token_consulta(exp_id_subvenciones)

    # Validar token para tool de escritura debe fallar
    with pytest.raises(AuthError) as exc_info:
        await validate_jwt(
            token,
            tool_name="añadir_documento",
            tool_args={"expediente_id": exp_id_subvenciones}
        )

    assert exc_info.value.status_code == 403
    assert "gestion" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_tc_perm_002_lectura_con_consulta(exp_id_subvenciones):
    """
    TC-PERM-002: Lectura con Solo Permiso Consulta

    Given: Un token JWT válido con permisos=["consulta"]
    When: Se invoca consultar_expediente(...)
    Then: Se retorna el expediente correctamente
    """
    token = token_consulta(exp_id_subvenciones)

    # Validar token para tool de lectura debe funcionar
    claims = await validate_jwt(
        token,
        tool_name="consultar_expediente",
        tool_args={"expediente_id": exp_id_subvenciones}
    )

    assert claims.exp_id == exp_id_subvenciones
    assert "consulta" in claims.permisos


@pytest.mark.asyncio
async def test_tc_tool_001_consultar_expediente(exp_id_subvenciones):
    """
    TC-TOOL-001: Consultar Expediente

    Given: Un token JWT válido con permisos de consulta
    When: Se ejecuta consultar_expediente("EXP-2024-001")
    Then: Se retorna el expediente con todos sus campos
    """
    # Ejecutar tool
    result = await call_tool(
        "consultar_expediente",
        {"expediente_id": exp_id_subvenciones}
    )

    # Verificar resultado
    assert len(result) == 1
    assert result[0].type == "text"

    # Parsear JSON
    expediente = json.loads(result[0].text)
    assert expediente["id"] == exp_id_subvenciones
    assert expediente["tipo"] == "SUBVENCIONES"
    assert expediente["estado"] == "EN_TRAMITE"
    assert "datos" in expediente
    assert "documentos" in expediente
    assert "historial" in expediente
    assert "metadatos" in expediente


@pytest.mark.asyncio
@pytest.mark.usefixtures("restore_expediente_data")
async def test_tc_tool_002_listar_documentos(exp_id_subvenciones):
    """
    TC-TOOL-002: Listar Documentos

    Given: Un token JWT válido con permisos de consulta
    When: Se ejecuta listar_documentos("EXP-2024-001")
    Then: Se retorna lista de 3 documentos con metadata
    """
    # Ejecutar tool
    result = await call_tool(
        "listar_documentos",
        {"expediente_id": exp_id_subvenciones}
    )

    # Verificar resultado
    assert len(result) == 1
    documentos = json.loads(result[0].text)

    # Verificar estructura
    assert len(documentos) == 3
    assert all("id" in doc for doc in documentos)
    assert all("nombre" in doc for doc in documentos)
    assert all("tipo" in doc for doc in documentos)


@pytest.mark.asyncio
async def test_tc_tool_003_obtener_documento(exp_id_subvenciones):
    """
    TC-TOOL-003: Obtener Documento Específico

    Given: Un token JWT válido con permisos de consulta
    When: Se ejecuta obtener_documento("EXP-2024-001", "DOC-001")
    Then: Se retorna la metadata del documento DOC-001
    """
    # Ejecutar tool
    result = await call_tool(
        "obtener_documento",
        {
            "expediente_id": exp_id_subvenciones,
            "documento_id": "DOC-001"
        }
    )

    # Verificar resultado
    assert len(result) == 1
    documento = json.loads(result[0].text)

    assert documento["id"] == "DOC-001"
    assert documento["nombre"] == "solicitud.pdf"
    assert documento["tipo"] == "SOLICITUD"


@pytest.mark.asyncio
async def test_tc_tool_004_obtener_documento_not_found(exp_id_subvenciones):
    """
    TC-TOOL-004: Obtener Documento Inexistente

    Given: Un token JWT válido
    When: Se ejecuta obtener_documento("EXP-2024-001", "DOC-999")
    Then: Se retorna error 404 "Documento no encontrado"
    """
    # Ejecutar tool (debería fallar)
    with pytest.raises(AuthError) as exc_info:
        await call_tool(
            "obtener_documento",
            {
                "expediente_id": exp_id_subvenciones,
                "documento_id": "DOC-999"
            }
        )

    assert exc_info.value.status_code == 404
    assert "no encontrado" in exc_info.value.message.lower()


@pytest.mark.asyncio
@pytest.mark.usefixtures("restore_expediente_data")
async def test_tc_tool_005_añadir_documento(exp_id_subvenciones):
    """
    TC-TOOL-005: Añadir Documento

    Given: Un token JWT válido con permisos de gestión
    When: Se ejecuta añadir_documento(exp_id, nombre, tipo, contenido)
    Then:
      - Se crea nuevo documento con ID único
      - Se añade al array de documentos
      - Se registra en historial
      - Se retorna success=true con documento_id
    """
    # Ejecutar tool
    result = await call_tool(
        "añadir_documento",
        {
            "expediente_id": exp_id_subvenciones,
            "nombre": "informe_test.pdf",
            "tipo": "INFORME",
            "contenido": "Contenido de prueba del documento"
        }
    )

    # Verificar resultado
    assert len(result) == 1
    response = json.loads(result[0].text)

    assert response["success"] is True
    assert "documento_id" in response
    assert response["documento_id"].startswith("DOC-")

    # Verificar que el documento fue añadido
    result_list = await call_tool(
        "listar_documentos",
        {"expediente_id": exp_id_subvenciones}
    )
    documentos = json.loads(result_list[0].text)

    # Ahora debería haber 4 documentos (3 originales + 1 nuevo)
    assert len(documentos) == 4
    assert any(doc["id"] == response["documento_id"] for doc in documentos)


@pytest.mark.asyncio
@pytest.mark.usefixtures("restore_expediente_data")
async def test_tc_tool_006_actualizar_datos(exp_id_subvenciones):
    """
    TC-TOOL-006: Actualizar Datos

    Given: Un token JWT válido con permisos de gestión
    When: Se ejecuta actualizar_datos("EXP-2024-001", "datos.documentacion_valida", true)
    Then:
      - El campo se actualiza en el expediente
      - Se registra en historial
      - Se retorna success=true con valor_anterior
    """
    # Ejecutar tool
    result = await call_tool(
        "actualizar_datos",
        {
            "expediente_id": exp_id_subvenciones,
            "campo": "datos.documentacion_valida",
            "valor": True
        }
    )

    # Verificar resultado
    assert len(result) == 1
    response = json.loads(result[0].text)

    assert response["success"] is True
    assert response["campo"] == "datos.documentacion_valida"
    assert response["valor_anterior"] is None  # Era null inicialmente
    assert response["valor_nuevo"] is True

    # Verificar que el valor fue actualizado
    result_consulta = await call_tool(
        "consultar_expediente",
        {"expediente_id": exp_id_subvenciones}
    )
    expediente = json.loads(result_consulta[0].text)

    assert expediente["datos"]["documentacion_valida"] is True


@pytest.mark.asyncio
@pytest.mark.usefixtures("restore_expediente_data")
async def test_tc_tool_007_añadir_anotacion(exp_id_subvenciones):
    """
    TC-TOOL-007: Añadir Anotación

    Given: Un token JWT válido con permisos de gestión
    When: Se ejecuta añadir_anotacion("EXP-2024-001", "Documentación verificada correctamente")
    Then:
      - Se añade entrada al historial
      - Tipo = "ANOTACION"
      - Usuario = "Automático"
      - Se retorna success=true
    """
    # Contar entradas de historial antes
    result_antes = await call_tool(
        "consultar_expediente",
        {"expediente_id": exp_id_subvenciones}
    )
    expediente_antes = json.loads(result_antes[0].text)
    num_historial_antes = len(expediente_antes["historial"])

    # Ejecutar tool
    result = await call_tool(
        "añadir_anotacion",
        {
            "expediente_id": exp_id_subvenciones,
            "texto": "Documentación verificada correctamente"
        }
    )

    # Verificar resultado
    assert len(result) == 1
    response = json.loads(result[0].text)

    assert response["success"] is True
    assert "historial_id" in response

    # Verificar que se añadió la anotación
    result_despues = await call_tool(
        "consultar_expediente",
        {"expediente_id": exp_id_subvenciones}
    )
    expediente_despues = json.loads(result_despues[0].text)

    assert len(expediente_despues["historial"]) == num_historial_antes + 1

    # Verificar la última entrada del historial
    ultima_entrada = expediente_despues["historial"][-1]
    assert ultima_entrada["tipo"] == "ANOTACION"
    assert ultima_entrada["usuario"] == "Automático"
    assert "Documentación verificada correctamente" in ultima_entrada["detalles"]
