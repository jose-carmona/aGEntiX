"""
Tests de Contrato - Interfaces del Sistema

Estos tests validan que las interfaces críticas del sistema permanecen estables
y compatibles cuando se realizan cambios, especialmente al introducir agentes
reales en el Paso 3.

Filosofía: Los tests de contrato NO validan comportamiento, validan ESTRUCTURA.
Si alguno de estos tests falla, significa que se rompió backward compatibility.

NOTA: El Paso 4 simplificó el API de ejecución de agentes. Los tests de contrato
han sido actualizados para reflejar el nuevo formato simplificado.
"""

import pytest
import inspect
from typing import Protocol, get_type_hints, Any, Dict, List
from pathlib import Path
from dataclasses import is_dataclass

# Imports del sistema
from src.backoffice.executor import AgentExecutor
from src.backoffice.models import AgentExecutionResult, AgentConfig, AgentError
from src.backoffice.agents.base import AgentMock  # Base class for agents
from src.backoffice.mcp.registry import MCPClientRegistry
from src.backoffice.logging.audit_logger import AuditLogger
from src.backoffice.auth.jwt_validator import JWTClaims
from src.backoffice.protocols import (
    JWTValidatorProtocol,
    ConfigLoaderProtocol,
    MCPRegistryFactoryProtocol,
    AuditLoggerFactoryProtocol,
    AgentRegistryProtocol
)


# ==============================================================================
# CONTRACT-1: AgentExecutor.execute() Signature
# ==============================================================================

def test_contract_agent_executor_execute_signature():
    """
    Test: Firma de AgentExecutor.execute() cumple contrato

    Si este test falla:
    - Se cambió la firma del método principal del sistema
    - Código que usa AgentExecutor se romperá
    - ACCIÓN: Revisar si el cambio es necesario, considerar deprecation
    """
    # Verificar que execute existe y es async
    assert hasattr(AgentExecutor, 'execute')
    execute_method = getattr(AgentExecutor, 'execute')
    assert inspect.iscoroutinefunction(execute_method)

    # Verificar parámetros requeridos
    sig = inspect.signature(execute_method)
    params = list(sig.parameters.keys())

    # Parámetros obligatorios (orden puede variar)
    assert 'self' in params
    assert 'token' in params
    assert 'expediente_id' in params
    assert 'tarea_id' in params
    assert 'agent_config' in params

    # Verificar que parámetros tienen tipos correctos (si están anotados)
    hints = get_type_hints(execute_method)
    if 'token' in hints:
        assert hints['token'] == str
    if 'expediente_id' in hints:
        assert hints['expediente_id'] == str
    if 'tarea_id' in hints:
        assert hints['tarea_id'] == str
    if 'agent_config' in hints:
        assert hints['agent_config'] == AgentConfig

    # Verificar tipo de retorno
    assert 'return' in hints
    assert hints['return'] == AgentExecutionResult


# ==============================================================================
# CONTRACT-2: AgentExecutionResult Structure
# ==============================================================================

def test_contract_agent_execution_result_structure():
    """
    Test: Estructura de AgentExecutionResult es estable

    Si este test falla:
    - Se cambió la estructura del resultado de ejecución
    - Código que consume resultados se romperá
    - ACCIÓN: Asegurar backward compatibility, campos nuevos opcionales
    """
    # Verificar que es un dataclass
    assert is_dataclass(AgentExecutionResult)

    # Verificar campos obligatorios vía __annotations__
    fields = AgentExecutionResult.__annotations__

    # Campos que DEBEN existir siempre
    required_fields = {'success', 'agent_run_id', 'resultado', 'log_auditoria', 'herramientas_usadas'}
    for field in required_fields:
        assert field in fields, f"Campo obligatorio '{field}' falta en AgentExecutionResult"

    # Campo error es opcional
    assert 'error' in fields

    # Verificar tipos básicos
    assert fields['success'] == bool
    assert fields['agent_run_id'] == str

    # Crear instancia de ejemplo para verificar que funciona
    sample_result = AgentExecutionResult(
        success=True,
        agent_run_id="RUN-TEST-001",
        resultado={"status": "ok"},
        log_auditoria=["Log line 1"],
        herramientas_usadas=["tool1"]
    )
    assert sample_result.success is True
    assert sample_result.agent_run_id == "RUN-TEST-001"


# ==============================================================================
# CONTRACT-3: AgentMock.execute() Interface
# ==============================================================================

