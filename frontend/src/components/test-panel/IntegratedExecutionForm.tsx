// components/test-panel/IntegratedExecutionForm.tsx

import React, { useState, useEffect } from 'react';
import { getAvailablePermissions, generateJWT, getAgentConfig } from '../../services/agentService';
import type { Permission, GenerateJWTRequest, JWTClaims, AgentConfig } from '../../types/agent';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

interface IntegratedExecutionFormProps {
  selectedAgentId: string | null;
  isExecuting: boolean;
  executionError: string | null; // Error del hook de ejecución
  onExecute: (jwtToken: string, jwtClaims: JWTClaims, expedienteId: string, tareaId: string, agentConfig: AgentConfig) => Promise<void>;
  onResetError?: () => void; // Callback para resetear errores de ejecución
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
  const [permisos, setPermisos] = useState<string[]>(['consulta']);
  const [expHours, setExpHours] = useState(1);
  const [contextoAdicional, setContextoAdicional] = useState('');

  // Estados de validación y UI
  const [availablePermissions, setAvailablePermissions] = useState<Permission[]>([]);
  const [loadingPermissions, setLoadingPermissions] = useState(true);
  const [expedienteError, setExpedienteError] = useState<string | null>(null);
  const [contextoError, setContextoError] = useState<string | null>(null);
  const [isGeneratingToken, setIsGeneratingToken] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'validation' | 'jwt' | 'config' | 'execution' | null>(null);

  // Cargar configuración guardada y permisos disponibles
  useEffect(() => {
    loadSavedConfiguration();
    loadPermissions();
  }, []);

