// components/simple-execution/SimpleExecutionForm.tsx
// Formulario simplificado para ejecución de agentes

import React, { useState, useEffect } from 'react';
import { getAvailablePermissions, generateJWT } from '../../services/agentService';
import type { Permission, GenerateJWTRequest, JWTClaims, ExecuteAgentRequest } from '../../types/agent';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

interface SimpleExecutionFormProps {
  selectedAgentId: string | null;
  isExecuting: boolean;
  executionError: string | null;
  onExecute: (jwtToken: string, jwtClaims: JWTClaims, request: ExecuteAgentRequest) => Promise<void>;
  onResetError?: () => void;
}

const STORAGE_KEY = 'agentix_simple_exec_config';

export const SimpleExecutionForm: React.FC<SimpleExecutionFormProps> = ({
  selectedAgentId,
  isExecuting,
  executionError,
  onExecute,
  onResetError
}) => {
  // Estados del formulario - Solo parámetros necesarios
  const [expedienteId, setExpedienteId] = useState('EXP-2024-001');
  const [tareaId, setTareaId] = useState('TAREA-001');
  const [permisos, setPermisos] = useState<string[]>(['consulta']);
  const [additionalGoal, setAdditionalGoal] = useState('');
  const [callbackUrl, setCallbackUrl] = useState('');

  // Estados de validación y UI
  const [availablePermissions, setAvailablePermissions] = useState<Permission[]>([]);
  const [loadingPermissions, setLoadingPermissions] = useState(true);
  const [expedienteError, setExpedienteError] = useState<string | null>(null);
  const [tareaError, setTareaError] = useState<string | null>(null);
  const [isGeneratingToken, setIsGeneratingToken] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'validation' | 'jwt' | 'execution' | null>(null);

  // Cargar configuración guardada y permisos disponibles
  useEffect(() => {
    loadSavedConfiguration();
    loadPermissions();
  }, []);

  // Guardar configuración cuando cambia
  useEffect(() => {
    saveConfiguration();
  }, [expedienteId, tareaId, permisos, callbackUrl]);

  // Resetear errores cuando el usuario cambia configuraciones
  useEffect(() => {
    if (localError) {
      setLocalError(null);
      setErrorType(null);
    }
    if (executionError && onResetError) {
      onResetError();
    }
  }, [expedienteId, tareaId, permisos, selectedAgentId]);

  const loadSavedConfiguration = () => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const config = JSON.parse(saved);
        setExpedienteId(config.expedienteId || 'EXP-2024-001');
        setTareaId(config.tareaId || 'TAREA-001');
        setPermisos(config.permisos || ['consulta']);
        setCallbackUrl(config.callbackUrl || '');
      }
    } catch (err) {
      console.error('Error loading saved configuration:', err);
    }
  };

  const saveConfiguration = () => {
    try {
      const config = {
        expedienteId,
        tareaId,
        permisos,
        callbackUrl
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
    } catch (err) {
      console.error('Error saving configuration:', err);
    }
  };

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
    if (!value.trim()) {
      setExpedienteError('El ID de expediente es requerido');
      return false;
    }
    setExpedienteError(null);
    return true;
  };

  const validateTareaId = (value: string): boolean => {
    if (!value.trim()) {
      setTareaError('El ID de tarea es requerido');
      return false;
    }
    setTareaError(null);
    return true;
  };

  const handleExpedienteIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setExpedienteId(value);
    validateExpedienteId(value);
  };

  const handleTareaIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setTareaId(value);
    validateTareaId(value);
  };

  const handlePermisoToggle = (permisoId: string) => {
    if (permisos.includes(permisoId)) {
      setPermisos(permisos.filter(p => p !== permisoId));
    } else {
      setPermisos([...permisos, permisoId]);
    }
  };

  const parseValidationError = (detail: any): string => {
    try {
      if (Array.isArray(detail)) {
        const errors = detail.map((err: any) => {
          const field = err.loc ? err.loc.join('.') : 'campo';
          const message = err.msg || 'error de validación';
          return `${field}: ${message}`;
        });
        return errors.join('; ');
      }
      if (typeof detail === 'string') {
        return detail;
      }
      if (detail?.message) {
        return detail.message;
      }
      return JSON.stringify(detail);
    } catch {
      return 'Error de validación desconocido';
    }
  };

  const handleExecute = async () => {
    // Limpiar errores previos
    setLocalError(null);
    setErrorType(null);
    if (onResetError) {
      onResetError();
    }

    // Validar formulario
    const isExpedienteValid = validateExpedienteId(expedienteId);
    const isTareaValid = validateTareaId(tareaId);

    if (!isExpedienteValid || !isTareaValid) {
      setLocalError('Por favor, corrige los errores de validación antes de continuar');
      setErrorType('validation');
      return;
    }

    if (!selectedAgentId) {
      setLocalError('Debes seleccionar un agente primero');
      setErrorType('validation');
      return;
    }

    if (permisos.length === 0) {
      setLocalError('Debes seleccionar al menos un permiso');
      setErrorType('validation');
      return;
    }

    setIsGeneratingToken(true);

    try {
      // 1. Generar JWT con parámetros mínimos
      const jwtRequest: GenerateJWTRequest = {
        exp_id: expedienteId,
        tarea_id: tareaId,
        permisos: permisos,
        exp_hours: 1  // Valor fijo por defecto
      };

      const jwtResponse = await generateJWT(jwtRequest);

      // 2. Construir request simplificado
      const executeRequest: ExecuteAgentRequest = {
        agent: selectedAgentId,
        context: {
          expediente_id: expedienteId,
          tarea_id: tareaId
        },
        additional_goal: additionalGoal.trim() || undefined,
        callback_url: callbackUrl.trim() || undefined
      };

      // 3. Ejecutar agente
      await onExecute(
        jwtResponse.token,
        jwtResponse.claims,
        executeRequest
      );

      // Si llegamos aquí sin errores, limpiamos cualquier error previo
      setLocalError(null);
      setErrorType(null);

    } catch (err: any) {
      console.error('Error during execution:', err);

      let errorMessage = 'Error desconocido';
      let type: 'jwt' | 'execution' | 'validation' = 'execution';

      try {
        if (err.response?.status === 401) {
          errorMessage = 'No autorizado. Por favor, inicia sesión nuevamente.';
          type = 'jwt';
        } else if (err.response?.status === 422) {
          errorMessage = parseValidationError(err.response.data?.detail);
          type = 'validation';
        } else if (err.response?.status === 400) {
          const detail = err.response.data?.detail;
          errorMessage = typeof detail === 'string' ? detail : parseValidationError(detail);
          if (errorMessage.toLowerCase().includes('jwt') || errorMessage.toLowerCase().includes('token')) {
            type = 'jwt';
          }
        } else if (err.response?.data?.detail) {
          errorMessage = typeof err.response.data.detail === 'string'
            ? err.response.data.detail
            : parseValidationError(err.response.data.detail);
        } else if (err.message) {
          errorMessage = err.message;
        }
      } catch (parseError) {
        console.error('Error parsing error message:', parseError);
        errorMessage = 'Error al procesar la respuesta del servidor';
      }

      setLocalError(errorMessage);
      setErrorType(type);
    } finally {
      setIsGeneratingToken(false);
    }
  };

  const canExecute =
    selectedAgentId &&
    expedienteId &&
    tareaId &&
    !expedienteError &&
    !tareaError &&
    permisos.length > 0 &&
    !isExecuting &&
    !isGeneratingToken;

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Parámetros de Ejecución
        </h3>
        <p className="text-sm text-gray-600">
          Configura los parámetros mínimos para ejecutar el agente.
        </p>
      </div>

      {/* Mostrar errores */}
      {(localError || executionError) && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <p className="text-sm font-semibold text-red-900">
                  {errorType === 'validation' && 'Error de Validación'}
                  {errorType === 'jwt' && 'Error de Autenticación'}
                  {errorType === 'execution' && 'Error de Ejecución'}
                  {!errorType && 'Error'}
                </p>
              </div>
              <p className="text-sm text-red-700">{localError || executionError}</p>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-6">
        {/* ID Expediente e ID Tarea */}
        <div className="grid grid-cols-2 gap-4">
          {/* ID Expediente */}
          <div>
            <label htmlFor="expediente-id" className="block text-sm font-medium text-gray-700 mb-2">
              ID Expediente *
            </label>
            <Input
              id="expediente-id"
              type="text"
              value={expedienteId}
              onChange={handleExpedienteIdChange}
              placeholder="EXP-2024-001"
              disabled={isExecuting || isGeneratingToken}
              className={expedienteError ? 'border-red-300' : ''}
            />
            {expedienteError && (
              <p className="mt-1 text-sm text-red-600">{expedienteError}</p>
            )}
          </div>

          {/* ID Tarea */}
          <div>
            <label htmlFor="tarea-id" className="block text-sm font-medium text-gray-700 mb-2">
              ID Tarea *
            </label>
            <Input
              id="tarea-id"
              type="text"
              value={tareaId}
              onChange={handleTareaIdChange}
              placeholder="TAREA-001"
              disabled={isExecuting || isGeneratingToken}
              className={tareaError ? 'border-red-300' : ''}
            />
            {tareaError && (
              <p className="mt-1 text-sm text-red-600">{tareaError}</p>
            )}
          </div>
        </div>

        {/* Permisos JWT */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Permisos JWT *
          </label>
          {loadingPermissions ? (
            <div className="text-sm text-gray-600">Cargando permisos...</div>
          ) : (
            <div className="grid grid-cols-2 gap-2">
              {availablePermissions.map((permiso) => (
                <label
                  key={permiso.id}
                  className={`
                    flex items-center p-2 rounded-lg border cursor-pointer transition-colors
                    ${permisos.includes(permiso.id)
                      ? 'border-blue-300 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                    }
                    ${isExecuting || isGeneratingToken ? 'opacity-50 cursor-not-allowed' : ''}
                  `}
                >
                  <input
                    type="checkbox"
                    checked={permisos.includes(permiso.id)}
                    onChange={() => handlePermisoToggle(permiso.id)}
                    disabled={isExecuting || isGeneratingToken}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <div className="ml-2">
                    <span className="text-sm font-medium text-gray-900">
                      {permiso.nombre}
                    </span>
                    <span className={`
                      ml-2 text-xs px-1.5 py-0.5 rounded
                      ${permiso.category === 'lectura' ? 'bg-green-100 text-green-800' : ''}
                      ${permiso.category === 'escritura' ? 'bg-yellow-100 text-yellow-800' : ''}
                      ${permiso.category === 'admin' ? 'bg-red-100 text-red-800' : ''}
                    `}>
                      {permiso.category}
                    </span>
                  </div>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Objetivo Adicional (Opcional) */}
        <div>
          <label htmlFor="additional-goal" className="block text-sm font-medium text-gray-700 mb-2">
            Objetivo Adicional <span className="text-gray-400 font-normal">(opcional)</span>
          </label>
          <textarea
            id="additional-goal"
            value={additionalGoal}
            onChange={(e) => setAdditionalGoal(e.target.value)}
            placeholder="Instrucciones adicionales para el agente..."
            disabled={isExecuting || isGeneratingToken}
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
          />
        </div>

        {/* URL Callback (Opcional) */}
        <div>
          <label htmlFor="callback-url" className="block text-sm font-medium text-gray-700 mb-2">
            URL Callback <span className="text-gray-400 font-normal">(opcional)</span>
          </label>
          <Input
            id="callback-url"
            type="url"
            value={callbackUrl}
            onChange={(e) => setCallbackUrl(e.target.value)}
            placeholder="https://ejemplo.com/webhook"
            disabled={isExecuting || isGeneratingToken}
          />
          <p className="mt-1 text-xs text-gray-500">
            URL para notificar cuando finalice la ejecución
          </p>
        </div>

        {/* Botón de ejecución */}
        <Button
          onClick={handleExecute}
          disabled={!canExecute}
          className="w-full"
        >
          {isGeneratingToken ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Generando token...
            </span>
          ) : isExecuting ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Ejecutando...
            </span>
          ) : (
            'Ejecutar'
          )}
        </Button>
      </div>
    </Card>
  );
};