def test_contract_base_agent_execute_interface():
    """
    Test: Interface de AgentMock (base de agentes) es estable para agentes reales

    Si este test falla:
    - Se cambió la interfaz base de agentes
    - Agentes reales (Paso 3) necesitarán cambios
    - ACCIÓN: Revisar si cambio es necesario, mantener backward compatibility
    """
    # Verificar que execute existe
    assert hasattr(AgentMock, 'execute')
    execute_method = getattr(AgentMock, 'execute')

    # Verificar que es async
    assert inspect.iscoroutinefunction(execute_method)

    # Verificar tipo de retorno
    hints = get_type_hints(execute_method)
    if 'return' in hints:
        # Debe retornar Dict
        assert hints['return'] == Dict[str, Any] or hints['return'] == dict

    # Verificar que hay otros métodos auxiliares
    assert hasattr(AgentMock, 'get_tools_used')


# ==============================================================================
# CONTRACT-4: MCPClientRegistry Interface
# ==============================================================================

def test_contract_mcp_client_registry_interface():
    """
    Test: Interface de MCP registry es estable

    Si este test falla:
    - Se cambió la interfaz de comunicación con MCP
    - Agentes que usan MCP necesitarán cambios
    - ACCIÓN: Revisar compatibilidad con agentes existentes
    """
    # Verificar métodos principales
    assert hasattr(MCPClientRegistry, 'get_available_tools')
    assert hasattr(MCPClientRegistry, 'call_tool')
    assert hasattr(MCPClientRegistry, 'close')

    # Verificar que call_tool es async
    call_tool_method = getattr(MCPClientRegistry, 'call_tool')
    assert inspect.iscoroutinefunction(call_tool_method)

    # Verificar firma de call_tool
    sig = inspect.signature(call_tool_method)
    params = list(sig.parameters.keys())
    assert 'self' in params
    # Puede ser 'tool_name' o 'name' - ambos aceptables
    assert 'tool_name' in params or 'name' in params
    assert 'arguments' in params

    # Verificar que get_available_tools NO es async (sincrónico)
    get_tools_method = getattr(MCPClientRegistry, 'get_available_tools')
    assert not inspect.iscoroutinefunction(get_tools_method)

    # Verificar tipo de retorno de get_available_tools
    hints = get_type_hints(get_tools_method)
    if 'return' in hints:
        # Debe retornar Dict[str, str] (tool_name -> server_id)
        assert hints['return'] == Dict[str, str] or 'Dict' in str(hints['return'])

    # Verificar que close es async
    close_method = getattr(MCPClientRegistry, 'close')
    assert inspect.iscoroutinefunction(close_method)


# ==============================================================================
# CONTRACT-5: API POST /api/v1/agent/execute (Simplificado - Paso 4)
# ==============================================================================

def test_contract_api_execute_request_response():
    """
    Test: Contrato de API simplificado es estable (OpenAPI spec)

    NOTA: El Paso 4 simplificó el API de ejecución de agentes.
    El nuevo formato usa: agent, context, additional_goal (opcional), callback_url (opcional).

    Si este test falla:
    - Se cambió la estructura de request/response de API
    - Clientes externos se romperán
    - ACCIÓN: Versionar API (v2), mantener v1 compatible
    """
    from src.api.models import ExecuteAgentRequest, AgentContext
    from pydantic import BaseModel

    # Verificar ExecuteAgentRequest (formato simplificado)
    assert issubclass(ExecuteAgentRequest, BaseModel)
    request_fields = ExecuteAgentRequest.model_fields

    # Campos obligatorios del request simplificado
    assert 'agent' in request_fields, "Campo 'agent' requerido"
    assert 'context' in request_fields, "Campo 'context' requerido"

    # Campos opcionales
    assert 'additional_goal' in request_fields, "Campo 'additional_goal' (opcional) requerido"
    assert 'callback_url' in request_fields, "Campo 'callback_url' (opcional) requerido"

    # Verificar AgentContext
    assert issubclass(AgentContext, BaseModel)
    context_fields = AgentContext.model_fields

    # Campos obligatorios del contexto
    assert 'expediente_id' in context_fields
    assert 'tarea_id' in context_fields

    # Verificar que models son serializables
    sample_context = AgentContext(
        expediente_id="EXP-TEST-001",
        tarea_id="TAREA-001"
    )
    sample_request = ExecuteAgentRequest(
        agent="ValidadorDocumental",
        additional_goal="Priorizar validación de NIFs",
        context=sample_context,
        callback_url="https://example.com/webhook"
    )

    # Serialización a JSON
    request_dict = sample_request.model_dump()
    assert isinstance(request_dict, dict)
    assert request_dict['agent'] == "ValidadorDocumental"
    assert request_dict['additional_goal'] == "Priorizar validación de NIFs"
    assert request_dict['context']['expediente_id'] == "EXP-TEST-001"


