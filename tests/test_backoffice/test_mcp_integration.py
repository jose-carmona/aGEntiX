# backoffice/tests/test_mcp_integration.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from backoffice.mcp.client import MCPClient
from backoffice.mcp.registry import MCPClientRegistry
from backoffice.mcp.exceptions import MCPConnectionError, MCPAuthError, MCPToolError
from backoffice.config.models import MCPServerConfig, MCPAuthConfig, MCPServersConfig


@pytest.fixture
def mock_server_config():
    """Configuración de servidor MCP para tests"""
    return MCPServerConfig(
        id="test-mcp",
        name="Test MCP",
        description="Test server",
        url="http://localhost:8000",
        type="http",
        auth=MCPAuthConfig(type="jwt", audience="test-audience"),
        timeout=30,
        enabled=True
    )


@pytest.fixture
def test_token():
    """Token JWT de prueba"""
    return "test-jwt-token-123"


def create_mock_response(json_data, status_code=200):
    """Helper para crear mock responses"""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json = MagicMock(return_value=json_data)
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def create_mock_async_client(mock_response):
    """Helper para crear un mock de httpx.AsyncClient"""
    mock_client = MagicMock()

    async def async_post(*args, **kwargs):
        return mock_response

    mock_client.post = MagicMock(side_effect=async_post)
    return mock_client


@pytest.mark.asyncio
async def test_mcp_client_connection_success(mock_server_config, test_token):
    """Test: Conexión exitosa al servidor MCP"""
    client = MCPClient(mock_server_config, test_token)

    json_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"content": [{"type": "text", "text": "Success"}]}
    }
    mock_response = create_mock_response(json_data)
    mock_async_client = create_mock_async_client(mock_response)

    with patch.object(client, '_get_async_client', return_value=mock_async_client):
        result = await client.call_tool("test_tool", {"arg": "value"})

        # Verificar llamada
        assert mock_async_client.post.call_count == 1
        call_args = mock_async_client.post.call_args
        assert call_args[0][0] == "/rpc"

        # Verificar JSON-RPC
        json_req = call_args[1]["json"]
        assert json_req["jsonrpc"] == "2.0"
        assert json_req["method"] == "tools/call"
        assert json_req["params"]["name"] == "test_tool"

        # Verificar resultado
        assert "content" in result

    await client.close()


@pytest.mark.asyncio
async def test_mcp_client_timeout(mock_server_config, test_token):
    """Test: Timeout al conectar con MCP"""
    client = MCPClient(mock_server_config, test_token)

    mock_client = MagicMock()
    mock_client.post = MagicMock(side_effect=httpx.TimeoutException("Timeout"))

    with patch.object(client, '_get_async_client', return_value=mock_client):
        with pytest.raises(MCPConnectionError) as exc_info:
            await client.call_tool("test_tool", {})

        assert exc_info.value.codigo == "MCP_TIMEOUT"
        assert "test_tool" in exc_info.value.mensaje

    await client.close()


@pytest.mark.asyncio
async def test_mcp_client_connection_error(mock_server_config, test_token):
    """Test: Error de conexión con MCP"""
    client = MCPClient(mock_server_config, test_token)

    mock_client = MagicMock()
    mock_client.post = MagicMock(side_effect=httpx.ConnectError("Connection refused"))

    with patch.object(client, '_get_async_client', return_value=mock_client):
        with pytest.raises(MCPConnectionError) as exc_info:
            await client.call_tool("test_tool", {})

        assert exc_info.value.codigo == "MCP_CONNECTION_ERROR"
        assert "test-mcp" in exc_info.value.mensaje

    await client.close()


@pytest.mark.asyncio
async def test_mcp_client_auth_error_401(mock_server_config, test_token):
    """Test: Error de autenticación 401"""
    client = MCPClient(mock_server_config, test_token)

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Invalid token"

    http_error = httpx.HTTPStatusError(
        "401 Unauthorized",
        request=MagicMock(),
        response=mock_response
    )

    mock_client = MagicMock()
    mock_client.post = MagicMock(side_effect=http_error)

    with patch.object(client, '_get_async_client', return_value=mock_client):
        with pytest.raises(MCPAuthError) as exc_info:
            await client.call_tool("test_tool", {})

        assert exc_info.value.codigo == "AUTH_INVALID_TOKEN"

    await client.close()


