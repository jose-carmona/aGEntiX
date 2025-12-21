export interface Metrics {
  total_executions: number;
  executions_today: number;
  success_rate: number;
  avg_execution_time: number;
  executions_by_agent: Record<string, number>;
  executions_by_status: {
    success: number;
    error: number;
    in_progress: number;
  };
  mcp_servers_status: Record<string, string>;
  pii_redacted: Record<string, number>;
}
