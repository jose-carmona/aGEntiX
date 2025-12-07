# Plan de Mejoras: AgentExecutor

**Objetivo:** Transformar AgentExecutor en una clase robusta, testeable y mantenible

**Fecha:** 2024-12-07
**Prioridad:** P0 (CRÍTICA) - Debe completarse antes de Paso 2

---

## Resumen Ejecutivo

### Estado Actual vs Objetivo

| Métrica | Actual | Objetivo | Gap |
|---------|--------|----------|-----|
| Tests unitarios | 0 | 30 | -30 tests |
| Cobertura | 0% | 80% | -80% |
| Acoplamiento | Alto | Bajo | DI requerida |
| Validaciones | 0 | 2 (entrada/salida) | -2 validadores |

### Esfuerzo Total

- **Tiempo:** 26-39 horas (3-5 días)
- **Complejidad:** Media-Alta
- **Riesgo:** Bajo (cambios backward-compatible)

---

## Fase 1: Tests Unitarios y Dependency Injection

**Prioridad:** P0 (CRÍTICA)
**Tiempo:** 14-21 horas
**Objetivo:** Permitir testing unitario mediante inyección de dependencias

### P0.1 - Crear Abstracciones (Protocols)

**Tiempo:** 2-3 horas

**Archivo:** `backoffice/protocols.py` (NUEVO)

```python
# backoffice/protocols.py

from typing import Protocol, Dict, Any, List
from backoffice.models import AgentConfig
from backoffice.auth.jwt_validator import JWTClaims
from backoffice.config.models import MCPServersConfig
from backoffice.logging.audit_logger import AuditLogger
from backoffice.mcp.registry import MCPClientRegistry


class JWTValidatorProtocol(Protocol):
    """Abstracción de validador JWT para testing"""

    def validate(
        self,
        token: str,
        secret: str,
        algorithm: str,
        expected_expediente_id: str,
        required_permissions: List[str]
    ) -> JWTClaims:
        """Valida un token JWT"""
        ...


class ConfigLoaderProtocol(Protocol):
    """Abstracción de cargador de configuración MCP"""

    def load(self, path: str) -> MCPServersConfig:
        """Carga configuración MCP desde archivo"""
        ...


class MCPRegistryFactoryProtocol(Protocol):
    """Factory para crear MCPClientRegistry"""

    async def create(
        self,
        config: MCPServersConfig,
        token: str
    ) -> MCPClientRegistry:
        """Crea y inicializa un MCPClientRegistry"""
        ...


class AuditLoggerFactoryProtocol(Protocol):
    """Factory para crear AuditLogger"""

    def create(
        self,
        expediente_id: str,
        agent_run_id: str,
        log_dir: str
    ) -> AuditLogger:
        """Crea un AuditLogger"""
        ...


class AgentRegistryProtocol(Protocol):
    """Registro de agentes disponibles"""

    def get(self, nombre: str) -> type:
        """Obtiene clase de agente por nombre"""
        ...
```

**Tests:**
```python
# backoffice/tests/test_protocols.py

def test_protocols_are_importable():
    from backoffice.protocols import (
        JWTValidatorProtocol,
        ConfigLoaderProtocol,
        MCPRegistryFactoryProtocol,
        AuditLoggerFactoryProtocol,
        AgentRegistryProtocol
    )
    # Si importa sin errores, el test pasa
```

**Criterio de aceptación:**
- ✅ Todos los protocols importan sin errores
- ✅ MyPy no reporta errores de tipo

---

### P0.2 - Refactorizar AgentExecutor para DI

**Tiempo:** 4-6 horas

**Archivo:** `backoffice/executor.py`

**Cambios:**

1. **Nuevo constructor con DI**

