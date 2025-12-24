// pages/TestPanel.tsx
// Paso 4: Panel de pruebas con API simplificada

import React, { useState, useEffect } from 'react';
import { AgentSelector } from '../components/test-panel/AgentSelector';
import { IntegratedExecutionForm } from '../components/test-panel/IntegratedExecutionForm';
import { ResultsViewer } from '../components/test-panel/ResultsViewer';
import { ExecutionHistory } from '../components/test-panel/ExecutionHistory';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { useAgentExecution } from '../hooks/useAgentExecution';
import type { JWTClaims, ExecutionHistoryItem, ExecuteAgentRequest } from '../types/agent';

const STORAGE_KEY_PREFIX = 'agentix_test_panel_';
const MAX_HISTORY_ITEMS = 10;

export const TestPanel: React.FC = () => {
  // Estado básico
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

  // Historial de ejecuciones
  const [executionHistory, setExecutionHistory] = useState<ExecutionHistoryItem[]>([]);

  // Hook de ejecución
  const {
    execution,
    isExecuting,
    error,
    execute,
    cancel,
    reset
  } = useAgentExecution();

  // Cargar historial al montar
  useEffect(() => {
    loadExecutionHistory();
  }, []);

  // Agregar ejecución al historial cuando completa
  useEffect(() => {
    if (execution && (execution.status === 'completed' || execution.status === 'failed')) {
      addToHistory(execution);
    }
  }, [execution?.status, execution?.agent_run_id]);

  const loadExecutionHistory = () => {
    try {
      const saved = localStorage.getItem(`${STORAGE_KEY_PREFIX}history`);
      if (saved) {
        const history = JSON.parse(saved);
        setExecutionHistory(history);
      }
    } catch (err) {
      console.error('Error loading execution history:', err);
    }
  };

  const addToHistory = (exec: any) => {
    const historyItem: ExecutionHistoryItem = {
      id: exec.agent_run_id,
      agent_run_id: exec.agent_run_id,
      agent_type: selectedAgentId || 'unknown',
      expediente_id: exec.expediente_id,
      status: exec.status,
      started_at: exec.started_at,
      completed_at: exec.completed_at,
      elapsed_seconds: exec.elapsed_seconds,
      success: exec.success
    };

    setExecutionHistory(prev => {
      // Evitar duplicados
      const filtered = prev.filter(item => item.agent_run_id !== exec.agent_run_id);
      // Agregar al inicio y limitar a MAX_HISTORY_ITEMS
      const updated = [historyItem, ...filtered].slice(0, MAX_HISTORY_ITEMS);

      // Guardar en localStorage
      try {
        localStorage.setItem(`${STORAGE_KEY_PREFIX}history`, JSON.stringify(updated));
      } catch (err) {
        console.error('Error saving execution history:', err);
      }

      return updated;
    });
  };

  /**
   * Handler de ejecución con API simplificada (Paso 4)
   */
  const handleExecute = async (
    jwtToken: string,
    _jwtClaims: JWTClaims,
    request: ExecuteAgentRequest
  ) => {
    await execute(request, jwtToken);
  };

  const handleReset = () => {
    reset();
  };

  const handleCancel = () => {
    cancel();
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Panel de Pruebas de Agentes
        </h1>
        <p className="text-gray-600">
          Ejecuta agentes con la API simplificada. Solo necesitas: agente, prompt y contexto.
        </p>
      </div>

      {/* Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Columna izquierda: Configuración */}
        <div className="lg:col-span-2 space-y-6">
          {/* Selector de agente */}
          <AgentSelector
            selectedAgentId={selectedAgentId}
            onAgentSelect={setSelectedAgentId}
            disabled={isExecuting}
          />

          {/* Formulario integrado de ejecución */}
          <ErrorBoundary>
            <IntegratedExecutionForm
              selectedAgentId={selectedAgentId}
              isExecuting={isExecuting}
              executionError={error}
              onExecute={handleExecute}
              onResetError={() => {
                if (error) {
                  reset();
                }
              }}
            />
          </ErrorBoundary>

          {/* Botón de cancelar si está ejecutando */}
          {isExecuting && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <svg className="w-5 h-5 text-yellow-600 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <div>
                    <p className="text-sm font-medium text-yellow-900">
                      Ejecución en progreso
                    </p>
                    <p className="text-xs text-yellow-700">
                      El agente está procesando la solicitud...
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleCancel}
                  className="px-4 py-2 text-sm font-medium text-yellow-900 bg-yellow-100 hover:bg-yellow-200 rounded-md transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Columna derecha: Resultados e Historial */}
        <div className="space-y-6">
          {/* Resultados */}
          <ErrorBoundary>
            <ResultsViewer
              execution={execution}
              isExecuting={isExecuting}
              error={error}
              onReset={handleReset}
            />
          </ErrorBoundary>

          {/* Historial */}
          <ErrorBoundary>
            <ExecutionHistory
              history={executionHistory}
            />
          </ErrorBoundary>
        </div>
      </div>

      {/* Información de ayuda */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="flex-1">
            <p className="text-sm font-medium text-blue-900 mb-2">
              API Simplificada (Paso 4):
            </p>
            <div className="text-sm text-blue-800 space-y-1">
              <p><strong>Request:</strong> <code className="bg-blue-100 px-1 rounded">agent</code>, <code className="bg-blue-100 px-1 rounded">prompt</code>, <code className="bg-blue-100 px-1 rounded">context</code></p>
              <p>La configuración del agente (modelo, system_prompt, tools) se carga automáticamente desde <code className="bg-blue-100 px-1 rounded">agents.yaml</code></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
