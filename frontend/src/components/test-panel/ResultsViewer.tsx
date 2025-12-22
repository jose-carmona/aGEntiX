// components/test-panel/ResultsViewer.tsx

import React, { useState } from 'react';
import type { AgentExecution } from '../../types/agent';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

interface ResultsViewerProps {
  execution: AgentExecution | null;
  isExecuting: boolean;
  error: string | null;
  onReset: () => void;
}

export const ResultsViewer: React.FC<ResultsViewerProps> = ({
  execution,
  isExecuting,
  error,
  onReset
}) => {
  const [showFullResult, setShowFullResult] = useState(false);
  const [showFullError, setShowFullError] = useState(false);

  const getStatusBadgeClass = (status: AgentExecution['status']) => {
    const baseClasses = 'px-3 py-1 text-sm font-medium rounded-full';
    switch (status) {
      case 'pending':
        return `${baseClasses} bg-gray-100 text-gray-800`;
      case 'running':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      case 'completed':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'failed':
        return `${baseClasses} bg-red-100 text-red-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  const getStatusIcon = (status: AgentExecution['status']) => {
    switch (status) {
      case 'pending':
        return (
          <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'running':
        return (
          <svg className="w-5 h-5 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        );
      case 'completed':
        return (
          <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'failed':
        return (
          <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const getStatusText = (status: AgentExecution['status']) => {
    switch (status) {
      case 'pending':
        return 'Pendiente';
      case 'running':
        return 'En ejecución';
      case 'completed':
        return 'Completado';
      case 'failed':
        return 'Fallido';
      default:
        return status;
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      console.error('Error copying to clipboard:', err);
    }
  };

  if (!execution && !error && !isExecuting) {
    return (
      <Card className="p-6">
        <div className="text-center text-gray-500">
          <svg className="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p className="text-sm">No hay resultados para mostrar</p>
          <p className="text-xs mt-1">Ejecuta un agente para ver los resultados aquí</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          Resultados de Ejecución
        </h3>
        {execution && !isExecuting && (
          <Button onClick={onReset} variant="secondary" size="sm">
            Nueva Ejecución
          </Button>
        )}
      </div>

      {/* Error de ejecución */}
      {error && !execution && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800 mb-1">Error</p>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Estado de ejecución */}
      {execution && (
        <div className="space-y-4">
          {/* Header con estado */}
          <div className="flex items-center gap-3 pb-4 border-b border-gray-200">
            {getStatusIcon(execution.status)}
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className={getStatusBadgeClass(execution.status)}>
                  {getStatusText(execution.status)}
                </span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900">
                {execution.elapsed_seconds.toFixed(2)}s
              </p>
              <p className="text-xs text-gray-500">Tiempo transcurrido</p>
            </div>
          </div>

          {/* Información de la ejecución */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-600 mb-1">Agent Run ID:</p>
              <p className="font-mono text-xs text-gray-900 break-all">{execution.agent_run_id}</p>
            </div>
            <div>
              <p className="text-gray-600 mb-1">Expediente ID:</p>
              <p className="font-mono text-gray-900">{execution.expediente_id}</p>
            </div>
            <div>
              <p className="text-gray-600 mb-1">Tarea ID:</p>
              <p className="font-mono text-gray-900">{execution.tarea_id}</p>
            </div>
            <div>
              <p className="text-gray-600 mb-1">Iniciado:</p>
              <p className="text-gray-900">{new Date(execution.started_at).toLocaleString('es-ES')}</p>
            </div>
            {execution.completed_at && (
              <div>
                <p className="text-gray-600 mb-1">Completado:</p>
                <p className="text-gray-900">{new Date(execution.completed_at).toLocaleString('es-ES')}</p>
              </div>
            )}
            {execution.success !== undefined && (
              <div>
                <p className="text-gray-600 mb-1">Éxito:</p>
                <p className={execution.success ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                  {execution.success ? 'Sí' : 'No'}
                </p>
              </div>
            )}
          </div>

          {/* Barra de progreso para ejecuciones en curso */}
          {execution.status === 'running' && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center gap-3 mb-2">
                <svg className="w-5 h-5 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <p className="text-sm font-medium text-blue-900">
                  El agente está procesando la solicitud...
                </p>
              </div>
              <div className="w-full bg-blue-200 rounded-full h-2 overflow-hidden">
                <div className="h-full bg-blue-600 animate-pulse" style={{ width: '100%' }}></div>
              </div>
            </div>
          )}

          {/* Resultado exitoso */}
          {execution.status === 'completed' && execution.resultado && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium text-gray-900">Resultado:</p>
                <button
                  onClick={() => copyToClipboard(JSON.stringify(execution.resultado, null, 2))}
                  className="text-xs text-blue-600 hover:text-blue-700"
                >
                  Copiar JSON
                </button>
              </div>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 overflow-x-auto">
                <pre className="text-xs font-mono text-gray-800 whitespace-pre-wrap">
                  {showFullResult
                    ? JSON.stringify(execution.resultado, null, 2)
                    : JSON.stringify(execution.resultado, null, 2).slice(0, 500)
                  }
                </pre>
                {JSON.stringify(execution.resultado).length > 500 && (
                  <button
                    onClick={() => setShowFullResult(!showFullResult)}
                    className="text-xs text-blue-600 hover:text-blue-700 mt-2"
                  >
                    {showFullResult ? 'Ver menos' : 'Ver más...'}
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Error de ejecución */}
          {execution.status === 'failed' && execution.error && (
            <div>
              <p className="text-sm font-medium text-gray-900 mb-2">Error:</p>
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 overflow-x-auto">
                <pre className="text-xs font-mono text-red-800 whitespace-pre-wrap">
                  {showFullError
                    ? JSON.stringify(execution.error, null, 2)
                    : JSON.stringify(execution.error, null, 2).slice(0, 500)
                  }
                </pre>
                {JSON.stringify(execution.error).length > 500 && (
                  <button
                    onClick={() => setShowFullError(!showFullError)}
                    className="text-xs text-red-600 hover:text-red-700 mt-2"
                  >
                    {showFullError ? 'Ver menos' : 'Ver más...'}
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
};