```python
# backoffice/executor.py

from typing import Optional
from .protocols import (
    JWTValidatorProtocol,
    ConfigLoaderProtocol,
    MCPRegistryFactoryProtocol,
    AuditLoggerFactoryProtocol,
    AgentRegistryProtocol
)


class AgentExecutor:
    """
    Ejecutor principal de agentes.

    Ahora con inyección de dependencias para facilitar testing.
    """

    def __init__(
        self,
        jwt_validator: JWTValidatorProtocol,
        config_loader: ConfigLoaderProtocol,
        registry_factory: MCPRegistryFactoryProtocol,
        logger_factory: AuditLoggerFactoryProtocol,
        agent_registry: AgentRegistryProtocol,
        mcp_config_path: str,
        jwt_secret: str,
        jwt_algorithm: str = "HS256"
    ):
        """
        Inicializa el executor con dependencias inyectadas.

        Args:
            jwt_validator: Validador de tokens JWT
            config_loader: Cargador de configuración MCP
            registry_factory: Factory para crear MCPClientRegistry
            logger_factory: Factory para crear AuditLogger
            agent_registry: Registro de agentes disponibles
            mcp_config_path: Ruta al archivo de configuración de MCPs
            jwt_secret: Clave secreta para validar JWT
            jwt_algorithm: Algoritmo JWT (default: HS256)
        """
        self.jwt_validator = jwt_validator
        self.config_loader = config_loader
        self.registry_factory = registry_factory
        self.logger_factory = logger_factory
        self.agent_registry = agent_registry
        self.mcp_config_path = mcp_config_path
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm

    async def execute(
        self,
        token: str,
        expediente_id: str,
        tarea_id: str,
        agent_config: AgentConfig
    ) -> AgentExecutionResult:
        """Ejecuta un agente (mismo comportamiento, nueva implementación)"""
        mcp_registry = None
        logger = None
        agent_run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}"

        try:
            # 0. Crear logger usando factory
            logger = self.logger_factory.create(
                expediente_id=expediente_id,
                agent_run_id=agent_run_id,
                log_dir=str(Path(self.mcp_config_path).parent.parent / "logs" / "agent_runs")
            )

            logger.log(f"Iniciando ejecución de agente {agent_config.nombre}")

            # 1. Validar JWT usando validador inyectado
            logger.log("Validando token JWT...")
            required_permissions = get_required_permissions_for_tools(agent_config.herramientas)
            claims = self.jwt_validator.validate(
                token=token,
                secret=self.jwt_secret,
                algorithm=self.jwt_algorithm,
                expected_expediente_id=expediente_id,
                required_permissions=required_permissions
            )
            logger.log(f"Token JWT válido para expediente {claims.exp_id}")

            # 2. Cargar configuración usando loader inyectado
            logger.log(f"Cargando configuración de MCPs desde {self.mcp_config_path}...")
            mcp_config = self.config_loader.load(self.mcp_config_path)

            # 3. Crear registry usando factory inyectado
            logger.log("Creando registry de clientes MCP...")
            mcp_registry = await self.registry_factory.create(mcp_config, token)

            # Logear MCPs disponibles
            enabled_mcps = [s.id for s in mcp_config.get_enabled_servers()]
            logger.log(f"MCPs habilitados: {enabled_mcps}")

            # 4. Crear agente usando registry inyectado
            logger.log(f"Creando agente {agent_config.nombre}...")
            agent_class = self.agent_registry.get(agent_config.nombre)
            agent = agent_class(
                expediente_id=expediente_id,
                tarea_id=tarea_id,
                run_id=agent_run_id,
                mcp_registry=mcp_registry,
                logger=logger
            )

            # 5. Ejecutar agente
            logger.log(f"Ejecutando agente {agent_config.nombre}...")
            resultado = await agent.execute()

            logger.log("Agente completado exitosamente")

            return AgentExecutionResult(
                success=True,
                agent_run_id=agent_run_id,
                resultado=resultado,
                log_auditoria=logger.get_log_entries(),
                herramientas_usadas=agent.get_tools_used()
            )

        except JWTValidationError as e:
            # Manejo de errores JWT
            if logger:
                logger.error(f"Error de validación JWT: {e.mensaje}")
            return AgentExecutionResult(
                success=False,
                agent_run_id=agent_run_id,
                resultado={},
                log_auditoria=logger.get_log_entries() if logger else [],
                herramientas_usadas=[],
                error=AgentError(
                    codigo=e.codigo,
                    mensaje=e.mensaje,
                    detalle=e.detalle
                )
            )

        # ... resto del error handling igual ...

        finally:
            if mcp_registry:
                await mcp_registry.close()
```

2. **Factory para backward compatibility**

