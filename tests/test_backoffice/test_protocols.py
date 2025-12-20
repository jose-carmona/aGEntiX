# backoffice/tests/test_protocols.py

"""
Tests de verificación de protocols.

Valida que los protocols se pueden importar y usar correctamente.
"""

import pytest
import inspect
from typing import Protocol, get_type_hints
from backoffice.protocols import (
    JWTValidatorProtocol,
    ConfigLoaderProtocol,
    MCPRegistryFactoryProtocol,
    AuditLoggerFactoryProtocol,
    AgentRegistryProtocol
)


def test_protocols_are_importable():
    """Test: Todos los protocols se pueden importar sin errores"""
    # Verificar que son clases (no None, no módulos, etc.)
    assert inspect.isclass(JWTValidatorProtocol)
    assert inspect.isclass(ConfigLoaderProtocol)
    assert inspect.isclass(MCPRegistryFactoryProtocol)
    assert inspect.isclass(AuditLoggerFactoryProtocol)
    assert inspect.isclass(AgentRegistryProtocol)


def test_protocols_inherit_from_protocol():
    """Test: Todos los protocols heredan de typing.Protocol"""
    # Verificar que son subclases de Protocol
    assert issubclass(JWTValidatorProtocol, Protocol)
    assert issubclass(ConfigLoaderProtocol, Protocol)
    assert issubclass(MCPRegistryFactoryProtocol, Protocol)
    assert issubclass(AuditLoggerFactoryProtocol, Protocol)
    assert issubclass(AgentRegistryProtocol, Protocol)


def test_jwt_validator_protocol_structure():
    """Test: JWTValidatorProtocol tiene la firma esperada"""
    # Verificar que el protocol tiene el método validate
    assert hasattr(JWTValidatorProtocol, 'validate')

    # Verificar que validate es un método
    method = getattr(JWTValidatorProtocol, 'validate')
    assert callable(method)

    # Verificar firma: debe tener 5 parámetros (self, token, secret, algorithm, expected_expediente_id, required_permissions)
    sig = inspect.signature(method)
    params = list(sig.parameters.keys())
    assert len(params) == 6  # self + 5 parámetros
    assert 'token' in params
    assert 'secret' in params
    assert 'algorithm' in params
    assert 'expected_expediente_id' in params
    assert 'required_permissions' in params


def test_config_loader_protocol_structure():
    """Test: ConfigLoaderProtocol tiene la firma esperada"""
    # Verificar que el protocol tiene el método load
    assert hasattr(ConfigLoaderProtocol, 'load')

    # Verificar que load es un método
    method = getattr(ConfigLoaderProtocol, 'load')
    assert callable(method)

    # Verificar firma: debe tener 1 parámetro (self, path)
    sig = inspect.signature(method)
    params = list(sig.parameters.keys())
    assert len(params) == 2  # self + path
    assert 'path' in params


def test_registry_factory_protocol_structure():
    """Test: MCPRegistryFactoryProtocol tiene la firma esperada"""
    # Verificar que el protocol tiene el método create
    assert hasattr(MCPRegistryFactoryProtocol, 'create')

    # Verificar que create es un método
    method = getattr(MCPRegistryFactoryProtocol, 'create')
    assert callable(method)

    # Verificar que es async
    assert inspect.iscoroutinefunction(method)

    # Verificar firma: debe tener 2 parámetros (self, config, token)
    sig = inspect.signature(method)
    params = list(sig.parameters.keys())
    assert len(params) == 3  # self + config + token
    assert 'config' in params
    assert 'token' in params


def test_logger_factory_protocol_structure():
    """Test: AuditLoggerFactoryProtocol tiene la firma esperada"""
    # Verificar que el protocol tiene el método create
    assert hasattr(AuditLoggerFactoryProtocol, 'create')

    # Verificar que create es un método
    method = getattr(AuditLoggerFactoryProtocol, 'create')
    assert callable(method)

    # Verificar firma: debe tener 3 parámetros (self, expediente_id, agent_run_id, log_dir)
    sig = inspect.signature(method)
    params = list(sig.parameters.keys())
    assert len(params) == 4  # self + 3 parámetros
    assert 'expediente_id' in params
    assert 'agent_run_id' in params
    assert 'log_dir' in params


def test_agent_registry_protocol_structure():
    """Test: AgentRegistryProtocol tiene la firma esperada"""
    # Verificar que el protocol tiene el método get
    assert hasattr(AgentRegistryProtocol, 'get')

    # Verificar que get es un método
    method = getattr(AgentRegistryProtocol, 'get')
    assert callable(method)

    # Verificar firma: debe tener 1 parámetro (self, nombre)
    sig = inspect.signature(method)
    params = list(sig.parameters.keys())
    assert len(params) == 2  # self + nombre
    assert 'nombre' in params


def test_protocol_can_be_used_as_type_hint():
    """Test: Protocols se pueden usar como type hints"""
    from typing import get_type_hints

    # Función de ejemplo que usa los protocols
    def example_function(
        jwt_validator: JWTValidatorProtocol,
        config_loader: ConfigLoaderProtocol,
        registry_factory: MCPRegistryFactoryProtocol,
        logger_factory: AuditLoggerFactoryProtocol,
        agent_registry: AgentRegistryProtocol
    ) -> None:
        pass

    # Verificar que los type hints se pueden extraer
    hints = get_type_hints(example_function)

    assert hints['jwt_validator'] == JWTValidatorProtocol
    assert hints['config_loader'] == ConfigLoaderProtocol
    assert hints['registry_factory'] == MCPRegistryFactoryProtocol
    assert hints['logger_factory'] == AuditLoggerFactoryProtocol
    assert hints['agent_registry'] == AgentRegistryProtocol
