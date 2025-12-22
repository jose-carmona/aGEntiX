import { useState, useEffect, useCallback } from 'react';
import { LogEntry, LogFilters, LogsResponse } from '../types/logs';
import { getLogs } from '../services/logsService';

interface UseLogsOptions {
  initialFilters?: LogFilters;
  pageSize?: number;
  autoRefresh?: boolean;
  refreshInterval?: number; // en milisegundos
}

interface UseLogsReturn {
  logs: LogEntry[];
  loading: boolean;
  error: Error | null;
  filters: LogFilters;
  setFilters: (filters: LogFilters) => void;
  total: number;
  page: number;
  hasMore: boolean;
  loadMore: () => void;
  refresh: () => void;
  clearFilters: () => void;
}

/**
 * Hook para gestionar el estado de logs con filtros y paginación
 */
export function useLogs(options: UseLogsOptions = {}): UseLogsReturn {
  const {
    initialFilters = {},
    pageSize = 50,
    autoRefresh = false,
    refreshInterval = 10000,
  } = options;

  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [filters, setFilters] = useState<LogFilters>(initialFilters);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  // Función para cargar logs
  const fetchLogs = useCallback(
    async (currentPage: number, append: boolean = false) => {
      try {
        setLoading(true);
        setError(null);

        const response: LogsResponse = await getLogs(filters, currentPage, pageSize);

        if (append) {
          // Append para "load more"
          setLogs((prev) => [...prev, ...response.logs]);
        } else {
          // Replace para nueva búsqueda o refresh
          setLogs(response.logs);
        }

        setTotal(response.total);
        setHasMore(response.has_more);
        setPage(currentPage);
      } catch (err) {
        setError(err as Error);
        console.error('Error fetching logs:', err);
      } finally {
        setLoading(false);
      }
    },
    [filters, pageSize]
  );

  // Cargar más logs (paginación)
  const loadMore = useCallback(() => {
    if (!loading && hasMore) {
      fetchLogs(page + 1, true);
    }
  }, [loading, hasMore, page, fetchLogs]);

  // Refrescar logs (desde página 1)
  const refresh = useCallback(() => {
    fetchLogs(1, false);
  }, [fetchLogs]);

  // Limpiar filtros
  const clearFilters = useCallback(() => {
    setFilters({});
  }, []);

  // Efecto: cargar logs cuando cambian los filtros
  useEffect(() => {
    setPage(1);
    fetchLogs(1, false);
  }, [filters, fetchLogs]);

  // Efecto: auto-refresh si está habilitado
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      refresh();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, refresh]);

  return {
    logs,
    loading,
    error,
    filters,
    setFilters,
    total,
    page,
    hasMore,
    loadMore,
    refresh,
    clearFilters,
  };
}
