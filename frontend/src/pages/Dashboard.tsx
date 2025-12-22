import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { MetricsCard } from '../components/dashboard/MetricsCard';
import {
  AgentExecutionsChart,
  AgentTypeChart,
} from '../components/dashboard/AgentExecutionsChart';
import {
  PIIRedactionChart,
  PIIHistoryChart,
  PIILegend,
} from '../components/dashboard/PIIRedactionChart';
import { SystemHealthStatus } from '../components/dashboard/SystemHealthStatus';
import { useMetrics } from '../hooks/useMetrics';
import { downloadMetricsCSV, downloadMetricsJSON } from '../services/metricsService';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

export const Dashboard = () => {
  const { metrics, executionHistory, piiHistory, loading, error, refetch } = useMetrics({
    autoRefresh: true,
    refreshInterval: 10000, // 10 segundos
  });

  const [chartType, setChartType] = useState<'line' | 'bar'>('line');
  const [piiChartType, setPiiChartType] = useState<'donut' | 'pie'>('donut');

  const handleExportCSV = () => {
    if (metrics) {
      downloadMetricsCSV(metrics);
    }
  };

  const handleExportJSON = () => {
    if (metrics) {
      downloadMetricsJSON(metrics);
    }
  };

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-700 mx-auto mb-4" />
          <p className="text-gray-600">Cargando métricas...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-red-800 font-semibold mb-2">Error al cargar métricas</h3>
        <p className="text-red-600">{error.message}</p>
        <Button onClick={refetch} className="mt-4">
          Reintentar
        </Button>
      </div>
    );
  }

  if (!metrics) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard de Métricas</h1>
          <p className="text-gray-600 mt-1">
            Última actualización: {format(new Date(metrics.timestamp), "dd 'de' MMMM 'a las' HH:mm", { locale: es })}
          </p>
        </div>

        <div className="flex gap-2">
          <Button onClick={refetch} variant="secondary">
            Actualizar
          </Button>
          <Button onClick={handleExportCSV} variant="secondary">
            Exportar CSV
          </Button>
          <Button onClick={handleExportJSON} variant="secondary">
            Exportar JSON
          </Button>
        </div>
      </div>

      {/* KPIs Principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricsCard
          title="Total de Ejecuciones"
          value={metrics.total_executions.toLocaleString()}
          description="Desde el inicio del sistema"
          color="blue"
        />
        <MetricsCard
          title="Ejecuciones Hoy"
          value={metrics.executions_today}
          description={`${metrics.executions_week} esta semana`}
          color="green"
        />
        <MetricsCard
          title="Tasa de Éxito"
          value={`${metrics.success_rate.toFixed(1)}%`}
          description="De todas las ejecuciones"
          color="green"
        />
        <MetricsCard
          title="Tiempo Promedio"
          value={`${metrics.avg_execution_time.toFixed(1)}s`}
          description="Duración de ejecución"
          color="blue"
        />
      </div>

      {/* KPIs Secundarios */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricsCard
          title="PII Redactados"
          value={metrics.pii_redacted_total.toLocaleString()}
          description="Campos protegidos (GDPR)"
          color="orange"
        />
        <MetricsCard
          title="Servidores MCP"
          value={`${Object.values(metrics.mcp_servers_status).filter((s) => s === 'active').length}/${Object.keys(metrics.mcp_servers_status).length}`}
          description={`${metrics.mcp_tools_available} herramientas disponibles`}
          color="blue"
        />
        <MetricsCard
          title="Latencia P95"
          value={`${metrics.performance.latency_p95}ms`}
          description={`P50: ${metrics.performance.latency_p50}ms`}
          color="gray"
        />
        <MetricsCard
          title="Llamadas MCP/s"
          value={metrics.performance.mcp_calls_per_second.toFixed(1)}
          description={`Promedio: ${metrics.performance.avg_response_time}ms`}
          color="gray"
        />
      </div>

      {/* Gráficos de Ejecuciones */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Histórico de Ejecuciones (24h)
            </h2>
            <div className="flex gap-2">
              <button
                onClick={() => setChartType('line')}
                className={`px-3 py-1 text-xs rounded ${
                  chartType === 'line'
                    ? 'bg-blue-700 text-white'
                    : 'bg-gray-200 text-gray-700'
                }`}
              >
                Líneas
              </button>
              <button
                onClick={() => setChartType('bar')}
                className={`px-3 py-1 text-xs rounded ${
                  chartType === 'bar'
                    ? 'bg-blue-700 text-white'
                    : 'bg-gray-200 text-gray-700'
                }`}
              >
                Barras
              </button>
            </div>
          </div>
          <AgentExecutionsChart data={executionHistory} type={chartType} />
        </Card>

        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Ejecuciones por Tipo de Agente
          </h2>
          <AgentTypeChart data={metrics.executions_by_agent} />
        </Card>
      </div>

      {/* Gráficos de PII */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Distribución de PII Redactados
            </h2>
            <div className="flex gap-2">
              <button
                onClick={() => setPiiChartType('donut')}
                className={`px-3 py-1 text-xs rounded ${
                  piiChartType === 'donut'
                    ? 'bg-blue-700 text-white'
                    : 'bg-gray-200 text-gray-700'
                }`}
              >
                Donut
              </button>
              <button
                onClick={() => setPiiChartType('pie')}
                className={`px-3 py-1 text-xs rounded ${
                  piiChartType === 'pie'
                    ? 'bg-blue-700 text-white'
                    : 'bg-gray-200 text-gray-700'
                }`}
              >
                Circular
              </button>
            </div>
          </div>
          <PIIRedactionChart data={metrics.pii_redacted} type={piiChartType} />
          <PIILegend data={metrics.pii_redacted} />
        </Card>

        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Histórico de PII (24h)
          </h2>
          <PIIHistoryChart data={piiHistory} />
        </Card>
      </div>

      {/* Estado del Sistema */}
      <Card>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Estado del Sistema</h2>
        <SystemHealthStatus
          mcpServers={metrics.mcp_servers_status}
          mcpToolsAvailable={metrics.mcp_tools_available}
          externalServices={metrics.external_services_status}
        />
      </Card>
    </div>
  );
};
