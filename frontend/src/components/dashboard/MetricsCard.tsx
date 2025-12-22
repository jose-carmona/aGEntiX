import { ReactNode } from 'react';

interface MetricsCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  color?: 'blue' | 'green' | 'orange' | 'red' | 'gray';
}

const colorClasses = {
  blue: {
    bg: 'bg-blue-50',
    text: 'text-blue-700',
    icon: 'text-blue-600',
  },
  green: {
    bg: 'bg-green-50',
    text: 'text-green-700',
    icon: 'text-green-600',
  },
  orange: {
    bg: 'bg-orange-50',
    text: 'text-orange-700',
    icon: 'text-orange-600',
  },
  red: {
    bg: 'bg-red-50',
    text: 'text-red-700',
    icon: 'text-red-600',
  },
  gray: {
    bg: 'bg-gray-50',
    text: 'text-gray-700',
    icon: 'text-gray-600',
  },
};

/**
 * Componente para mostrar una métrica KPI en formato de tarjeta
 */
export const MetricsCard = ({
  title,
  value,
  description,
  icon,
  trend,
  color = 'blue',
}: MetricsCardProps) => {
  const colors = colorClasses[color];

  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>

          {description && (
            <p className="text-sm text-gray-500 mt-2">{description}</p>
          )}

          {trend && (
            <div className="flex items-center mt-2">
              <span
                className={`text-sm font-medium ${
                  trend.isPositive ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
              </span>
              <span className="text-sm text-gray-500 ml-2">vs. período anterior</span>
            </div>
          )}
        </div>

        {icon && (
          <div className={`${colors.bg} rounded-full p-3 ${colors.icon}`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Componente para mostrar un KPI simple sin tarjeta (inline)
 */
export const MetricsInline = ({
  label,
  value,
  color = 'gray',
}: {
  label: string;
  value: string | number;
  color?: 'blue' | 'green' | 'orange' | 'red' | 'gray';
}) => {
  const colors = colorClasses[color];

  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
      <span className="text-sm text-gray-600">{label}</span>
      <span className={`text-sm font-semibold ${colors.text}`}>{value}</span>
    </div>
  );
};
