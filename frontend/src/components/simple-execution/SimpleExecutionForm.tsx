// components/simple-execution/SimpleExecutionForm.tsx
// Formulario simplificado para ejecución de agentes
// Usa componentes JWT unificados

import React, { useState, useEffect, useCallback } from 'react';
import { generateJWT } from '../../services/agentService';
import type { GenerateJWTRequest, JWTClaims, ExecuteAgentRequest } from '../../types/agent';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import {
  ExpedienteSelector,
  PermisosSelector,
  DEFAULT_PERMISOS
} from '@/components/jwt';

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
  // Estados del formulario
  const [expedienteId, setExpedienteId] = useState('EXP-2024-001');
  const [tareaId, setTareaId] = useState('TAREA-001');
  const [permisos, setPermisos] = useState<string[]>([...DEFAULT_PERMISOS]);
  const [additionalGoal, setAdditionalGoal] = useState('');
  const [callbackUrl, setCallbackUrl] = useState('');

  // Estados de validación y UI
  const [expedienteError, setExpedienteError] = useState<string | null>(null);
  const [tareaError, setTareaError] = useState<string | null>(null);
  const [isGeneratingToken, setIsGeneratingToken] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'validation' | 'jwt' | 'execution' | null>(null);

  // Cargar configuración guardada
  useEffect(() => {
    loadSavedConfiguration();
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
        // Migrar permisos antiguos a los nuevos si es necesario
        const savedPermisos = config.permisos || [];
        // Si tiene permisos antiguos, usar los nuevos por defecto
        if (savedPermisos.length === 0 || savedPermisos.includes('lectura') || savedPermisos.includes('escritura')) {
          setPermisos([...DEFAULT_PERMISOS]);
        } else {
          setPermisos(savedPermisos);
        }
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

  const handleExpedienteChange = useCallback((id: string) => {
    setExpedienteId(id);
    validateExpedienteId(id);
  }, []);

  const handleTareaIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setTareaId(value);
    validateTareaId(value);
  };

  const handlePermisosChange = useCallback((newPermisos: string[]) => {
    setPermisos(newPermisos);
  }, []);

  const parseValidationError = (detail: unknown): string => {
    try {
      if (Array.isArray(detail)) {
        const errors = detail.map((err: { loc?: string[]; msg?: string }) => {
          const field = err.loc ? err.loc.join('.') : 'campo';
          const message = err.msg || 'error de validación';
          return `${field}: ${message}`;
        });
        return errors.join('; ');
      }
      if (typeof detail === 'string') {
        return detail;
      }
      if (detail && typeof detail === 'object' && 'message' in detail) {
        return String((detail as { message: unknown }).message);
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
      // 1. Generar JWT con parámetros
      const jwtRequest: GenerateJWTRequest = {
        exp_id: expedienteId,
        tarea_id: tareaId,
        permisos: permisos,
        exp_hours: 1
      };

      const jwtResponse = await generateJWT(jwtRequest);

      // 2. Construir request de ejecución
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

      setLocalError(null);
      setErrorType(null);

    } catch (err: unknown) {
      console.error('Error during execution:', err);

      let errorMessage = 'Error desconocido';
      let type: 'jwt' | 'execution' | 'validation' = 'execution';

      const error = err as { response?: { status?: number; data?: { detail?: unknown } }; message?: string };

      try {
        if (error.response?.status === 401) {
          errorMessage = 'No autorizado. Por favor, inicia sesión nuevamente.';
          type = 'jwt';
        } else if (error.response?.status === 422) {
          errorMessage = parseValidationError(error.response.data?.detail);
          type = 'validation';
        } else if (error.response?.status === 400) {
          const detail = error.response.data?.detail;
          errorMessage = typeof detail === 'string' ? detail : parseValidationError(detail);
          if (errorMessage.toLowerCase().includes('jwt') || errorMessage.toLowerCase().includes('token')) {
            type = 'jwt';
          }
        } else if (error.response?.data?.detail) {
          errorMessage = typeof error.response.data.detail === 'string'
            ? error.response.data.detail
            : parseValidationError(error.response.data.detail);
        } else if (error.message) {
          errorMessage = error.message;
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

  const isDisabled = isExecuting || isGeneratingToken;

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
        {/* Expediente y Tarea */}
        <div className="grid grid-cols-2 gap-4">
          {/* Expediente - usando input libre */}
          <ExpedienteSelector
            value={expedienteId}
            onChange={handleExpedienteChange}
            mode="input"
            disabled={isDisabled}
            showTipo={false}
            label="ID Expediente *"
            error={expedienteError || undefined}
          />

          {/* ID Tarea */}
          <div>
            <label htmlFor="tarea-id" className="block text-sm font-medium text-gray-700 mb-1">
              ID Tarea *
            </label>
            <Input
              id="tarea-id"
              type="text"
              value={tareaId}
              onChange={handleTareaIdChange}
              placeholder="TAREA-001"
              disabled={isDisabled}
              className={tareaError ? 'border-red-300' : ''}
            />
            {tareaError && (
              <p className="mt-1 text-sm text-red-600">{tareaError}</p>
            )}
          </div>
        </div>

        {/* Permisos JWT - usando componente unificado */}
        <PermisosSelector
          selected={permisos}
          onChange={handlePermisosChange}
          disabled={isDisabled}
          layout="grid"
          label="Permisos JWT *"
        />

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
            disabled={isDisabled}
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
            disabled={isDisabled}
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