# ==============================================================================
# CONTRACT-6: Webhook Callback Payload
# ==============================================================================

def test_contract_webhook_payload_structure():
    """
    Test: Payload de webhook es estable

    Si este test falla:
    - Se cambió la estructura del webhook callback
    - Sistemas BPMN externos no recibirán datos correctos
    - ACCIÓN: CRÍTICO - coordinar cambios con equipo BPMN
    """
    from src.api.models import WebhookPayload
    from pydantic import BaseModel

    # Verificar que existe el modelo
    assert issubclass(WebhookPayload, BaseModel)

    # Verificar campos obligatorios
    payload_fields = WebhookPayload.model_fields

    # Campos que BPMN espera recibir
    critical_fields = {'agent_run_id', 'status', 'success', 'timestamp'}
    for field in critical_fields:
        assert field in payload_fields, f"Campo crítico '{field}' falta en webhook payload"

    # Campos opcionales esperados
    optional_fields = {'resultado', 'herramientas_usadas', 'error'}
    for field in optional_fields:
        assert field in payload_fields, f"Campo opcional '{field}' falta en webhook payload"

    # Verificar serialización
    sample_payload = WebhookPayload(
        agent_run_id="RUN-001",
        status="completed",
        success=True,
        timestamp="2025-01-01T00:00:00Z",
        resultado={"data": "test"},
        herramientas_usadas=["tool1"]
    )

    payload_dict = sample_payload.model_dump()
    assert isinstance(payload_dict, dict)
    assert payload_dict['agent_run_id'] == "RUN-001"
    assert payload_dict['status'] == "completed"
    assert payload_dict['success'] is True


# ==============================================================================
# CONTRACT-7: JWTClaims Structure
# ==============================================================================

def test_contract_jwt_claims_structure():
    """
    Test: Estructura de JWT claims es estable

    Si este test falla:
    - Se cambió la estructura de claims del JWT
    - Sistema BPMN que genera tokens necesita actualización
    - ACCIÓN: Coordinar con equipo BPMN, mantener backward compatibility
    """
    from pydantic import BaseModel

    # Verificar que es Pydantic model
    assert issubclass(JWTClaims, BaseModel)

    # Verificar claims estándar JWT
    claims_fields = JWTClaims.model_fields
    standard_claims = {'iss', 'sub', 'aud', 'exp', 'iat', 'nbf', 'jti'}
    for claim in standard_claims:
        assert claim in claims_fields, f"Claim estándar '{claim}' falta en JWTClaims"

    # Verificar claims custom
    custom_claims = {'exp_id', 'permisos'}
    for claim in custom_claims:
        assert claim in claims_fields, f"Claim custom '{claim}' falta en JWTClaims"

    # Verificar que es serializable
    sample_claims = JWTClaims(
        iss="test-issuer",
        sub="test-subject",
        aud=["test-audience"],
        exp=1234567890,
        iat=1234567800,
        nbf=1234567800,
        jti="test-jti",
        exp_id="EXP-001",
        permisos=["consulta"]
    )

    claims_dict = sample_claims.model_dump()
    assert isinstance(claims_dict, dict)
    assert claims_dict['exp_id'] == "EXP-001"


# ==============================================================================
# CONTRACT-8: AuditLogger Methods
# ==============================================================================

def test_contract_audit_logger_methods():
    """
    Test: Interface de AuditLogger es estable

    Si este test falla:
    - Se cambió la interfaz de logging de auditoría
    - Código que registra eventos necesita cambios
    - ACCIÓN: Mantener métodos legacy con deprecation warnings
    """
    # Verificar métodos principales
    assert hasattr(AuditLogger, 'log')  # Método base
    assert hasattr(AuditLogger, 'error')
    assert hasattr(AuditLogger, 'warning')

    # Verificar firmas
    error_method = getattr(AuditLogger, 'error')
    sig = inspect.signature(error_method)
    params = list(sig.parameters.keys())

    # Debe aceptar mensaje
    assert 'self' in params
    assert 'mensaje' in params

    # Verificar que métodos NO son async (logging sincrónico)
    assert not inspect.iscoroutinefunction(error_method)

    warning_method = getattr(AuditLogger, 'warning')
    assert not inspect.iscoroutinefunction(warning_method)


