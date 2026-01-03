"""
Tests de tools MCP para documentos.

Casos de prueba para las nuevas tools de gestión de documentos:
- obtener_texto_documento
- obtener_metadatos_documento
- actualizar_metadatos_documento
- crear_documento_desde_markdown
"""

import json
import pytest

from mcp_mock.mcp_expedientes.auth import AuthError
from mcp_mock.mcp_expedientes.tools import call_tool


# ========== Tests de Lectura ==========

@pytest.mark.asyncio
async def test_obtener_texto_documento_existente(exp_id_subvenciones):
    """
    Given: Un token válido y un documento con texto_markdown
    When: Se invoca obtener_texto_documento(EXP-2024-001, DOC-002)
    Then: Se retorna el texto markdown del DNI
    """
    result = await call_tool(
        "obtener_texto_documento",
        {
            "expediente_id": exp_id_subvenciones,
            "documento_id": "DOC-002"
        }
    )

    assert len(result) == 1
    response = json.loads(result[0].text)

    assert response["success"] is True
    assert response["documento_id"] == "DOC-002"
    assert response["nombre"] == "dni.pdf"
    assert response["tipo"] == "IDENTIFICACION"
    assert "texto_markdown" in response
    assert "Documento Nacional de Identidad" in response["texto_markdown"]
    assert "12345678A" in response["texto_markdown"]


@pytest.mark.asyncio
async def test_obtener_texto_documento_not_found(exp_id_subvenciones):
    """
    Given: Un documento que no existe
    When: Se invoca obtener_texto_documento
    Then: Se retorna error 404
    """
    with pytest.raises(AuthError) as exc_info:
        await call_tool(
            "obtener_texto_documento",
            {
                "expediente_id": exp_id_subvenciones,
                "documento_id": "DOC-999"
            }
        )

    assert exc_info.value.status_code == 404
    assert "no encontrado" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_obtener_metadatos_documento_existente(exp_id_subvenciones):
    """
    Given: Un documento con metadatos_extraidos
    When: Se invoca obtener_metadatos_documento(EXP-2024-001, DOC-002)
    Then: Se retorna el NIF, nombre, fechas del DNI
    """
    result = await call_tool(
        "obtener_metadatos_documento",
        {
            "expediente_id": exp_id_subvenciones,
            "documento_id": "DOC-002"
        }
    )

    assert len(result) == 1
    response = json.loads(result[0].text)

    assert response["success"] is True
    assert response["documento_id"] == "DOC-002"
    assert response["tipo"] == "IDENTIFICACION"
    assert "metadatos_extraidos" in response

    metadatos = response["metadatos_extraidos"]
    assert metadatos["numero_documento"] == "12345678A"
    assert metadatos["tipo_documento"] == "DNI"
    assert metadatos["nombre_completo"] == "María García López"
    assert metadatos["fecha_nacimiento"] == "1985-03-15"
    assert metadatos["fecha_caducidad"] == "2030-01-10"


@pytest.mark.asyncio
async def test_obtener_metadatos_documento_bancario(exp_id_subvenciones):
    """
    Given: Un documento bancario con metadatos
    When: Se obtienen los metadatos
    Then: Contiene entidad, IBAN, titular
    """
    result = await call_tool(
        "obtener_metadatos_documento",
        {
            "expediente_id": exp_id_subvenciones,
            "documento_id": "DOC-003"
        }
    )

    response = json.loads(result[0].text)
    metadatos = response["metadatos_extraidos"]

    assert metadatos["entidad"] == "Banco Ejemplo S.A."
    assert "ES79 2100 0813 4501 2345 6789" in metadatos["numero_cuenta_completo"]
    assert metadatos["titular"] == "María García López"


@pytest.mark.asyncio
async def test_obtener_metadatos_documento_not_found(exp_id_subvenciones):
    """
    Given: Un documento que no existe
    When: Se invoca obtener_metadatos_documento
    Then: Se retorna error 404
    """
    with pytest.raises(AuthError) as exc_info:
        await call_tool(
            "obtener_metadatos_documento",
            {
                "expediente_id": exp_id_subvenciones,
                "documento_id": "DOC-999"
            }
        )

    assert exc_info.value.status_code == 404