```python
# backoffice/executor_factory.py (NUEVO)

from pathlib import Path
from backoffice.executor import AgentExecutor
from backoffice.settings import settings
from backoffice.auth.jwt_validator import validate_jwt
from backoffice.config.models import MCPServersConfig
from backoffice.mcp.registry import MCPClientRegistry
from backoffice.logging.audit_logger import AuditLogger
from backoffice.agents.registry import get_agent_class


class DefaultJWTValidator:
    """Implementación por defecto de JWTValidatorProtocol"""

    def validate(self, token, secret, algorithm, expected_expediente_id, required_permissions):
        return validate_jwt(
            token=token,
            secret=secret,
            algorithm=algorithm,
            expected_expediente_id=expected_expediente_id,
            required_permissions=required_permissions
        )


class DefaultConfigLoader:
    """Implementación por defecto de ConfigLoaderProtocol"""

    def load(self, path: str) -> MCPServersConfig:
        return MCPServersConfig.load_from_file(path)


class DefaultMCPRegistryFactory:
    """Implementación por defecto de MCPRegistryFactoryProtocol"""

    async def create(self, config: MCPServersConfig, token: str) -> MCPClientRegistry:
        registry = MCPClientRegistry(config, token)
        await registry.initialize()
        return registry


class DefaultAuditLoggerFactory:
    """Implementación por defecto de AuditLoggerFactoryProtocol"""

    def create(self, expediente_id: str, agent_run_id: str, log_dir: str) -> AuditLogger:
        return AuditLogger(
            expediente_id=expediente_id,
            agent_run_id=agent_run_id,
            log_dir=Path(log_dir)
        )


class DefaultAgentRegistry:
    """Implementación por defecto de AgentRegistryProtocol"""

    def get(self, nombre: str) -> type:
        return get_agent_class(nombre)


def create_default_executor(
    mcp_config_path: str = None,
    log_dir: str = None,
    jwt_secret: str = None,
    jwt_algorithm: str = "HS256"
) -> AgentExecutor:
    """
    Factory para crear AgentExecutor con implementaciones por defecto.

    Mantiene backward compatibility con código existente.
    """
    return AgentExecutor(
        jwt_validator=DefaultJWTValidator(),
        config_loader=DefaultConfigLoader(),
        registry_factory=DefaultMCPRegistryFactory(),
        logger_factory=DefaultAuditLoggerFactory(),
        agent_registry=DefaultAgentRegistry(),
        mcp_config_path=mcp_config_path or settings.mcp_config_path,
        jwt_secret=jwt_secret or settings.jwt_secret,
        jwt_algorithm=jwt_algorithm
    )
```

**Criterio de aceptación:**
- ✅ Código existente sigue funcionando sin cambios (usando factory)
- ✅ Se pueden inyectar mocks en tests
- ✅ MyPy no reporta errores de tipo

---

### P0.3 - Crear Suite de Tests Unitarios

**Tiempo:** 8-12 horas

**Archivo:** `backoffice/tests/test_executor.py` (NUEVO)

**Estructura:**

```python
# backoffice/tests/test_executor.py

import pytest
from unittest.mock import Mock, AsyncMock
from backoffice.executor import AgentExecutor
from backoffice.models import AgentConfig, AgentExecutionResult, AgentError
from backoffice.auth.jwt_validator import JWTClaims, JWTValidationError


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
    mock_registry.get_available_tools = Mock(return_value=["consultar_expediente"])
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


# === TESTS DE VALIDACIÓN JWT ===

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


# === TESTS DE CONFIGURACIÓN MCP ===

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


# === TESTS DE CREACIÓN DE AGENTE ===

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


# === TESTS DE EJECUCIÓN DE AGENTE ===

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


# === TESTS DE LOGGING Y AUDITORÍA ===

@pytest.mark.asyncio
async def test_logger_created_early_captures_jwt_error(executor, mock_logger_factory, mock_jwt_validator, agent_config):
    """Test: Logger creado temprano captura error JWT"""
    # Setup: JWT inválido
    mock_jwt_validator.validate.side_effect = JWTValidationError(
        codigo="AUTH_INVALID_TOKEN",
        mensaje="Token inválido"
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


# === TESTS DE CLEANUP ===

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
    mock_registry = await mock_registry_factory.create.return_value
    mock_registry.close.assert_called_once()


@pytest.mark.asyncio
async def test_registry_closed_on_error(executor, mock_registry_factory, mock_jwt_validator, agent_config):
    """Test: Registry se cierra incluso con error JWT"""
    # Setup: Error JWT (antes de crear registry)
    mock_jwt_validator.validate.side_effect = JWTValidationError(
        codigo="AUTH_INVALID_TOKEN",
        mensaje="Token inválido"
    )

    result = await executor.execute(
        token="invalid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    # Assert: Registry NO se creó, así que NO debería cerrarse
    assert result.success is False
    assert not mock_registry_factory.create.called


# === TESTS DE RESULTADO ===

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
```

**Total:** 30 tests unitarios

**Criterio de aceptación:**
- ✅ Todos los tests pasan (30/30)
- ✅ Cobertura de `executor.py` > 80%
- ✅ Tests se ejecutan en < 5 segundos (sin I/O real)

---

## Fase 2: Validaciones de Entrada/Salida

**Prioridad:** P1 (ALTA)
**Tiempo:** 5-8 horas
**Objetivo:** Validar parámetros de entrada y resultado de agentes

### P1.1 - Validación de Parámetros de Entrada

**Tiempo:** 2-3 horas

**Archivo:** `backoffice/executor.py`

**Código:**

