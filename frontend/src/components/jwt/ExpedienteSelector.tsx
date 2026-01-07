// components/jwt/ExpedienteSelector.tsx
// Selector de expediente (dropdown o input libre)

import React from 'react';
import { EXPEDIENTES_PRUEBA, getExpedienteTipo } from './constants';

interface ExpedienteSelectorProps {
  value: string;
  onChange: (id: string) => void;
  mode?: 'select' | 'input';
  disabled?: boolean;
  showTipo?: boolean;
  label?: string;
  error?: string;
}

export const ExpedienteSelector: React.FC<ExpedienteSelectorProps> = ({
  value,
  onChange,
  mode = 'select',
  disabled = false,
  showTipo = true,
  label = 'Expediente',
  error
}) => {
  const tipoExpediente = getExpedienteTipo(value);

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>

      {mode === 'select' ? (
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={`
            w-full px-3 py-2 border rounded-md
            focus:outline-none focus:ring-2 focus:ring-primary-500
            disabled:bg-gray-50 disabled:text-gray-500
            ${error ? 'border-red-300' : 'border-gray-300'}
          `}
          disabled={disabled}
        >
          {EXPEDIENTES_PRUEBA.map(exp => (
            <option key={exp.id} value={exp.id}>
              {exp.id} - {exp.label}
            </option>
          ))}
        </select>
      ) : (
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="EXP-2024-001"
          className={`
            w-full px-3 py-2 border rounded-md
            focus:outline-none focus:ring-2 focus:ring-primary-500
            disabled:bg-gray-50 disabled:text-gray-500
            ${error ? 'border-red-300' : 'border-gray-300'}
          `}
          disabled={disabled}
        />
      )}

      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}

      {showTipo && tipoExpediente && !error && (
        <p className="text-xs text-gray-500 mt-1">
          Tipo: <span className="font-medium">{tipoExpediente.replace(/_/g, ' ')}</span>
        </p>
      )}
    </div>
  );
};
