// Tipos para el sistema de logs

export type LogLevel = 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL' | 'DEBUG';

export type LogComponent =
  | 'AgentExecutor'
  | 'MCPClient'
  | 'PIIRedactor'
  | 'AuditLogger'
  | 'JWTValidator'
  | 'APIServer'
  | 'WebhookService'
  | 'TaskTracker'
  | 'Unknown';

export type AgentType =
  | 'ValidadorDocumental'
  | 'AnalizadorSubvencion'
  | 'GeneradorInforme'
  | 'Unknown';

export interface LogEntry {
  id: string;
  timestamp: string; // ISO 8601 format
  level: LogLevel;
  component: LogComponent;
  agent?: AgentType;
  expediente_id?: string;
  message: string;
  context?: Record<string, any>;
  user_id?: string;
  agent_run_id?: string;
  duration_ms?: number;
  error?: {
    type: string;
    message: string;
    stacktrace?: string;
  };
}

export interface LogFilters {
  level?: LogLevel[];
  component?: LogComponent[];
  agent?: AgentType[];
  expediente_id?: string;
  dateFrom?: Date;
  dateTo?: Date;
  searchText?: string;
}

export interface LogsResponse {
  logs: LogEntry[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface LogsStreamMessage {
  type: 'log' | 'ping' | 'error';
  data?: LogEntry;
  message?: string;
}

export interface ExportOptions {
  format: 'json' | 'jsonl' | 'csv';
  filters?: LogFilters;
}
