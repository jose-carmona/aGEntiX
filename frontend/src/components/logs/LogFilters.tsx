import { useState, useEffect } from 'react';
import { LogFilters as LogFiltersType, LogLevel, LogComponent, AgentType } from '../../types/logs';
import { FunnelIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface LogFiltersProps {
  filters: LogFiltersType;
  onFiltersChange: (filters: LogFiltersType) => void;
  onClearFilters: () => void;
}

const LOG_LEVELS: LogLevel[] = ['INFO', 'WARNING', 'ERROR', 'CRITICAL', 'DEBUG'];

const LOG_COMPONENTS: LogComponent[] = [
  'AgentExecutor',
  'MCPClient',
  'PIIRedactor',
  'AuditLogger',
  'JWTValidator',
  'APIServer',
  'WebhookService',
  'TaskTracker',
];

const AGENT_TYPES: AgentType[] = [
  'ValidadorDocumental',
  'AnalizadorSubvencion',
  'GeneradorInforme',
];

export function LogFilters({ filters, onFiltersChange, onClearFilters }: LogFiltersProps) {
  const [showFilters, setShowFilters] = useState(true);
  const [localExpedienteId, setLocalExpedienteId] = useState(filters.expediente_id || '');

  // Actualizar expediente_id local cuando cambian los filtros externos
  useEffect(() => {
    setLocalExpedienteId(filters.expediente_id || '');
  }, [filters.expediente_id]);

  const handleLevelToggle = (level: LogLevel) => {
    const currentLevels = filters.level || [];
    const newLevels = currentLevels.includes(level)
      ? currentLevels.filter((l) => l !== level)
      : [...currentLevels, level];

    onFiltersChange({ ...filters, level: newLevels.length > 0 ? newLevels : undefined });
  };

  const handleComponentToggle = (component: LogComponent) => {
    const currentComponents = filters.component || [];
    const newComponents = currentComponents.includes(component)
      ? currentComponents.filter((c) => c !== component)
      : [...currentComponents, component];

    onFiltersChange({
      ...filters,
      component: newComponents.length > 0 ? newComponents : undefined,
    });
  };

  const handleAgentToggle = (agent: AgentType) => {
    const currentAgents = filters.agent || [];
    const newAgents = currentAgents.includes(agent)
      ? currentAgents.filter((a) => a !== agent)
      : [...currentAgents, agent];

    onFiltersChange({ ...filters, agent: newAgents.length > 0 ? newAgents : undefined });
  };

  const handleExpedienteIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setLocalExpedienteId(value);

    // Debounce: actualizar filtro después de que el usuario deje de escribir
    const timer = setTimeout(() => {
      onFiltersChange({ ...filters, expediente_id: value || undefined });
    }, 500);

    return () => clearTimeout(timer);
  };

  const handleDateFromChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    onFiltersChange({ ...filters, dateFrom: value ? new Date(value) : undefined });
  };

  const handleDateToChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    onFiltersChange({ ...filters, dateTo: value ? new Date(value) : undefined });
  };

  const hasActiveFilters =
    (filters.level && filters.level.length > 0) ||
    (filters.component && filters.component.length > 0) ||
    (filters.agent && filters.agent.length > 0) ||
    filters.expediente_id ||
    filters.dateFrom ||
    filters.dateTo;

  return (
    <div className="bg-white rounded-lg shadow mb-6">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <FunnelIcon className="h-5 w-5 text-gray-500" />
          <h3 className="text-lg font-semibold text-gray-900">Filtros</h3>
          {hasActiveFilters && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
              Activos
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {hasActiveFilters && (
            <button
              onClick={onClearFilters}
              className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1"
            >
              <XMarkIcon className="h-4 w-4" />
              Limpiar
            </button>
          )}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            {showFilters ? 'Ocultar' : 'Mostrar'}
          </button>
        </div>
      </div>

      {/* Filtros */}
      {showFilters && (
        <div className="p-4 space-y-4">
          {/* Nivel de Log */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Nivel de Log</label>
            <div className="flex flex-wrap gap-2">
              {LOG_LEVELS.map((level) => (
                <button
                  key={level}
                  onClick={() => handleLevelToggle(level)}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    filters.level?.includes(level)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>

          {/* Componente */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Componente</label>
            <div className="flex flex-wrap gap-2">
              {LOG_COMPONENTS.map((component) => (
                <button
                  key={component}
                  onClick={() => handleComponentToggle(component)}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    filters.component?.includes(component)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {component}
                </button>
              ))}
            </div>
          </div>

          {/* Agente */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Agente</label>
            <div className="flex flex-wrap gap-2">
              {AGENT_TYPES.map((agent) => (
                <button
                  key={agent}
                  onClick={() => handleAgentToggle(agent)}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    filters.agent?.includes(agent)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {agent}
                </button>
              ))}
            </div>
          </div>

          {/* Expediente ID */}
          <div>
            <label htmlFor="expediente-id" className="block text-sm font-medium text-gray-700 mb-2">
              Expediente ID
            </label>
            <input
              id="expediente-id"
              type="text"
              value={localExpedienteId}
              onChange={handleExpedienteIdChange}
              placeholder="EXP-2024-001"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Rango de Fechas */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="date-from" className="block text-sm font-medium text-gray-700 mb-2">
                Desde
              </label>
              <input
                id="date-from"
                type="datetime-local"
                value={filters.dateFrom ? filters.dateFrom.toISOString().slice(0, 16) : ''}
                onChange={handleDateFromChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label htmlFor="date-to" className="block text-sm font-medium text-gray-700 mb-2">
                Hasta
              </label>
              <input
                id="date-to"
                type="datetime-local"
                value={filters.dateTo ? filters.dateTo.toISOString().slice(0, 16) : ''}
                onChange={handleDateToChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
