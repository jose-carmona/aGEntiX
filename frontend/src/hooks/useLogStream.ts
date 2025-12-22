import { useState, useEffect, useCallback, useRef } from 'react';
import { LogEntry } from '../types/logs';
import { connectToLogStream } from '../services/logsService';

interface UseLogStreamOptions {
  enabled?: boolean; // Si está habilitado el streaming
  maxBufferSize?: number; // Máximo número de logs en buffer
  onNewLog?: (log: LogEntry) => void; // Callback cuando llega un nuevo log
}

interface UseLogStreamReturn {
  streamLogs: LogEntry[];
  isConnected: boolean;
  error: Error | null;
  clearStream: () => void;
  toggleStream: () => void;
}

/**
 * Hook para gestionar streaming de logs en tiempo real via SSE
 */
export function useLogStream(options: UseLogStreamOptions = {}): UseLogStreamReturn {
  const { enabled = false, maxBufferSize = 100, onNewLog } = options;

  const [streamLogs, setStreamLogs] = useState<LogEntry[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [streamEnabled, setStreamEnabled] = useState(enabled);

  // Ref para la función de cleanup
  const cleanupRef = useRef<(() => void) | null>(null);

  // Función para limpiar el buffer de logs
  const clearStream = useCallback(() => {
    setStreamLogs([]);
  }, []);

  // Función para toggle del streaming
  const toggleStream = useCallback(() => {
    setStreamEnabled((prev) => !prev);
  }, []);

  // Efecto: conectar/desconectar streaming
  useEffect(() => {
    if (!streamEnabled) {
      // Desconectar si está deshabilitado
      if (cleanupRef.current) {
        cleanupRef.current();
        cleanupRef.current = null;
        setIsConnected(false);
      }
      return;
    }

    // Conectar al stream
    setIsConnected(true);
    setError(null);

    const cleanup = connectToLogStream(
      // onLog callback
      (newLog: LogEntry) => {
        setStreamLogs((prev) => {
          // Añadir nuevo log al principio (más reciente primero)
          const updated = [newLog, ...prev];

          // Limitar tamaño del buffer
          if (updated.length > maxBufferSize) {
            return updated.slice(0, maxBufferSize);
          }

          return updated;
        });

        // Llamar callback externo si existe
        onNewLog?.(newLog);
      },
      // onError callback
      (err: Error) => {
        setError(err);
        setIsConnected(false);
      }
    );

    cleanupRef.current = cleanup;

    // Cleanup al desmontar o cuando cambia streamEnabled
    return () => {
      if (cleanupRef.current) {
        cleanupRef.current();
        cleanupRef.current = null;
      }
      setIsConnected(false);
    };
  }, [streamEnabled, maxBufferSize, onNewLog]);

  return {
    streamLogs,
    isConnected,
    error,
    clearStream,
    toggleStream,
  };
}