# ==============================================================================
# CONTRACT-9: MCP Tool Call Format
# ==============================================================================

@pytest.mark.asyncio
async def test_contract_mcp_tool_call_format():
    """
    Test: Formato de llamada MCP tool es estable

    Si este test falla:
    - Se cambió el formato de comunicación con MCP
    - Servidores MCP externos pueden fallar
    - ACCIÓN: Verificar cumplimiento con spec MCP oficial
    """
    from src.backoffice.mcp.client import MCPClient

    # Verificar que MCPClient tiene método call_tool
    assert hasattr(MCPClient, 'call_tool')

    call_tool = getattr(MCPClient, 'call_tool')
    assert inspect.iscoroutinefunction(call_tool)

    # Verificar firma
    sig = inspect.signature(call_tool)
    params = list(sig.parameters.keys())

    # Parámetros esperados por spec MCP
    assert 'self' in params
    # Acepta 'name' como parámetro
    assert 'name' in params
    assert 'arguments' in params


# ==============================================================================
# CONTRACT-10: Error Codes Stability
# ==============================================================================

def test_contract_error_codes_are_stable():
    """
    Test: Códigos de error son estables y documentados

    Si este test falla:
    - Se eliminó o renombró un código de error
    - Código que maneja errores se romperá
    - ACCIÓN: NUNCA eliminar códigos, solo deprecar
    """
    # Códigos de error JWT (deben existir siempre)
    jwt_error_codes = {
        "AUTH_TOKEN_EXPIRED",
        "AUTH_INVALID_TOKEN",
        "AUTH_PERMISSION_DENIED",
        "AUTH_EXPEDIENTE_MISMATCH",
        "AUTH_INSUFFICIENT_PERMISSIONS",
        "AUTH_TOKEN_NOT_YET_VALID"
    }

    # Importar módulo de errores JWT
    from src.backoffice.auth import jwt_validator

    # Verificar que cada código está definido en el código
    # (pueden estar en excepciones, constantes, o enums)
    source_code = inspect.getsource(jwt_validator)

    for error_code in jwt_error_codes:
        assert error_code in source_code, \
            f"Código de error '{error_code}' fue eliminado o renombrado - BREAKING CHANGE"

    # Códigos de error MCP
    mcp_error_codes = {
        "MCP_CONNECTION_ERROR",
        "MCP_TIMEOUT",
        "MCP_TOOL_ERROR"
    }

    from src.backoffice.mcp import exceptions
    mcp_source = inspect.getsource(exceptions)

    for error_code in mcp_error_codes:
        assert error_code in mcp_source, \
            f"Código de error MCP '{error_code}' fue eliminado - BREAKING CHANGE"


# ==============================================================================
# CONTRACT-11: Pydantic Models JSON Serializable
# ==============================================================================

def test_contract_pydantic_models_json_serializable():
    """
    Test: Todos los Pydantic models serializan a JSON

    Si este test falla:
    - Se agregaron campos no serializables
    - API no podrá retornar respuestas
    - ACCIÓN: Usar serializers custom o cambiar tipo de campo
    """
    import json

    # JWTClaims
    claims = JWTClaims(
        iss="test",
        sub="test",
        aud=["test"],
        exp=1234567890,
        iat=1234567800,
        nbf=1234567800,
        jti="test",
        exp_id="EXP-001",
        permisos=["consulta"]
    )
    claims_json = claims.model_dump_json()
    claims_parsed = json.loads(claims_json)
    assert claims_parsed['exp_id'] == "EXP-001"

    # API Models (formato simplificado)
    from src.api.models import ExecuteAgentRequest, AgentContext
    context = AgentContext(
        expediente_id="EXP-001",
        tarea_id="TAREA-001"
    )
    request = ExecuteAgentRequest(
        agent="ValidadorDocumental",
        context=context
    )
    request_json = request.model_dump_json()
    request_parsed = json.loads(request_json)
    assert request_parsed['agent'] == "ValidadorDocumental"

    # WebhookPayload
    from src.api.models import WebhookPayload
    payload = WebhookPayload(
        agent_run_id="RUN-001",
        status="completed",
        success=True,
        timestamp="2025-01-01T00:00:00Z"
    )
    payload_json = payload.model_dump_json()
    payload_parsed = json.loads(payload_json)
    assert payload_parsed['agent_run_id'] == "RUN-001"


