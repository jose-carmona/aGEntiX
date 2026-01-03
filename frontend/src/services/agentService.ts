// services/agentService.ts

import { api } from './api';
import type {
  GenerateJWTRequest,
  GenerateJWTResponse,
  ExecuteAgentRequest,
  ExecuteAgentResponse,
  AgentExecution,
  AgentInfo,
  Permission,
  MCPServer
} from '../types/agent';

// ============================================================================
// JWT Generation
// ============================================================================

/**
 * Genera un JWT de prueba para testing de agentes
 * Requiere autenticación de admin (Bearer token)
 */
export const generateJWT = async (request: GenerateJWTRequest): Promise<GenerateJWTResponse> => {
  const response = await api.post<GenerateJWTResponse>('/api/v1/auth/generate-jwt', request);
  return response.data;
};

// ============================================================================
// Agent Execution (Simplificado - Paso 4)
// ============================================================================

/**
 * Ejecuta un agente con el JWT proporcionado
 *
 * Request simplificado:
 * - agent: Nombre del agente (ej: "ValidadorDocumental")
 * - additional_goal: Objetivo adicional opcional que se añade al goal del agente
 * - context: { expediente_id, tarea_id }
 * - callback_url: URL de callback (opcional)
 */
export const executeAgent = async (
  request: ExecuteAgentRequest,
  jwt: string
): Promise<ExecuteAgentResponse> => {
  const response = await api.post<ExecuteAgentResponse>(
    '/api/v1/agent/execute',
    request,
    {
      headers: {
        Authorization: `Bearer ${jwt}`
      }
    }
  );
  return response.data;
};

/**
 * Obtiene el estado de una ejecución de agente
 * El JWT debe incluirse en el header Authorization
 */
export const getAgentStatus = async (
  agentRunId: string,
  jwt: string
): Promise<AgentExecution> => {
  const response = await api.get<AgentExecution>(
    `/api/v1/agent/status/${agentRunId}`,
    {
      headers: {
        Authorization: `Bearer ${jwt}`
      }
    }
  );
  return response.data;
};

// ============================================================================
// Agent Information (Paso 4 - Usando API real)
// ============================================================================

/**
 * Obtiene la lista de agentes disponibles desde el backend
 * GET /api/v1/agent/agents
 */
export const getAvailableAgents = async (): Promise<AgentInfo[]> => {
  const response = await api.get<{ agents: AgentInfo[] }>('/api/v1/agent/agents');
  return response.data.agents;
};

// ============================================================================
// Permissions (Mock Data)
// ============================================================================

/**
 * Obtiene la lista de permisos disponibles
 * TODO: Implementar endpoint real en backend cuando esté disponible
 */
export const getAvailablePermissions = async (): Promise<Permission[]> => {
  // Mock data - permisos del sistema
  return Promise.resolve([
    {
      id: 'consulta',
      nombre: 'Consulta',
      descripcion: 'Permite leer expedientes y documentos',
      category: 'lectura'
    },
    {
      id: 'gestion',
      nombre: 'Gestión',
      descripcion: 'Permite modificar expedientes y documentos',
      category: 'escritura'
    },
    {
      id: 'firma',
      nombre: 'Firma',
      descripcion: 'Permite firmar documentos',
      category: 'escritura'
    },
    {
      id: 'administracion',
      nombre: 'Administración',
      descripcion: 'Permisos administrativos completos',
      category: 'admin'
    }
  ]);
};

// ============================================================================
// MCP Servers (Mock Data)
// ============================================================================

/**
 * Obtiene la lista de servidores MCP disponibles
 * TODO: Implementar endpoint real en backend cuando esté disponible
 */
export const getAvailableMCPServers = async (): Promise<MCPServer[]> => {
  // Mock data - servidores MCP configurados
  return Promise.resolve([
    {
      id: 'agentix-mcp-expedientes',
      name: 'MCP Expedientes',
      enabled: true,
      url: 'http://localhost:8000'
    },
    {
      id: 'agentix-mcp-firma',
      name: 'MCP Firma Electrónica',
      enabled: false,
      url: 'http://localhost:8001'
    },
    {
      id: 'agentix-mcp-normativa',
      name: 'MCP Normativa',
      enabled: false,
      url: 'http://localhost:8002'
    }
  ]);
};

// ============================================================================
// Utilities
// ============================================================================

/**
 * Decodifica un JWT y retorna sus claims (sin validación)
 * NOTA: Esto es solo para visualización, NO valida el token
 */
export const decodeJWT = (token: string): any => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Error decoding JWT:', error);
    return null;
  }
};

/**
 * Formatea timestamps Unix a strings legibles
 */
export const formatTimestamp = (timestamp: number): string => {
  return new Date(timestamp * 1000).toLocaleString('es-ES', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};
