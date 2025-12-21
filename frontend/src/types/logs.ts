export type LogLevel = 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  component: string;
  agent?: string;
  expediente_id?: string;
  message: string;
  context?: Record<string, any>;
}

export interface LogFilters {
  level?: LogLevel;
  component?: string;
  agent?: string;
  expediente_id?: string;
  search?: string;
  startDate?: string;
  endDate?: string;
}
