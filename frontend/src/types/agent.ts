export interface AgentConfig {
  nombre: string;
  system_prompt: string;
  modelo: string;
  prompt_tarea: string;
  herramientas: string[];
}

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
