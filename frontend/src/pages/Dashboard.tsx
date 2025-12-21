import React from 'react';
import { Card } from '@/components/ui/Card';

export const Dashboard: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Métricas del Sistema
          </h2>
          <p className="text-gray-600">
            Visualización de métricas y KPIs en tiempo real.
          </p>
          <p className="mt-4 text-sm text-gray-500">
            Disponible en Fase 2
          </p>
        </Card>

        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Estado de Agentes
          </h2>
          <p className="text-gray-600">
            Información sobre ejecuciones de agentes.
          </p>
          <p className="mt-4 text-sm text-gray-500">
            Disponible en Fase 2
          </p>
        </Card>

        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Servidores MCP
          </h2>
          <p className="text-gray-600">
            Estado de los servidores MCP disponibles.
          </p>
          <p className="mt-4 text-sm text-gray-500">
            Disponible en Fase 2
          </p>
        </Card>
      </div>
    </div>
  );
};
