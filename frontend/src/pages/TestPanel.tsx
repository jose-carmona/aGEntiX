import React from 'react';
import { Card } from '@/components/ui/Card';

export const TestPanel: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">
        Panel de Pruebas de Agentes
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Ejecución Manual
          </h2>
          <p className="text-gray-600">
            Ejecuta agentes manualmente con parámetros personalizados.
          </p>
          <p className="mt-4 text-sm text-gray-500">
            Disponible en Fase 4
          </p>
        </Card>

        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Generador de JWT
          </h2>
          <p className="text-gray-600">
            Genera tokens JWT de prueba para testing de agentes.
          </p>
          <p className="mt-4 text-sm text-gray-500">
            Disponible en Fase 4
          </p>
        </Card>
      </div>

      <Card className="mt-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          Historial de Ejecuciones
        </h2>
        <p className="text-gray-600">
          Últimas ejecuciones de agentes con sus resultados.
        </p>
        <p className="mt-4 text-sm text-gray-500">
          Disponible en Fase 4
        </p>
      </Card>
    </div>
  );
};