  // Guardar configuración cuando cambia
  useEffect(() => {
    saveConfiguration();
  }, [expedienteId, expTipo, tareaId, tareaNombre, permisos, expHours, contextoAdicional]);

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
      const saved = localStorage.getItem('agentix_test_panel_config');
      if (saved) {
        const config = JSON.parse(saved);
        setExpedienteId(config.expedienteId || 'EXP-2024-001');
        setExpTipo(config.expTipo || 'SUBVENCIONES');
        setTareaId(config.tareaId || 'TAREA-TEST-001');
        setTareaNombre(config.tareaNombre || 'VALIDAR_DOCUMENTACION');
        setPermisos(config.permisos || ['consulta']);
        setExpHours(config.expHours || 1);
        setContextoAdicional(config.contextoAdicional || '');
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
        expHours,
        contextoAdicional
      };
      localStorage.setItem('agentix_test_panel_config', JSON.stringify(config));
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
    setExpedienteId(value);
    validateExpedienteId(value);
  };

  const handleContextoChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setContextoAdicional(value);
    validateContexto(value);
  };

  const handlePermisoToggle = (permisoId: string) => {
    if (permisos.includes(permisoId)) {
      setPermisos(permisos.filter(p => p !== permisoId));
    } else {
      setPermisos([...permisos, permisoId]);
    }
  };

  /**
   * Parsea errores de validación de FastAPI/Pydantic (422)
   */
  const parseValidationError = (detail: any): string => {
    try {
      // Si detail es un array (errores de validación Pydantic)
      if (Array.isArray(detail)) {
        const errors = detail.map((err: any) => {
          const field = err.loc ? err.loc.join('.') : 'campo';
          const message = err.msg || 'error de validación';
          return `${field}: ${message}`;
        });
        return errors.join('; ');
      }

      // Si detail es un string
      if (typeof detail === 'string') {
        return detail;
      }

      // Si detail es un objeto con mensaje
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
    const isContextoValid = validateContexto(contextoAdicional);

    if (!isExpedienteValid || !isContextoValid) {
      setLocalError('Por favor, corrige los errores de validación antes de continuar');
      setErrorType('validation');
      return;
    }

    if (!selectedAgentId) {
      setLocalError('Debes seleccionar un agente primero');
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

      // 2. Obtener configuración del agente
      const agentConfig = await getAgentConfig(selectedAgentId);

      // 3. Ejecutar agente
      await onExecute(
        jwtResponse.token,
        jwtResponse.claims,
        expedienteId,
        tareaId,
        agentConfig
      );

      // Si llegamos aquí sin errores, limpiamos cualquier error previo
      setLocalError(null);
      setErrorType(null);

    } catch (err: any) {
      console.error('Error during execution:', err);

      let errorMessage = 'Error desconocido';
      let type: 'jwt' | 'config' | 'execution' | 'validation' = 'execution';

      try {
        // Determinar el tipo de error basado en el código HTTP
        if (err.response?.status === 401) {
          errorMessage = 'No autorizado. Por favor, inicia sesión nuevamente.';
          type = 'jwt';
        } else if (err.response?.status === 422) {
          // Error de validación de FastAPI/Pydantic
          errorMessage = parseValidationError(err.response.data?.detail);
          type = 'validation';
        } else if (err.response?.status === 400) {
          const detail = err.response.data?.detail;
          errorMessage = typeof detail === 'string' ? detail : parseValidationError(detail);

          // Determinar subtipo basado en el mensaje
          if (errorMessage.toLowerCase().includes('jwt') || errorMessage.toLowerCase().includes('token')) {
            type = 'jwt';
          } else if (errorMessage.toLowerCase().includes('agente') || errorMessage.toLowerCase().includes('config')) {
            type = 'config';
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
    !expedienteError &&
    !contextoError &&
    !isExecuting &&
    !isGeneratingToken;

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Configuración de Ejecución
        </h3>
        <p className="text-sm text-gray-600">
          Configura los parámetros necesarios para ejecutar el agente. El token JWT se generará automáticamente.
        </p>
      </div>

      {/* Mostrar errores locales (JWT, Config, Validación) */}
      {localError && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <p className="text-sm font-semibold text-red-900">
                  {errorType === 'validation' && 'Error de Validación'}
                  {errorType === 'jwt' && 'Error de Autenticación (JWT)'}
                  {errorType === 'config' && 'Error de Configuración'}
                  {!errorType && 'Error'}
                </p>
                <span className="text-xs px-2 py-0.5 rounded bg-red-100 text-red-800 font-medium">
                  {errorType === 'validation' && 'VALIDACIÓN'}
                  {errorType === 'jwt' && 'JWT'}
                  {errorType === 'config' && 'CONFIG'}
                  {!errorType && 'DESCONOCIDO'}
                </span>
              </div>
              <p className="text-sm text-red-700">{localError}</p>
            </div>
          </div>
        </div>
      )}

      {/* Mostrar errores de ejecución del agente (desde el hook) */}
      {executionError && !localError && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <p className="text-sm font-semibold text-red-900">Error de Ejecución</p>
                <span className="text-xs px-2 py-0.5 rounded bg-red-100 text-red-800 font-medium">
                  EJECUCIÓN
                </span>
              </div>
              <p className="text-sm text-red-700">{executionError}</p>
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

          <div className="space-y-4">
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
              <p className="mt-1 text-xs text-gray-500">
                Formato: EXP-YYYY-NNN (ejemplo: EXP-2024-001)
              </p>
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
              <p className="mt-1 text-xs text-gray-500">
                Tipo de expediente (ej: SUBVENCIONES, LICENCIAS, etc.)
              </p>
            </div>
          </div>
        </div>

        {/* Sección: Datos de la Tarea BPMN */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
            2. Datos de la Tarea BPMN
          </h4>

          <div className="space-y-4">
            {/* Tarea ID */}
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
              <p className="mt-1 text-xs text-gray-500">
                Identificador de la tarea BPMN
              </p>
            </div>

            {/* Tarea Nombre */}
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
              <p className="mt-1 text-xs text-gray-500">
                Nombre descriptivo de la tarea (ej: VALIDAR_DOCUMENTACION)
              </p>
            </div>
          </div>
        </div>

        {/* Sección: Permisos JWT */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
            3. Permisos del Token JWT
          </h4>

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
                    ${isExecuting || isGeneratingToken ? 'opacity-50 cursor-not-allowed' : ''}
                  `}
                >
                  <input
                    type="checkbox"
                    checked={permisos.includes(permiso.id)}
                    onChange={() => handlePermisoToggle(permiso.id)}
                    disabled={isExecuting || isGeneratingToken}
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

        {/* Sección: Configuración del Token */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
            4. Configuración del Token
          </h4>

          <div>
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
            <p className="mt-1 text-xs text-gray-500">
              El token JWT expirará después de {expHours} hora(s)
            </p>
          </div>
        </div>

        {/* Sección: Contexto del Agente */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
            5. Contexto Adicional para el Agente (Opcional)
          </h4>

          <div>
            <label htmlFor="contexto" className="block text-sm font-medium text-gray-700 mb-2">
              Contexto Adicional (JSON)
            </label>
            <textarea
              id="contexto"
              value={contextoAdicional}
              onChange={handleContextoChange}
              placeholder='{"clave": "valor"}'
              disabled={isExecuting || isGeneratingToken}
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
              Generando token JWT...
            </span>
          ) : isExecuting ? (
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
              Ejecutando agente...
            </span>
          ) : (
            'Ejecutar Agente'
          )}
        </Button>

        {/* Información de ayuda */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <p className="text-xs text-blue-800">
                Al hacer clic en "Ejecutar Agente", se generará automáticamente un token JWT con los datos configurados
                y se ejecutará el agente seleccionado.
              </p>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};
