import { MCPServersStatus } from '../../types/metrics';

interface SystemHealthStatusProps {
  mcpServers: MCPServersStatus;
  mcpToolsAvailable: number;
  externalServices: {
    [key: string]: 'connected' | 'disconnected';
  };
}

interface StatusBadgeProps {
  status: 'active' | 'inactive' | 'connected' | 'disconnected';
  label?: string;
}

/**
 * Badge para mostrar el estado de un servicio
 */
const StatusBadge = ({ status, label }: StatusBadgeProps) => {
  const isActive = status === 'active' || status === 'connected';
  const displayLabel = label || (isActive ? 'Activo' : 'Inactivo');

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
        isActive
          ? 'bg-green-100 text-green-800'
          : 'bg-red-100 text-red-800'
      }`}
    >
      <span
        className={`w-2 h-2 rounded-full mr-1.5 ${
          isActive ? 'bg-green-500' : 'bg-red-500'
        }`}
      />
      {displayLabel}
    </span>
  );
};

/**
 * Componente para mostrar el estado de salud del sistema
 */
export const SystemHealthStatus = ({
  mcpServers,
  mcpToolsAvailable,
  externalServices,
}: SystemHealthStatusProps) => {
  const activeServers = Object.values(mcpServers).filter(
    (status) => status === 'active'
  ).length;
  const totalServers = Object.keys(mcpServers).length;

  const connectedServices = Object.values(externalServices).filter(
    (status) => status === 'connected'
  ).length;
  const totalServices = Object.keys(externalServices).length;

  const systemHealthPercentage = Math.round(
    ((activeServers + connectedServices) / (totalServers + totalServices)) * 100
  );

  return (
    <div className="space-y-6">
      {/* Resumen general */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Estado del Sistema</h3>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-600 mb-1">Salud General</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    systemHealthPercentage >= 80
                      ? 'bg-green-500'
                      : systemHealthPercentage >= 50
                      ? 'bg-orange-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${systemHealthPercentage}%` }}
                />
              </div>
              <span className="text-sm font-semibold text-gray-900">
                {systemHealthPercentage}%
              </span>
            </div>
          </div>

          <div>
            <p className="text-sm text-gray-600 mb-1">Servidores MCP</p>
            <p className="text-2xl font-bold text-gray-900">
              {activeServers}/{totalServers}
            </p>
          </div>

          <div>
            <p className="text-sm text-gray-600 mb-1">Herramientas Disponibles</p>
            <p className="text-2xl font-bold text-gray-900">{mcpToolsAvailable}</p>
          </div>
        </div>
      </div>

      {/* Servidores MCP */}
      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-md font-semibold text-gray-900 mb-4">Servidores MCP</h4>
        <div className="space-y-3">
          {Object.entries(mcpServers).map(([name, status]) => (
            <div key={name} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
              <span className="text-sm font-medium text-gray-700 capitalize">{name}</span>
              <StatusBadge status={status} />
            </div>
          ))}
        </div>
      </div>

      {/* Servicios Externos */}
      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-md font-semibold text-gray-900 mb-4">Servicios Externos</h4>
        <div className="space-y-3">
          {Object.entries(externalServices).map(([name, status]) => (
            <div key={name} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
              <span className="text-sm font-medium text-gray-700">{name}</span>
              <StatusBadge
                status={status}
                label={status === 'connected' ? 'Conectado' : 'Desconectado'}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

/**
 * Versión compacta para mostrar en el dashboard principal
 */
export const SystemHealthStatusCompact = ({
  mcpServers,
  externalServices,
}: Omit<SystemHealthStatusProps, 'mcpToolsAvailable'>) => {
  const activeServers = Object.values(mcpServers).filter(
    (status) => status === 'active'
  ).length;
  const totalServers = Object.keys(mcpServers).length;

  const connectedServices = Object.values(externalServices).filter(
    (status) => status === 'connected'
  ).length;
  const totalServices = Object.keys(externalServices).length;

  const allHealthy = activeServers === totalServers && connectedServices === totalServices;

  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-2">
        <span
          className={`w-3 h-3 rounded-full ${
            allHealthy ? 'bg-green-500' : 'bg-orange-500'
          }`}
        />
        <span className="text-sm font-medium text-gray-700">
          {allHealthy ? 'Todo operativo' : 'Servicios degradados'}
        </span>
      </div>

      <div className="text-xs text-gray-600">
        MCP: {activeServers}/{totalServers} | Externos: {connectedServices}/{totalServices}
      </div>
    </div>
  );
};
