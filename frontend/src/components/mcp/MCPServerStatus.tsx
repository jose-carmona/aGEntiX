// components/mcp/MCPServerStatus.tsx
// Panel de estado del servidor MCP (Health + Info)

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import {
  getHealth,
  getServerInfo,
  getMcpBaseUrl,
  type MCPHealthResponse,
  type MCPServerInfo
} from '@/services/mcpService';

interface MCPServerStatusProps {
  onStatusChange?: (isOnline: boolean) => void;
}

export const MCPServerStatus: React.FC<MCPServerStatusProps> = ({ onStatusChange }) => {
  const [health, setHealth] = useState<MCPHealthResponse | null>(null);
  const [serverInfo, setServerInfo] = useState<MCPServerInfo | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadServerInfo();
  }, []);

  const loadServerInfo = async () => {
    setIsLoading(true);
    setServerError(null);

    try {
      const [healthData, infoData] = await Promise.all([
        getHealth(),
        getServerInfo()
      ]);
      setHealth(healthData);
      setServerInfo(infoData);
      onStatusChange?.(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error conectando con el servidor MCP';
      setServerError(message);
      onStatusChange?.(false);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Health Check */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Health Check</h2>
          <button
            onClick={loadServerInfo}
            disabled={isLoading}
            className="text-gray-400 hover:text-gray-600"
            title="Refrescar estado"
          >
            <svg className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
        ) : isLoading ? (
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

      {/* Endpoints MCP */}
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
  );
};
