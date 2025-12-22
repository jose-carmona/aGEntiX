import { useState, useEffect, useCallback } from 'react';
import { DashboardMetrics, MetricsFilter, ExecutionHistoryPoint, PIIHistoryPoint } from '../types/metrics';
import { getMetrics, getExecutionHistory, getPIIHistory } from '../services/metricsService';

interface UseMetricsOptions {
  autoRefresh?: boolean;
  refreshInterval?: number; // en milisegundos
  filter?: MetricsFilter;
}

interface UseMetricsReturn {
  metrics: DashboardMetrics | null;
  executionHistory: ExecutionHistoryPoint[];
  piiHistory: PIIHistoryPoint[];
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

/**
 * Hook para obtener y gestionar las métricas del dashboard
 * @param options Opciones de configuración
 * @returns Estado de las métricas
 */
export const useMetrics = (options: UseMetricsOptions = {}): UseMetricsReturn => {
  const {
    autoRefresh = true,
    refreshInterval = 10000, // 10 segundos por defecto
    filter,
  } = options;

  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [executionHistory, setExecutionHistory] = useState<ExecutionHistoryPoint[]>([]);
  const [piiHistory, setPIIHistory] = useState<PIIHistoryPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  /**
   * Función para obtener las métricas
   */
  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Obtener métricas, histórico de ejecuciones e histórico de PII en paralelo
      const [metricsData, executionHistoryData, piiHistoryData] = await Promise.all([
        getMetrics(filter),
        getExecutionHistory(24),
        getPIIHistory(24),
      ]);

      setMetrics(metricsData);
      setExecutionHistory(executionHistoryData);
      setPIIHistory(piiHistoryData);
    } catch (err) {
      console.error('Error fetching metrics:', err);
      setError(err instanceof Error ? err : new Error('Error desconocido al obtener métricas'));
    } finally {
      setLoading(false);
    }
  }, [filter]);

  /**
   * Función para refrescar manualmente
   */
  const refetch = useCallback(async () => {
    await fetchMetrics();
  }, [fetchMetrics]);

  // Efecto para la carga inicial
  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  // Efecto para el auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const intervalId = setInterval(() => {
      fetchMetrics();
    }, refreshInterval);

    // Cleanup
    return () => {
      clearInterval(intervalId);
    };
  }, [autoRefresh, refreshInterval, fetchMetrics]);

  return {
    metrics,
    executionHistory,
    piiHistory,
    loading,
    error,
    refetch,
  };
};