```python
# backoffice/executor.py

import re

class AgentExecutor:
    # ... constructor ...

    def _validate_inputs(
        self,
        token: str,
        expediente_id: str,
        tarea_id: str,
        agent_config: AgentConfig
    ) -> Optional[AgentError]:
        """
        Valida parámetros de entrada antes de ejecutar.

        Args:
            token: Token JWT
            expediente_id: ID del expediente
            tarea_id: ID de la tarea
            agent_config: Configuración del agente

        Returns:
            AgentError si hay error de validación, None si todo OK
        """
        # 1. Validar token
        if not token or not token.strip():
            return AgentError(
                codigo="INPUT_VALIDATION_ERROR",
                mensaje="Token JWT vacío o inválido",
                detalle="El parámetro 'token' es obligatorio y no puede estar vacío"
            )

        # 2. Validar expediente_id (formato: EXP-YYYY-NNN)
        if not expediente_id or not expediente_id.strip():
            return AgentError(
                codigo="INPUT_VALIDATION_ERROR",
                mensaje="expediente_id vacío",
                detalle="El parámetro 'expediente_id' es obligatorio"
            )

        if not re.match(r'^EXP-\d{4}-\d{3}$', expediente_id):
            return AgentError(
                codigo="INPUT_VALIDATION_ERROR",
                mensaje=f"Formato de expediente_id inválido: '{expediente_id}'",
                detalle="Formato esperado: EXP-YYYY-NNN (ej: EXP-2024-001)"
            )

        # 3. Validar tarea_id
        if not tarea_id or not tarea_id.strip():
            return AgentError(
                codigo="INPUT_VALIDATION_ERROR",
                mensaje="tarea_id vacío",
                detalle="El parámetro 'tarea_id' es obligatorio"
            )

        # 4. Validar agent_config
        if not agent_config.nombre or not agent_config.nombre.strip():
            return AgentError(
                codigo="AGENT_CONFIG_INVALID",
                mensaje="Nombre de agente vacío en configuración",
                detalle="agent_config.nombre es obligatorio"
            )

        if not agent_config.herramientas or len(agent_config.herramientas) == 0:
            return AgentError(
                codigo="AGENT_CONFIG_INVALID",
                mensaje="Lista de herramientas vacía en configuración",
                detalle="agent_config.herramientas debe contener al menos una herramienta"
            )

        # Todo OK
        return None

    async def execute(
        self,
        token: str,
        expediente_id: str,
        tarea_id: str,
        agent_config: AgentConfig
    ) -> AgentExecutionResult:
        """Ejecuta un agente con validación de entrada"""

        # === VALIDACIÓN DE INPUTS ===
        validation_error = self._validate_inputs(token, expediente_id, tarea_id, agent_config)
        if validation_error:
            return AgentExecutionResult(
                success=False,
                agent_run_id="INVALID-INPUT",
                resultado={},
                log_auditoria=[f"Error de validación: {validation_error.mensaje}"],
                herramientas_usadas=[],
                error=validation_error
            )

        # === FLUJO NORMAL ===
        mcp_registry = None
        logger = None
        agent_run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}"

        try:
            # ... resto del código igual ...
```

**Criterio de aceptación:**
- ✅ Inputs inválidos retornan error antes de crear logger
- ✅ Formato de expediente_id validado correctamente
- ✅ Tests de validación pasan (ver P1.3)

---

### P1.2 - Validación de Resultado del Agente

**Tiempo:** 1-2 horas

**Archivo:** `backoffice/executor.py`

**Código:**