# ========== Tests de Escritura ==========

@pytest.mark.asyncio
@pytest.mark.usefixtures("restore_expediente_data")
async def test_actualizar_metadatos_documento_merge(exp_id_subvenciones):
    """
    Given: Un documento con metadatos existentes
    When: Se invoca actualizar_metadatos_documento con reemplazar=false
    Then: Los nuevos metadatos se mezclan con los existentes
    """
    # Añadir nuevos metadatos (merge)
    result = await call_tool(
        "actualizar_metadatos_documento",
        {
            "expediente_id": exp_id_subvenciones,
            "documento_id": "DOC-002",
            "metadatos": {
                "validado_por_agente": True,
                "fecha_validacion": "2024-01-16T10:30:00Z",
                "nif_verificado": True
            },
            "reemplazar": False
        }
    )

    response = json.loads(result[0].text)

    assert response["success"] is True
    assert response["documento_id"] == "DOC-002"

    # Verificar que los metadatos anteriores siguen presentes
    metadatos_nuevos = response["metadatos_nuevos"]
    assert metadatos_nuevos["numero_documento"] == "12345678A"  # Original
    assert metadatos_nuevos["validado_por_agente"] is True  # Nuevo


@pytest.mark.asyncio
@pytest.mark.usefixtures("restore_expediente_data")
async def test_actualizar_metadatos_documento_replace(exp_id_subvenciones):
    """
    Given: Un documento con metadatos existentes
    When: Se invoca actualizar_metadatos_documento con reemplazar=true
    Then: Los metadatos anteriores se reemplazan completamente
    """
    # Reemplazar todos los metadatos
    result = await call_tool(
        "actualizar_metadatos_documento",
        {
            "expediente_id": exp_id_subvenciones,
            "documento_id": "DOC-002",
            "metadatos": {
                "nuevo_campo": "nuevo_valor",
                "otro_campo": 123
            },
            "reemplazar": True
        }
    )

    response = json.loads(result[0].text)

    assert response["success"] is True

    # Los metadatos anteriores ya no deben estar
    metadatos_nuevos = response["metadatos_nuevos"]
    assert "numero_documento" not in metadatos_nuevos  # Ya no está
    assert metadatos_nuevos["nuevo_campo"] == "nuevo_valor"


@pytest.mark.asyncio
@pytest.mark.usefixtures("restore_expediente_data")
async def test_actualizar_metadatos_registra_historial(exp_id_subvenciones):
    """
    Given: Se actualizan metadatos de un documento
    When: Se consulta el expediente
    Then: La acción está registrada en el historial
    """
    # Obtener número de entradas de historial antes
    result_antes = await call_tool(
        "consultar_expediente",
        {"expediente_id": exp_id_subvenciones}
    )
    expediente_antes = json.loads(result_antes[0].text)
    num_historial_antes = len(expediente_antes["historial"])

    # Actualizar metadatos
    await call_tool(
        "actualizar_metadatos_documento",
        {
            "expediente_id": exp_id_subvenciones,
            "documento_id": "DOC-002",
            "metadatos": {"test": True},
            "reemplazar": False
        }
    )

    # Verificar historial
    result_despues = await call_tool(
        "consultar_expediente",
        {"expediente_id": exp_id_subvenciones}
    )
    expediente_despues = json.loads(result_despues[0].text)

    assert len(expediente_despues["historial"]) == num_historial_antes + 1
    ultima_entrada = expediente_despues["historial"][-1]
    assert ultima_entrada["accion"] == "ACTUALIZAR_METADATOS_DOCUMENTO"
    assert "DOC-002" in ultima_entrada["detalles"]


