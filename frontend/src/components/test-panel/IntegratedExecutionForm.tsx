// components/test-panel/IntegratedExecutionForm.tsx
// Paso 4: Formulario simplificado para ejecución de agentes

import React, { useState, useEffect } from 'react';
import { getAvailablePermissions, generateJWT } from '../../services/agentService';
import type { Permission, GenerateJWTRequest, JWTClaims, ExecuteAgentRequest } from '../../types/agent';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

interface IntegratedExecutionFormProps {
  selectedAgentId: string | null;
  isExecuting: boolean;
  executionError: string | null;
  onExecute: (jwtToken: string, jwtClaims: JWTClaims, request: ExecuteAgentRequest) => Promise<void>;
  onResetError?: () => void;
}

export const IntegratedExecutionForm: React.FC<IntegratedExecutionFormProps> = ({
  selectedAgentId,
  isExecuting,
  executionError,
  onExecute,
  onResetError
}) => {
  // Estados del formulario
  const [expedienteId, setExpedienteId] = useState('EXP-2024-001');
  const [expTipo, setExpTipo] = useState('SUBVENCIONES');
  const [tareaId, setTareaId] = useState('TAREA-TEST-001');
  const [tareaNombre, setTareaNombre] = useState('VALIDAR_DOCUMENTACION');
  const [prompt, setPrompt] = useState('');
  const [permisos, setPermisos] = useState<string[]>(['consulta']);
  const [expHours, setExpHours] = useState(1);

  // Estados de validación y UI
  const [availablePermissions, setAvailablePermissions] = useState<Permission[]>([]);
  const [loadingPermissions, setLoadingPermissions] = useState(true);
  const [expedienteError, setExpedienteError] = useState<string | null>(null);
  const [isGeneratingToken, setIsGeneratingToken] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'validation' | 'jwt' | 'execution' | null>(null);

  // Prompts predeterminados por agente
  const defaultPrompts: Record<string, string> = {
    'ValidadorDocumental': 'Valida los documentos del expediente y verifica que toda la documentación esté completa',
    'AnalizadorSubvencion': 'Analiza la solicitud de subvención y verifica el cumplimiento de requisitos',
    'GeneradorInforme': 'Genera un informe técnico resumiendo el estado del expediente'
  };

  // Cargar configuración guardada y permisos disponibles
  useEffect(() => {
    loadSavedConfiguration();
    loadPermissions();
  }, []);

  // Actualizar prompt predeterminado cuando cambia el agente
  useEffect(() => {
    if (selectedAgentId && defaultPrompts[selectedAgentId]) {
      setPrompt(defaultPrompts[selectedAgentId]);
    }
  }, [selectedAgentId]);

  // Guardar configuración cuando cambia
  useEffect(() => {
    saveConfiguration();
  }, [expedienteId, expTipo, tareaId, tareaNombre, permisos, expHours]);

  // Resetear errores cuando el usuario cambia configuraciones
  useEffect(() => {
    if (localError) {
      setLocalError(null);
      setErrorType(null);
    }
    if (executionError && onResetError) {
      onResetError();
    }
  }, [expedienteId, expTipo, tareaId, tareaNombre, permisos, selectedAgentId]);

  const loadSavedConfiguration = () => {
    try {
      const saved = localStorage.getItem('agentix_test_panel_config_v2');
      if (saved) {
        const config = JSON.parse(saved);
        setExpedienteId(config.expedienteId || 'EXP-2024-001');
        setExpTipo(config.expTipo || 'SUBVENCIONES');
        setTareaId(config.tareaId || 'TAREA-TEST-001');
        setTareaNombre(config.tareaNombre || 'VALIDAR_DOCUMENTACION');
        setPermisos(config.permisos || ['consulta']);
        setExpHours(config.expHours || 1);
      }
    } catch (err) {
      console.error('Error loading saved configuration:', err);
    }
  };

  const saveConfiguration = () => {
    try {
      const config = {
        expedienteId,
        expTipo,
        tareaId,
        tareaNombre,
        permisos,
        expHours
      };
      localStorage.setItem('agentix_test_panel_config_v2', JSON.stringify(config));
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

  const handleExpedienteIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setExpedienteId(value);
    validateExpedienteId(value);
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

    if (!isExpedienteValid) {
      setLocalError('Por favor, corrige los errores de validación antes de continuar');
      setErrorType('validation');
      return;
    }

    if (!selectedAgentId) {
      setLocalError('Debes seleccionar un agente primero');
      setErrorType('validation');
      return;
    }

    if (!prompt.trim()) {
      setLocalError('El prompt es requerido');
      setErrorType('validation');
      return;
    }

    setIsGeneratingToken(true);

    try {
      // 1. Generar JWT
      const jwtRequest: GenerateJWTRequest = {
        exp_id: expedienteId,
        exp_tipo: expTipo,
        tarea_id: tareaId,
        tarea_nombre: tareaNombre,
        permisos: permisos.length > 0 ? permisos : ['consulta'],
        exp_hours: expHours
      };

      const jwtResponse = await generateJWT(jwtRequest);

      // 2. Construir request simplificado (Paso 4)
      const executeRequest: ExecuteAgentRequest = {
        agent: selectedAgentId,
        prompt: prompt,
        context: {
          expediente_id: expedienteId,
          tarea_id: tareaId
        }
        // callback_url omitido para testing
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
    prompt.trim() &&
    !expedienteError &&
    !isExecuting &&
    !isGeneratingToken;

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Configuración de Ejecución
        </h3>
        <p className="text-sm text-gray-600">
          Configura los parámetros del expediente y el prompt. El token JWT se genera automáticamente.
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
        {/* Sección: Datos del Expediente */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
            1. Datos del Expediente
          </h4>

          <div className="grid grid-cols-2 gap-4">
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
                disabled={isExecuting || isGeneratingToken}
                className={expedienteError ? 'border-red-300' : ''}
              />
              {expedienteError && (
                <p className="mt-1 text-sm text-red-600">{expedienteError}</p>
              )}
            </div>

            {/* Tipo de Expediente */}
            <div>
              <label htmlFor="exp-tipo" className="block text-sm font-medium text-gray-700 mb-2">
                Tipo de Expediente
              </label>
              <Input
                id="exp-tipo"
                type="text"
                value={expTipo}
                onChange={(e) => setExpTipo(e.target.value)}
                placeholder="SUBVENCIONES"
                disabled={isExecuting || isGeneratingToken}
              />
            </div>
          </div>
        </div>

        {/* Sección: Datos de la Tarea */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
            2. Datos de la Tarea BPMN
          </h4>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="tarea-id" className="block text-sm font-medium text-gray-700 mb-2">
                ID de Tarea
              </label>
              <Input
                id="tarea-id"
                type="text"
                value={tareaId}
                onChange={(e) => setTareaId(e.target.value)}
                placeholder="TAREA-TEST-001"
                disabled={isExecuting || isGeneratingToken}
              />
            </div>

            <div>
              <label htmlFor="tarea-nombre" className="block text-sm font-medium text-gray-700 mb-2">
                Nombre de Tarea
              </label>
              <Input
                id="tarea-nombre"
                type="text"
                value={tareaNombre}
                onChange={(e) => setTareaNombre(e.target.value)}
                placeholder="VALIDAR_DOCUMENTACION"
                disabled={isExecuting || isGeneratingToken}
              />
            </div>
          </div>
        </div>

        {/* Sección: Prompt del Agente */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
            3. Instrucciones para el Agente *
          </h4>

          <div>
            <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
              Prompt
            </label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Escribe las instrucciones específicas para el agente..."
              disabled={isExecuting || isGeneratingToken}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Estas instrucciones se combinarán con el system_prompt del agente
            </p>
          </div>
        </div>

        {/* Sección: Permisos JWT */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
            4. Permisos del Token JWT
          </h4>

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

        {/* Sección: Configuración del Token */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
            5. Configuración del Token
          </h4>

          <div className="w-1/2">
            <label htmlFor="exp-hours" className="block text-sm font-medium text-gray-700 mb-2">
              Horas hasta expiración
            </label>
            <Input
              id="exp-hours"
              type="number"
              min="1"
              max="24"
              value={expHours}
              onChange={(e) => setExpHours(parseInt(e.target.value) || 1)}
              disabled={isExecuting || isGeneratingToken}
            />
          </div>
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
              Generando token JWT...
            </span>
          ) : isExecuting ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Ejecutando agente...
            </span>
          ) : (
            'Ejecutar Agente'
          )}
        </Button>

        {/* Info de ayuda */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
          <p className="text-xs text-gray-600">
            <strong>API Simplificada (Paso 4):</strong> Solo se envía el nombre del agente, prompt y contexto.
            La configuración del agente (modelo, system_prompt, tools) se carga automáticamente desde el servidor.
          </p>
        </div>
      </div>
    </Card>
  );
};