```python
# backoffice/executor.py

class AgentExecutor:
    # ... otros métodos ...

    def _validate_agent_result(self, resultado: Any) -> Optional[AgentError]:
        """
        Valida que el resultado del agente tenga estructura esperada.

        Args:
            resultado: Resultado retornado por agent.execute()

        Returns:
            AgentError si hay error de validación, None si todo OK
        """
        # 1. Debe ser un diccionario
        if not isinstance(resultado, dict):
            return AgentError(
                codigo="OUTPUT_VALIDATION_ERROR",
                mensaje="Resultado del agente no es un diccionario",
                detalle=f"Tipo recibido: {type(resultado).__name__}, esperado: dict"
            )

        # 2. Debe tener campo 'completado' (bool)
        if "completado" not in resultado:
            return AgentError(
                codigo="OUTPUT_VALIDATION_ERROR",
                mensaje="Resultado del agente falta campo 'completado'",
                detalle=f"Campos presentes: {list(resultado.keys())}"
            )

        if not isinstance(resultado["completado"], bool):
            return AgentError(
                codigo="OUTPUT_VALIDATION_ERROR",
                mensaje="Campo 'completado' debe ser booleano",
                detalle=f"Tipo recibido: {type(resultado['completado']).__name__}"
            )

        # 3. Debe tener campo 'mensaje' (str)
        if "mensaje" not in resultado:
            return AgentError(
                codigo="OUTPUT_VALIDATION_ERROR",
                mensaje="Resultado del agente falta campo 'mensaje'",
                detalle=f"Campos presentes: {list(resultado.keys())}"
            )

        if not isinstance(resultado["mensaje"], str):
            return AgentError(
                codigo="OUTPUT_VALIDATION_ERROR",
                mensaje="Campo 'mensaje' debe ser string",
                detalle=f"Tipo recibido: {type(resultado['mensaje']).__name__}"
            )

        # Todo OK
        return None

    async def execute(self, token, expediente_id, tarea_id, agent_config):
        # ... setup y validación de inputs ...

        try:
            # ... creación y ejecución del agente ...

            logger.log(f"Ejecutando agente {agent_config.nombre}...")
            resultado = await agent.execute()

            # === VALIDAR RESULTADO DEL AGENTE ===
            validation_error = self._validate_agent_result(resultado)
            if validation_error:
                logger.error(f"Resultado de agente inválido: {validation_error.mensaje}")
                return AgentExecutionResult(
                    success=False,
                    agent_run_id=agent_run_id,
                    resultado={},
                    log_auditoria=logger.get_log_entries(),
                    herramientas_usadas=agent.get_tools_used(),
                    error=validation_error
                )

            logger.log("Agente completado exitosamente")

            return AgentExecutionResult(
                success=True,
                agent_run_id=agent_run_id,
                resultado=resultado,
                log_auditoria=logger.get_log_entries(),
                herramientas_usadas=agent.get_tools_used()
            )

        # ... resto del error handling ...
```

**Criterio de aceptación:**
- ✅ Resultado no-dict detectado
- ✅ Campos faltantes detectados
- ✅ Tests de validación pasan (ver P1.3)

---

### P1.3 - Tests de Validaciones

**Tiempo:** 2-3 horas

**Archivo:** `backoffice/tests/test_executor.py`

**Código adicional:**

```python
# === TESTS DE VALIDACIÓN DE ENTRADA ===

@pytest.mark.asyncio
async def test_empty_token_returns_validation_error(executor, agent_config):
    """Test: Token vacío retorna INPUT_VALIDATION_ERROR"""
    result = await executor.execute(
        token="",  # Token vacío
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is False
    assert result.error.codigo == "INPUT_VALIDATION_ERROR"
    assert "token" in result.error.mensaje.lower()


@pytest.mark.asyncio
async def test_empty_expediente_id_returns_validation_error(executor, agent_config):
    """Test: expediente_id vacío retorna INPUT_VALIDATION_ERROR"""
    result = await executor.execute(
        token="valid-token",
        expediente_id="",  # Expediente vacío
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is False
    assert result.error.codigo == "INPUT_VALIDATION_ERROR"
    assert "expediente_id" in result.error.mensaje.lower()


@pytest.mark.asyncio
async def test_invalid_expediente_format_returns_validation_error(executor, agent_config):
    """Test: Formato inválido de expediente_id retorna INPUT_VALIDATION_ERROR"""
    result = await executor.execute(
        token="valid-token",
        expediente_id="INVALID-FORMAT",  # Formato incorrecto
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is False
    assert result.error.codigo == "INPUT_VALIDATION_ERROR"
    assert "formato" in result.error.mensaje.lower()
    assert "EXP-YYYY-NNN" in result.error.detalle


@pytest.mark.asyncio
async def test_empty_tarea_id_returns_validation_error(executor, agent_config):
    """Test: tarea_id vacío retorna INPUT_VALIDATION_ERROR"""
    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="",  # Tarea vacía
        agent_config=agent_config
    )

    assert result.success is False
    assert result.error.codigo == "INPUT_VALIDATION_ERROR"
    assert "tarea_id" in result.error.mensaje.lower()


@pytest.mark.asyncio
async def test_invalid_agent_config_returns_validation_error(executor):
    """Test: agent_config inválido retorna AGENT_CONFIG_INVALID"""
    invalid_config = AgentConfig(
        nombre="",  # Nombre vacío
        system_prompt="Test",
        modelo="claude",
        prompt_tarea="Test",
        herramientas=[]
    )

    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=invalid_config
    )

    assert result.success is False
    assert result.error.codigo == "AGENT_CONFIG_INVALID"


# === TESTS DE VALIDACIÓN DE SALIDA ===

@pytest.mark.asyncio
async def test_agent_result_not_dict_returns_validation_error(executor, mock_agent_registry, agent_config):
    """Test: Resultado no-dict retorna OUTPUT_VALIDATION_ERROR"""
    # Setup: Agente retorna lista en lugar de dict
    mock_agent = Mock()
    mock_agent.execute = AsyncMock(return_value=["not", "a", "dict"])
    mock_agent.get_tools_used = Mock(return_value=[])
    mock_agent_class = Mock(return_value=mock_agent)
    mock_agent_registry.get = Mock(return_value=mock_agent_class)

    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is False
    assert result.error.codigo == "OUTPUT_VALIDATION_ERROR"
    assert "diccionario" in result.error.mensaje.lower()


@pytest.mark.asyncio
async def test_agent_result_missing_completado_returns_validation_error(executor, mock_agent_registry, agent_config):
    """Test: Resultado sin campo 'completado' retorna OUTPUT_VALIDATION_ERROR"""
    # Setup: Resultado sin campo 'completado'
    mock_agent = Mock()
    mock_agent.execute = AsyncMock(return_value={"mensaje": "OK"})  # Falta 'completado'
    mock_agent.get_tools_used = Mock(return_value=[])
    mock_agent_class = Mock(return_value=mock_agent)
    mock_agent_registry.get = Mock(return_value=mock_agent_class)

    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is False
    assert result.error.codigo == "OUTPUT_VALIDATION_ERROR"
    assert "completado" in result.error.mensaje.lower()


@pytest.mark.asyncio
async def test_agent_result_missing_mensaje_returns_validation_error(executor, mock_agent_registry, agent_config):
    """Test: Resultado sin campo 'mensaje' retorna OUTPUT_VALIDATION_ERROR"""
    # Setup: Resultado sin campo 'mensaje'
    mock_agent = Mock()
    mock_agent.execute = AsyncMock(return_value={"completado": True})  # Falta 'mensaje'
    mock_agent.get_tools_used = Mock(return_value=[])
    mock_agent_class = Mock(return_value=mock_agent)
    mock_agent_registry.get = Mock(return_value=mock_agent_class)

    result = await executor.execute(
        token="valid-token",
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-001",
        agent_config=agent_config
    )

    assert result.success is False
    assert result.error.codigo == "OUTPUT_VALIDATION_ERROR"
    assert "mensaje" in result.error.mensaje.lower()
```

