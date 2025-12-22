// components/test-panel/ExecutionForm.tsx

import React, { useState, useEffect } from 'react';
import { getAvailablePermissions } from '../../services/agentService';
import type { Permission } from '../../types/agent';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

interface ExecutionFormProps {
  expedienteId: string;
  onExpedienteIdChange: (value: string) => void;
  permisos: string[];
  onPermisosChange: (permisos: string[]) => void;
  contextoAdicional: string;
  onContextoAdicionalChange: (value: string) => void;
  onExecute: () => void;
  isExecuting: boolean;
  disabled?: boolean;
}

export const ExecutionForm: React.FC<ExecutionFormProps> = ({
  expedienteId,
  onExpedienteIdChange,
  permisos,
  onPermisosChange,
  contextoAdicional,
  onContextoAdicionalChange,
  onExecute,
  isExecuting,
  disabled = false
}) => {
  const [availablePermissions, setAvailablePermissions] = useState<Permission[]>([]);
  const [loadingPermissions, setLoadingPermissions] = useState(true);
  const [expedienteError, setExpedienteError] = useState<string | null>(null);
  const [contextoError, setContextoError] = useState<string | null>(null);

  useEffect(() => {
    loadPermissions();
  }, []);

  const loadPermissions = async () => {
    try {
      setLoadingPermissions(true);
      const permissions = await getAvailablePermissions();
      setAvailablePermissions(permissions);
    } catch (err) {
      console.error('Error loading permissions:', err);
    } finally {
      setLoadingPermissions(false);
    }
  };

  const validateExpedienteId = (value: string): boolean => {
    // Validar formato EXP-YYYY-NNN
    const regex = /^EXP-\d{4}-\d{3,}$/;
    if (!value) {
      setExpedienteError('El ID de expediente es requerido');
      return false;
    }
    if (!regex.test(value)) {
      setExpedienteError('Formato inválido. Use: EXP-YYYY-NNN (ej: EXP-2024-001)');
      return false;
    }
    setExpedienteError(null);
    return true;
  };

  const validateContexto = (value: string): boolean => {
    if (!value) {
      setContextoError(null);
      return true;
    }

    try {
      JSON.parse(value);
      setContextoError(null);
      return true;
    } catch (err) {
      setContextoError('JSON inválido');
      return false;
    }
  };

  const handleExpedienteIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    onExpedienteIdChange(value);
    validateExpedienteId(value);
  };

  const handleContextoChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    onContextoAdicionalChange(value);
    validateContexto(value);
  };

  const handlePermisoToggle = (permisoId: string) => {
    if (permisos.includes(permisoId)) {
      onPermisosChange(permisos.filter(p => p !== permisoId));
    } else {
      onPermisosChange([...permisos, permisoId]);
    }
  };

  const handleExecute = () => {
    const isExpedienteValid = validateExpedienteId(expedienteId);
    const isContextoValid = validateContexto(contextoAdicional);

    if (isExpedienteValid && isContextoValid) {
      onExecute();
    }
  };

  const canExecute = expedienteId && !expedienteError && !contextoError && !isExecuting;

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Configuración de Ejecución
        </h3>
        <p className="text-sm text-gray-600">
          Configura los parámetros necesarios para ejecutar el agente.
        </p>
      </div>

      <div className="space-y-6">
        {/* Expediente ID */}
        <div>
          <label htmlFor="expediente-id" className="block text-sm font-medium text-gray-700 mb-2">
            ID de Expediente *
          </label>
          <Input
            id="expediente-id"
            type="text"
            value={expedienteId}
            onChange={handleExpedienteIdChange}
            placeholder="EXP-2024-001"
            disabled={disabled || isExecuting}
            className={expedienteError ? 'border-red-300' : ''}
          />
          {expedienteError && (
            <p className="mt-1 text-sm text-red-600">{expedienteError}</p>
          )}
          <p className="mt-1 text-xs text-gray-500">
            Formato: EXP-YYYY-NNN (ejemplo: EXP-2024-001)
          </p>
        </div>

        {/* Permisos */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Permisos a incluir en JWT
          </label>
          {loadingPermissions ? (
            <div className="text-sm text-gray-600">Cargando permisos...</div>
          ) : (
            <div className="space-y-2">
              {availablePermissions.map((permiso) => (
                <label
                  key={permiso.id}
                  className={`
                    flex items-start p-3 rounded-lg border cursor-pointer transition-colors
                    ${permisos.includes(permiso.id)
                      ? 'border-blue-300 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                    }
                    ${disabled || isExecuting ? 'opacity-50 cursor-not-allowed' : ''}
                  `}
                >
                  <input
                    type="checkbox"
                    checked={permisos.includes(permiso.id)}
                    onChange={() => handlePermisoToggle(permiso.id)}
                    disabled={disabled || isExecuting}
                    className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <div className="ml-3 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-900">
                        {permiso.nombre}
                      </span>
                      <span className={`
                        text-xs px-2 py-0.5 rounded
                        ${permiso.category === 'lectura' ? 'bg-green-100 text-green-800' : ''}
                        ${permiso.category === 'escritura' ? 'bg-yellow-100 text-yellow-800' : ''}
                        ${permiso.category === 'admin' ? 'bg-red-100 text-red-800' : ''}
                      `}>
                        {permiso.category}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">
                      {permiso.descripcion}
                    </p>
                  </div>
                </label>
              ))}
            </div>
          )}
          <p className="mt-2 text-xs text-gray-500">
            {permisos.length === 0
              ? 'Si no seleccionas ninguno, se usará "consulta" por defecto'
              : `${permisos.length} permiso(s) seleccionado(s)`
            }
          </p>
        </div>

        {/* Contexto Adicional (JSON) */}
        <div>
          <label htmlFor="contexto" className="block text-sm font-medium text-gray-700 mb-2">
            Contexto Adicional (JSON) - Opcional
          </label>
          <textarea
            id="contexto"
            value={contextoAdicional}
            onChange={handleContextoChange}
            placeholder='{"clave": "valor"}'
            disabled={disabled || isExecuting}
            rows={4}
            className={`
              w-full px-3 py-2 border rounded-md font-mono text-sm
              focus:ring-2 focus:ring-blue-500 focus:border-blue-500
              disabled:bg-gray-50 disabled:text-gray-500
              ${contextoError ? 'border-red-300' : 'border-gray-300'}
            `}
          />
          {contextoError && (
            <p className="mt-1 text-sm text-red-600">{contextoError}</p>
          )}
          <p className="mt-1 text-xs text-gray-500">
            JSON válido con información de contexto adicional para el agente
          </p>
        </div>

        {/* Botón de ejecución */}
        <Button
          onClick={handleExecute}
          disabled={!canExecute || disabled}
          className="w-full"
        >
          {isExecuting ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Ejecutando...
            </span>
          ) : (
            'Ejecutar Agente'
          )}
        </Button>
      </div>
    </Card>
  );
};
