// Types for dashboard metrics

export interface ExecutionsByAgent {
  ValidadorDocumental: number;
  AnalizadorSubvencion: number;
  GeneradorInforme: number;
}

export interface ExecutionsByStatus {
  success: number;
  error: number;
  in_progress: number;
}

export interface MCPServersStatus {
  [key: string]: 'active' | 'inactive';
}

export interface PIIRedacted {
  DNI: number;
  NIE: number;
  email: number;
  telefono_movil: number;
  telefono_fijo: number;
  IBAN: number;
  tarjeta: number;
  CCC: number;
}

export interface PerformanceMetrics {
  avg_response_time: number; // ms
  mcp_calls_per_second: number;
  latency_p50: number; // ms
  latency_p95: number; // ms
  latency_p99: number; // ms
}

export interface DashboardMetrics {
  // Ejecuciones de agentes
  total_executions: number;
  executions_today: number;
  executions_week: number;
  executions_month: number;
  success_rate: number; // Percentage
  avg_execution_time: number; // seconds
  executions_by_agent: ExecutionsByAgent;
  executions_by_status: ExecutionsByStatus;

  // Recursos del sistema
  mcp_servers_status: MCPServersStatus;
  mcp_tools_available: number;
  external_services_status: {
    [key: string]: 'connected' | 'disconnected';
  };

  // PII redactados
  pii_redacted: PIIRedacted;
  pii_redacted_total: number;

  // Performance
  performance: PerformanceMetrics;

  // Timestamp
  timestamp: string;
}

export interface DateRange {
  start: Date;
  end: Date;
}

export interface MetricsFilter {
  dateRange?: DateRange;
  agentType?: keyof ExecutionsByAgent;
}

// Tipos para los gráficos de histórico
export interface ExecutionHistoryPoint {
  timestamp: string;
  total: number;
  success: number;
  error: number;
  in_progress: number;
}

export interface PIIHistoryPoint {
  timestamp: string;
  DNI: number;
  NIE: number;
  email: number;
  telefono: number;
  IBAN: number;
  other: number;
}

// Legacy type for compatibility
export type Metrics = DashboardMetrics;
