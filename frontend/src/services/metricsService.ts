import { generateMockMetrics, mockExecutionHistory, mockPIIHistory } from '../mocks/metrics.mock';
import { DashboardMetrics, ExecutionHistoryPoint, MetricsFilter, PIIHistoryPoint } from '../types/metrics';
import { api } from './api';

// Flag para usar datos mock o la API real
const USE_MOCK_DATA = true; // Cambiar a false cuando la API esté disponible

/**
 * Obtiene las métricas del dashboard
 * @param filter Filtros opcionales para las métricas
 * @returns Métricas del dashboard
 */
export const getMetrics = async (filter?: MetricsFilter): Promise<DashboardMetrics> => {
  if (USE_MOCK_DATA) {
    // Simular latencia de red
    await new Promise((resolve) => setTimeout(resolve, 300));
    return generateMockMetrics();
  }

  try {
    const params = filter?.dateRange
      ? {
          start: filter.dateRange.start.toISOString(),
          end: filter.dateRange.end.toISOString(),
          agent_type: filter.agentType,
        }
      : {};

    /* const response = await api.get<DashboardMetrics>('/api/v1/dashboard/metrics', { params }); */
    const response = await api.get<DashboardMetrics>('/metrics', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching metrics:', error);
    throw error;
  }
};

/**
 * Obtiene el histórico de ejecuciones
 * @param hours Número de horas hacia atrás (por defecto 24)
 * @returns Puntos históricos de ejecución
 */
export const getExecutionHistory = async (hours: number = 24): Promise<ExecutionHistoryPoint[]> => {
  if (USE_MOCK_DATA) {
    // Simular latencia de red
    await new Promise((resolve) => setTimeout(resolve, 200));
    return mockExecutionHistory;
  }

  try {
    const response = await api.get<ExecutionHistoryPoint[]>('/api/v1/dashboard/execution-history', {
      params: { hours },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching execution history:', error);
    throw error;
  }
};

/**
 * Obtiene el histórico de PII redactados
 * @param hours Número de horas hacia atrás (por defecto 24)
 * @returns Puntos históricos de PII
 */
export const getPIIHistory = async (hours: number = 24): Promise<PIIHistoryPoint[]> => {
  if (USE_MOCK_DATA) {
    // Simular latencia de red
    await new Promise((resolve) => setTimeout(resolve, 200));
    return mockPIIHistory;
  }

  try {
    const response = await api.get<PIIHistoryPoint[]>('/api/v1/dashboard/pii-history', {
      params: { hours },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching PII history:', error);
    throw error;
  }
};

/**
 * Exporta las métricas a formato CSV
 * @param metrics Métricas a exportar
 * @returns Blob con el archivo CSV
 */
export const exportMetricsToCSV = (metrics: DashboardMetrics): Blob => {
  // Cabecera CSV
  const headers = [
    'Métrica',
    'Valor',
  ];

  // Datos CSV
  const rows = [
    ['Total de Ejecuciones', metrics.total_executions.toString()],
    ['Ejecuciones Hoy', metrics.executions_today.toString()],
    ['Ejecuciones Semana', metrics.executions_week.toString()],
    ['Ejecuciones Mes', metrics.executions_month.toString()],
    ['Tasa de Éxito (%)', metrics.success_rate.toFixed(1)],
    ['Tiempo Promedio Ejecución (s)', metrics.avg_execution_time.toFixed(2)],
    ['', ''],
    ['Ejecuciones por Agente', ''],
    ['ValidadorDocumental', metrics.executions_by_agent.ValidadorDocumental.toString()],
    ['AnalizadorSubvencion', metrics.executions_by_agent.AnalizadorSubvencion.toString()],
    ['GeneradorInforme', metrics.executions_by_agent.GeneradorInforme.toString()],
    ['', ''],
    ['Ejecuciones por Estado', ''],
    ['Exitosas', metrics.executions_by_status.success.toString()],
    ['Errores', metrics.executions_by_status.error.toString()],
    ['En Progreso', metrics.executions_by_status.in_progress.toString()],
    ['', ''],
    ['PII Redactados', ''],
    ['DNI', metrics.pii_redacted.DNI.toString()],
    ['NIE', metrics.pii_redacted.NIE.toString()],
    ['Email', metrics.pii_redacted.email.toString()],
    ['Teléfono Móvil', metrics.pii_redacted.telefono_movil.toString()],
    ['Teléfono Fijo', metrics.pii_redacted.telefono_fijo.toString()],
    ['IBAN', metrics.pii_redacted.IBAN.toString()],
    ['Tarjeta', metrics.pii_redacted.tarjeta.toString()],
    ['CCC', metrics.pii_redacted.CCC.toString()],
    ['Total PII', metrics.pii_redacted_total.toString()],
    ['', ''],
    ['Performance', ''],
    ['Tiempo Respuesta Promedio (ms)', metrics.performance.avg_response_time.toString()],
    ['Llamadas MCP/s', metrics.performance.mcp_calls_per_second.toFixed(1)],
    ['Latencia P50 (ms)', metrics.performance.latency_p50.toString()],
    ['Latencia P95 (ms)', metrics.performance.latency_p95.toString()],
    ['Latencia P99 (ms)', metrics.performance.latency_p99.toString()],
  ];

  // Construir CSV
  const csv = [
    headers.join(','),
    ...rows.map((row) => row.join(',')),
  ].join('\n');

  // Crear Blob
  return new Blob([csv], { type: 'text/csv;charset=utf-8;' });
};

/**
 * Descarga las métricas como archivo CSV
 * @param metrics Métricas a descargar
 * @param filename Nombre del archivo (opcional)
 */
export const downloadMetricsCSV = (metrics: DashboardMetrics, filename?: string): void => {
  const blob = exportMetricsToCSV(metrics);
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');

  link.href = url;
  link.download = filename || `agentix-metrics-${new Date().toISOString().split('T')[0]}.csv`;
  document.body.appendChild(link);
  link.click();

  // Limpieza
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Exporta las métricas a formato JSON
 * @param metrics Métricas a exportar
 * @returns Blob con el archivo JSON
 */
export const exportMetricsToJSON = (metrics: DashboardMetrics): Blob => {
  const json = JSON.stringify(metrics, null, 2);
  return new Blob([json], { type: 'application/json;charset=utf-8;' });
};

/**
 * Descarga las métricas como archivo JSON
 * @param metrics Métricas a descargar
 * @param filename Nombre del archivo (opcional)
 */
export const downloadMetricsJSON = (metrics: DashboardMetrics, filename?: string): void => {
  const blob = exportMetricsToJSON(metrics);
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');

  link.href = url;
  link.download = filename || `agentix-metrics-${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(link);
  link.click();

  // Limpieza
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};
