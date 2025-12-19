# backoffice/protocols.py

"""
Protocols (abstracciones) para inyección de dependencias en AgentExecutor.

Este módulo define las interfaces que deben implementar las dependencias
del AgentExecutor, permitiendo inyectar mocks para testing unitario.

Siguiendo el principio de Inversión de Dependencias (SOLID).
"""

from typing import Protocol, List, Dict, Any
from pathlib import Path


class JWTValidatorProtocol(Protocol):
    """
    Abstracción de validador JWT para testing.

    Permite inyectar mocks del validador en tests unitarios.
    """

    def validate(
        self,
        token: str,
        secret: str,
        algorithm: str,
        expected_expediente_id: str,
        required_permissions: List[str]
    ) -> 'JWTClaims':
        """
        Valida un token JWT y retorna los claims validados.

        Args:
            token: Token JWT a validar
            secret: Clave secreta para verificar firma
            algorithm: Algoritmo de firma (ej: HS256)
            expected_expediente_id: ID del expediente esperado
            required_permissions: Permisos requeridos

        Returns:
            JWTClaims validados

        Raises:
            JWTValidationError: Si el token es inválido
        """
        ...


class ConfigLoaderProtocol(Protocol):
    """
    Abstracción de cargador de configuración MCP.

    Permite inyectar mocks del loader en tests unitarios.
    """

    def load(self, path: str) -> 'MCPServersConfig':
        """
        Carga configuración MCP desde archivo.

        Args:
            path: Ruta al archivo de configuración

        Returns:
            MCPServersConfig con la configuración cargada

        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el YAML es inválido
        """
        ...


class MCPRegistryFactoryProtocol(Protocol):
    """
    Factory para crear MCPClientRegistry.

    Permite inyectar mocks del registry en tests unitarios.
    """

    async def create(
        self,
        config: 'MCPServersConfig',
        token: str
    ) -> 'MCPClientRegistry':
        """
        Crea y inicializa un MCPClientRegistry.

        Args:
            config: Configuración de servidores MCP
            token: Token JWT para autenticación

        Returns:
            MCPClientRegistry inicializado

        Raises:
            MCPConnectionError: Si falla la conexión
        """
        ...


class AuditLoggerFactoryProtocol(Protocol):
    """
    Factory para crear AuditLogger.

    Permite inyectar mocks del logger en tests unitarios.
    """

    def create(
        self,
        expediente_id: str,
        agent_run_id: str,
        log_dir: Path | str
    ) -> 'AuditLogger':
        """
        Crea un AuditLogger para el expediente.

        Args:
            expediente_id: ID del expediente
            agent_run_id: ID único de esta ejecución
            log_dir: Directorio para guardar logs

        Returns:
            AuditLogger configurado
        """
        ...


class AgentRegistryProtocol(Protocol):
    """
    Registro de agentes disponibles.

    Permite inyectar mocks del registry en tests unitarios.
    """

    def get(self, nombre: str) -> type:
        """
        Obtiene clase de agente por nombre.

        Args:
            nombre: Nombre del agente (ej: "ValidadorDocumental")

        Returns:
            Clase del agente

        Raises:
            KeyError: Si el agente no está registrado
        """
        ...


# Type hints forward references (evita imports circulares)
# Estos tipos se importan en el módulo que implementa los protocols

if False:  # TYPE_CHECKING equivalente sin usar typing.TYPE_CHECKING
    from backoffice.auth.jwt_validator import JWTClaims
    from backoffice.config.models import MCPServersConfig
    from backoffice.mcp.registry import MCPClientRegistry
    from backoffice.logging.audit_logger import AuditLogger