@pytest.mark.asyncio
async def test_mcp_client_auth_error_403(mock_server_config, test_token):
    """Test: Error de permisos 403"""
    client = MCPClient(mock_server_config, test_token)

    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "Insufficient permissions"

    http_error = httpx.HTTPStatusError(
        "403 Forbidden",
        request=MagicMock(),
        response=mock_response
    )

    mock_client = MagicMock()
    mock_client.post = MagicMock(side_effect=http_error)

    with patch.object(client, '_get_async_client', return_value=mock_client):
        with pytest.raises(MCPAuthError) as exc_info:
            await client.call_tool("test_tool", {})

        assert exc_info.value.codigo == "AUTH_PERMISSION_DENIED"

    await client.close()


@pytest.mark.asyncio
async def test_mcp_client_tool_not_found_404(mock_server_config, test_token):
    """Test: Tool no encontrada (404)"""
    client = MCPClient(mock_server_config, test_token)

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Tool not found"

    http_error = httpx.HTTPStatusError(
        "404 Not Found",
        request=MagicMock(),
        response=mock_response
    )

    mock_client = MagicMock()
    mock_client.post = MagicMock(side_effect=http_error)

    with patch.object(client, '_get_async_client', return_value=mock_client):
        with pytest.raises(MCPToolError) as exc_info:
            await client.call_tool("unknown_tool", {})

        assert exc_info.value.codigo == "MCP_TOOL_NOT_FOUND"
        assert "unknown_tool" in exc_info.value.mensaje

    await client.close()


@pytest.mark.asyncio
async def test_mcp_client_server_unavailable_502(mock_server_config, test_token):
    """Test: Servidor no disponible (502)"""
    client = MCPClient(mock_server_config, test_token)

    mock_response = MagicMock()
    mock_response.status_code = 502
    mock_response.text = "Bad Gateway"

    http_error = httpx.HTTPStatusError(
        "502 Bad Gateway",
        request=MagicMock(),
        response=mock_response
    )

    mock_client = MagicMock()
    mock_client.post = MagicMock(side_effect=http_error)

    with patch.object(client, '_get_async_client', return_value=mock_client):
        with pytest.raises(MCPConnectionError) as exc_info:
            await client.call_tool("test_tool", {})

        assert exc_info.value.codigo == "MCP_SERVER_UNAVAILABLE"
        assert "502" in exc_info.value.mensaje

    await client.close()


@pytest.mark.asyncio
async def test_mcp_client_json_rpc_error(mock_server_config, test_token):
    """Test: Error en respuesta JSON-RPC"""
    client = MCPClient(mock_server_config, test_token)

    json_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": -32600,
            "message": "Invalid Request"
        }
    }
    mock_response = create_mock_response(json_data)
    mock_async_client = create_mock_async_client(mock_response)

    with patch.object(client, '_get_async_client', return_value=mock_async_client):
        with pytest.raises(MCPToolError) as exc_info:
            await client.call_tool("test_tool", {})

        assert exc_info.value.codigo == "MCP_TOOL_ERROR"
        assert "Invalid Request" in exc_info.value.mensaje

    await client.close()


@pytest.mark.asyncio
async def test_mcp_registry_initialization(mock_server_config, test_token):
    """Test: Inicialización del registry"""
    config = MCPServersConfig(mcp_servers=[mock_server_config])
    registry = MCPClientRegistry(config, test_token)

    json_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "tools": [
                {"name": "consultar_expediente", "description": "..."},
                {"name": "actualizar_datos", "description": "..."}
            ]
        }
    }
    mock_response = create_mock_response(json_data)

    async def async_post(*args, **kwargs):
        return mock_response

    with patch('httpx.AsyncClient.post', side_effect=async_post):
        await registry.initialize()

        # Verificar cliente creado
        assert "test-mcp" in registry._clients

        # Verificar tools descubiertas
        tools = registry.get_available_tools()
        assert "consultar_expediente" in tools
        assert "actualizar_datos" in tools

    await registry.close()


