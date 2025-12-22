import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from 'recharts';
import { PIIRedacted, PIIHistoryPoint } from '../../types/metrics';
import { format, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';

interface PIIRedactionChartProps {
  data: PIIRedacted;
  type?: 'pie' | 'donut';
}

const COLORS = {
  DNI: '#3b82f6',
  NIE: '#8b5cf6',
  email: '#10b981',
  telefono_movil: '#f59e0b',
  telefono_fijo: '#f97316',
  IBAN: '#ef4444',
  tarjeta: '#ec4899',
  CCC: '#6366f1',
};

const LABELS = {
  DNI: 'DNI',
  NIE: 'NIE',
  email: 'Email',
  telefono_movil: 'Teléfono Móvil',
  telefono_fijo: 'Teléfono Fijo',
  IBAN: 'IBAN',
  tarjeta: 'Tarjeta',
  CCC: 'CCC',
};

/**
 * Gráfico circular/donut para mostrar la distribución de PII redactados
 */
export const PIIRedactionChart = ({ data, type = 'donut' }: PIIRedactionChartProps) => {
  const chartData = Object.entries(data).map(([key, value]) => ({
    name: LABELS[key as keyof PIIRedacted],
    value,
    color: COLORS[key as keyof PIIRedacted],
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const total = chartData.reduce((sum, item) => sum + item.value, 0);
      const percentage = ((payload[0].value / total) * 100).toFixed(1);

      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
          <p className="text-sm font-medium text-gray-900">{payload[0].name}</p>
          <p className="text-lg font-bold" style={{ color: payload[0].payload.color }}>
            {payload[0].value.toLocaleString()} campos
          </p>
          <p className="text-xs text-gray-600">{percentage}% del total</p>
        </div>
      );
    }
    return null;
  };

  const renderLabel = (entry: any) => {
    const total = chartData.reduce((sum, item) => sum + item.value, 0);
    const percentage = ((entry.value / total) * 100).toFixed(0);
    return `${percentage}%`;
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={renderLabel}
          outerRadius={type === 'donut' ? 100 : 110}
          innerRadius={type === 'donut' ? 60 : 0}
          fill="#8884d8"
          dataKey="value"
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
      </PieChart>
    </ResponsiveContainer>
  );
};

interface PIIHistoryChartProps {
  data: PIIHistoryPoint[];
}

/**
 * Gráfico de barras apiladas para mostrar el histórico de PII redactados
 */
export const PIIHistoryChart = ({ data }: PIIHistoryChartProps) => {
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
        <Bar dataKey="DNI" name="DNI" fill={COLORS.DNI} stackId="a" />
        <Bar dataKey="NIE" name="NIE" fill={COLORS.NIE} stackId="a" />
        <Bar dataKey="email" name="Email" fill={COLORS.email} stackId="a" />
        <Bar dataKey="telefono" name="Teléfono" fill={COLORS.telefono_movil} stackId="a" />
        <Bar dataKey="IBAN" name="IBAN" fill={COLORS.IBAN} stackId="a" />
        <Bar dataKey="other" name="Otros" fill={COLORS.CCC} stackId="a" />
      </BarChart>
    </ResponsiveContainer>
  );
};

interface PIILegendProps {
  data: PIIRedacted;
}

/**
 * Leyenda personalizada para el gráfico de PII con valores numéricos
 */
export const PIILegend = ({ data }: PIILegendProps) => {
  const total = Object.values(data).reduce((sum, value) => sum + value, 0);

  return (
    <div className="grid grid-cols-2 gap-2 mt-4">
      {Object.entries(data).map(([key, value]) => {
        const percentage = ((value / total) * 100).toFixed(1);
        return (
          <div key={key} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-sm"
              style={{ backgroundColor: COLORS[key as keyof PIIRedacted] }}
            />
            <span className="text-xs text-gray-700">
              {LABELS[key as keyof PIIRedacted]}: {value.toLocaleString()} ({percentage}%)
            </span>
          </div>
        );
      })}
    </div>
  );
};
