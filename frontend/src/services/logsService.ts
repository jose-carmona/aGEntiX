import { api } from './api';
import { LogEntry, LogFilters, LogsResponse, ExportOptions } from '../types/logs';
import { mockLogs, largeMockDataset } from '../mocks/logs.mock';

// Flag para cambiar entre mock y API real
const USE_MOCK_DATA = true;

/**
 * Filtra logs según los criterios especificados
 */
function filterLogs(logs: LogEntry[], filters: LogFilters): LogEntry[] {
  let filtered = [...logs];

  // Filtro por nivel
  if (filters.level && filters.level.length > 0) {
    filtered = filtered.filter((log) => filters.level!.includes(log.level));
  }

  // Filtro por componente
  if (filters.component && filters.component.length > 0) {
    filtered = filtered.filter((log) => filters.component!.includes(log.component));
  }

  // Filtro por agente
  if (filters.agent && filters.agent.length > 0) {
    filtered = filtered.filter((log) => log.agent && filters.agent!.includes(log.agent));
  }

  // Filtro por expediente_id
  if (filters.expediente_id) {
    filtered = filtered.filter(
      (log) =>
        log.expediente_id &&
        log.expediente_id.toLowerCase().includes(filters.expediente_id!.toLowerCase())
    );
  }

  // Filtro por rango de fechas
  if (filters.dateFrom) {
    filtered = filtered.filter((log) => new Date(log.timestamp) >= filters.dateFrom!);
  }

  if (filters.dateTo) {
    filtered = filtered.filter((log) => new Date(log.timestamp) <= filters.dateTo!);
  }

  // Búsqueda de texto completo
  if (filters.searchText && filters.searchText.trim() !== '') {
    const searchLower = filters.searchText.toLowerCase();
    filtered = filtered.filter((log) => {
      // Buscar en mensaje
      if (log.message.toLowerCase().includes(searchLower)) return true;

      // Buscar en contexto (JSON stringified)
      if (log.context && JSON.stringify(log.context).toLowerCase().includes(searchLower))
        return true;

      // Buscar en error
      if (
        log.error &&
        (log.error.message.toLowerCase().includes(searchLower) ||
          log.error.type.toLowerCase().includes(searchLower))
      )
        return true;

      return false;
    });
  }

  return filtered;
}

/**
 * Obtiene logs con filtros y paginación
 */
export async function getLogs(
  filters: LogFilters = {},
  page: number = 1,
  pageSize: number = 50
): Promise<LogsResponse> {
  if (USE_MOCK_DATA) {
    // Simular delay de red
    await new Promise((resolve) => setTimeout(resolve, 300));

    // Usar dataset grande para simular muchos logs
    const allLogs = largeMockDataset;
    const filtered = filterLogs(allLogs, filters);

    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedLogs = filtered.slice(startIndex, endIndex);

    return {
      logs: paginatedLogs,
      total: filtered.length,
      page,
      page_size: pageSize,
      has_more: endIndex < filtered.length,
    };
  }

  // Llamada real a la API (cuando esté implementada)
  const response = await api.get<LogsResponse>('/api/v1/logs', {
    params: {
      ...filters,
      page,
      page_size: pageSize,
      // Convertir arrays a strings separados por comas
      level: filters.level?.join(','),
      component: filters.component?.join(','),
      agent: filters.agent?.join(','),
      // Convertir fechas a ISO strings
      date_from: filters.dateFrom?.toISOString(),
      date_to: filters.dateTo?.toISOString(),
      search: filters.searchText,
    },
  });

  return response.data;
}

/**
 * Exporta logs en el formato especificado
 */
export function exportLogs(logs: LogEntry[], options: ExportOptions): void {
  let content: string;
  let filename: string;
  let mimeType: string;

  switch (options.format) {
    case 'json':
      content = JSON.stringify(logs, null, 2);
      filename = `logs-${new Date().toISOString()}.json`;
      mimeType = 'application/json';
      break;

    case 'jsonl':
      content = logs.map((log) => JSON.stringify(log)).join('\n');
      filename = `logs-${new Date().toISOString()}.jsonl`;
      mimeType = 'application/x-ndjson';
      break;

    case 'csv':
      // CSV headers
      const headers = [
        'timestamp',
        'level',
        'component',
        'agent',
        'expediente_id',
        'message',
        'duration_ms',
        'error_type',
        'error_message',
      ];

      // CSV rows
      const rows = logs.map((log) => [
        log.timestamp,
        log.level,
        log.component,
        log.agent || '',
        log.expediente_id || '',
        `"${log.message.replace(/"/g, '""')}"`, // Escapar comillas
        log.duration_ms || '',
        log.error?.type || '',
        log.error?.message ? `"${log.error.message.replace(/"/g, '""')}"` : '',
      ]);

      content = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
      filename = `logs-${new Date().toISOString()}.csv`;
      mimeType = 'text/csv';
      break;

    default:
      throw new Error(`Formato de exportación no soportado: ${options.format}`);
  }

  // Crear blob y descargar
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Conecta a streaming de logs via Server-Sent Events
 */
export function connectToLogStream(
  onLog: (log: LogEntry) => void,
  onError?: (error: Error) => void
): () => void {
  if (USE_MOCK_DATA) {
    // Simular streaming con interval
    const interval = setInterval(() => {
      // Generar log aleatorio cada 2-5 segundos
      const randomDelay = 2000 + Math.random() * 3000;

      setTimeout(() => {
        const mockLog = mockLogs[Math.floor(Math.random() * mockLogs.length)];
        const newLog: LogEntry = {
          ...mockLog,
          id: `log-stream-${Date.now()}`,
          timestamp: new Date().toISOString(),
        };
        onLog(newLog);
      }, randomDelay);
    }, 100);

    // Retornar función de cleanup
    return () => clearInterval(interval);
  }

  // Conexión real a SSE (cuando esté implementada)
  const eventSource = new EventSource(
    `${import.meta.env.VITE_API_URL}/api/v1/logs/stream`,
    {
      withCredentials: false,
    }
  );

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'log' && data.data) {
        onLog(data.data);
      }
    } catch (error) {
      console.error('Error parsing SSE message:', error);
      onError?.(error as Error);
    }
  };

  eventSource.onerror = (error) => {
    console.error('SSE connection error:', error);
    onError?.(new Error('SSE connection failed'));
  };

  // Retornar función de cleanup
  return () => {
    eventSource.close();
  };
}