@pytest.mark.asyncio
@pytest.mark.usefixtures("restore_expediente_data")
async def test_crear_documento_desde_markdown(exp_id_subvenciones):
    """
    Given: Un token con permiso de gestión
    When: Se invoca crear_documento_desde_markdown con un informe
    Then: Se crea el documento con texto_markdown y metadatos
    And: Se registra en el historial del expediente
    """
    texto_informe = """# Informe de Validación de Documentos

## Expediente: EXP-2024-001

### Resultado: FAVORABLE

Se han revisado todos los documentos aportados y se verifica:
- DNI válido y coincide con datos del solicitante
- Certificado bancario vigente
- Solicitud completa

**Conclusión:** Documentación completa y válida.
"""

    result = await call_tool(
        "crear_documento_desde_markdown",
        {
            "expediente_id": exp_id_subvenciones,
            "nombre": "informe_validacion.md",
            "tipo": "INFORME",
            "texto_markdown": texto_informe,
            "metadatos": {
                "tipo_informe": "VALIDACION_DOCUMENTAL",
                "autor": "Agente ValidadorDocumental",
                "fecha_emision": "2024-01-16T10:45:00Z",
                "resultado": "FAVORABLE"
            }
        }
    )

    response = json.loads(result[0].text)

    assert response["success"] is True
    assert "documento_id" in response
    assert response["documento_id"].startswith("DOC-")
    assert response["nombre"] == "informe_validacion.md"
    assert response["tipo"] == "INFORME"

    # Verificar que el documento aparece en la lista
    result_list = await call_tool(
        "listar_documentos",
        {"expediente_id": exp_id_subvenciones}
    )
    documentos = json.loads(result_list[0].text)
    nuevo_doc = next(
        (doc for doc in documentos if doc["id"] == response["documento_id"]),
        None
    )
    assert nuevo_doc is not None
    assert nuevo_doc["tipo"] == "INFORME"
    assert nuevo_doc["texto_markdown"] is not None
    assert nuevo_doc["metadatos_extraidos"]["resultado"] == "FAVORABLE"


@pytest.mark.asyncio
@pytest.mark.usefixtures("restore_expediente_data")
async def test_crear_documento_sin_metadatos(exp_id_subvenciones):
    """
    Given: Se crea un documento sin metadatos opcionales
    When: Se invoca crear_documento_desde_markdown
    Then: El documento se crea correctamente sin metadatos
    """
    result = await call_tool(
        "crear_documento_desde_markdown",
        {
            "expediente_id": exp_id_subvenciones,
            "nombre": "nota_simple.md",
            "tipo": "OTRO",
            "texto_markdown": "# Nota simple\n\nContenido de prueba."
        }
    )

    response = json.loads(result[0].text)
    assert response["success"] is True

    # Verificar que el documento se puede obtener
    result_doc = await call_tool(
        "obtener_documento",
        {
            "expediente_id": exp_id_subvenciones,
            "documento_id": response["documento_id"]
        }
    )
    doc = json.loads(result_doc[0].text)
    assert doc["metadatos_extraidos"] is None
    assert "Nota simple" in doc["texto_markdown"]


@pytest.mark.asyncio
@pytest.mark.usefixtures("restore_expediente_data")
async def test_crear_documento_registra_historial(exp_id_subvenciones):
    """
    Given: Se crea un documento desde markdown
    When: Se consulta el expediente
    Then: La acción está registrada en el historial
    """
    await call_tool(
        "crear_documento_desde_markdown",
        {
            "expediente_id": exp_id_subvenciones,
            "nombre": "test_historial.md",
            "tipo": "INFORME",
            "texto_markdown": "# Test"
        }
    )

    result = await call_tool(
        "consultar_expediente",
        {"expediente_id": exp_id_subvenciones}
    )
    expediente = json.loads(result[0].text)

    ultima_entrada = expediente["historial"][-1]
    assert ultima_entrada["accion"] == "CREAR_DOCUMENTO_MARKDOWN"
    assert "test_historial.md" in ultima_entrada["detalles"]


# ========== Tests de Integración ==========

