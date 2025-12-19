# backoffice/tests/test_protocols.py

"""
Tests de verificación de protocols.

Valida que los protocols se pueden importar y usar correctamente.
"""

import pytest
from backoffice.protocols import (
    JWTValidatorProtocol,
    ConfigLoaderProtocol,
    MCPRegistryFactoryProtocol,
    AuditLoggerFactoryProtocol,
    AgentRegistryProtocol
)


def test_protocols_are_importable():
    """Test: Todos los protocols se pueden importar sin errores"""
    # Si llegamos aquí, la importación fue exitosa
    assert JWTValidatorProtocol is not None
    assert ConfigLoaderProtocol is not None
    assert MCPRegistryFactoryProtocol is not None
    assert AuditLoggerFactoryProtocol is not None
    assert AgentRegistryProtocol is not None


def test_jwt_validator_protocol_structure():
    """Test: JWTValidatorProtocol tiene la firma esperada"""
    # Verificar que el protocol tiene el método validate
    assert hasattr(JWTValidatorProtocol, 'validate')


def test_config_loader_protocol_structure():
    """Test: ConfigLoaderProtocol tiene la firma esperada"""
    # Verificar que el protocol tiene el método load
    assert hasattr(ConfigLoaderProtocol, 'load')


def test_registry_factory_protocol_structure():
    """Test: MCPRegistryFactoryProtocol tiene la firma esperada"""
    # Verificar que el protocol tiene el método create
    assert hasattr(MCPRegistryFactoryProtocol, 'create')


def test_logger_factory_protocol_structure():
    """Test: AuditLoggerFactoryProtocol tiene la firma esperada"""
    # Verificar que el protocol tiene el método create
    assert hasattr(AuditLoggerFactoryProtocol, 'create')


def test_agent_registry_protocol_structure():
    """Test: AgentRegistryProtocol tiene la firma esperada"""
    # Verificar que el protocol tiene el método get
    assert hasattr(AgentRegistryProtocol, 'get')


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
