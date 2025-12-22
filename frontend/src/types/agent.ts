// ============================================================================
// Agent Configuration
// ============================================================================

export interface AgentConfig {
  nombre: string;
  system_prompt: string;
  modelo: string;
  prompt_tarea: string;
  herramientas: string[];
}

export interface AgentInfo {
  id: string;
  nombre: string;
  descripcion: string;
  estado: 'disponible' | 'ocupado' | 'inactivo';
  tipo: 'ValidadorDocumental' | 'AnalizadorSubvencion' | 'GeneradorInforme';
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
// Agent Execution
// ============================================================================

export interface ExecuteAgentRequest {
  expediente_id: string;
  tarea_id: string;
  agent_config: AgentConfig;
  webhook_url: string;
  timeout_seconds: number;
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