# ==============================================================================
# CONTRACT-12: Backward Compatibility (Formato Simplificado)
# ==============================================================================

def test_contract_backward_compatibility_optional_fields():
    """
    Test: Campos opcionales funcionan correctamente

    Si este test falla:
    - Se agregó un campo obligatorio nuevo
    - Clientes antiguos se romperán
    - ACCIÓN: Hacer campo opcional con valor por defecto
    """
    # Test: AgentExecutionResult puede crearse solo con campos mínimos
    minimal_result = AgentExecutionResult(
        success=True,
        agent_run_id="RUN-001",
        resultado={"status": "ok"},
        log_auditoria=["log1"],
        herramientas_usadas=["tool1"]
    )
    assert minimal_result.success is True

    # Test: API request con callback_url opcional
    from src.api.models import ExecuteAgentRequest, AgentContext

    context = AgentContext(
        expediente_id="EXP-001",
        tarea_id="TAREA-001"
    )

    # Sin additional_goal y sin callback_url (son opcionales)
    minimal_request = ExecuteAgentRequest(
        agent="ValidadorDocumental",
        context=context
    )

    assert minimal_request.agent == "ValidadorDocumental"
    assert minimal_request.additional_goal is None
    assert minimal_request.callback_url is None

    # Con additional_goal y callback_url
    full_request = ExecuteAgentRequest(
        agent="ValidadorDocumental",
        additional_goal="Objetivo adicional",
        context=context,
        callback_url="https://example.com/webhook"
    )
    assert full_request.additional_goal is not None
    assert full_request.callback_url is not None

    # Test: WebhookPayload con campos mínimos
    from src.api.models import WebhookPayload
    minimal_webhook = WebhookPayload(
        agent_run_id="RUN-001",
        status="completed",
        success=True,
        timestamp="2025-01-01T00:00:00Z"
    )
    assert minimal_webhook.agent_run_id == "RUN-001"

    # Campos opcionales pueden ser None
    assert minimal_webhook.resultado is None
    assert minimal_webhook.error is None


# ==============================================================================
# CONTRACT-13: Agent Config Loader (Nuevo en Paso 4)
# ==============================================================================

def test_contract_agent_config_loader():
    """
    Test: AgentConfigLoader carga agentes correctamente

    Este contrato asegura que la configuración de agentes
    desde YAML funciona correctamente.
    """
    from src.backoffice.config import AgentConfigLoader, AgentDefinition

    # Verificar métodos principales
    assert hasattr(AgentConfigLoader, 'get')
    assert hasattr(AgentConfigLoader, 'list_agents')
    assert hasattr(AgentConfigLoader, 'list_agent_names')
    assert hasattr(AgentConfigLoader, 'exists')

    # Verificar estructura de AgentDefinition
    from pydantic import BaseModel
    assert issubclass(AgentDefinition, BaseModel)

    fields = AgentDefinition.model_fields
    required_fields = {'name', 'description', 'model', 'system_prompt', 'tools'}
    for field in required_fields:
        assert field in fields, f"Campo '{field}' falta en AgentDefinition"


# ==============================================================================
# CONTRACT-14: List Agents API (Nuevo en Paso 4)
# ==============================================================================

def test_contract_list_agents_response():
    """
    Test: Response de GET /api/v1/agent/agents es estable

    Este contrato asegura que el endpoint de listado de agentes
    retorna la estructura esperada.
    """
    from src.api.models import ListAgentsResponse, AgentInfo
    from pydantic import BaseModel

    # Verificar modelos
    assert issubclass(ListAgentsResponse, BaseModel)
    assert issubclass(AgentInfo, BaseModel)

    # Verificar campos de AgentInfo
    agent_fields = AgentInfo.model_fields
    assert 'name' in agent_fields
    assert 'description' in agent_fields
    assert 'required_permissions' in agent_fields

    # Verificar campos de ListAgentsResponse
    response_fields = ListAgentsResponse.model_fields
    assert 'agents' in response_fields

    # Verificar serialización
    sample_agent = AgentInfo(
        name="TestAgent",
        description="Test description",
        required_permissions=["perm1", "perm2"]
    )
    sample_response = ListAgentsResponse(agents=[sample_agent])

    response_dict = sample_response.model_dump()
    assert isinstance(response_dict, dict)
    assert len(response_dict['agents']) == 1
    assert response_dict['agents'][0]['name'] == "TestAgent"