**Total adicional:** 8 tests de validación

**Criterio de aceptación:**
- ✅ Todos los tests pasan (38/38 total)
- ✅ Validaciones detectan todos los casos edge

---

## Fase 3: Mejoras Opcionales

**Prioridad:** P2-P3 (MEDIA-BAJA)
**Tiempo:** 7-10 horas
**Objetivo:** Mejorar mantenibilidad y debugging

### P2.1 - Mejorar Logging de Excepciones

**Tiempo:** 1 hora

**Archivo:** `backoffice/executor.py`

**Código:**

```python
except Exception as e:
    # Logging mejorado con stacktrace
    import traceback
    stacktrace = traceback.format_exc()

    if logger:
        logger.error(f"Error inesperado: {type(e).__name__}: {str(e)}")
        logger.error(f"Stacktrace completo:")
        for line in stacktrace.split('\n'):
            if line.strip():
                logger.error(f"  {line}")

    return AgentExecutionResult(
        success=False,
        agent_run_id=agent_run_id,
        resultado={},
        log_auditoria=logger.get_log_entries() if logger else [],
        herramientas_usadas=[],
        error=AgentError(
            codigo="INTERNAL_ERROR",
            mensaje=f"Error interno del sistema: {type(e).__name__}",
            detalle=f"{str(e)}\n\n--- Stacktrace Completo ---\n{stacktrace}"
        )
    )
```

---

### P3.1 - Split execute() en Métodos Privados

**Tiempo:** 4-6 horas

**Archivo:** `backoffice/executor.py`

**Código:**

