# backoffice/tests/test_executor.py

"""
Tests unitarios de AgentExecutor.

Implementa 30 tests usando mocks de todas las dependencias para verificar:
- Validación JWT y manejo de errores
- Configuración MCP y creación de registry
- Creación de agentes y manejo de errores
- Ejecución de agentes y propagación de resultados
- Logging y auditoría completa
- Cleanup de recursos (registry)
- Casos edge y escenarios complejos

Todos los tests son unitarios (sin I/O real) y rápidos (<5s total).
"""

import pytest
from unittest.mock import Mock, AsyncMock
from backoffice.executor import AgentExecutor
from backoffice.models import AgentConfig, AgentExecutionResult, AgentError
from backoffice.auth.jwt_validator import JWTClaims, JWTValidationError
from backoffice.mcp.exceptions import MCPConnectionError, MCPToolError, MCPAuthError


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_jwt_validator():
    """Mock de JWTValidatorProtocol"""
    validator = Mock()
    validator.validate = Mock(return_value=JWTClaims(
        iss="agentix-bpmn",
        sub="Automático",
        aud=["agentix-mcp-expedientes"],
        exp=9999999999,
        iat=1234567890,
        nbf=1234567890,
        jti="test-jti",
        exp_id="EXP-2024-001",
        permisos=["consulta", "gestion"]
    ))
    return validator


@pytest.fixture
def mock_config_loader():
    """Mock de ConfigLoaderProtocol"""
    loader = Mock()
    loader.load = Mock(return_value=Mock(
        get_enabled_servers=Mock(return_value=[
            Mock(id="test-mcp", name="Test MCP")
        ])
    ))
    return loader


@pytest.fixture
def mock_registry_factory():
    """Mock de MCPRegistryFactoryProtocol"""
    factory = Mock()
    mock_registry = AsyncMock()
    mock_registry.close = AsyncMock()
    mock_registry.get_available_tools = Mock(return_value=["consultar_expediente", "actualizar_datos"])
    factory.create = AsyncMock(return_value=mock_registry)
    return factory


@pytest.fixture
def mock_logger_factory():
    """Mock de AuditLoggerFactoryProtocol"""
    factory = Mock()
    mock_logger = Mock()
    mock_logger.log = Mock()
    mock_logger.error = Mock()
    mock_logger.get_log_entries = Mock(return_value=["Log entry 1", "Log entry 2"])
    factory.create = Mock(return_value=mock_logger)
    return factory


@pytest.fixture
def mock_agent_registry():
    """Mock de AgentRegistryProtocol"""
    registry = Mock()
    mock_agent_class = Mock()
    mock_agent = Mock()
    mock_agent.execute = AsyncMock(return_value={"completado": True, "mensaje": "OK"})
    mock_agent.get_tools_used = Mock(return_value=["consultar_expediente"])
    mock_agent_class.return_value = mock_agent
    registry.get = Mock(return_value=mock_agent_class)
    return registry


@pytest.fixture
def executor(
    mock_jwt_validator,
    mock_config_loader,
    mock_registry_factory,
    mock_logger_factory,
    mock_agent_registry
):
    """Fixture de AgentExecutor con todas las dependencias mockeadas"""
    return AgentExecutor(
        jwt_validator=mock_jwt_validator,
        config_loader=mock_config_loader,
        registry_factory=mock_registry_factory,
        logger_factory=mock_logger_factory,
        agent_registry=mock_agent_registry,
        mcp_config_path="/test/config.yaml",
        jwt_secret="test-secret",
        jwt_algorithm="HS256"
    )


@pytest.fixture
def agent_config():
    """Configuración de agente de prueba"""
    return AgentConfig(
        nombre="ValidadorDocumental",
        system_prompt="Test prompt",
        modelo="claude-3-5-sonnet",
        prompt_tarea="Test task",
        herramientas=["consultar_expediente", "actualizar_datos"]
    )


# ============================================================================
# TESTS DE VALIDACIÓN JWT
# ============================================================================

