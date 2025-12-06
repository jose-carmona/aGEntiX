# backoffice/executor.py

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import AgentConfig, AgentExecutionResult, AgentError
from .config.models import MCPServersConfig
from .mcp.registry import MCPClientRegistry
from .mcp.exceptions import MCPConnectionError, MCPToolError, MCPAuthError
from .logging.audit_logger import AuditLogger
from .auth.jwt_validator import validate_jwt, get_required_permissions_for_tools, JWTValidationError
from .agents.registry import get_agent_class


class AgentExecutor:
    """
    Ejecutor principal de agentes.

    Orquesta la validación JWT, configuración MCP, logging y ejecución de agentes.
    """

    def __init__(self, mcp_config_path: str, log_dir: str, jwt_secret: str, jwt_algorithm: str = "HS256"):
        """
        Inicializa el executor.

        Args:
            mcp_config_path: Ruta al archivo de configuración de MCPs
            log_dir: Directorio para logs
            jwt_secret: Clave secreta para validar JWT
            jwt_algorithm: Algoritmo JWT (default: HS256)
        """
        self.mcp_config_path = mcp_config_path
        self.log_dir = Path(log_dir)
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm

    async def execute(
        self,
        token: str,
        expediente_id: str,
        tarea_id: str,
        agent_config: AgentConfig
    ) -> AgentExecutionResult:
        """
        Ejecuta un agente y maneja errores del cliente MCP.

        Args:
            token: Token JWT completo
            expediente_id: ID del expediente
            tarea_id: ID de la tarea BPMN
            agent_config: Configuración del agente

        Returns:
            Resultado de la ejecución del agente
        """
        mcp_registry: Optional[MCPClientRegistry] = None
        logger: Optional[AuditLogger] = None
        agent_run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}"

        try:
            # 0. Crear logger temprano para capturar todos los eventos
            logger = AuditLogger(
                expediente_id=expediente_id,
                agent_run_id=agent_run_id,
                log_dir=self.log_dir
            )

            logger.log(f"Iniciando ejecución de agente {agent_config.nombre}")
            logger.log(f"Tarea: {tarea_id}")

            # 1. Validar JWT
            logger.log("Validando token JWT...")
            try:
                required_permissions = get_required_permissions_for_tools(agent_config.herramientas)
                claims = validate_jwt(
                    token=token,
                    secret=self.jwt_secret,
                    algorithm=self.jwt_algorithm,
                    expected_expediente_id=expediente_id,
                    required_permissions=required_permissions
                )
                logger.log(f"Token JWT válido para expediente {claims.exp_id}")
                logger.log(f"Permisos: {claims.permisos}")

            except JWTValidationError as e:
                logger.error(f"Error de validación JWT: {e.mensaje}")
                return AgentExecutionResult(
                    success=False,
                    agent_run_id=agent_run_id,
                    resultado={},
                    log_auditoria=logger.get_log_entries(),
                    herramientas_usadas=[],
                    error=AgentError(
                        codigo=e.codigo,
                        mensaje=e.mensaje,
                        detalle=e.detalle
                    )
                )

            # 2. Cargar configuración de MCPs
            logger.log(f"Cargando configuración de MCPs desde {self.mcp_config_path}...")
            mcp_config = MCPServersConfig.load_from_file(self.mcp_config_path)

            # 3. Crear registry de clientes MCP
            logger.log("Creando registry de clientes MCP...")
            mcp_registry = MCPClientRegistry(
                config=mcp_config,
                token=token
            )

            # 4. Inicializar (crea clientes para MCPs habilitados y descubre tools)
            logger.log("Inicializando registry (descubriendo tools)...")
            await mcp_registry.initialize()

            # Logear qué MCPs están disponibles
            enabled_mcps = [s.id for s in mcp_config.get_enabled_servers()]
            logger.log(f"MCPs habilitados: {enabled_mcps}")

            available_tools = mcp_registry.get_available_tools()
            logger.log(f"Tools disponibles: {len(available_tools)}")

            # 5. Crear y ejecutar agente mock
            logger.log(f"Creando agente {agent_config.nombre}...")
            try:
                agent_class = get_agent_class(agent_config.nombre)
                agent = agent_class(
                    expediente_id=expediente_id,
                    tarea_id=tarea_id,
                    run_id=agent_run_id,
                    mcp_registry=mcp_registry,
                    logger=logger
                )
            except KeyError as e:
                logger.error(f"Agente no configurado: {str(e)}")
                return AgentExecutionResult(
                    success=False,
                    agent_run_id=agent_run_id,
                    resultado={},
                    log_auditoria=logger.get_log_entries(),
                    herramientas_usadas=[],
                    error=AgentError(
                        codigo="AGENT_NOT_CONFIGURED",
                        mensaje=f"Tipo de agente '{agent_config.nombre}' no configurado",
                        detalle=str(e)
                    )
                )

            logger.log(f"Ejecutando agente {agent_config.nombre}...")
            resultado = await agent.execute()

            logger.log(f"Agente completado exitosamente")

            return AgentExecutionResult(
                success=True,
                agent_run_id=agent_run_id,
                resultado=resultado,
                log_auditoria=logger.get_log_entries(),
                herramientas_usadas=agent.get_tools_used()
            )

        except MCPConnectionError as e:
            # Error de conexión - propagar al BPMN
            if logger:
                logger.error(f"Error de conexión MCP: {e}")
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

        except MCPAuthError as e:
            # Error de autenticación - propagar al BPMN
            if logger:
                logger.error(f"Error de autenticación MCP: {e}")
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

        except MCPToolError as e:
            # Error en tool - propagar al BPMN
            if logger:
                logger.error(f"Error en tool MCP: {e}")
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

        except Exception as e:
            # Error inesperado
            if logger:
                logger.error(f"Error inesperado: {type(e).__name__}: {str(e)}")
            return AgentExecutionResult(
                success=False,
                agent_run_id=agent_run_id,
                resultado={},
                log_auditoria=logger.get_log_entries() if logger else [],
                herramientas_usadas=[],
                error=AgentError(
                    codigo="INTERNAL_ERROR",
                    mensaje=f"Error interno del sistema: {type(e).__name__}",
                    detalle=str(e)
                )
            )

        finally:
            # Cerrar registry de clientes MCP
            if mcp_registry:
                await mcp_registry.close()
