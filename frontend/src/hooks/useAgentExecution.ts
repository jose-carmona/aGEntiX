// hooks/useAgentExecution.ts

import { useState, useCallback, useEffect, useRef } from 'react';
import { executeAgent, getAgentStatus } from '../services/agentService';
import type { AgentExecution, ExecuteAgentRequest } from '../types/agent';

interface UseAgentExecutionResult {
  execution: AgentExecution | null;
  isExecuting: boolean;
  error: string | null;
  execute: (request: ExecuteAgentRequest, jwt: string) => Promise<void>;
  cancel: () => void;
  reset: () => void;
}

const POLLING_INTERVAL_MS = 2000; // Poll cada 2 segundos
const MAX_POLLING_DURATION_MS = 5 * 60 * 1000; // Máximo 5 minutos de polling

/**
 * Hook para gestionar la ejecución de agentes
 *
 * Maneja el ciclo de vida completo de una ejecución:
 * 1. Ejecutar agente
 * 2. Polling del estado
 * 3. Actualización automática
 * 4. Cancelación
 *
 * @returns {UseAgentExecutionResult} Estado y funciones de control
 */
export const useAgentExecution = (): UseAgentExecutionResult => {
  const [execution, setExecution] = useState<AgentExecution | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pollingIntervalRef = useRef<number | null>(null);
  const pollingStartTimeRef = useRef<number | null>(null);
  const currentJWTRef = useRef<string | null>(null);

  /**
   * Detiene el polling de estado
   */
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    pollingStartTimeRef.current = null;
  }, []);

  /**
   * Inicia el polling de estado
   */
  const startPolling = useCallback((agentRunId: string, jwt: string) => {
    stopPolling();

    pollingStartTimeRef.current = Date.now();
    currentJWTRef.current = jwt;

    const poll = async () => {
      try {
        // Verificar timeout del polling
        const elapsed = Date.now() - (pollingStartTimeRef.current || 0);
        if (elapsed > MAX_POLLING_DURATION_MS) {
          stopPolling();
          setError('Tiempo máximo de espera excedido');
          setIsExecuting(false);
          return;
        }

        // Obtener estado actual
        const status = await getAgentStatus(agentRunId, jwt);
        setExecution(status);

        // Si la ejecución terminó, detener polling
        if (status.status === 'completed' || status.status === 'failed') {
          stopPolling();
          setIsExecuting(false);
        }
      } catch (err: any) {
        console.error('Error polling agent status:', err);

        // Si es error 401, detener polling
        if (err.response?.status === 401) {
          stopPolling();
          setError('Token JWT expirado o inválido');
          setIsExecuting(false);
        }
      }
    };

    // Poll inmediato
    poll();

    // Poll periódico
    pollingIntervalRef.current = window.setInterval(poll, POLLING_INTERVAL_MS);
  }, [stopPolling]);

  /**
   * Ejecuta un agente y comienza el polling de estado
   */
  const execute = useCallback(async (request: ExecuteAgentRequest, jwt: string) => {
    try {
      setIsExecuting(true);
      setError(null);
      setExecution(null);

      // Ejecutar agente
      const response = await executeAgent(request, jwt);

      // Iniciar polling
      startPolling(response.agent_run_id, jwt);

    } catch (err: any) {
      console.error('Error executing agent:', err);

      let errorMessage = 'Error al ejecutar el agente';

      if (err.response?.status === 401) {
        errorMessage = 'Token JWT inválido o expirado';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
      setIsExecuting(false);
    }
  }, [startPolling]);

  /**
   * Cancela la ejecución actual (detiene polling)
   */
  const cancel = useCallback(() => {
    stopPolling();
    setIsExecuting(false);
    setError('Ejecución cancelada por el usuario');
  }, [stopPolling]);

  /**
   * Resetea el estado a inicial
   */
  const reset = useCallback(() => {
    stopPolling();
    setExecution(null);
    setIsExecuting(false);
    setError(null);
    currentJWTRef.current = null;
  }, [stopPolling]);

  /**
   * Cleanup: detener polling al desmontar
   */
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return {
    execution,
    isExecuting,
    error,
    execute,
    cancel,
    reset
  };
};
