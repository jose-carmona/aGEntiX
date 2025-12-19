"""
Tests de resources MCP.

Casos de prueba:
- TC-RES-001: Resource Expediente Completo
- TC-RES-002: Resource Documentos
- TC-RES-003: Resource Historial
"""

import os
import sys
import json
import pytest

# Path para imports configurado por setup.py y run-tests.sh

from mcp_mock.mcp_expedientes.resources import list_resources, get_resource
from fixtures.tokens import token_consulta

# Configurar JWT_SECRET
os.environ["JWT_SECRET"] = "test-secret-key"


@pytest.mark.asyncio
async def test_tc_res_001_resource_expediente(exp_id_subvenciones):
    """
    TC-RES-001: Resource Expediente Completo

    Given: Un token JWT válido
    When: Se lee el resource "expediente://EXP-2024-001"
    Then: Se retorna el JSON completo del expediente
    """
    uri = f"expediente://{exp_id_subvenciones}"

    # Obtener resource
    content = await get_resource(uri)

    # Parsear JSON
    expediente = json.loads(content)

    # Verificar estructura completa
    assert expediente["id"] == exp_id_subvenciones
    assert expediente["tipo"] == "SUBVENCIONES"
    assert "datos" in expediente
    assert "documentos" in expediente
    assert "historial" in expediente
    assert "metadatos" in expediente


@pytest.mark.asyncio
async def test_tc_res_002_resource_documentos(exp_id_subvenciones):
    """
    TC-RES-002: Resource Documentos

    Given: Un token JWT válido
    When: Se lee el resource "expediente://EXP-2024-001/documentos"
    Then: Se retorna un array con todos los documentos
    """
    uri = f"expediente://{exp_id_subvenciones}/documentos"

    # Obtener resource
    content = await get_resource(uri)

    # Parsear JSON
    documentos = json.loads(content)

    # Verificar estructura
    assert isinstance(documentos, list)
    assert len(documentos) >= 3  # Al menos los 3 documentos originales
    assert all("id" in doc for doc in documentos)
    assert all("nombre" in doc for doc in documentos)


@pytest.mark.asyncio
async def test_tc_res_003_resource_historial(exp_id_subvenciones):
    """
    TC-RES-003: Resource Historial

    Given: Un token JWT válido
    When: Se lee el resource "expediente://EXP-2024-001/historial"
    Then: Se retorna un array con el historial de acciones
    """
    uri = f"expediente://{exp_id_subvenciones}/historial"

    # Obtener resource
    content = await get_resource(uri)

    # Parsear JSON
    historial = json.loads(content)

    # Verificar estructura
    assert isinstance(historial, list)
    assert len(historial) >= 2  # Al menos las 2 entradas originales
    assert all("id" in entry for entry in historial)
    assert all("usuario" in entry for entry in historial)
    assert all("tipo" in entry for entry in historial)
    assert all("accion" in entry for entry in historial)


@pytest.mark.asyncio
async def test_tc_res_004_resource_documento_especifico(exp_id_subvenciones):
    """
    Test adicional: Resource de documento específico

    Given: Un token JWT válido
    When: Se lee el resource "expediente://EXP-2024-001/documento/DOC-001"
    Then: Se retorna la metadata del documento específico
    """
    uri = f"expediente://{exp_id_subvenciones}/documento/DOC-001"

    # Obtener resource
    content = await get_resource(uri)

    # Parsear JSON
    documento = json.loads(content)

    # Verificar estructura
    assert documento["id"] == "DOC-001"
    assert documento["nombre"] == "solicitud.pdf"
    assert documento["tipo"] == "SOLICITUD"


@pytest.mark.asyncio
async def test_list_resources():
    """
    Test adicional: Listar todos los resources disponibles

    Given: Un servidor MCP funcionando
    When: Se lista los resources
    Then: Se retornan resources para todos los expedientes
    """
    resources = await list_resources()

    # Debe haber al menos resources para 3 expedientes
    # Cada expediente tiene 3 resources (expediente, documentos, historial)
    assert len(resources) >= 9  # 3 expedientes × 3 resources

    # Verificar que hay resources del expediente de prueba
    uris = [str(r.uri) for r in resources]
    assert "expediente://EXP-2024-001" in uris
    assert "expediente://EXP-2024-001/documentos" in uris
    assert "expediente://EXP-2024-001/historial" in uris


@pytest.mark.asyncio
async def test_resource_expediente_inexistente():
    """
    Test adicional: Acceso a expediente inexistente

    Given: Un token JWT válido
    When: Se intenta acceder a un expediente que no existe
    Then: Se retorna error 404
    """
    from mcp_mock.mcp_expedientes.auth import AuthError

    uri = "expediente://EXP-9999-999"

    # Debe fallar con 404
    with pytest.raises(AuthError) as exc_info:
        await get_resource(uri)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_resource_uri_invalida():
    """
    Test adicional: URI inválida

    Given: Una URI que no sigue el formato correcto
    When: Se intenta obtener el resource
    Then: Se retorna error 400
    """
    from mcp_mock.mcp_expedientes.auth import AuthError

    uri = "invalid://something"

    # Debe fallar con 400
    with pytest.raises(AuthError) as exc_info:
        await get_resource(uri)

    assert exc_info.value.status_code == 400