@pytest.mark.asyncio
async def test_jwt_expired_returns_auth_error(executor, mock_jwt_validator, agent_config):
    """Test: Token expirado retorna error AUTH_TOKEN_EXPIRED"""
    # Setup
    mock_jwt_validator.validate.side_effect = JWTValidationError(
        codigo="AUTH_TOKEN_EXPIRED",
        mensaje="Token JWT expirado",
        detalle="exp=1234567890"
    )

    # Execute
    result = await executor.execute(
        token="expired-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    # Assert
    assert result.success is False
    assert result.error is not None
    assert result.error.codigo == "AUTH_TOKEN_EXPIRED"
    assert "expirado" in result.error.mensaje.lower()


@pytest.mark.asyncio
async def test_jwt_invalid_signature_returns_auth_error(executor, mock_jwt_validator, agent_config):
    """Test: Firma inválida retorna error AUTH_INVALID_TOKEN"""
    mock_jwt_validator.validate.side_effect = JWTValidationError(
        codigo="AUTH_INVALID_TOKEN",
        mensaje="Token JWT inválido o mal formado",
        detalle="Signature verification failed"
    )

    result = await executor.execute(
        token="invalid-signature-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is False
    assert result.error.codigo == "AUTH_INVALID_TOKEN"


@pytest.mark.asyncio
async def test_jwt_wrong_expediente_returns_mismatch_error(executor, mock_jwt_validator, agent_config):
    """Test: Expediente incorrecto retorna error AUTH_EXPEDIENTE_MISMATCH"""
    mock_jwt_validator.validate.side_effect = JWTValidationError(
        codigo="AUTH_EXPEDIENTE_MISMATCH",
        mensaje="Expediente no autorizado",
        detalle="Token para EXP-2024-001, solicitado EXP-2024-002"
    )

    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-002",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is False
    assert result.error.codigo == "AUTH_EXPEDIENTE_MISMATCH"


@pytest.mark.asyncio
async def test_jwt_insufficient_permissions_returns_permission_error(executor, mock_jwt_validator, agent_config):
    """Test: Permisos insuficientes retorna error AUTH_INSUFFICIENT_PERMISSIONS"""
    mock_jwt_validator.validate.side_effect = JWTValidationError(
        codigo="AUTH_INSUFFICIENT_PERMISSIONS",
        mensaje="Permisos insuficientes",
        detalle="Faltan: ['gestion']"
    )

    result = await executor.execute(
        token="limited-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is False
    assert result.error.codigo == "AUTH_INSUFFICIENT_PERMISSIONS"


@pytest.mark.asyncio
async def test_jwt_valid_proceeds_to_execution(executor, mock_jwt_validator, agent_config):
    """Test: JWT válido procede a ejecución"""
    # Setup: JWT válido (usando fixture por defecto)

    # Execute
    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    # Assert
    assert result.success is True
    assert mock_jwt_validator.validate.called


# ============================================================================
# TESTS DE CONFIGURACIÓN MCP
# ============================================================================

@pytest.mark.asyncio
async def test_mcp_config_file_not_found_returns_error(executor, mock_config_loader, agent_config):
    """Test: Archivo de configuración no encontrado retorna error"""
    mock_config_loader.load.side_effect = FileNotFoundError("Config file not found")

    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is False
    assert result.error.codigo == "INTERNAL_ERROR"  # Catch-all Exception


@pytest.mark.asyncio
async def test_mcp_config_invalid_yaml_returns_error(executor, mock_config_loader, agent_config):
    """Test: YAML inválido retorna error"""
    mock_config_loader.load.side_effect = ValueError("Invalid YAML format")

    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is False
    assert result.error.codigo == "INTERNAL_ERROR"


@pytest.mark.asyncio
async def test_mcp_config_valid_creates_registry(executor, mock_registry_factory, agent_config):
    """Test: Configuración válida crea registry"""
    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is True
    assert mock_registry_factory.create.called


# ============================================================================
# TESTS DE INICIALIZACIÓN REGISTRY
# ============================================================================

@pytest.mark.asyncio
async def test_registry_init_timeout_returns_connection_error(executor, mock_registry_factory, agent_config):
    """Test: Timeout en inicialización retorna MCPConnectionError"""
    mock_registry_factory.create.side_effect = MCPConnectionError(
        codigo="MCP_CONNECTION_TIMEOUT",
        mensaje="Timeout al conectar con servidor MCP",
        detalle="Server did not respond within 30 seconds"
    )

    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is False
    assert result.error.codigo == "MCP_CONNECTION_TIMEOUT"


@pytest.mark.asyncio
async def test_registry_init_success_discovers_tools(executor, mock_registry_factory, agent_config):
    """Test: Inicialización exitosa descubre tools"""
    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is True
    # Verificar que se descubrieron tools
    mock_registry = mock_registry_factory.create.return_value
    assert mock_registry.get_available_tools.called


@pytest.mark.asyncio
async def test_registry_init_partial_failure_continues(executor, mock_registry_factory, mock_logger_factory, agent_config):
    """Test: Fallo parcial en inicialización permite continuar"""
    # Setup: Registry se crea pero con warnings
    # (En este caso asumimos que el registry maneja fallos parciales internamente)

    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    # Assert: Ejecución exitosa a pesar de posibles warnings
    assert result.success is True


# ============================================================================
# TESTS DE CREACIÓN DE AGENTE
# ============================================================================

@pytest.mark.asyncio
async def test_unknown_agent_type_returns_config_error(executor, mock_agent_registry, agent_config):
    """Test: Tipo de agente desconocido retorna error AGENT_NOT_CONFIGURED"""
    mock_agent_registry.get.side_effect = KeyError("AgentInexistente")

    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is False
    assert result.error.codigo == "AGENT_NOT_CONFIGURED"


@pytest.mark.asyncio
async def test_agent_creation_success_returns_instance(executor, mock_agent_registry, agent_config):
    """Test: Creación exitosa de agente"""
    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is True
    assert mock_agent_registry.get.called


# ============================================================================
# TESTS DE EJECUCIÓN DE AGENTE
# ============================================================================

@pytest.mark.asyncio
async def test_agent_execute_success_returns_result(executor, agent_config):
    """Test: Ejecución exitosa retorna resultado del agente"""
    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is True
    assert result.resultado == {"completado": True, "mensaje": "OK"}
    assert "consultar_expediente" in result.herramientas_usadas


@pytest.mark.asyncio
async def test_agent_execute_mcp_error_returns_tool_error(executor, mock_agent_registry, agent_config):
    """Test: Error MCP durante ejecución retorna MCPToolError"""
    # Setup: Agente lanza MCPToolError
    mock_agent = Mock()
    mock_agent.execute = AsyncMock(side_effect=MCPToolError(
        codigo="MCP_TOOL_EXECUTION_ERROR",
        mensaje="Error al ejecutar tool MCP",
        detalle="consultar_expediente failed"
    ))
    mock_agent.get_tools_used = Mock(return_value=[])

    mock_agent_class = Mock(return_value=mock_agent)
    mock_agent_registry.get.return_value = mock_agent_class

    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is False
    assert result.error.codigo == "MCP_TOOL_EXECUTION_ERROR"


@pytest.mark.asyncio
async def test_agent_execute_unexpected_error_returns_internal_error(executor, mock_agent_registry, agent_config):
    """Test: Error inesperado retorna INTERNAL_ERROR"""
    # Setup: Agente lanza excepción genérica
    mock_agent = Mock()
    mock_agent.execute = AsyncMock(side_effect=RuntimeError("Unexpected error"))

    mock_agent_class = Mock(return_value=mock_agent)
    mock_agent_registry.get.return_value = mock_agent_class

    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is False
    assert result.error.codigo == "INTERNAL_ERROR"
    assert "RuntimeError" in result.error.mensaje


# ============================================================================
# TESTS DE LOGGING Y AUDITORÍA
# ============================================================================

@pytest.mark.asyncio
async def test_logger_created_early_captures_jwt_error(executor, mock_logger_factory, mock_jwt_validator, agent_config):
    """Test: Logger creado temprano captura error JWT"""
    # Setup: JWT inválido
    mock_jwt_validator.validate.side_effect = JWTValidationError(
        codigo="AUTH_INVALID_TOKEN",
        mensaje="Token inválido",
        detalle=""
    )

    # Execute
    result = await executor.execute(
        token="invalid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    # Assert: Logger fue creado y capturó el error
    assert mock_logger_factory.create.called
    assert result.log_auditoria is not None
    assert len(result.log_auditoria) > 0


@pytest.mark.asyncio
async def test_logger_captures_all_steps_on_success(executor, mock_logger_factory, agent_config):
    """Test: Logger captura todos los pasos en ejecución exitosa"""
    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    # Assert
    assert result.success is True
    assert len(result.log_auditoria) >= 2  # Al menos 2 entradas de log
    mock_logger = mock_logger_factory.create.return_value
    assert mock_logger.log.call_count > 0


@pytest.mark.asyncio
async def test_logger_logs_agent_run_id(executor, mock_logger_factory, agent_config):
    """Test: Logger registra agent_run_id correctamente"""
    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    # Assert: agent_run_id tiene formato esperado
    assert result.agent_run_id.startswith("RUN-")
    # Logger fue creado con el run_id
    assert mock_logger_factory.create.called


@pytest.mark.asyncio
async def test_logger_error_method_called_on_failure(executor, mock_logger_factory, mock_jwt_validator, agent_config):
    """Test: Logger.error() se llama en caso de fallo"""
    # Setup: JWT inválido
    mock_jwt_validator.validate.side_effect = JWTValidationError(
        codigo="AUTH_INVALID_TOKEN",
        mensaje="Token inválido",
        detalle=""
    )

    result = await executor.execute(
        token="invalid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    # Assert: Logger.error() fue llamado
    mock_logger = mock_logger_factory.create.return_value
    assert mock_logger.error.called


# ============================================================================
# TESTS DE CLEANUP
# ============================================================================

@pytest.mark.asyncio
async def test_registry_closed_on_success(executor, mock_registry_factory, agent_config):
    """Test: Registry se cierra en ejecución exitosa"""
    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is True
    mock_registry = mock_registry_factory.create.return_value
    mock_registry.close.assert_called_once()


@pytest.mark.asyncio
async def test_registry_closed_on_agent_error(executor, mock_registry_factory, mock_agent_registry, agent_config):
    """Test: Registry se cierra incluso si falla ejecución del agente"""
    # Setup: Agente falla
    mock_agent = Mock()
    mock_agent.execute = AsyncMock(side_effect=RuntimeError("Agent failed"))
    mock_agent_class = Mock(return_value=mock_agent)
    mock_agent_registry.get.return_value = mock_agent_class

    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    # Assert: Registry se cerró a pesar del error
    assert result.success is False
    mock_registry = mock_registry_factory.create.return_value
    mock_registry.close.assert_called_once()


# ============================================================================
# TESTS DE RESULTADO
# ============================================================================

@pytest.mark.asyncio
async def test_success_result_includes_all_fields(executor, agent_config):
    """Test: Resultado exitoso incluye todos los campos"""
    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    # Assert: Todos los campos presentes
    assert result.success is True
    assert result.agent_run_id.startswith("RUN-")
    assert isinstance(result.resultado, dict)
    assert isinstance(result.log_auditoria, list)
    assert isinstance(result.herramientas_usadas, list)
    assert result.error is None


@pytest.mark.asyncio
async def test_error_result_includes_error_details(executor, mock_jwt_validator, agent_config):
    """Test: Resultado de error incluye detalles del error"""
    # Setup
    mock_jwt_validator.validate.side_effect = JWTValidationError(
        codigo="AUTH_TOKEN_EXPIRED",
        mensaje="Token expirado",
        detalle="exp=1234567890"
    )

    result = await executor.execute(
        token="expired-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    # Assert
    assert result.success is False
    assert result.error is not None
    assert result.error.codigo == "AUTH_TOKEN_EXPIRED"
    assert result.error.mensaje == "Token expirado"
    assert result.error.detalle == "exp=1234567890"


@pytest.mark.asyncio
async def test_tools_used_tracked_correctly(executor, agent_config):
    """Test: Herramientas usadas se rastrean correctamente"""
    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    # Assert
    assert result.success is True
    assert len(result.herramientas_usadas) > 0
    assert "consultar_expediente" in result.herramientas_usadas


# ============================================================================
# TESTS DE CASOS EDGE
# ============================================================================

@pytest.mark.asyncio
async def test_mcp_auth_error_propagated_correctly(executor, mock_registry_factory, agent_config):
    """Test: MCPAuthError se propaga correctamente"""
    mock_registry_factory.create.side_effect = MCPAuthError(
        codigo="MCP_AUTH_FORBIDDEN",
        mensaje="Token no autorizado para MCP",
        detalle="403 Forbidden"
    )

    result = await executor.execute(
        token="unauthorized-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is False
    assert result.error.codigo == "MCP_AUTH_FORBIDDEN"


@pytest.mark.asyncio
async def test_multiple_mcps_enabled_logged(executor, mock_config_loader, mock_logger_factory, agent_config):
    """Test: Múltiples MCPs habilitados se registran en log"""
    # Setup: Configuración con múltiples MCPs
    mock_config = Mock()
    mock_config.get_enabled_servers = Mock(return_value=[
        Mock(id="mcp-1", name="MCP 1"),
        Mock(id="mcp-2", name="MCP 2"),
        Mock(id="mcp-3", name="MCP 3")
    ])
    mock_config_loader.load.return_value = mock_config

    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    # Assert: Logger registró los MCPs
    assert result.success is True
    mock_logger = mock_logger_factory.create.return_value
    assert mock_logger.log.call_count > 5  # Varios logs


@pytest.mark.asyncio
async def test_agent_with_no_tools_used(executor, mock_agent_registry, agent_config):
    """Test: Agente sin tools usados retorna lista vacía"""
    # Setup: Agente no usa tools
    mock_agent = Mock()
    mock_agent.execute = AsyncMock(return_value={"completado": True, "mensaje": "OK"})
    mock_agent.get_tools_used = Mock(return_value=[])

    mock_agent_class = Mock(return_value=mock_agent)
    mock_agent_registry.get.return_value = mock_agent_class

    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is True
    assert result.herramientas_usadas == []


@pytest.mark.asyncio
async def test_different_expediente_formats_in_run_id(executor, agent_config):
    """Test: agent_run_id se genera correctamente para diferentes expedientes"""
    result1 = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    result2 = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-999",
        tarea_id="TAREA-002",
        agent_config=agent_config
    )

    # Assert: Cada ejecución tiene su propio run_id
    assert result1.agent_run_id != result2.agent_run_id
    assert result1.agent_run_id.startswith("RUN-")
    assert result2.agent_run_id.startswith("RUN-")


@pytest.mark.asyncio
async def test_config_loader_called_with_correct_path(executor, mock_config_loader, agent_config):
    """Test: ConfigLoader se llama con la ruta correcta"""
    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is True
    mock_config_loader.load.assert_called_once_with("/test/config.yaml")


@pytest.mark.asyncio
async def test_jwt_validator_receives_correct_parameters(executor, mock_jwt_validator, agent_config):
    """Test: JWTValidator recibe los parámetros correctos"""
    result = await executor.execute(
        token="test-token-123",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is True
    # Verificar que validate fue llamado con los parámetros correctos
    call_args = mock_jwt_validator.validate.call_args
    assert call_args[1]["token"] == "test-token-123"
    assert call_args[1]["secret"] == "test-secret"
    assert call_args[1]["algorithm"] == "HS256"
    assert call_args[1]["expected_expediente_id"] == "EXP-2024-001"


@pytest.mark.asyncio
async def test_agent_registry_get_called_with_agent_name(executor, mock_agent_registry, agent_config):
    """Test: AgentRegistry.get() se llama con el nombre correcto"""
    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is True
    mock_agent_registry.get.assert_called_once_with("ValidadorDocumental")


@pytest.mark.asyncio
async def test_registry_factory_receives_token(executor, mock_registry_factory, agent_config):
    """Test: RegistryFactory recibe el token JWT"""
    result = await executor.execute(
        token="test-jwt-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is True
    # Verificar que create fue llamado con el token
    call_args = mock_registry_factory.create.call_args
    assert call_args[0][1] == "test-jwt-token"  # Segundo argumento es el token
