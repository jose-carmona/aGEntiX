// pages/MCPServerMock.tsx
// Página de pruebas del MCP Server Mock - Refactorizada con Tabs

import React, { useState } from 'react';
import {
  MCPServerStatus,
  MCPTokenGenerator,
  MCPTabs,
  useTokenGenerator,
  ExpedientesPanel,
  DocumentacionPanel,
  ExplorerPanel,
  type MCPTabId
} from '@/components/mcp';

export const MCPServerMock: React.FC = () => {
  const [activeTab, setActiveTab] = useState<MCPTabId>('expedientes');
  const [isServerOnline, setIsServerOnline] = useState(false);
  const { token, handleTokenGenerated, hasToken } = useTokenGenerator();

  const renderTabContent = () => {
    switch (activeTab) {
      case 'expedientes':
        return <ExpedientesPanel token={token} />;
      case 'documentacion':
        return <DocumentacionPanel token={token} />;
      case 'explorer':
        return <ExplorerPanel token={token} />;
      default:
        return null;
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          MCP Server Mock
        </h1>
        <p className="text-gray-600">
          Panel unificado para probar los módulos MCP: Expedientes y Documentación
        </p>
      </div>

      {/* Layout Grid: 3 columnas */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Columna izquierda (3/4): Tabs y contenido */}
        <div className="lg:col-span-3 space-y-6">
          {/* Generador de Token */}
          <MCPTokenGenerator
            onTokenGenerated={handleTokenGenerated}
            disabled={!isServerOnline}
          />

          {/* Tabs de navegación */}
          <MCPTabs
            activeTab={activeTab}
            onTabChange={setActiveTab}
            disabled={!hasToken}
          />

          {/* Contenido del tab activo */}
          <div className="min-h-[400px]">
            {renderTabContent()}
          </div>
        </div>

        {/* Columna derecha (1/4): Estado del servidor */}
        <div className="lg:col-span-1">
          <MCPServerStatus onStatusChange={setIsServerOnline} />
        </div>
      </div>
    </div>
  );
};