```python
class AgentExecutor:
    # ... constructor y validadores ...

    async def execute(
        self,
        token: str,
        expediente_id: str,
        tarea_id: str,
        agent_config: AgentConfig
    ) -> AgentExecutionResult:
        """
        Ejecuta un agente (refactorizado en métodos privados).

        Flujo:
        1. Validar inputs
        2. Setup (logger, JWT, config MCP)
        3. Infraestructura (registry MCP)
        4. Ejecución (agente)
        5. Validación de resultado
        6. Cleanup
        """
        # 1. Validar inputs
        validation_error = self._validate_inputs(token, expediente_id, tarea_id, agent_config)
        if validation_error:
            return self._create_error_result("INVALID-INPUT", validation_error, [])

        # 2. Setup
        agent_run_id = self._generate_run_id()
        logger = self._create_logger(expediente_id, agent_run_id)
        mcp_registry = None

        try:
            # 3. Validar JWT
            claims = await self._validate_jwt_and_log(token, expediente_id, agent_config, logger)

            # 4. Setup infraestructura MCP
            mcp_registry = await self._setup_mcp_infrastructure(token, logger)

            # 5. Ejecutar agente
            resultado, tools_used = await self._execute_agent(
                expediente_id, tarea_id, agent_run_id,
                agent_config, mcp_registry, logger
            )

            # 6. Validar resultado
            validation_error = self._validate_agent_result(resultado)
            if validation_error:
                logger.error(f"Resultado de agente inválido: {validation_error.mensaje}")
                return self._create_error_result(agent_run_id, validation_error, logger, tools_used)

            logger.log("Agente completado exitosamente")
            return self._create_success_result(agent_run_id, resultado, logger, tools_used)

        except JWTValidationError as e:
            return self._handle_jwt_error(agent_run_id, e, logger)
        except MCPConnectionError as e:
            return self._handle_mcp_connection_error(agent_run_id, e, logger)
        except MCPAuthError as e:
            return self._handle_mcp_auth_error(agent_run_id, e, logger)
        except MCPToolError as e:
            return self._handle_mcp_tool_error(agent_run_id, e, logger)
        except Exception as e:
            return self._handle_unexpected_error(agent_run_id, e, logger)

        finally:
            if mcp_registry:
                await mcp_registry.close()

    def _generate_run_id(self) -> str:
        """Genera ID único de ejecución"""
        return f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}"

    def _create_logger(self, expediente_id: str, agent_run_id: str) -> AuditLogger:
        """Crea logger de auditoría"""
        return self.logger_factory.create(
            expediente_id=expediente_id,
            agent_run_id=agent_run_id,
            log_dir=str(Path(self.mcp_config_path).parent.parent / "logs" / "agent_runs")
        )

    async def _validate_jwt_and_log(
        self,
        token: str,
        expediente_id: str,
        agent_config: AgentConfig,
        logger: AuditLogger
    ) -> JWTClaims:
        """Valida JWT y loguea resultado"""
        logger.log("Validando token JWT...")
        required_permissions = get_required_permissions_for_tools(agent_config.herramientas)
        claims = self.jwt_validator.validate(
            token=token,
            secret=self.jwt_secret,
            algorithm=self.jwt_algorithm,
            expected_expediente_id=expediente_id,
            required_permissions=required_permissions
        )
        logger.log(f"Token JWT válido para expediente {claims.exp_id}")
        logger.log(f"Permisos: {claims.permisos}")
        return claims

    async def _setup_mcp_infrastructure(self, token: str, logger: AuditLogger) -> MCPClientRegistry:
        """Configura infraestructura MCP (config + registry + discovery)"""
        # Cargar configuración
        logger.log(f"Cargando configuración de MCPs desde {self.mcp_config_path}...")
        mcp_config = self.config_loader.load(self.mcp_config_path)

        # Crear y inicializar registry
        logger.log("Creando registry de clientes MCP...")
        mcp_registry = await self.registry_factory.create(mcp_config, token)

        # Logear MCPs disponibles
        enabled_mcps = [s.id for s in mcp_config.get_enabled_servers()]
        logger.log(f"MCPs habilitados: {enabled_mcps}")
        available_tools = mcp_registry.get_available_tools()
        logger.log(f"Tools disponibles: {len(available_tools)}")

        return mcp_registry

    async def _execute_agent(
        self,
        expediente_id: str,
        tarea_id: str,
        run_id: str,
        agent_config: AgentConfig,
        mcp_registry: MCPClientRegistry,
        logger: AuditLogger
    ) -> tuple[Dict[str, Any], List[str]]:
        """Crea y ejecuta agente, retorna (resultado, tools_used)"""
        logger.log(f"Creando agente {agent_config.nombre}...")
        agent_class = self.agent_registry.get(agent_config.nombre)
        agent = agent_class(
            expediente_id=expediente_id,
            tarea_id=tarea_id,
            run_id=run_id,
            mcp_registry=mcp_registry,
            logger=logger
        )

        logger.log(f"Ejecutando agente {agent_config.nombre}...")
        resultado = await agent.execute()
        tools_used = agent.get_tools_used()

        return resultado, tools_used

    def _create_success_result(
        self,
        agent_run_id: str,
        resultado: Dict[str, Any],
        logger: AuditLogger,
        tools_used: List[str]
    ) -> AgentExecutionResult:
        """Crea resultado exitoso"""
        return AgentExecutionResult(
            success=True,
            agent_run_id=agent_run_id,
            resultado=resultado,
            log_auditoria=logger.get_log_entries(),
            herramientas_usadas=tools_used
        )

    def _create_error_result(
        self,
        agent_run_id: str,
        error: AgentError,
        logger: Optional[AuditLogger],
        tools_used: List[str] = None
    ) -> AgentExecutionResult:
        """Crea resultado de error"""
        return AgentExecutionResult(
            success=False,
            agent_run_id=agent_run_id,
            resultado={},
            log_auditoria=logger.get_log_entries() if logger else [],
            herramientas_usadas=tools_used or [],
            error=error
        )

    def _handle_jwt_error(
        self,
        agent_run_id: str,
        error: JWTValidationError,
        logger: Optional[AuditLogger]
    ) -> AgentExecutionResult:
        """Maneja errores de validación JWT"""
        if logger:
            logger.error(f"Error de validación JWT: {error.mensaje}")
        return self._create_error_result(
            agent_run_id,
            AgentError(codigo=error.codigo, mensaje=error.mensaje, detalle=error.detalle),
            logger
        )

    # ... _handle_mcp_connection_error, _handle_mcp_auth_error, etc. ...
```

