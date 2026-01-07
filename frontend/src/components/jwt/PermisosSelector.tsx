// components/jwt/PermisosSelector.tsx
// Selector de permisos JWT con checkboxes organizados por módulo

import React, { useCallback } from 'react';
import { PERMISOS_DISPONIBLES, getPermisosByModulo } from './constants';

interface PermisosSelectorProps {
  selected: string[];
  onChange: (permisos: string[]) => void;
  disabled?: boolean;
  layout?: 'grid' | 'compact' | 'list';
  label?: string;
}

export const PermisosSelector: React.FC<PermisosSelectorProps> = ({
  selected,
  onChange,
  disabled = false,
  layout = 'grid',
  label = 'Permisos'
}) => {
  const togglePermiso = useCallback((permisoId: string) => {
    if (selected.includes(permisoId)) {
      onChange(selected.filter(p => p !== permisoId));
    } else {
      onChange([...selected, permisoId]);
    }
  }, [selected, onChange]);

  const permisosExpedientes = getPermisosByModulo('expedientes');
  const permisosDocumentacion = getPermisosByModulo('documentacion');

  // Layout compacto: una sola fila
  if (layout === 'compact') {
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
        </label>
        <div className="flex flex-wrap gap-2">
          {PERMISOS_DISPONIBLES.map(permiso => (
            <label
              key={permiso.id}
              className={`
                flex items-center gap-2 px-3 py-1.5 rounded-full border cursor-pointer transition-colors
                ${selected.includes(permiso.id)
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              <input
                type="checkbox"
                checked={selected.includes(permiso.id)}
                onChange={() => togglePermiso(permiso.id)}
                disabled={disabled}
                className="sr-only"
              />
              <span className="text-sm">{permiso.label}</span>
            </label>
          ))}
        </div>
      </div>
    );
  }

  // Layout lista: checkboxes verticales
  if (layout === 'list') {
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
        </label>
        <div className="space-y-2">
          {PERMISOS_DISPONIBLES.map(permiso => (
            <label
              key={permiso.id}
              className={`
                flex items-center gap-2 p-2 rounded border cursor-pointer transition-colors
                ${selected.includes(permiso.id)
                  ? 'border-primary-300 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              <input
                type="checkbox"
                checked={selected.includes(permiso.id)}
                onChange={() => togglePermiso(permiso.id)}
                disabled={disabled}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <div className="flex-1">
                <span className="text-sm font-medium text-gray-900">{permiso.label}</span>
                <span className="ml-2 text-xs text-gray-500">({permiso.modulo})</span>
              </div>
            </label>
          ))}
        </div>
      </div>
    );
  }

  // Layout grid (default): dos columnas por módulo
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {label}
      </label>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Módulo Expedientes */}
        <div className="bg-gray-50 rounded-lg p-3">
          <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">
            Expedientes
          </h4>
          <div className="space-y-2">
            {permisosExpedientes.map(permiso => (
              <label
                key={permiso.id}
                className={`flex items-start gap-2 cursor-pointer ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={selected.includes(permiso.id)}
                  onChange={() => togglePermiso(permiso.id)}
                  disabled={disabled}
                  className="mt-0.5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <div>
                  <span className="text-sm font-medium text-gray-700">{permiso.label}</span>
                  <p className="text-xs text-gray-500">{permiso.description}</p>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Módulo Documentación */}
        <div className="bg-gray-50 rounded-lg p-3">
          <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">
            Documentación
          </h4>
          <div className="space-y-2">
            {permisosDocumentacion.map(permiso => (
              <label
                key={permiso.id}
                className={`flex items-start gap-2 cursor-pointer ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={selected.includes(permiso.id)}
                  onChange={() => togglePermiso(permiso.id)}
                  disabled={disabled}
                  className="mt-0.5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <div>
                  <span className="text-sm font-medium text-gray-700">{permiso.label}</span>
                  <p className="text-xs text-gray-500">{permiso.description}</p>
                </div>
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
