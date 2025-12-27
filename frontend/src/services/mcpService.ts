// services/mcpService.ts
// Servicio para comunicación con el MCP Server Mock

import axios from 'axios';

const MCP_BASE_URL = import.meta.env.VITE_MCP_URL || 'http://localhost:8000';

// Cliente axios específico para MCP (sin interceptors del admin token)
const mcpApi = axios.create({
  baseURL: MCP_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================================
// Types
// ============================================================================

export interface MCPHealthResponse {
  status: string;
  service: string;
  version: string;
  protocol: string;
  capabilities: Record<string, boolean>;
}

export interface MCPServerInfo {
  name: string;
  version: string;
  protocol_version: string;
  capabilities: Record<string, boolean>;
}

export interface MCPTool {
  name: string;
  description: string;
  inputSchema?: Record<string, unknown>;
}

export interface MCPResource {
  uri: string;
  name: string;
  description?: string;
  mimeType?: string;
}

export interface MCPToolResult {
  content: Array<{ type: string; text: string }>;
}

export interface MCPResourceContent {
  contents: Array<{
    uri: string;
    mimeType: string;
    text: string;
  }>;
}

export interface JsonRpcResponse<T> {
  jsonrpc: string;
  id: number | string;
  result?: T;
  error?: {
    code: number;
    message: string;
  };
}

// ============================================================================
// Public Endpoints (sin autenticación)
// ============================================================================

/**
 * Health check del servidor MCP
 */
export const getHealth = async (): Promise<MCPHealthResponse> => {
  const response = await mcpApi.get<MCPHealthResponse>('/health');
  return response.data;
};

/**
 * Información del servidor MCP
 */
export const getServerInfo = async (): Promise<MCPServerInfo> => {
  const response = await mcpApi.get<MCPServerInfo>('/info');
  return response.data;
};

// ============================================================================
// Authenticated Endpoints (requieren JWT)
// ============================================================================

/**
 * Lista las tools disponibles en el servidor MCP
 */
export const listTools = async (jwt: string): Promise<MCPTool[]> => {
  const response = await mcpApi.post<JsonRpcResponse<{ tools: MCPTool[] }>>(
    '/rpc',
    {
      jsonrpc: '2.0',
      id: 1,
      method: 'tools/list'
    },
    {
      headers: { Authorization: `Bearer ${jwt}` }
    }
  );

  if (response.data.error) {
    throw new Error(response.data.error.message);
  }

  return response.data.result?.tools || [];
};

/**
 * Lista los resources disponibles en el servidor MCP
 */
export const listResources = async (jwt: string): Promise<MCPResource[]> => {
  const response = await mcpApi.post<JsonRpcResponse<{ resources: MCPResource[] }>>(
    '/rpc',
    {
      jsonrpc: '2.0',
      id: 2,
      method: 'resources/list'
    },
    {
      headers: { Authorization: `Bearer ${jwt}` }
    }
  );

  if (response.data.error) {
    throw new Error(response.data.error.message);
  }

  return response.data.result?.resources || [];
};

/**
 * Ejecuta una tool del servidor MCP
 */
export const callTool = async (
  jwt: string,
  toolName: string,
  args: Record<string, unknown>
): Promise<MCPToolResult> => {
  const response = await mcpApi.post<JsonRpcResponse<MCPToolResult>>(
    '/rpc',
    {
      jsonrpc: '2.0',
      id: 3,
      method: 'tools/call',
      params: {
        name: toolName,
        arguments: args
      }
    },
    {
      headers: { Authorization: `Bearer ${jwt}` }
    }
  );

  if (response.data.error) {
    throw new Error(response.data.error.message);
  }

  return response.data.result || { content: [] };
};

/**
 * Lee un resource del servidor MCP
 */
export const readResource = async (
  jwt: string,
  uri: string
): Promise<MCPResourceContent> => {
  const response = await mcpApi.post<JsonRpcResponse<MCPResourceContent>>(
    '/rpc',
    {
      jsonrpc: '2.0',
      id: 4,
      method: 'resources/read',
      params: { uri }
    },
    {
      headers: { Authorization: `Bearer ${jwt}` }
    }
  );

  if (response.data.error) {
    throw new Error(response.data.error.message);
  }

  return response.data.result || { contents: [] };
};

// ============================================================================
// Utilities
// ============================================================================

/**
 * Parsea el contenido JSON de una respuesta de tool
 */
export const parseToolContent = (result: MCPToolResult): unknown => {
  try {
    const text = result.content[0]?.text;
    if (text) {
      return JSON.parse(text);
    }
    return null;
  } catch {
    return result.content[0]?.text || null;
  }
};

/**
 * Parsea el contenido JSON de un resource
 */
export const parseResourceContent = (result: MCPResourceContent): unknown => {
  try {
    const text = result.contents[0]?.text;
    if (text) {
      return JSON.parse(text);
    }
    return null;
  } catch {
    return result.contents[0]?.text || null;
  }
};

/**
 * Obtiene la URL base del MCP server
 */
export const getMcpBaseUrl = (): string => MCP_BASE_URL;
