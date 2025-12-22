import { useState } from 'react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { LogEntry as LogEntryType, LogLevel } from '../../types/logs';
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

interface LogEntryProps {
  log: LogEntryType;
}

// Colores por nivel de log
const LEVEL_COLORS: Record<LogLevel, { bg: string; text: string; border: string }> = {
  INFO: {
    bg: 'bg-blue-50',
    text: 'text-blue-700',
    border: 'border-blue-200',
  },
  WARNING: {
    bg: 'bg-yellow-50',
    text: 'text-yellow-700',
    border: 'border-yellow-200',
  },
  ERROR: {
    bg: 'bg-red-50',
    text: 'text-red-700',
    border: 'border-red-200',
  },
  CRITICAL: {
    bg: 'bg-red-100',
    text: 'text-red-900',
    border: 'border-red-400',
  },
  DEBUG: {
    bg: 'bg-gray-50',
    text: 'text-gray-700',
    border: 'border-gray-200',
  },
};

/**
 * Resalta PII redactado en el texto
 */
function highlightPII(text: string): React.ReactNode {
  // Regex para detectar patrones de PII redactado
  const piiPattern = /\[(DNI|NIE|EMAIL|TELEFONO_MOVIL|TELEFONO_FIJO|IBAN|TARJETA|CCC)-REDACTED\]/g;

  const parts = text.split(piiPattern);
  const elements: React.ReactNode[] = [];

  for (let i = 0; i < parts.length; i++) {
    if (
      i % 2 === 1 &&
      [
        'DNI',
        'NIE',
        'EMAIL',
        'TELEFONO_MOVIL',
        'TELEFONO_FIJO',
        'IBAN',
        'TARJETA',
        'CCC',
      ].includes(parts[i])
    ) {
      // Es un tipo de PII
      elements.push(
        <span
          key={i}
          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800"
        >
          [{parts[i]}-REDACTED]
        </span>
      );
    } else {
      // Texto normal
      elements.push(<span key={i}>{parts[i]}</span>);
    }
  }

  return <>{elements}</>;
}

export function LogEntry({ log }: LogEntryProps) {
  const [expanded, setExpanded] = useState(false);

  const colors = LEVEL_COLORS[log.level];
  const hasDetails = log.context || log.error || log.duration_ms;

  return (
    <div className={`border-l-4 ${colors.border} ${colors.bg} p-4 mb-2 rounded-r`}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Primera línea: timestamp, nivel, componente */}
          <div className="flex items-center gap-3 mb-1">
            <span className="text-xs text-gray-500 font-mono">
              {format(new Date(log.timestamp), 'dd/MM/yyyy HH:mm:ss.SSS', { locale: es })}
            </span>

            <span
              className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${colors.text}`}
            >
              {log.level}
            </span>

            <span className="text-xs font-medium text-gray-700">{log.component}</span>

            {log.agent && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">
                {log.agent}
              </span>
            )}

            {log.expediente_id && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
                {log.expediente_id}
              </span>
            )}
          </div>

          {/* Segunda línea: mensaje */}
          <p className="text-sm text-gray-900">{highlightPII(log.message)}</p>

          {/* Metadata adicional */}
          {(log.agent_run_id || log.duration_ms) && (
            <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
              {log.agent_run_id && <span>Run ID: {log.agent_run_id}</span>}
              {log.duration_ms && <span>Duración: {log.duration_ms}ms</span>}
            </div>
          )}
        </div>

        {/* Botón expandir/colapsar */}
        {hasDetails && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="ml-4 p-1 hover:bg-gray-200 rounded transition-colors"
            aria-label={expanded ? 'Colapsar detalles' : 'Expandir detalles'}
          >
            {expanded ? (
              <ChevronDownIcon className="h-5 w-5 text-gray-500" />
            ) : (
              <ChevronRightIcon className="h-5 w-5 text-gray-500" />
            )}
          </button>
        )}
      </div>

      {/* Detalles expandidos */}
      {expanded && hasDetails && (
        <div className="mt-3 pt-3 border-t border-gray-300">
          {/* Error details */}
          {log.error && (
            <div className="mb-3">
              <h4 className="text-xs font-semibold text-gray-700 mb-1">Error:</h4>
              <div className="bg-white rounded p-2 border border-gray-200">
                <p className="text-xs font-mono text-red-700">
                  <strong>{log.error.type}:</strong> {log.error.message}
                </p>
                {log.error.stacktrace && (
                  <pre className="mt-2 text-xs font-mono text-gray-600 whitespace-pre-wrap">
                    {log.error.stacktrace}
                  </pre>
                )}
              </div>
            </div>
          )}

          {/* Context */}
          {log.context && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 mb-1">Contexto:</h4>
              <pre className="bg-white rounded p-2 border border-gray-200 text-xs font-mono text-gray-700 overflow-x-auto">
                {JSON.stringify(log.context, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
