import { useRef, useEffect } from 'react';
import { LogEntry as LogEntryType } from '../../types/logs';
import { LogEntry } from './LogEntry';
import {
  ArrowPathIcon,
  ChevronDownIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline';

interface LogsViewerProps {
  logs: LogEntryType[];
  loading: boolean;
  error: Error | null;
  hasMore: boolean;
  onLoadMore: () => void;
  onRefresh: () => void;
  total: number;
  autoScroll?: boolean;
}

export function LogsViewer({
  logs,
  loading,
  error,
  hasMore,
  onLoadMore,
  onRefresh,
  total,
  autoScroll = false,
}: LogsViewerProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll cuando llegan nuevos logs (si está habilitado)
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  // Infinite scroll: detectar cuando el usuario llega al final
  useEffect(() => {
    if (!hasMore || loading) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          onLoadMore();
        }
      },
      { threshold: 0.1 }
    );

    if (bottomRef.current) {
      observer.observe(bottomRef.current);
    }

    return () => observer.disconnect();
  }, [hasMore, loading, onLoadMore]);

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="text-center">
          <ExclamationCircleIcon className="mx-auto h-12 w-12 text-red-500" />
          <h3 className="mt-2 text-lg font-semibold text-gray-900">Error al cargar logs</h3>
          <p className="mt-1 text-sm text-gray-500">{error.message}</p>
          <button
            onClick={onRefresh}
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <ArrowPathIcon className="h-5 w-5 mr-2" />
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  if (logs.length === 0 && !loading) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="text-center">
          <p className="text-gray-500">No se encontraron logs con los filtros seleccionados</p>
          <button
            onClick={onRefresh}
            className="mt-4 text-sm text-blue-600 hover:text-blue-800"
          >
            Refrescar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header con contador y botón de refresh */}
      <div className="bg-white rounded-lg shadow p-4 flex items-center justify-between">
        <div className="text-sm text-gray-600">
          Mostrando <span className="font-semibold text-gray-900">{logs.length}</span> de{' '}
          <span className="font-semibold text-gray-900">{total}</span> logs
        </div>

        <button
          onClick={onRefresh}
          disabled={loading}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <ArrowPathIcon className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refrescar
        </button>
      </div>

      {/* Lista de logs */}
      <div className="space-y-2">
        {logs.map((log) => (
          <LogEntry key={log.id} log={log} />
        ))}

        {/* Loading spinner */}
        {loading && (
          <div className="bg-white rounded-lg shadow p-8">
            <div className="flex items-center justify-center">
              <ArrowPathIcon className="h-8 w-8 text-blue-600 animate-spin" />
              <span className="ml-3 text-gray-600">Cargando logs...</span>
            </div>
          </div>
        )}

        {/* Botón "Cargar más" */}
        {hasMore && !loading && (
          <div ref={bottomRef} className="bg-white rounded-lg shadow p-4">
            <button
              onClick={onLoadMore}
              className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <ChevronDownIcon className="h-5 w-5 mr-2" />
              Cargar más logs
            </button>
          </div>
        )}

        {/* Marcador de final */}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
}
