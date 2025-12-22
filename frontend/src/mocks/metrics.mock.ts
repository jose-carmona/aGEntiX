import { DashboardMetrics, ExecutionHistoryPoint, PIIHistoryPoint } from '../types/metrics';

// Datos mock para el dashboard de métricas
export const mockMetrics: DashboardMetrics = {
  // Ejecuciones de agentes
  total_executions: 1247,
  executions_today: 34,
  executions_week: 178,
  executions_month: 756,
  success_rate: 94.2,
  avg_execution_time: 2.3,
  executions_by_agent: {
    ValidadorDocumental: 512,
    AnalizadorSubvencion: 423,
    GeneradorInforme: 312,
  },
  executions_by_status: {
    success: 1175,
    error: 62,
    in_progress: 10,
  },

  // Recursos del sistema
  mcp_servers_status: {
    expedientes: 'active',
    firma: 'inactive',
    notificaciones: 'active',
  },
  mcp_tools_available: 12,
  external_services_status: {
    'Base de Datos GEX': 'connected',
    'Servicio de Firma': 'disconnected',
    'API de Notificaciones': 'connected',
  },

  // PII redactados
  pii_redacted: {
    DNI: 3421,
    NIE: 234,
    email: 2134,
    telefono_movil: 1876,
    telefono_fijo: 892,
    IBAN: 1234,
    tarjeta: 156,
    CCC: 423,
  },
  pii_redacted_total: 10370,

  // Performance
  performance: {
    avg_response_time: 234, // ms
    mcp_calls_per_second: 12.5,
    latency_p50: 180,
    latency_p95: 450,
    latency_p99: 890,
  },

  // Timestamp
  timestamp: new Date().toISOString(),
};

// Datos históricos de ejecuciones (últimas 24 horas)
export const mockExecutionHistory: ExecutionHistoryPoint[] = [
  {
    timestamp: '2025-12-21T00:00:00Z',
    total: 45,
    success: 42,
    error: 2,
    in_progress: 1,
  },
  {
    timestamp: '2025-12-21T02:00:00Z',
    total: 38,
    success: 35,
    error: 3,
    in_progress: 0,
  },
  {
    timestamp: '2025-12-21T04:00:00Z',
    total: 52,
    success: 49,
    error: 2,
    in_progress: 1,
  },
  {
    timestamp: '2025-12-21T06:00:00Z',
    total: 67,
    success: 64,
    error: 2,
    in_progress: 1,
  },
  {
    timestamp: '2025-12-21T08:00:00Z',
    total: 89,
    success: 85,
    error: 3,
    in_progress: 1,
  },
  {
    timestamp: '2025-12-21T10:00:00Z',
    total: 123,
    success: 118,
    error: 4,
    in_progress: 1,
  },
  {
    timestamp: '2025-12-21T12:00:00Z',
    total: 156,
    success: 145,
    error: 9,
    in_progress: 2,
  },
  {
    timestamp: '2025-12-21T14:00:00Z',
    total: 134,
    success: 127,
    error: 5,
    in_progress: 2,
  },
  {
    timestamp: '2025-12-21T16:00:00Z',
    total: 98,
    success: 92,
    error: 5,
    in_progress: 1,
  },
  {
    timestamp: '2025-12-21T18:00:00Z',
    total: 76,
    success: 71,
    error: 4,
    in_progress: 1,
  },
  {
    timestamp: '2025-12-21T20:00:00Z',
    total: 54,
    success: 51,
    error: 2,
    in_progress: 1,
  },
  {
    timestamp: '2025-12-21T22:00:00Z',
    total: 42,
    success: 40,
    error: 1,
    in_progress: 1,
  },
];

// Datos históricos de PII redactados (últimas 24 horas)
export const mockPIIHistory: PIIHistoryPoint[] = [
  {
    timestamp: '2025-12-21T00:00:00Z',
    DNI: 156,
    NIE: 12,
    email: 89,
    telefono: 67,
    IBAN: 45,
    other: 23,
  },
  {
    timestamp: '2025-12-21T02:00:00Z',
    DNI: 134,
    NIE: 8,
    email: 76,
    telefono: 54,
    IBAN: 38,
    other: 19,
  },
  {
    timestamp: '2025-12-21T04:00:00Z',
    DNI: 178,
    NIE: 15,
    email: 98,
    telefono: 72,
    IBAN: 51,
    other: 27,
  },
  {
    timestamp: '2025-12-21T06:00:00Z',
    DNI: 234,
    NIE: 19,
    email: 123,
    telefono: 89,
    IBAN: 67,
    other: 34,
  },
  {
    timestamp: '2025-12-21T08:00:00Z',
    DNI: 312,
    NIE: 25,
    email: 167,
    telefono: 112,
    IBAN: 89,
    other: 45,
  },
  {
    timestamp: '2025-12-21T10:00:00Z',
    DNI: 423,
    NIE: 34,
    email: 221,
    telefono: 156,
    IBAN: 112,
    other: 58,
  },
  {
    timestamp: '2025-12-21T12:00:00Z',
    DNI: 567,
    NIE: 45,
    email: 289,
    telefono: 198,
    IBAN: 145,
    other: 72,
  },
  {
    timestamp: '2025-12-21T14:00:00Z',
    DNI: 489,
    NIE: 38,
    email: 245,
    telefono: 167,
    IBAN: 123,
    other: 61,
  },
  {
    timestamp: '2025-12-21T16:00:00Z',
    DNI: 367,
    NIE: 29,
    email: 189,
    telefono: 134,
    IBAN: 98,
    other: 48,
  },
  {
    timestamp: '2025-12-21T18:00:00Z',
    DNI: 289,
    NIE: 23,
    email: 145,
    telefono: 103,
    IBAN: 76,
    other: 37,
  },
  {
    timestamp: '2025-12-21T20:00:00Z',
    DNI: 212,
    NIE: 17,
    email: 112,
    telefono: 79,
    IBAN: 58,
    other: 28,
  },
  {
    timestamp: '2025-12-21T22:00:00Z',
    DNI: 167,
    NIE: 13,
    email: 89,
    telefono: 62,
    IBAN: 45,
    other: 22,
  },
];

// Función helper para generar métricas con variaciones aleatorias
export function generateMockMetrics(): DashboardMetrics {
  const variation = (base: number, percent: number = 0.1): number => {
    const randomVariation = (Math.random() - 0.5) * 2 * percent;
    return Math.round(base * (1 + randomVariation));
  };

  return {
    ...mockMetrics,
    executions_today: variation(mockMetrics.executions_today),
    executions_week: variation(mockMetrics.executions_week),
    executions_month: variation(mockMetrics.executions_month),
    executions_by_status: {
      success: variation(mockMetrics.executions_by_status.success),
      error: variation(mockMetrics.executions_by_status.error),
      in_progress: variation(mockMetrics.executions_by_status.in_progress, 0.5),
    },
    performance: {
      avg_response_time: variation(mockMetrics.performance.avg_response_time, 0.15),
      mcp_calls_per_second: parseFloat((mockMetrics.performance.mcp_calls_per_second * (1 + (Math.random() - 0.5) * 0.2)).toFixed(1)),
      latency_p50: variation(mockMetrics.performance.latency_p50, 0.15),
      latency_p95: variation(mockMetrics.performance.latency_p95, 0.15),
      latency_p99: variation(mockMetrics.performance.latency_p99, 0.15),
    },
    timestamp: new Date().toISOString(),
  };
}
