import { useState, useEffect } from 'react';
import { useLogs } from '../hooks/useLogs';
import { useLogStream } from '../hooks/useLogStream';
import { LogFilters } from '../components/logs/LogFilters';
import { LogSearch } from '../components/logs/LogSearch';
import { LogsViewer } from '../components/logs/LogsViewer';
import { LogFilters as LogFiltersType, ExportOptions } from '../types/logs';
import { exportLogs } from '../services/logsService';
import {
  ArrowDownTrayIcon,
  SignalIcon,
  SignalSlashIcon,
} from '@heroicons/react/24/outline';

// Clave para persistencia de filtros
const FILTERS_STORAGE_KEY = 'agentix_logs_filters';

// Cargar filtros desde sessionStorage
function loadFiltersFromStorage(): LogFiltersType {
  try {
    const saved = sessionStorage.getItem(FILTERS_STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      // Convertir fechas de string a Date
      if (parsed.dateFrom) parsed.dateFrom = new Date(parsed.dateFrom);
      if (parsed.dateTo) parsed.dateTo = new Date(parsed.dateTo);
      return parsed;
    }
  } catch (error) {
    console.error('Error loading filters from storage:', error);
  }
  return {};
}

// Guardar filtros en sessionStorage
function saveFiltersToStorage(filters: LogFiltersType): void {
  try {
    sessionStorage.setItem(FILTERS_STORAGE_KEY, JSON.stringify(filters));
  } catch (error) {
    console.error('Error saving filters to storage:', error);
  }
}

export function Logs() {
  const [showExportMenu, setShowExportMenu] = useState(false);

  // Cargar filtros guardados al montar
  const initialFilters = loadFiltersFromStorage();

  // Hook de logs con auto-refresh
  const { logs, loading, error, filters, setFilters, total, hasMore, loadMore, refresh, clearFilters } =
    useLogs({
      initialFilters,
      pageSize: 50,
      autoRefresh: false, // Deshabilitado para evitar conflicto con streaming
    });

  // Hook de streaming
  const { streamLogs, isConnected, toggleStream, clearStream } = useLogStream({
    enabled: false,
    maxBufferSize: 100,
    onNewLog: (newLog) => {
      console.log('Nuevo log recibido:', newLog);
    },
  });

  // Persistir filtros cuando cambian
  useEffect(() => {
    saveFiltersToStorage(filters);
  }, [filters]);

  // Combinar logs estáticos y de streaming
  const allLogs = isConnected ? [...streamLogs, ...logs] : logs;

  const handleFiltersChange = (newFilters: LogFiltersType) => {
    setFilters(newFilters);
  };

  const handleSearchChange = (searchText: string | undefined) => {
    setFilters({ ...filters, searchText });
  };

  const handleClearFilters = () => {
    clearFilters();
    sessionStorage.removeItem(FILTERS_STORAGE_KEY);
  };

  const handleExport = (format: ExportOptions['format']) => {
    exportLogs(allLogs, { format, filters });
    setShowExportMenu(false);
  };

  const handleToggleStream = () => {
    toggleStream();
    if (isConnected) {
      clearStream();
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Logs del Sistema</h1>

          <div className="flex items-center gap-3">
            {/* Toggle Streaming */}
            <button
              onClick={handleToggleStream}
              className={`inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md ${
                isConnected
                  ? 'bg-green-50 text-green-700 border-green-300 hover:bg-green-100'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
            >
              {isConnected ? (
                <>
                  <SignalIcon className="h-5 w-5 mr-2 animate-pulse" />
                  Streaming Activo
                </>
              ) : (
                <>
                  <SignalSlashIcon className="h-5 w-5 mr-2" />
                  Activar Streaming
                </>
              )}
            </button>

            {/* Exportar */}
            <div className="relative">
              <button
                onClick={() => setShowExportMenu(!showExportMenu)}
                disabled={allLogs.length === 0}
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
                Exportar
              </button>

              {showExportMenu && (
                <div className="absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-10">
                  <div className="py-1">
                    <button
                      onClick={() => handleExport('json')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      JSON (.json)
                    </button>
                    <button
                      onClick={() => handleExport('jsonl')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      JSON Lines (.jsonl)
                    </button>
                    <button
                      onClick={() => handleExport('csv')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      CSV (.csv)
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <p className="mt-2 text-sm text-gray-600">
          Visualización y filtrado de logs del sistema con búsqueda en tiempo real
        </p>

        {isConnected && (
          <div className="mt-2 inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <span className="flex h-2 w-2 mr-2">
              <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            Recibiendo logs en tiempo real
          </div>
        )}
      </div>

      {/* Búsqueda */}
      <LogSearch searchText={filters.searchText} onSearchChange={handleSearchChange} />

      {/* Filtros */}
      <LogFilters
        filters={filters}
        onFiltersChange={handleFiltersChange}
        onClearFilters={handleClearFilters}
      />

      {/* Visor de Logs */}
      <LogsViewer
        logs={allLogs}
        loading={loading}
        error={error}
        hasMore={hasMore}
        onLoadMore={loadMore}
        onRefresh={refresh}
        total={total}
        autoScroll={isConnected}
      />
    </div>
  );
}
