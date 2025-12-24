// components/test-panel/AgentSelector.tsx

import React, { useEffect, useState } from 'react';
import { getAvailableAgents } from '../../services/agentService';
import type { AgentInfo } from '../../types/agent';
import { Card } from '../ui/Card';

interface AgentSelectorProps {
  selectedAgentId: string | null;
  onAgentSelect: (agentId: string) => void;
  disabled?: boolean;
}

export const AgentSelector: React.FC<AgentSelectorProps> = ({
  selectedAgentId,
  onAgentSelect,
  disabled = false
}) => {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setLoading(true);
      setError(null);
      const availableAgents = await getAvailableAgents();
      setAgents(availableAgents);

      // Si no hay agente seleccionado, seleccionar el primero
      if (!selectedAgentId && availableAgents.length > 0) {
        onAgentSelect(availableAgents[0].name);
      }
    } catch (err) {
      console.error('Error loading agents:', err);
      setError('Error al cargar la lista de agentes');
    } finally {
      setLoading(false);
    }
  };

  const selectedAgent = agents.find(a => a.name === selectedAgentId);

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center gap-3 text-gray-600">
          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span>Cargando agentes...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <div className="text-red-600 mb-2">{error}</div>
          <button
            onClick={loadAgents}
            className="text-sm text-blue-600 hover:text-blue-800 underline"
          >
            Reintentar
          </button>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Seleccionar Agente
        </h3>
        <p className="text-sm text-gray-600">
          Elige el agente que deseas probar. La configuración se carga desde el servidor.
        </p>
      </div>

      {/* Lista de agentes */}
      <div className="space-y-3">
        {agents.map((agent) => (
          <button
            key={agent.name}
            onClick={() => !disabled && onAgentSelect(agent.name)}
            disabled={disabled}
            className={`
              w-full text-left p-4 rounded-lg border-2 transition-all
              ${selectedAgentId === agent.name
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 bg-white hover:border-blue-300'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900 mb-1">
                  {agent.name}
                </h4>
                <p className="text-sm text-gray-600">
                  {agent.description}
                </p>
              </div>
              <span className="px-2 py-1 text-xs font-medium rounded bg-green-100 text-green-800">
                disponible
              </span>
            </div>
            {/* Permisos requeridos */}
            <div className="flex flex-wrap gap-1 mt-2">
              {agent.required_permissions.map((perm) => (
                <span
                  key={perm}
                  className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded"
                >
                  {perm}
                </span>
              ))}
            </div>
          </button>
        ))}
      </div>

      {/* Agente seleccionado - Info adicional */}
      {selectedAgent && (
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start gap-2">
            <svg
              className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-900 mb-1">
                Agente seleccionado: {selectedAgent.name}
              </p>
              <p className="text-xs text-blue-700">
                Este agente requiere los permisos: {selectedAgent.required_permissions.join(', ')}
              </p>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};
