"""
Tests de autenticación y autorización.

Casos de prueba:
- TC-AUTH-001: Token Válido con Permisos Consulta
- TC-AUTH-002: Token Válido con Permisos Gestión
- TC-AUTH-003: Token Expirado
- TC-AUTH-004: Token con Firma Inválida
- TC-AUTH-005: Acceso a Expediente No Autorizado
- TC-AUTH-006: Usuario No Automático
"""

import pytest

# ELIMINADO: os, sys imports - no necesarios
# JWT_SECRET ya configurado por fixture autouse en conftest.py global

from mcp_mock.mcp_expedientes.auth import validate_jwt, AuthError
from fixtures.tokens import (
    token_consulta,
    token_gestion,
    token_expirado,
    token_firma_invalida,
    token_otro_expediente,
    token_usuario_invalido
)


@pytest.mark.asyncio
async def test_tc_auth_001_token_valido_consulta():
    """
    TC-AUTH-001: Token Válido con Permisos Consulta

    Given: Un token JWT válido con permisos de consulta para EXP-2024-001
    When: Se valida el token
    Then: La validación es exitosa y se retornan los claims correctos
    """
    token = token_consulta("EXP-2024-001")

    # La validación debe ser exitosa
    claims = await validate_jwt(token)

    # Verificar claims
    assert claims.sub == "Automático"
    assert claims.exp_id == "EXP-2024-001"
    assert "consulta" in claims.permisos
    assert claims.iss == "agentix-bpmn"


@pytest.mark.asyncio
async def test_tc_auth_002_token_valido_gestion():
    """
    TC-AUTH-002: Token Válido con Permisos Gestión

    Given: Un token JWT válido con permisos de gestión para EXP-2024-001
    When: Se valida el token
    Then: La validación es exitosa y el token tiene permisos de gestión
    """
    token = token_gestion("EXP-2024-001")

    # La validación debe ser exitosa
    claims = await validate_jwt(token)

    # Verificar permisos
    assert "consulta" in claims.permisos
    assert "gestion" in claims.permisos
    assert claims.exp_id == "EXP-2024-001"


@pytest.mark.asyncio
async def test_tc_auth_003_token_expirado():
    """
    TC-AUTH-003: Token Expirado

    Given: Un token JWT expirado (exp < now)
    When: Se intenta validar el token
    Then: Se retorna error 401 "Token expirado"
    """
    token = token_expirado("EXP-2024-001")

    # La validación debe fallar
    with pytest.raises(AuthError) as exc_info:
        await validate_jwt(token)

    assert exc_info.value.status_code == 401
    assert "expirado" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_tc_auth_004_firma_invalida():
    """
    TC-AUTH-004: Token con Firma Inválida

    Given: Un token JWT con firma incorrecta
    When: Se intenta validar el token
    Then: Se retorna error 401 "Firma inválida"
    """
    token = token_firma_invalida("EXP-2024-001")

    # La validación debe fallar
    with pytest.raises(AuthError) as exc_info:
        await validate_jwt(token)

    assert exc_info.value.status_code == 401
    assert "firma" in exc_info.value.message.lower() or "inválida" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_tc_auth_005_expediente_no_autorizado():
    """
    TC-AUTH-005: Acceso a Expediente No Autorizado

    Given: Un token JWT válido para EXP-2024-999
    When: Se intenta acceder a EXP-2024-001 con herramientas
    Then: Se retorna error 403 "Acceso no autorizado al expediente"
    """
    token = token_otro_expediente("EXP-2024-999")

    # Intentar validar con acceso a EXP-2024-001 (no autorizado)
    with pytest.raises(AuthError) as exc_info:
        await validate_jwt(
            token,
            tool_args={"expediente_id": "EXP-2024-001"}
        )

    assert exc_info.value.status_code == 403
    assert "no autorizado" in exc_info.value.message.lower()
    assert "EXP-2024-001" in exc_info.value.message


@pytest.mark.asyncio
async def test_tc_auth_006_usuario_no_automatico():
    """
    TC-AUTH-006: Usuario No Automático

    Given: Un token JWT con sub="Usuario Humano"
    When: Se intenta validar el token
    Then: Se retorna error 403 "Usuario no autorizado"
    """
    token = token_usuario_invalido("EXP-2024-001")

    # La validación debe fallar
    with pytest.raises(AuthError) as exc_info:
        await validate_jwt(token)

    assert exc_info.value.status_code == 403
    assert "usuario" in exc_info.value.message.lower()
    assert "autorizado" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_token_sin_proporcionar():
    """
    Test adicional: Token no proporcionado

    Given: No se proporciona token (None)
    When: Se intenta validar
    Then: Se retorna error 401 "Token JWT no proporcionado"
    """
    with pytest.raises(AuthError) as exc_info:
        await validate_jwt(None)

    assert exc_info.value.status_code == 401
    assert "no proporcionado" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_validacion_audiencia_string():
    """
    Test adicional: Validación de audiencia cuando aud es string

    Given: Un token con aud como string (no array)
    When: Se valida el token
    Then: La validación es exitosa si el servidor coincide
    """
    token = token_consulta("EXP-2024-001")

    # Debe validar correctamente (aud es string "agentix-mcp-expedientes")
    claims = await validate_jwt(token)
    assert claims.exp_id == "EXP-2024-001"


@pytest.mark.asyncio
async def test_validacion_resource_uri():
    """
    Test adicional: Validación de acceso a resource URI

    Given: Un token válido para EXP-2024-001
    When: Se valida acceso a resource expediente://EXP-2024-001
    Then: La validación es exitosa
    """
    token = token_consulta("EXP-2024-001")

    # Validar acceso al resource correcto
    claims = await validate_jwt(
        token,
        resource_uri="expediente://EXP-2024-001"
    )
    assert claims.exp_id == "EXP-2024-001"


@pytest.mark.asyncio
async def test_validacion_resource_uri_no_autorizado():
    """
    Test adicional: Validación de acceso a resource URI no autorizado

    Given: Un token válido para EXP-2024-001
    When: Se intenta acceder a resource expediente://EXP-2024-002
    Then: Se retorna error 403
    """
    token = token_consulta("EXP-2024-001")

    # Intentar acceder a otro expediente
    with pytest.raises(AuthError) as exc_info:
        await validate_jwt(
            token,
            resource_uri="expediente://EXP-2024-002"
        )

    assert exc_info.value.status_code == 403
    assert "no autorizado" in exc_info.value.message.lower()
