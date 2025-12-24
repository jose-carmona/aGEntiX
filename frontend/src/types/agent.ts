// ============================================================================
// Agent Configuration (Simplificado - Paso 4)
// ============================================================================

/**
 * Información de un agente disponible (desde GET /api/v1/agent/agents)
 */
export interface AgentInfo {
  name: string;
  description: string;
  required_permissions: string[];
}

/**
 * Contexto de ejecución del agente
 */
export interface AgentContext {
  expediente_id: string;
  tarea_id: string;
}

// ============================================================================
// JWT Generation
// ============================================================================

export interface GenerateJWTRequest {
  exp_id: string;
  exp_tipo?: string;
  tarea_id?: string;
  tarea_nombre?: string;
  permisos: string[];
  mcp_servers?: string[];
  exp_hours?: number;
}

export interface JWTClaims {
  sub: string;
  iss: string;
  aud: string | string[];
  exp: number;
  iat: number;
  nbf: number;
  jti: string;
  exp_id: string;
  exp_tipo: string;
  tarea_id: string;
  tarea_nombre: string;
  permisos: string[];
}

export interface GenerateJWTResponse {
  token: string;
  claims: JWTClaims;
}

// ============================================================================
// Agent Execution (Simplificado - Paso 4)
// ============================================================================

/**
 * Request simplificado para ejecutar un agente
 * La configuración del agente (model, system_prompt, tools) se carga desde agents.yaml
 */
export interface ExecuteAgentRequest {
  agent: string;           // Nombre del agente (ej: "ValidadorDocumental")
  prompt: string;          // Instrucciones específicas para esta ejecución
  context: AgentContext;   // Contexto con expediente_id y tarea_id
  callback_url?: string;   // URL de callback opcional
}

/**
 * Respuesta del endpoint execute
 */
export interface ExecuteAgentResponse {
  agent_run_id: string;
  status: string;
  message: string;
  callback_url: string | null;
}

export interface AgentExecution {
  agent_run_id: string;
  expediente_id: string;
  tarea_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  elapsed_seconds: number;
  success?: boolean;
  resultado?: Record<string, any>;
  error?: Record<string, string>;
}

export interface ExecutionHistoryItem {
  id: string;
  agent_run_id: string;
  agent_type: string;
  expediente_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  elapsed_seconds: number;
  success?: boolean;
}

// ============================================================================
// Permissions
// ============================================================================

export interface Permission {
  id: string;
  nombre: string;
  descripcion: string;
  category: 'lectura' | 'escritura' | 'admin';
}

// ============================================================================
// MCP Servers
// ============================================================================

export interface MCPServer {
  id: string;
  name: string;
  enabled: boolean;
  url: string;
}
