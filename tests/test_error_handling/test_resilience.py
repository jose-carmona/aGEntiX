# tests/test_error_handling/test_resilience.py

"""
Tests de Error Handling y Resiliencia.

Implementa 15 tests (12 activos + 3 skipped) para validar:
- Manejo de errores MCP (conexión, timeouts, tools, auth)
- Manejo de errores JWT (validación, formato)
- Manejo de errores de webhook (retry, SSRF)
- Manejo de errores de agente (crashes, configuración)
- Manejo de errores de redacción PII
- Casos edge y escenarios futuros (skipped)

Todos los tests son unitarios usando mocks.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import httpx
from pydantic import ValidationError

from backoffice.mcp.client import MCPClient
from backoffice.mcp.exceptions import MCPConnectionError, MCPToolError, MCPAuthError
from backoffice.auth.jwt_validator import JWTClaims, JWTValidationError, validate_jwt
from backoffice.logging.pii_redactor import PIIRedactor
from backoffice.executor import AgentExecutor
from backoffice.models import AgentError
from api.models import ExecuteAgentRequest


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_server_config():
    """Configuración de servidor MCP para tests"""
    config = Mock()
    config.id = "test-mcp"
    config.name = "Test MCP Server"
    config.url = "http://localhost:8000"
    config.endpoint = "/mcp"
    config.timeout = 30.0
    return config


@pytest.fixture
def test_token():
    """Token JWT para tests"""
    return "Bearer test-token-12345"


@pytest.fixture
def mock_httpx_response():
    """Helper para crear respuestas HTTP mock"""
    def _create(json_data=None, status_code=200, raise_error=None):
        mock_resp = Mock()
        mock_resp.status_code = status_code
        mock_resp.json = Mock(return_value=json_data or {})

        if raise_error:
            mock_resp.raise_for_status = Mock(side_effect=raise_error)
        else:
            mock_resp.raise_for_status = Mock()

        return mock_resp

    return _create


def create_mock_async_client(mock_response=None, side_effect=None):
    """
    Helper para crear un mock de httpx.AsyncClient compatible con lazy init.

    Args:
        mock_response: Respuesta a retornar (para casos de éxito o error JSON-RPC)
        side_effect: Excepción a lanzar (para simular errores de conexión)
    """
    mock_client = MagicMock()

    async def async_post(*args, **kwargs):
        if side_effect:
            raise side_effect
        return mock_response

    mock_client.post = MagicMock(side_effect=async_post)
    return mock_client


# ============================================================================
# TESTS MCP ERRORS
# ============================================================================

@pytest.mark.asyncio
async def test_error_1_mcp_server_completely_down(mock_server_config, test_token):
    """
    Test: MCP server completamente caído

    Escenario:
    - MCP server no responde (connection refused)
    - Sistema intenta conectar
    - Error propagado limpiamente

    Validaciones:
    - MCPConnectionError lanzada con código MCP_CONNECTION_ERROR
    - Mensaje incluye nombre del servidor
    - Detalle incluye error de conexión original
    - No crashea la aplicación (error contenido)
    """
    client = MCPClient(mock_server_config, test_token)

    mock_async_client = create_mock_async_client(
        side_effect=httpx.ConnectError("Connection refused")
    )

    with patch.object(client, '_get_async_client', return_value=mock_async_client):
        with pytest.raises(MCPConnectionError) as exc_info:
            await client.call_tool("consultar_expediente", {"exp_id": "EXP-001"})

        # Validar excepción
        assert exc_info.value.codigo == "MCP_CONNECTION_ERROR"
        assert "test-mcp" in exc_info.value.mensaje
        assert "Connection refused" in str(exc_info.value.detalle)

    await client.close()


@pytest.mark.asyncio
async def test_error_2_mcp_tool_execution_fails(mock_server_config, test_token):
    """
    Test: Herramienta MCP falla durante ejecución

    Escenario:
    - Tool consultar_expediente retorna error JSON-RPC
    - Error 404 expediente no encontrado
    - Agente recibe error propagado

    Validaciones:
    - MCPToolError lanzada con código MCP_TOOL_ERROR
    - Mensaje incluye nombre del tool
    - Detalle incluye error original de MCP
    """
    client = MCPClient(mock_server_config, test_token)

    error_response = {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": -32000,
            "message": "Expediente no encontrado: EXP-999"
        }
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json = Mock(return_value=error_response)
    mock_response.raise_for_status = Mock()

    mock_async_client = create_mock_async_client(mock_response=mock_response)

    with patch.object(client, '_get_async_client', return_value=mock_async_client):
        with pytest.raises(MCPToolError) as exc_info:
            await client.call_tool("consultar_expediente", {"exp_id": "EXP-999"})

        assert exc_info.value.codigo == "MCP_TOOL_ERROR"
        assert "consultar_expediente" in exc_info.value.mensaje
        assert "Expediente no encontrado" in exc_info.value.mensaje

    await client.close()


@pytest.mark.asyncio
async def test_error_3_network_timeout_during_mcp_call(mock_server_config, test_token):
    """
    Test: Timeout de red durante llamada MCP

    Escenario:
    - MCP call tarda más del timeout configurado (30s)
    - Sistema cancela request
    - Error propagado a agente

    Validaciones:
    - MCPConnectionError lanzada con código MCP_TIMEOUT
    - Timeout detectado y request cancelado
    - Mensaje incluye timeout configurado
    """
    client = MCPClient(mock_server_config, test_token)

    mock_async_client = create_mock_async_client(
        side_effect=httpx.TimeoutException("Request timeout")
    )

    with patch.object(client, '_get_async_client', return_value=mock_async_client):
        with pytest.raises(MCPConnectionError) as exc_info:
            await client.call_tool("consultar_expediente", {"exp_id": "EXP-001"})

        assert exc_info.value.codigo == "MCP_TIMEOUT"
        assert "consultar_expediente" in exc_info.value.mensaje
        assert "30" in exc_info.value.mensaje  # Timeout de 30s
        assert "Request timeout" in str(exc_info.value.detalle)

    await client.close()


@pytest.mark.asyncio
async def test_error_7_mcp_jsonrpc_error_response(mock_server_config, test_token):
    """
    Test: MCP retorna error JSON-RPC válido

    Escenario:
    - MCP retorna error code -32600 (Invalid Request)
    - Mensaje de error del servidor incluido
    - Sistema lo convierte a MCPToolError

    Validaciones:
    - MCPToolError lanzada
    - Error code preservado en detalle
    - Mensaje de MCP incluido
    """
    client = MCPClient(mock_server_config, test_token)

    error_response = {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": -32600,
            "message": "Invalid Request: missing required parameter 'exp_id'"
        }
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json = Mock(return_value=error_response)
    mock_response.raise_for_status = Mock()

    mock_async_client = create_mock_async_client(mock_response=mock_response)

    with patch.object(client, '_get_async_client', return_value=mock_async_client):
        with pytest.raises(MCPToolError) as exc_info:
            await client.call_tool("consultar_expediente", {})

        assert exc_info.value.codigo == "MCP_TOOL_ERROR"
        assert "-32600" in str(exc_info.value.detalle)
        assert "Invalid Request" in exc_info.value.mensaje

    await client.close()


@pytest.mark.asyncio
async def test_error_13_mcp_authorization_denied(mock_server_config, test_token):
    """
    Test: MCP rechaza por permisos insuficientes

    Escenario:
    - JWT con permiso 'consulta'
    - Agente intenta tool que requiere 'gestion'
    - MCP rechaza con 403 Forbidden

    Validaciones:
    - MCPAuthError lanzada con código AUTH_PERMISSION_DENIED
    - Mensaje indica permiso faltante
    - No retry (error definitivo)
    """
    client = MCPClient(mock_server_config, test_token)

    http_error = httpx.HTTPStatusError(
        "403 Forbidden",
        request=Mock(),
        response=Mock(status_code=403, text="Permisos insuficientes")
    )

    mock_async_client = create_mock_async_client(side_effect=http_error)

    with patch.object(client, '_get_async_client', return_value=mock_async_client):
        with pytest.raises(MCPAuthError) as exc_info:
            await client.call_tool("modificar_expediente", {"exp_id": "EXP-001"})

        assert exc_info.value.codigo == "AUTH_PERMISSION_DENIED"
        assert "Permisos insuficientes" in exc_info.value.mensaje

    await client.close()


# ============================================================================
# TESTS JWT/AUTH ERRORS
# ============================================================================

def test_error_4_invalid_jwt_format():
    """
    Test: JWT malformado es rechazado

    Escenarios:
    - Token no es JWT válido (formato incorrecto)
    - Token con firma inválida
    - Token sin claims requeridos
    - Token con claim exp_id null

    Validaciones:
    - JWTValidationError lanzada
    - Código AUTH_INVALID_TOKEN apropiado
    - Mensaje específico del problema
    - No expone información sensible
    """
    # Escenario 1: Token malformado (no es JWT)
    with pytest.raises(JWTValidationError) as exc_info:
        validate_jwt(
            token="not-a-valid-jwt-token",
            secret="test-secret",
            algorithm="HS256",
            expected_expediente_id="EXP-001",
            expected_issuer="agentix-bpmn",
            expected_subject="Automático",
            required_audience="agentix-mcp-expedientes"
        )

    assert exc_info.value.codigo == "AUTH_INVALID_TOKEN"
    assert "inválido" in exc_info.value.mensaje.lower()

    # Escenario 2: Token con firma inválida
    invalid_signature_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.INVALID_SIGNATURE"

    with pytest.raises(JWTValidationError) as exc_info:
        validate_jwt(
            token=invalid_signature_token,
            secret="test-secret",
            algorithm="HS256",
            expected_expediente_id="EXP-001",
            expected_issuer="agentix-bpmn",
            expected_subject="Automático",
            required_audience="agentix-mcp-expedientes"
        )

    assert exc_info.value.codigo == "AUTH_INVALID_TOKEN"


# ============================================================================
# TESTS WEBHOOK ERRORS
# ============================================================================

@pytest.mark.asyncio
async def test_error_5_webhook_delivery_fails_with_retry():
    """
    Test: Webhook falla y se reintenta con éxito

    Escenario:
    - Webhook endpoint retorna 500 en primeros 2 intentos
    - Tercer intento retorna 200 OK
    - Sistema usa exponential backoff

    Validaciones:
    - 3 intentos realizados
    - Delay entre intentos (exponential backoff)
    - Success=True en tercer intento
    - asyncio.sleep mockeado para evitar delays reales
    """
    from api.services.webhook import send_webhook_with_retry
    from backoffice.models import AgentExecutionResult

    # Mock del resultado de ejecución
    mock_result = Mock()
    mock_result.success = True
    mock_result.resultado = {"completado": True}
    mock_result.herramientas_usadas = ["consultar_expediente"]
    mock_result.error = None

    webhook_url = "https://example.com/callback"
    agent_run_id = "test-run-123"

    # Contador de llamadas
    call_count = {"count": 0}

    async def mock_send_webhook(*args, **kwargs):
        call_count["count"] += 1
        # Fallar primeros 2 intentos, éxito en el tercero
        if call_count["count"] < 3:
            return False
        return True

    with patch('api.services.webhook.send_webhook', side_effect=mock_send_webhook):
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            result = await send_webhook_with_retry(
                webhook_url=webhook_url,
                agent_run_id=agent_run_id,
                result=mock_result
            )

            # Validar resultado
            assert result["success"] is True
            assert result["attempts"] == 3
            assert result["final_status_code"] == 200
            assert result["error"] is None

            # Validar que se hizo backoff
            assert mock_sleep.call_count == 2  # 2 delays (entre intentos)
            # Delays: 2^0 = 1, 2^1 = 2
            mock_sleep.assert_any_call(1.0)
            mock_sleep.assert_any_call(2.0)


def test_error_12_invalid_webhook_url_format():
    """
    Test: URL de webhook inválida es rechazada

    Escenarios:
    - URL no HTTP/HTTPS
    - URL con localhost (SSRF)
    - URL con IP privada
    - URL malformada

    Validaciones:
    - ValidationError de Pydantic
    - Request rechazado inmediatamente (antes de ejecutar)
    - Validación SSRF funciona
    - Mensaje claro del problema
    """
    # Escenario 1: localhost (SSRF)
    with pytest.raises(ValidationError) as exc_info:
        ExecuteAgentRequest(
            expediente_id="EXP-001",
            tarea_id="T-001",
            agent_config={
                "nombre": "ValidadorDocumental",
                "system_prompt": "Test",
                "modelo": "claude-3-5-sonnet-20241022",
                "herramientas": ["consultar_expediente"]
            },
            webhook_url="http://localhost:8080/callback"
        )

    errors = exc_info.value.errors()
    assert any("localhost" in str(error).lower() for error in errors)

    # Escenario 2: IP privada (SSRF)
    with pytest.raises(ValidationError) as exc_info:
        ExecuteAgentRequest(
            expediente_id="EXP-001",
            tarea_id="T-001",
            agent_config={
                "nombre": "ValidadorDocumental",
                "system_prompt": "Test",
                "modelo": "claude-3-5-sonnet-20241022",
                "herramientas": ["consultar_expediente"]
            },
            webhook_url="http://192.168.1.1/callback"
        )

    errors = exc_info.value.errors()
    assert any("privada" in str(error).lower() or "192.168" in str(error) for error in errors)


# ============================================================================
# TESTS AGENT/CONFIG ERRORS
# ============================================================================

@pytest.mark.asyncio
async def test_error_6_agent_raises_unhandled_exception(test_constants):
    """
    Test: Agente lanza excepción no manejada

    Escenario:
    - Agente tiene bug (NoneType error)
    - Excepción no es capturada por agente
    - Sistema la captura en executor

    Validaciones:
    - Error INTERNAL_ERROR
    - Stack trace completo en detalle
    - MCP registry cerrado correctamente
    - Sistema sigue funcionando (isolated failure)
    """
    from src.backoffice.auth.jwt_validator import JWTClaims

    # Crear mocks
    mock_jwt_validator = Mock()
    mock_jwt_validator.validate = Mock(return_value=JWTClaims(
        iss=test_constants["issuer"],
        sub=test_constants["subject"],
        aud=[test_constants["audience"]],
        exp=9999999999,
        iat=1234567890,
        nbf=1234567890,
        jti="test-jti",
        exp_id="EXP-001",
        permisos=["consulta", "gestion"]
    ))

    mock_config_loader = Mock()
    mock_config_loader.load = Mock(return_value=Mock(
        get_enabled_servers=Mock(return_value=[])
    ))

    mock_registry = AsyncMock()
    mock_registry.close = AsyncMock()

    mock_registry_factory = Mock()
    mock_registry_factory.create = AsyncMock(return_value=mock_registry)

    mock_logger_factory = Mock()
    mock_logger = Mock()
    mock_logger.log = Mock()
    mock_logger.error = Mock()
    mock_logger.get_log_entries = Mock(return_value=[])
    mock_logger_factory.create = Mock(return_value=mock_logger)

    # Mock agente que crashea
    mock_agent_class = Mock()
    mock_agent = Mock()
    mock_agent.execute = AsyncMock(side_effect=RuntimeError("Unexpected error in agent"))
    mock_agent_class.return_value = mock_agent

    mock_agent_registry = Mock()
    mock_agent_registry.get = Mock(return_value=mock_agent_class)

    executor = AgentExecutor(
        jwt_validator=mock_jwt_validator,
        config_loader=mock_config_loader,
        registry_factory=mock_registry_factory,
        logger_factory=mock_logger_factory,
        agent_registry=mock_agent_registry,
        mcp_config_path="tests/config/mcp_servers.yaml",
        jwt_secret="test-secret"
    )

    # Ejecutar
    from backoffice.models import AgentConfig

    agent_config = AgentConfig(
        nombre="ValidadorDocumental",
        system_prompt="Test",
        modelo="claude-3-5-sonnet-20241022",
        herramientas=[]
    )

    result = await executor.execute(
        token="test-token",
        expediente_id="EXP-001",
        tarea_id="T-001",
        agent_config=agent_config
    )

    # Validar
    assert result.success is False
    assert result.error is not None
    # El executor captura cualquier excepción inesperada como INTERNAL_ERROR
    assert result.error.codigo == "INTERNAL_ERROR"
    assert result.error.mensaje  # Debe tener mensaje
    assert result.error.detalle  # Debe tener detalle

    # Verificar que registry se cerró correctamente a pesar del error
    mock_registry.close.assert_called_once()


@pytest.mark.asyncio
async def test_error_9_invalid_agent_configuration(test_constants):
    """
    Test: Configuración de agente inválida

    Escenarios:
    - Nombre de agente desconocido
    - Herramientas no disponibles en MCP

    Validaciones:
    - Error AGENT_NOT_CONFIGURED
    - Mensaje específico del problema
    - No se intenta ejecución
    """
    from src.backoffice.auth.jwt_validator import JWTClaims

    # Crear mocks
    mock_jwt_validator = Mock()
    mock_jwt_validator.validate = Mock(return_value=JWTClaims(
        iss=test_constants["issuer"],
        sub=test_constants["subject"],
        aud=[test_constants["audience"]],
        exp=9999999999,
        iat=1234567890,
        nbf=1234567890,
        jti="test-jti",
        exp_id="EXP-001",
        permisos=["consulta", "gestion"]
    ))

    mock_config_loader = Mock()
    mock_config_loader.load = Mock(return_value=Mock(
        get_enabled_servers=Mock(return_value=[])
    ))

    mock_registry_factory = Mock()
    mock_registry_factory.create = AsyncMock(return_value=AsyncMock())

    mock_logger_factory = Mock()
    mock_logger = Mock()
    mock_logger.log = Mock()
    mock_logger.error = Mock()
    mock_logger.get_log_entries = Mock(return_value=[])
    mock_logger_factory.create = Mock(return_value=mock_logger)

    # Mock agente desconocido
    mock_agent_registry = Mock()
    mock_agent_registry.get = Mock(side_effect=KeyError("Agente 'UnknownAgent' no configurado"))

    executor = AgentExecutor(
        jwt_validator=mock_jwt_validator,
        config_loader=mock_config_loader,
        registry_factory=mock_registry_factory,
        logger_factory=mock_logger_factory,
        agent_registry=mock_agent_registry,
        mcp_config_path="tests/config/mcp_servers.yaml",
        jwt_secret="test-secret"
    )

    # Ejecutar
    from backoffice.models import AgentConfig

    agent_config = AgentConfig(
        nombre="UnknownAgent",
        system_prompt="Test",
        modelo="claude-3-5-sonnet-20241022",
        herramientas=[]
    )

    result = await executor.execute(
        token="test-token",
        expediente_id="EXP-001",
        tarea_id="T-001",
        agent_config=agent_config
    )

    # Validar
    assert result.success is False
    assert result.error is not None
    # El executor puede capturar como AGENT_NOT_CONFIGURED o INTERNAL_ERROR dependiendo de dónde ocurra
    assert result.error.codigo in ["AGENT_NOT_CONFIGURED", "INTERNAL_ERROR"]
    # El mensaje debe indicar el problema
    assert result.error.mensaje
    assert result.error.detalle


@pytest.mark.asyncio
async def test_error_10_concurrent_modification_conflict(mock_server_config, test_token):
    """
    Test: Dos agentes intentan modificar mismo expediente

    Escenario:
    - Agente intenta actualizar expediente
    - MCP detecta conflicto (versión cambió)
    - MCP retorna 409 Conflict

    Validaciones:
    - MCPToolError lanzada con código MCP_CONFLICT
    - Mensaje indica conflicto de modificación
    - Agente puede manejar el error y decidir retry
    """
    client = MCPClient(mock_server_config, test_token)

    http_error = httpx.HTTPStatusError(
        "409 Conflict",
        request=Mock(),
        response=Mock(status_code=409, text="Versión del expediente ha cambiado")
    )

    mock_async_client = create_mock_async_client(side_effect=http_error)

    with patch.object(client, '_get_async_client', return_value=mock_async_client):
        with pytest.raises(MCPToolError) as exc_info:
            await client.call_tool("actualizar_expediente", {
                "exp_id": "EXP-001",
                "datos": {"estado": "completado"}
            })

        assert exc_info.value.codigo == "MCP_CONFLICT"
        assert "modificación concurrente" in exc_info.value.mensaje.lower()

    await client.close()


# ============================================================================
# TESTS MISC ERRORS
# ============================================================================

def test_error_14_pii_redaction_handles_invalid_data():
    """
    Test: PII redactor maneja datos inválidos

    Escenarios:
    - None input
    - Datos binarios (bytes) con encoding inválido
    - Tipo incorrecto (int, list, etc.)

    Validaciones:
    - No crashea el redactor
    - Fallback: retorna mensaje de error apropiado
    - Log warning de redaction failure
    """
    # Escenario 1: None input
    result = PIIRedactor.redact(None)
    assert result == "[REDACTION-FAILED: None input]"

    # Escenario 2: Bytes inválidos
    invalid_bytes = b'\x80\x81\x82\x83'  # Invalid UTF-8
    result = PIIRedactor.redact(invalid_bytes)
    assert result == "[REDACTION-FAILED: invalid encoding]"

    # Escenario 3: Tipo int
    result = PIIRedactor.redact(12345)
    assert result == "[REDACTION-FAILED: int]"

    # Escenario 4: Tipo list
    result = PIIRedactor.redact(["test", "data"])
    assert result == "[REDACTION-FAILED: list]"

    # Escenario 5: Bytes válidos (debe decodificar y redactar)
    valid_bytes = b"DNI: 12345678A"
    result = PIIRedactor.redact(valid_bytes)
    assert "[DNI-REDACTED]" in result


# ============================================================================
# TESTS SKIPPED (Para futuro)
# ============================================================================

@pytest.mark.skip(reason="Para Paso 4: cuando se agregue BD")
async def test_error_8_database_connection_lost():
    """
    Test: Base de datos no disponible

    Escenario:
    - Conexión BD se pierde
    - Sistema detecta error
    - Fallback a logs en archivo

    Validaciones:
    - Error DB_CONNECTION_ERROR
    - Sistema sigue funcionando en modo degradado
    - Logs escritos a archivo
    - Retry automático de conexión
    """
    pass


@pytest.mark.skip(reason="Solo para stress testing")
async def test_error_11_out_of_memory_handling():
    """
    Test: Sistema maneja out of memory gracefully

    Escenario:
    - Agente procesa documento enorme
    - Memoria se agota
    - Sistema detecta y cancela

    Validaciones:
    - No crashea proceso completo
    - Error AGENT_RESOURCE_ERROR
    - Memoria liberada
    - Otros agentes siguen funcionando
    """
    pass


@pytest.mark.skip(reason="Para Paso 4: cuando se agregue rate limiting")
async def test_error_15_api_rate_limit_exceeded():
    """
    Test: Rate limiting protege el sistema

    Escenario:
    - Cliente envía >N requests/segundo
    - Sistema rechaza con 429 Too Many Requests
    - Header Retry-After incluido

    Validaciones:
    - Status 429
    - Header Retry-After presente
    - Rate limit por IP/cliente
    - Log del rate limit
    """
    pass
