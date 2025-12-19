# backoffice/executor_factory.py

"""
Factory para crear AgentExecutor con implementaciones por defecto.

Provee backward compatibility manteniendo el patrón de creación original
mientras permite inyección de dependencias para testing.
"""

from pathlib import Path
from typing import List, Optional

from .executor import AgentExecutor
from .auth.jwt_validator import validate_jwt, JWTClaims
from .config.models import MCPServersConfig
from .mcp.registry import MCPClientRegistry
from .logging.audit_logger import AuditLogger
from .agents.registry import get_agent_class


class DefaultJWTValidator:
    """Implementación por defecto de JWTValidatorProtocol"""

    def validate(
        self,
        token: str,
        secret: str,
        algorithm: str,
        expected_expediente_id: str,
        required_permissions: List[str]
    ) -> JWTClaims:
        """
        Delega a la función validate_jwt del módulo jwt_validator.

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
        from .settings import settings

        return validate_jwt(
            token=token,
            secret=secret,
            algorithm=algorithm,
            expected_expediente_id=expected_expediente_id,
            required_permissions=required_permissions,
            expected_issuer=settings.JWT_EXPECTED_ISSUER,
            expected_subject=settings.JWT_EXPECTED_SUBJECT,
            required_audience=settings.JWT_REQUIRED_AUDIENCE
        )


class DefaultConfigLoader:
    """Implementación por defecto de ConfigLoaderProtocol"""

    def load(self, path: str) -> MCPServersConfig:
        """
        Carga configuración MCP desde archivo YAML.

        Args:
            path: Ruta al archivo de configuración

        Returns:
            MCPServersConfig con la configuración cargada

        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el YAML es inválido
        """
        return MCPServersConfig.load_from_file(path)


class DefaultMCPRegistryFactory:
    """Factory por defecto de MCPClientRegistry"""

    async def create(
        self,
        config: MCPServersConfig,
        token: str
    ) -> MCPClientRegistry:
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
        registry = MCPClientRegistry()
        await registry.initialize(config, token)
        return registry


class DefaultAuditLoggerFactory:
    """Factory por defecto de AuditLogger"""

    def create(
        self,
        expediente_id: str,
        agent_run_id: str,
        log_dir: Path | str
    ) -> AuditLogger:
        """
        Crea un AuditLogger para el expediente.

        Args:
            expediente_id: ID del expediente
            agent_run_id: ID único de esta ejecución
            log_dir: Directorio para guardar logs

        Returns:
            AuditLogger configurado
        """
        return AuditLogger(
            expediente_id=expediente_id,
            agent_run_id=agent_run_id,
            log_dir=log_dir
        )


class DefaultAgentRegistry:
    """Registry por defecto de agentes disponibles"""

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
        return get_agent_class(nombre)


def create_default_executor(
    mcp_config_path: str,
    jwt_secret: str,
    jwt_algorithm: str = "HS256"
) -> AgentExecutor:
    """
    Factory para crear AgentExecutor con implementaciones por defecto.

    Esta función provee backward compatibility con el patrón de creación
    original de AgentExecutor, permitiendo usar el nuevo sistema de DI
    sin cambiar el código existente.

    Args:
        mcp_config_path: Ruta al archivo de configuración de MCPs
        jwt_secret: Clave secreta para validar JWT
        jwt_algorithm: Algoritmo JWT (default: HS256)

    Returns:
        AgentExecutor configurado con implementaciones por defecto

    Example:
        ```python
        # Uso original (backward compatible)
        executor = create_default_executor(
            mcp_config_path="/path/to/mcp_servers.yaml",
            jwt_secret="mi-secreto",
            jwt_algorithm="HS256"
        )

        # Uso nuevo (con DI para testing)
        executor = AgentExecutor(
            jwt_validator=MockJWTValidator(),
            config_loader=MockConfigLoader(),
            # ... otros mocks
        )
        ```
    """
    return AgentExecutor(
        jwt_validator=DefaultJWTValidator(),
        config_loader=DefaultConfigLoader(),
        registry_factory=DefaultMCPRegistryFactory(),
        logger_factory=DefaultAuditLoggerFactory(),
        agent_registry=DefaultAgentRegistry(),
        mcp_config_path=mcp_config_path,
        jwt_secret=jwt_secret,
        jwt_algorithm=jwt_algorithm
    )