@pytest.mark.asyncio
async def test_mcp_registry_routing(mock_server_config, test_token):
    """Test: Routing de tools a servidores"""
    config = MCPServersConfig(mcp_servers=[mock_server_config])
    registry = MCPClientRegistry(config, test_token)

    # Mock para list_tools
    list_json = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"tools": [{"name": "test_tool", "description": "..."}]}
    }
    list_resp = create_mock_response(list_json)

    # Mock para call_tool
    call_json = {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {"status": "success"}
    }
    call_resp = create_mock_response(call_json)

    call_count = [0]

    async def async_post(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return list_resp
        return call_resp

    with patch('httpx.AsyncClient.post', side_effect=async_post):
        await registry.initialize()
        result = await registry.call_tool("test_tool", {"arg": "val"})
        assert result == {"status": "success"}

    await registry.close()


@pytest.mark.asyncio
async def test_mcp_registry_tool_not_found(mock_server_config, test_token):
    """Test: Error al llamar tool inexistente"""
    config = MCPServersConfig(mcp_servers=[mock_server_config])
    registry = MCPClientRegistry(config, test_token)

    json_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"tools": [{"name": "known_tool", "description": "..."}]}
    }
    mock_response = create_mock_response(json_data)

    async def async_post(*args, **kwargs):
        return mock_response

    with patch('httpx.AsyncClient.post', side_effect=async_post):
        await registry.initialize()

        with pytest.raises(MCPToolError) as exc_info:
            await registry.call_tool("unknown_tool", {})

        assert exc_info.value.codigo == "MCP_TOOL_NOT_FOUND"
        assert "unknown_tool" in exc_info.value.mensaje
        assert "known_tool" in exc_info.value.detalle

    await registry.close()


@pytest.mark.asyncio
async def test_mcp_registry_discovery_failure_graceful(mock_server_config, test_token):
    """Test: Fallo en discovery no impide inicialización"""
    config = MCPServersConfig(mcp_servers=[mock_server_config])
    registry = MCPClientRegistry(config, test_token)

    with patch('httpx.AsyncClient.post', side_effect=httpx.ConnectError("Failed")):
        await registry.initialize()

        assert registry._initialized is True
        assert "test-mcp" in registry._clients
        assert len(registry._tool_routing) == 0

    await registry.close()


@pytest.mark.asyncio
async def test_mcp_client_list_tools(mock_server_config, test_token):
    """Test: Listado de tools"""
    client = MCPClient(mock_server_config, test_token)

    json_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "tools": [
                {"name": "tool1", "description": "..."},
                {"name": "tool2", "description": "..."}
            ]
        }
    }
    mock_response = create_mock_response(json_data)
    mock_async_client = create_mock_async_client(mock_response)

    with patch.object(client, '_get_async_client', return_value=mock_async_client):
        result = await client.list_tools()

        # Verificar método
        call_args = mock_async_client.post.call_args
        assert call_args[1]["json"]["method"] == "tools/list"

        # Verificar resultado
        assert "tools" in result
        assert len(result["tools"]) == 2

    await client.close()


@pytest.mark.asyncio
async def test_mcp_client_headers_propagation(mock_server_config, test_token):
    """Test: Headers JWT propagados correctamente"""
    client = MCPClient(mock_server_config, test_token)

    # Verificar propiedades de configuración
    assert client._headers["Authorization"] == f"Bearer {test_token}"
    assert client._headers["Content-Type"] == "application/json"

    # Verificar que el cliente async se crea con los headers correctos
    async_client = client._get_async_client()
    assert "Authorization" in async_client.headers
    assert async_client.headers["Authorization"] == f"Bearer {test_token}"

    await client.close()


@pytest.mark.asyncio
async def test_mcp_registry_multiple_servers():
    """Test: Registry con múltiples servidores"""
    server1 = MCPServerConfig(
        id="mcp-expedientes",
        name="MCP Expedientes",
        description="Servidor de expedientes",
        url="http://localhost:8000",
        type="http",
        auth=MCPAuthConfig(type="jwt", audience="agentix-mcp-expedientes"),
        enabled=True
    )

    server2 = MCPServerConfig(
        id="mcp-firma",
        name="MCP Firma",
        description="Servidor de firma",
        url="http://localhost:8001",
        type="http",
        auth=MCPAuthConfig(type="jwt", audience="agentix-mcp-firma"),
        enabled=True
    )

    config = MCPServersConfig(mcp_servers=[server1, server2])
    registry = MCPClientRegistry(config, "test-token")

    resp1_json = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"tools": [{"name": "consultar_expediente", "description": "..."}]}
    }
    resp1 = create_mock_response(resp1_json)

    resp2_json = {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {"tools": [{"name": "firmar_documento", "description": "..."}]}
    }
    resp2 = create_mock_response(resp2_json)

    call_count = [0]

    async def async_post(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return resp1
        return resp2

    with patch('httpx.AsyncClient.post', side_effect=async_post):
        await registry.initialize()

        assert "mcp-expedientes" in registry._clients
        assert "mcp-firma" in registry._clients
        assert registry._tool_routing["consultar_expediente"] == "mcp-expedientes"
        assert registry._tool_routing["firmar_documento"] == "mcp-firma"

    await registry.close()
