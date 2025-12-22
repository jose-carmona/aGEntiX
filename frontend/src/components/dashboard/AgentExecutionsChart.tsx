import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';
import { ExecutionHistoryPoint, ExecutionsByAgent } from '../../types/metrics';
import { format, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';

interface AgentExecutionsChartProps {
  data: ExecutionHistoryPoint[];
  type?: 'line' | 'bar';
}

/**
 * Gráfico de líneas/barras para mostrar el histórico de ejecuciones
 */
export const AgentExecutionsChart = ({ data, type = 'line' }: AgentExecutionsChartProps) => {
  // Formatear datos para el gráfico
  const chartData = data.map((point) => ({
    ...point,
    time: format(parseISO(point.timestamp), 'HH:mm', { locale: es }),
    fullTime: format(parseISO(point.timestamp), 'dd/MM HH:mm', { locale: es }),
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
          <p className="text-sm font-medium text-gray-900 mb-2">{payload[0].payload.fullTime}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between gap-4">
              <span className="text-xs" style={{ color: entry.color }}>
                {entry.name}:
              </span>
              <span className="text-xs font-semibold">{entry.value}</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  if (type === 'bar') {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 12 }}
            stroke="#6b7280"
          />
          <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: '12px' }}
            iconType="rect"
          />
          <Bar dataKey="success" name="Exitosas" fill="#10b981" stackId="a" />
          <Bar dataKey="error" name="Errores" fill="#ef4444" stackId="a" />
          <Bar dataKey="in_progress" name="En Progreso" fill="#f59e0b" stackId="a" />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="time"
          tick={{ fontSize: 12 }}
          stroke="#6b7280"
        />
        <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: '12px' }}
          iconType="line"
        />
        <Line
          type="monotone"
          dataKey="total"
          name="Total"
          stroke="#1e40af"
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
        />
        <Line
          type="monotone"
          dataKey="success"
          name="Exitosas"
          stroke="#10b981"
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
        />
        <Line
          type="monotone"
          dataKey="error"
          name="Errores"
          stroke="#ef4444"
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

interface AgentTypeChartProps {
  data: ExecutionsByAgent;
}

/**
 * Gráfico de barras para mostrar ejecuciones por tipo de agente
 */
export const AgentTypeChart = ({ data }: AgentTypeChartProps) => {
  const chartData = [
    { name: 'Validador\nDocumental', value: data.ValidadorDocumental, fill: '#3b82f6' },
    { name: 'Analizador\nSubvención', value: data.AnalizadorSubvencion, fill: '#10b981' },
    { name: 'Generador\nInforme', value: data.GeneradorInforme, fill: '#f59e0b' },
  ];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
          <p className="text-sm font-medium text-gray-900">
            {payload[0].payload.name.replace('\n', ' ')}
          </p>
          <p className="text-lg font-bold" style={{ color: payload[0].fill }}>
            {payload[0].value} ejecuciones
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="name"
          tick={{ fontSize: 11 }}
          stroke="#6b7280"
          interval={0}
        />
        <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="value" name="Ejecuciones" fill="#3b82f6" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
};
