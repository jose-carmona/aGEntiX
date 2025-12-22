// components/test-panel/ExecutionHistory.tsx

import React from 'react';
import type { ExecutionHistoryItem } from '../../types/agent';
import { Card } from '../ui/Card';

interface ExecutionHistoryProps {
  history: ExecutionHistoryItem[];
  onSelectExecution?: (executionId: string) => void;
}

export const ExecutionHistory: React.FC<ExecutionHistoryProps> = ({
  history,
  onSelectExecution
}) => {
  const getStatusBadgeClass = (status: ExecutionHistoryItem['status']) => {
    const baseClasses = 'px-2 py-0.5 text-xs font-medium rounded';
    switch (status) {
      case 'pending':
        return `${baseClasses} bg-gray-100 text-gray-700`;
      case 'running':
        return `${baseClasses} bg-blue-100 text-blue-700`;
      case 'completed':
        return `${baseClasses} bg-green-100 text-green-700`;
      case 'failed':
        return `${baseClasses} bg-red-100 text-red-700`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-700`;
    }
  };

  const getStatusIcon = (status: ExecutionHistoryItem['status']) => {
    switch (status) {
      case 'completed':
        return '✓';
      case 'failed':
        return '✗';
      case 'running':
        return '⟳';
      case 'pending':
        return '○';
      default:
        return '○';
    }
  };

  const formatElapsedTime = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  };

  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Hace un momento';
    if (diffMins < 60) return `Hace ${diffMins}min`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `Hace ${diffHours}h`;

    const diffDays = Math.floor(diffHours / 24);
    return `Hace ${diffDays}d`;
  };

  if (history.length === 0) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Historial de Ejecuciones
        </h3>
        <div className="text-center text-gray-500 py-8">
          <svg className="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm">No hay ejecuciones recientes</p>
          <p className="text-xs mt-1">Las ejecuciones aparecerán aquí</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          Historial de Ejecuciones
        </h3>
        <span className="text-xs text-gray-500">
          {history.length} ejecución{history.length !== 1 ? 'es' : ''}
        </span>
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {history.map((item) => (
          <div
            key={item.id}
            onClick={() => onSelectExecution?.(item.id)}
            className={`
              p-3 rounded-lg border transition-colors
              ${onSelectExecution ? 'cursor-pointer hover:bg-gray-50' : ''}
              ${item.status === 'running' ? 'border-blue-200 bg-blue-50' : 'border-gray-200 bg-white'}
            `}
          >
            <div className="flex items-start gap-3">
              {/* Icono de estado */}
              <div className="flex-shrink-0 mt-0.5">
                <span className={getStatusBadgeClass(item.status)}>
                  {getStatusIcon(item.status)}
                </span>
              </div>

              {/* Información */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-sm text-gray-900 truncate">
                    {item.agent_type}
                  </span>
                  {item.status === 'running' && (
                    <span className="flex items-center gap-1 text-xs text-blue-600">
                      <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      En progreso
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <span className="font-mono">{item.expediente_id}</span>
                  <span>•</span>
                  <span>{formatRelativeTime(item.started_at)}</span>
                  {item.completed_at && (
                    <>
                      <span>•</span>
                      <span>{formatElapsedTime(item.elapsed_seconds)}</span>
                    </>
                  )}
                </div>

                {/* Success indicator */}
                {item.success !== undefined && (
                  <div className="mt-1">
                    {item.success ? (
                      <span className="text-xs text-green-600 font-medium">
                        ✓ Exitoso
                      </span>
                    ) : (
                      <span className="text-xs text-red-600 font-medium">
                        ✗ Fallido
                      </span>
                    )}
                  </div>
                )}

                {/* Agent Run ID (colapsado por defecto) */}
                <details className="mt-2">
                  <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                    Ver ID de ejecución
                  </summary>
                  <div className="mt-1 font-mono text-xs text-gray-600 break-all">
                    {item.agent_run_id}
                  </div>
                </details>
              </div>
            </div>
          </div>
        ))}
      </div>

      {history.length >= 10 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500 text-center">
            Mostrando las últimas 10 ejecuciones
          </p>
        </div>
      )}
    </Card>
  );
};
