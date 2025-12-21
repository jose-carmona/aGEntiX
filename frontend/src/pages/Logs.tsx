import React from 'react';
import { Card } from '@/components/ui/Card';

export const Logs: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Logs del Sistema</h1>

      <Card>
        <div className="text-center py-12">
          <p className="text-lg text-gray-600 mb-4">
            Visor de logs en tiempo real
          </p>
          <p className="text-sm text-gray-500">
            Sistema de filtrado y búsqueda de logs
          </p>
          <p className="mt-8 text-sm font-medium text-gray-500">
            Disponible en Fase 3
          </p>
        </div>
      </Card>
    </div>
  );
};