@pytest.mark.asyncio
@pytest.mark.usefixtures("restore_expediente_data")
async def test_flujo_validacion_documento(exp_id_subvenciones):
    """
    Test de integración: Validación completa de un DNI

    1. Agente obtiene texto_markdown del DNI
    2. Agente obtiene metadatos_extraidos
    3. Agente verifica que el NIF del metadato coincide con el del expediente
    4. Agente actualiza metadatos con resultado de validación
    5. Agente crea informe de validación desde markdown
    """
    # 1. Obtener texto del DNI
    result_texto = await call_tool(
        "obtener_texto_documento",
        {
            "expediente_id": exp_id_subvenciones,
            "documento_id": "DOC-002"
        }
    )
    texto_response = json.loads(result_texto[0].text)
    assert "GARCÍA LÓPEZ" in texto_response["texto_markdown"]

    # 2. Obtener metadatos del DNI
    result_meta = await call_tool(
        "obtener_metadatos_documento",
        {
            "expediente_id": exp_id_subvenciones,
            "documento_id": "DOC-002"
        }
    )
    meta_response = json.loads(result_meta[0].text)
    nif_documento = meta_response["metadatos_extraidos"]["numero_documento"]

    # 3. Verificar NIF (consultando expediente)
    result_exp = await call_tool(
        "consultar_expediente",
        {"expediente_id": exp_id_subvenciones}
    )
    expediente = json.loads(result_exp[0].text)
    nif_expediente = expediente["datos"]["solicitante"]["nif"]
    nif_coincide = nif_documento == nif_expediente

    # 4. Actualizar metadatos con resultado
    await call_tool(
        "actualizar_metadatos_documento",
        {
            "expediente_id": exp_id_subvenciones,
            "documento_id": "DOC-002",
            "metadatos": {
                "validacion_automatica": True,
                "nif_verificado": nif_coincide,
                "fecha_verificacion": "2024-01-16T10:30:00Z"
            },
            "reemplazar": False
        }
    )

    # 5. Crear informe de validación
    informe_md = f"""# Informe de Validación Automática

## Expediente: {exp_id_subvenciones}
## Documento: DOC-002 (DNI)

### Resultado: {"VÁLIDO" if nif_coincide else "INVÁLIDO"}

| Verificación | Resultado |
|--------------|-----------|
| NIF documento | {nif_documento} |
| NIF expediente | {nif_expediente} |
| Coincidencia | {"Sí" if nif_coincide else "No"} |

**Conclusión:** El documento de identidad ha sido verificado automáticamente.
"""

    result_informe = await call_tool(
        "crear_documento_desde_markdown",
        {
            "expediente_id": exp_id_subvenciones,
            "nombre": "informe_validacion_dni.md",
            "tipo": "INFORME",
            "texto_markdown": informe_md,
            "metadatos": {
                "tipo_informe": "VALIDACION_IDENTIDAD",
                "documento_validado": "DOC-002",
                "resultado": "VALIDO" if nif_coincide else "INVALIDO"
            }
        }
    )

    assert json.loads(result_informe[0].text)["success"] is True


@pytest.mark.asyncio
async def test_obtener_texto_todos_documentos_exp001(exp_id_subvenciones):
    """
    Verificar que todos los documentos de EXP-2024-001 tienen texto_markdown
    """
    docs_ids = ["DOC-001", "DOC-002", "DOC-003"]

    for doc_id in docs_ids:
        result = await call_tool(
            "obtener_texto_documento",
            {
                "expediente_id": exp_id_subvenciones,
                "documento_id": doc_id
            }
        )
        response = json.loads(result[0].text)
        assert response["success"] is True
        assert len(response["texto_markdown"]) > 100  # Tiene contenido significativo


@pytest.mark.asyncio
async def test_obtener_metadatos_todos_documentos_exp001(exp_id_subvenciones):
    """
    Verificar que todos los documentos de EXP-2024-001 tienen metadatos_extraidos
    """
    docs_ids = ["DOC-001", "DOC-002", "DOC-003"]

    for doc_id in docs_ids:
        result = await call_tool(
            "obtener_metadatos_documento",
            {
                "expediente_id": exp_id_subvenciones,
                "documento_id": doc_id
            }
        )
        response = json.loads(result[0].text)
        assert response["success"] is True
        assert len(response["metadatos_extraidos"]) > 0
