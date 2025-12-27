// pages/MCPServerMock.tsx
// Página de pruebas del MCP Server Mock

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { generateJWT } from '@/services/agentService';
import {
  getHealth,
  getServerInfo,
  listTools,
  listResources,
  callTool,
  readResource,
  parseToolContent,
  parseResourceContent,
  getMcpBaseUrl,
  type MCPHealthResponse,
  type MCPServerInfo
} from '@/services/mcpService';

interface PanelData {
  id: string;
  title: string;
  status: 'pending' | 'loading' | 'success' | 'error';
  data?: unknown;
  error?: string;
}

export const MCPServerMock: React.FC = () => {
  // Estado del servidor
  const [health, setHealth] = useState<MCPHealthResponse | null>(null);
  const [serverInfo, setServerInfo] = useState<MCPServerInfo | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [isLoadingServer, setIsLoadingServer] = useState(true);

  // Estado del token
  const [expedienteId, setExpedienteId] = useState('EXP-2024-001');
  const [jwtClaims, setJwtClaims] = useState<Record<string, unknown> | null>(null);
  const [isGeneratingToken, setIsGeneratingToken] = useState(false);

  // Estado de los paneles de resultados
  const [panels, setPanels] = useState<PanelData[]>([]);

  // Cargar info del servidor al montar
  useEffect(() => {
    loadServerInfo();
  }, []);

  const loadServerInfo = async () => {
    setIsLoadingServer(true);
    setServerError(null);

    try {
      const [healthData, infoData] = await Promise.all([
        getHealth(),
        getServerInfo()
      ]);
      setHealth(healthData);
      setServerInfo(infoData);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error conectando con el servidor MCP';
      setServerError(message);
    } finally {
      setIsLoadingServer(false);
    }
  };

  const decodeJwtPayload = (token: string): Record<string, unknown> | null => {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch {
      return null;
    }
  };

  const handleGenerateToken = async () => {
    setIsGeneratingToken(true);
    setPanels([]);

    try {
      // Generar JWT usando el backend
      const response = await generateJWT({
        exp_id: expedienteId,
        tarea_id: 'TAREA-MCP-TEST',
        permisos: ['consulta', 'gestion'],
        mcp_servers: ['agentix-mcp-expedientes']
      });

      setJwtClaims(decodeJwtPayload(response.token));

      // Ejecutar todas las pruebas secuencialmente
      await runAllTests(response.token);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error generando token';
      setPanels([{
        id: 'token-error',
        title: 'Error generando token',
        status: 'error',
        error: message
      }]);
    } finally {
      setIsGeneratingToken(false);
    }
  };

  const runAllTests = async (token: string) => {
    const tests = [
      { id: 'tools-list', title: 'Listando Tools Disponibles', run: () => listTools(token) },
      { id: 'resources-list', title: 'Listando Resources Disponibles', run: () => listResources(token) },
      {
        id: 'consultar-expediente',
        title: 'Ejecutando Tool: consultar_expediente',
        run: async () => {
          const result = await callTool(token, 'consultar_expediente', { expediente_id: expedienteId });
          return parseToolContent(result);
        }
      },
      {
        id: 'listar-documentos',
        title: 'Ejecutando Tool: listar_documentos',
        run: async () => {
          const result = await callTool(token, 'listar_documentos', { expediente_id: expedienteId });
          return parseToolContent(result);
        }
      },
      {
        id: 'read-historial',
        title: 'Leyendo Resource: historial',
        run: async () => {
          const result = await readResource(token, `expediente://${expedienteId}/historial`);
          return parseResourceContent(result);
        }
      },
      {
        id: 'añadir-anotacion',
        title: 'Ejecutando Tool: añadir_anotacion (ESCRITURA)',
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
      // Añadir panel en estado loading
      setPanels(prev => [...prev, {
        id: test.id,
        title: test.title,
        status: 'loading'
      }]);

      try {
        const data = await test.run();
        // Actualizar panel con resultado
        setPanels(prev => prev.map(p =>
          p.id === test.id ? { ...p, status: 'success', data } : p
        ));
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error desconocido';
        setPanels(prev => prev.map(p =>
          p.id === test.id ? { ...p, status: 'error', error: message } : p
        ));
      }

      // Pequeña pausa entre tests para mejor visualización
      await new Promise(resolve => setTimeout(resolve, 300));
    }
  };

  const renderJsonContent = (data: unknown, maxHeight = '300px'): React.ReactNode => {
    if (!data) return null;

    return (
      <pre
        className="bg-gray-900 text-green-400 p-3 rounded text-xs overflow-auto font-mono"
        style={{ maxHeight }}
      >
        {JSON.stringify(data, null, 2)}
      </pre>
    );
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          MCP Server Mock
        </h1>
        <p className="text-gray-600">
          Prueba las funcionalidades del servidor MCP de Expedientes (puerto 8000)
        </p>
      </div>

      {/* Layout Grid: 2 columnas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Columna izquierda (2/3): Token y resultados */}
        <div className="lg:col-span-2 space-y-6">
          {/* Generar Token */}
          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Generar Token JWT
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Expediente ID
                </label>
                <input
                  type="text"
                  value={expedienteId}
                  onChange={(e) => setExpedienteId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="EXP-2024-001"
                  disabled={isGeneratingToken}
                />
              </div>

              <Button
                onClick={handleGenerateToken}
                disabled={isGeneratingToken || !expedienteId}
                className="w-full"
              >
                {isGeneratingToken ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Ejecutando pruebas...
                  </span>
                ) : (
                  'Generar Token y Ejecutar Pruebas'
                )}
              </Button>
            </div>

            {/* Claims del token */}
            {jwtClaims && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Claims del Token:</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-gray-500">iss:</span> {String(jwtClaims.iss)}</div>
                  <div><span className="text-gray-500">sub:</span> {String(jwtClaims.sub)}</div>
                  <div><span className="text-gray-500">exp_id:</span> {String(jwtClaims.exp_id)}</div>
                  <div><span className="text-gray-500">permisos:</span> {Array.isArray(jwtClaims.permisos) ? jwtClaims.permisos.join(', ') : ''}</div>
                </div>
              </div>
            )}
          </Card>

          {/* Paneles de resultados */}
          {panels.map(panel => (
            <Card key={panel.id}>
              <div className="flex items-center gap-3 mb-3">
                {/* Icono de estado */}
                {panel.status === 'loading' && (
                  <svg className="w-5 h-5 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                )}
                {panel.status === 'success' && (
                  <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                )}
                {panel.status === 'error' && (
                  <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}

                <h3 className="text-md font-semibold text-gray-900">{panel.title}</h3>
              </div>

              {panel.status === 'loading' && (
                <div className="text-gray-500 text-sm">Cargando...</div>
              )}

              {panel.status === 'success' && panel.data ? renderJsonContent(panel.data) : null}

              {panel.status === 'error' && (
                <div className="bg-red-50 border border-red-200 rounded p-3 text-red-700 text-sm">
                  {panel.error}
                </div>
              )}
            </Card>
          ))}
        </div>

        {/* Columna derecha (1/3): Info del servidor */}
        <div className="space-y-6">
          {/* Health Check */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Health Check</h2>
              <button
                onClick={loadServerInfo}
                disabled={isLoadingServer}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className={`w-5 h-5 ${isLoadingServer ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            </div>

            {serverError ? (
              <div className="bg-red-50 border border-red-200 rounded p-3">
                <div className="flex items-center gap-2 text-red-700">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="font-medium">Servidor no disponible</span>
                </div>
                <p className="text-sm text-red-600 mt-1">{serverError}</p>
                <p className="text-xs text-red-500 mt-2">
                  Ejecuta: <code className="bg-red-100 px-1 rounded">./run-mcp.sh</code>
                </p>
              </div>
            ) : isLoadingServer ? (
              <div className="flex items-center gap-2 text-gray-500">
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Conectando...
              </div>
            ) : health ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                  <span className="font-medium text-green-700">Online</span>
                </div>
                <div className="text-sm text-gray-600">
                  <p><span className="text-gray-500">URL:</span> {getMcpBaseUrl()}</p>
                  <p><span className="text-gray-500">Status:</span> {health.status}</p>
                </div>
              </div>
            ) : null}
          </Card>

          {/* Información del Servidor */}
          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Información del Servidor
            </h2>

            {serverInfo ? (
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-gray-500">Servicio:</span>
                  <span className="ml-2 font-medium">{serverInfo.name}</span>
                </div>
                <div>
                  <span className="text-gray-500">Versión:</span>
                  <span className="ml-2">{serverInfo.version}</span>
                </div>
                <div>
                  <span className="text-gray-500">Protocolo MCP:</span>
                  <span className="ml-2">{serverInfo.protocol_version}</span>
                </div>
                <div className="pt-2 border-t border-gray-200">
                  <span className="text-gray-500 block mb-2">Capabilities:</span>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(serverInfo.capabilities).map(([key, value]) => (
                      <span
                        key={key}
                        className={`px-2 py-1 rounded text-xs ${
                          value ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                        }`}
                      >
                        {key}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : serverError ? (
              <p className="text-gray-500 text-sm">No disponible</p>
            ) : (
              <div className="text-gray-500 text-sm">Cargando...</div>
            )}
          </Card>

          {/* Endpoints disponibles */}
          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Endpoints MCP
            </h2>
            <div className="space-y-2 text-sm font-mono">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">GET</span>
                <span>/health</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">GET</span>
                <span>/info</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">POST</span>
                <span>/rpc</span>
                <span className="text-gray-400 text-xs">(JWT)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">POST</span>
                <span>/sse</span>
                <span className="text-gray-400 text-xs">(JWT)</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