**Criterio de aceptación:**
- ✅ `execute()` < 50 líneas
- ✅ Cada método privado < 20 líneas
- ✅ Todos los tests siguen pasando

---

## Verificación de Completitud

### Checklist de Fase 1 (P0)

- [ ] `backoffice/protocols.py` creado con 5 protocolos
- [ ] `backoffice/executor.py` refactorizado para DI
- [ ] `backoffice/executor_factory.py` creado con defaults
- [ ] `backoffice/tests/test_executor.py` creado con 30 tests
- [ ] Todos los tests pasan (30/30)
- [ ] Cobertura > 80%
- [ ] Código existente sigue funcionando (backward compatible)

### Checklist de Fase 2 (P1)

- [ ] `_validate_inputs()` implementado
- [ ] `_validate_agent_result()` implementado
- [ ] 8 tests de validación añadidos
- [ ] Todos los tests pasan (38/38)
- [ ] Inputs inválidos retornan errores apropiados

### Checklist de Fase 3 (P2-P3)

- [ ] Logging con stacktrace implementado
- [ ] `execute()` split en métodos privados
- [ ] Todos los tests siguen pasando
- [ ] `execute()` < 50 líneas

---

## Métricas de Éxito

### Antes de Mejoras

| Métrica | Valor |
|---------|-------|
| Tests unitarios | 0 |
| Cobertura | 0% |
| Complejidad execute() | ~15 |
| Líneas execute() | 196 |
| Acoplamiento | Alto |

### Después de Fase 1 (P0)

| Métrica | Valor | Mejora |
|---------|-------|--------|
| Tests unitarios | 30 | +30 |
| Cobertura | >80% | +80% |
| Complejidad execute() | ~15 | = |
| Líneas execute() | ~180 | -16 |
| Acoplamiento | Bajo | ✅ |

### Después de Fase 2 (P1)

| Métrica | Valor | Mejora |
|---------|-------|--------|
| Tests unitarios | 38 | +38 |
| Cobertura | >85% | +85% |
| Complejidad execute() | ~17 | +2 |
| Líneas execute() | ~210 | +14 |
| Validaciones | 2 | +2 |

### Después de Fase 3 (P2-P3)

| Métrica | Valor | Mejora |
|---------|-------|--------|
| Tests unitarios | 38 | = |
| Cobertura | >85% | = |
| Complejidad execute() | ~8 | -9 ✅ |
| Líneas execute() | ~40 | -170 ✅ |
| Mantenibilidad | Alta | ✅ |

---

## Riesgos y Mitigaciones

### Riesgo 1: Romper Código Existente

**Probabilidad:** Media
**Impacto:** Alto

**Mitigación:**
- Crear `executor_factory.py` con defaults (backward compatible)
- No cambiar firma pública de `execute()`
- Correr suite completa de tests existentes (79 tests)
- Test manual con servidor MCP real

### Riesgo 2: Validaciones Demasiado Estrictas

**Probabilidad:** Baja
**Impacto:** Medio

**Mitigación:**
- Validar solo campos críticos (token, expediente_id, nombre)
- No validar formato de herramientas (puede variar)
- Permitir campos adicionales en resultado del agente

### Riesgo 3: Refactoring de execute() Introduce Bugs

**Probabilidad:** Media
**Impacto:** Alto

**Mitigación:**
- Hacer refactoring DESPUÉS de tener 30 tests unitarios
- Refactorizar método por método
- Correr tests después de cada cambio
- Usar git para revertir si falla

---

## Siguiente Paso

**ACCIÓN INMEDIATA:** Comenzar con Fase 1 - P0.1 (Crear Protocols)

**Comando:**
```bash
# 1. Crear branch de feature
git checkout -b feature/executor-tests-di

# 2. Crear archivo de protocols
touch backoffice/protocols.py

# 3. Implementar protocols según especificación

# 4. Commit
git add backoffice/protocols.py
git commit -m "Implementar P0.1: Crear abstracciones (Protocols) para AgentExecutor"
```

---

**Autor:** Claude Code
**Fecha:** 2024-12-07
**Versión:** 1.0
