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
      const availableAgents = await getAvailableAgents();
      setAgents(availableAgents);

      // Si no hay agente seleccionado, seleccionar el primero
      if (!selectedAgentId && availableAgents.length > 0) {
        onAgentSelect(availableAgents[0].id);
      }
    } catch (err) {
      console.error('Error loading agents:', err);
      setError('Error al cargar la lista de agentes');
    } finally {
      setLoading(false);
    }
  };

  const selectedAgent = agents.find(a => a.id === selectedAgentId);

  const getEstadoBadgeClass = (estado: AgentInfo['estado']) => {
    const baseClasses = 'px-2 py-1 text-xs font-medium rounded';
    switch (estado) {
      case 'disponible':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'ocupado':
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      case 'inactivo':
        return `${baseClasses} bg-gray-100 text-gray-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="text-center text-gray-600">Cargando agentes...</div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center text-red-600">{error}</div>
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
          Elige el agente que deseas probar en modo testing.
        </p>
      </div>

      {/* Lista de agentes */}
      <div className="space-y-3">
        {agents.map((agent) => (
          <button
            key={agent.id}
            onClick={() => !disabled && onAgentSelect(agent.id)}
            disabled={disabled}
            className={`
              w-full text-left p-4 rounded-lg border-2 transition-all
              ${selectedAgentId === agent.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 bg-white hover:border-blue-300'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900 mb-1">
                  {agent.nombre}
                </h4>
                <p className="text-sm text-gray-600">
                  {agent.descripcion}
                </p>
              </div>
              <span className={getEstadoBadgeClass(agent.estado)}>
                {agent.estado}
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className="font-mono bg-gray-100 px-2 py-1 rounded">
                {agent.tipo}
              </span>
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
                Agente seleccionado: {selectedAgent.nombre}
              </p>
              <p className="text-xs text-blue-700">
                Este agente será ejecutado con el expediente y permisos que configures a continuación.
              </p>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};
