// components/mcp/expedientes/ExpedientesPanel.tsx
// Panel de pruebas para el módulo de Expedientes

import React, { useState, useCallback } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { EXPEDIENTES_PRUEBA } from '../MCPTokenGenerator';
import {
  callTool,
  readResource,
  parseToolContent,
  parseResourceContent
} from '@/services/mcpService';

interface ExpedientesPanelProps {
  token: string | null;
}

interface PanelResult {
  id: string;
  title: string;
  status: 'loading' | 'success' | 'error';
  data?: unknown;
  error?: string;
}

export const ExpedientesPanel: React.FC<ExpedientesPanelProps> = ({ token }) => {
  const [expedienteId, setExpedienteId] = useState<string>(EXPEDIENTES_PRUEBA[0].id);
  const [results, setResults] = useState<PanelResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const addResult = useCallback((result: PanelResult) => {
    setResults(prev => [...prev, result]);
  }, []);

  const updateResult = useCallback((id: string, update: Partial<PanelResult>) => {
    setResults(prev => prev.map(r => r.id === id ? { ...r, ...update } : r));
  }, []);

  const clearResults = useCallback(() => {
    setResults([]);
  }, []);

  const runTest = async (
    id: string,
    title: string,
    action: () => Promise<unknown>
  ) => {
    addResult({ id, title, status: 'loading' });
    try {
      const data = await action();
      updateResult(id, { status: 'success', data });
    } catch (err) {
      const error = err instanceof Error ? err.message : 'Error desconocido';
      updateResult(id, { status: 'error', error });
    }
  };

  const handleConsultarExpediente = async () => {
    if (!token) return;
    clearResults();
    setIsRunning(true);

    await runTest('consultar', 'Consultar Expediente', async () => {
      const result = await callTool(token, 'consultar_expediente', { expediente_id: expedienteId });
      return parseToolContent(result);
    });

    setIsRunning(false);
  };

  const handleListarDocumentos = async () => {
    if (!token) return;
    clearResults();
    setIsRunning(true);

    await runTest('listar-docs', 'Listar Documentos', async () => {
      const result = await callTool(token, 'listar_documentos', { expediente_id: expedienteId });
      return parseToolContent(result);
    });

    setIsRunning(false);
  };

  const handleVerHistorial = async () => {
    if (!token) return;
    clearResults();
    setIsRunning(true);

    await runTest('historial', 'Ver Historial', async () => {
      const result = await readResource(token, `expediente://${expedienteId}/historial`);
      return parseResourceContent(result);
    });

    setIsRunning(false);
  };

  const handleRunAllTests = async () => {
    if (!token) return;
    clearResults();
    setIsRunning(true);

    const tests = [
      {
        id: 'consultar',
        title: 'Consultar Expediente',
        run: async () => {
          const result = await callTool(token, 'consultar_expediente', { expediente_id: expedienteId });
          return parseToolContent(result);
        }
      },
      {
        id: 'listar-docs',
        title: 'Listar Documentos',
        run: async () => {
          const result = await callTool(token, 'listar_documentos', { expediente_id: expedienteId });
          return parseToolContent(result);
        }
      },
      {
        id: 'historial',
        title: 'Ver Historial (Resource)',
        run: async () => {
          const result = await readResource(token, `expediente://${expedienteId}/historial`);
          return parseResourceContent(result);
        }
      },
      {
        id: 'texto-doc',
        title: 'Obtener Texto DOC-001',
        run: async () => {
          const result = await callTool(token, 'obtener_texto_documento', {
            expediente_id: expedienteId,
            documento_id: 'DOC-001'
          });
          return parseToolContent(result);
        }
      },
      {
        id: 'metadatos-doc',
        title: 'Obtener Metadatos DOC-002',
        run: async () => {
          const result = await callTool(token, 'obtener_metadatos_documento', {
            expediente_id: expedienteId,
            documento_id: 'DOC-002'
          });
          return parseToolContent(result);
        }
      },
      {
        id: 'anotacion',
        title: 'Añadir Anotación (Escritura)',
        run: async () => {
          const timestamp = new Date().toLocaleString('es-ES');
          const result = await callTool(token, 'añadir_anotacion', {
            expediente_id: expedienteId,
            texto: `[TEST] Anotación desde Dashboard - ${timestamp}`
          });
          return parseToolContent(result);
        }
      }
    ];

    for (const test of tests) {
      await runTest(test.id, test.title, test.run);
      await new Promise(resolve => setTimeout(resolve, 200));
    }

    setIsRunning(false);
  };

  const renderJsonContent = (data: unknown): React.ReactNode => (
    <pre className="bg-gray-900 text-green-400 p-3 rounded text-xs overflow-auto font-mono max-h-64">
      {JSON.stringify(data, null, 2)}
    </pre>
  );

  const selectedExp = EXPEDIENTES_PRUEBA.find(e => e.id === expedienteId);

  return (
    <div className="space-y-6">
      {/* Selector de Expediente */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Expedientes</h2>
          {!token && (
            <span className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
              Genera un token primero
            </span>
          )}
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Seleccionar Expediente
            </label>
            <select
              value={expedienteId}
              onChange={(e) => setExpedienteId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              disabled={!token || isRunning}
            >
              {EXPEDIENTES_PRUEBA.map(exp => (
                <option key={exp.id} value={exp.id}>
                  {exp.id} - {exp.label}
                </option>
              ))}
            </select>
            {selectedExp && (
              <p className="text-xs text-gray-500 mt-1">
                Tipo: <span className="font-medium">{selectedExp.tipo.replace(/_/g, ' ')}</span>
              </p>
            )}
          </div>

          {/* Acciones Rápidas */}
          <div className="grid grid-cols-3 gap-2">
            <Button
              onClick={handleConsultarExpediente}
              disabled={!token || isRunning}
              variant="secondary"
              className="text-sm"
            >
              Consultar
            </Button>
            <Button
              onClick={handleListarDocumentos}
              disabled={!token || isRunning}
              variant="secondary"
              className="text-sm"
            >
              Documentos
            </Button>
            <Button
              onClick={handleVerHistorial}
              disabled={!token || isRunning}
              variant="secondary"
              className="text-sm"
            >
              Historial
            </Button>
          </div>

          <Button
            onClick={handleRunAllTests}
            disabled={!token || isRunning}
            className="w-full"
          >
            {isRunning ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Ejecutando pruebas...
              </span>
            ) : (
              'Ejecutar Todas las Pruebas'
            )}
          </Button>
        </div>
      </Card>

      {/* Resultados */}
      {results.map(result => (
        <Card key={result.id}>
          <div className="flex items-center gap-3 mb-3">
            {result.status === 'loading' && (
              <svg className="w-5 h-5 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            )}
            {result.status === 'success' && (
              <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            )}
            {result.status === 'error' && (
              <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            )}
            <h3 className="text-md font-semibold text-gray-900">{result.title}</h3>
          </div>

          {result.status === 'loading' && (
            <div className="text-gray-500 text-sm">Cargando...</div>
          )}
          {result.status === 'success' && result.data ? renderJsonContent(result.data) : null}
          {result.status === 'error' && (
            <div className="bg-red-50 border border-red-200 rounded p-3 text-red-700 text-sm">
              {result.error}
            </div>
          )}
        </Card>
      ))}
    </div>
  );
};
