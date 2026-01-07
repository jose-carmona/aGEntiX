// components/mcp/MCPTokenGenerator.tsx
// Generador de tokens JWT configurable para pruebas MCP

import React, { useState, useCallback } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { generateJWT } from '@/services/agentService';

// Tipos de expediente disponibles
export type TipoExpediente = 'subvenciones' | 'licencias_obras' | 'certificado_empadronamiento';

// Expedientes de prueba disponibles
export const EXPEDIENTES_PRUEBA = [
  { id: 'EXP-2024-001', tipo: 'subvenciones' as TipoExpediente, label: 'Subvención Asociación Cultural' },
  { id: 'EXP-2024-002', tipo: 'licencias_obras' as TipoExpediente, label: 'Licencia Obra Menor' },
  { id: 'EXP-2024-003', tipo: 'certificado_empadronamiento' as TipoExpediente, label: 'Certificado Empadronamiento' },
] as const;

// Permisos disponibles por módulo
export const PERMISOS_DISPONIBLES = [
  { id: 'consulta', label: 'Consulta', modulo: 'expedientes', description: 'Lectura de expedientes y documentos' },
  { id: 'gestion', label: 'Gestión', modulo: 'expedientes', description: 'Escritura en expedientes' },
  { id: 'documentacion:leer', label: 'Leer Documentación', modulo: 'documentacion', description: 'Listar y obtener documentación' },
  { id: 'documentacion:buscar', label: 'Buscar', modulo: 'documentacion', description: 'Búsqueda en documentación' },
] as const;

export interface TokenConfig {
  expedienteId: string;
  tipoExpediente: TipoExpediente;
  permisos: string[];
}

export interface TokenResult {
  token: string;
  claims: Record<string, unknown>;
}

interface MCPTokenGeneratorProps {
  onTokenGenerated?: (result: TokenResult) => void;
  disabled?: boolean;
  compact?: boolean;
}

export const MCPTokenGenerator: React.FC<MCPTokenGeneratorProps> = ({
  onTokenGenerated,
  disabled = false,
  compact = false
}) => {
  const [expedienteId, setExpedienteId] = useState<string>(EXPEDIENTES_PRUEBA[0].id);
  const [permisos, setPermisos] = useState<string[]>(['consulta', 'gestion', 'documentacion:leer', 'documentacion:buscar']);
  const [isGenerating, setIsGenerating] = useState(false);
  const [tokenClaims, setTokenClaims] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Obtener el tipo de expediente basado en el ID seleccionado
  const tipoExpediente = EXPEDIENTES_PRUEBA.find(e => e.id === expedienteId)?.tipo || 'subvenciones';

  const decodeJwtPayload = (token: string): Record<string, unknown> | null => {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch {
      return null;
    }
  };

  const togglePermiso = useCallback((permisoId: string) => {
    setPermisos(prev =>
      prev.includes(permisoId)
        ? prev.filter(p => p !== permisoId)
        : [...prev, permisoId]
    );
  }, []);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      const response = await generateJWT({
        exp_id: expedienteId,
        tarea_id: 'TAREA-MCP-TEST',
        permisos: permisos,
        mcp_servers: ['agentix-mcp-expedientes']
      });

      const claims = decodeJwtPayload(response.token);
      setTokenClaims(claims);

      onTokenGenerated?.({
        token: response.token,
        claims: claims || {}
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error generando token';
      setError(message);
    } finally {
      setIsGenerating(false);
    }
  };

  const permisosExpedientes = PERMISOS_DISPONIBLES.filter(p => p.modulo === 'expedientes');
  const permisosDocumentacion = PERMISOS_DISPONIBLES.filter(p => p.modulo === 'documentacion');

  return (
    <Card>
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Configuración del Token JWT
      </h2>

      <div className="space-y-4">
        {/* Selector de Expediente */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Expediente
          </label>
          <select
            value={expedienteId}
            onChange={(e) => setExpedienteId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            disabled={disabled || isGenerating}
          >
            {EXPEDIENTES_PRUEBA.map(exp => (
              <option key={exp.id} value={exp.id}>
                {exp.id} - {exp.label}
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Tipo: <span className="font-medium">{tipoExpediente.replace(/_/g, ' ')}</span>
          </p>
        </div>

        {/* Permisos */}
        {!compact && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Permisos
            </label>
            <div className="grid grid-cols-2 gap-4">
              {/* Expedientes */}
              <div className="bg-gray-50 rounded-lg p-3">
                <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">Expedientes</h4>
                <div className="space-y-2">
                  {permisosExpedientes.map(permiso => (
                    <label key={permiso.id} className="flex items-start gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={permisos.includes(permiso.id)}
                        onChange={() => togglePermiso(permiso.id)}
                        disabled={disabled || isGenerating}
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

              {/* Documentación */}
              <div className="bg-gray-50 rounded-lg p-3">
                <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">Documentación</h4>
                <div className="space-y-2">
                  {permisosDocumentacion.map(permiso => (
                    <label key={permiso.id} className="flex items-start gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={permisos.includes(permiso.id)}
                        onChange={() => togglePermiso(permiso.id)}
                        disabled={disabled || isGenerating}
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
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded p-3 text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Botón Generar */}
        <Button
          onClick={handleGenerate}
          disabled={disabled || isGenerating || permisos.length === 0}
          className="w-full"
        >
          {isGenerating ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Generando...
            </span>
          ) : (
            'Generar Token'
          )}
        </Button>

        {/* Claims del token */}
        {tokenClaims && (
          <div className="pt-4 border-t border-gray-200">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Claims del Token:</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div><span className="text-gray-500">iss:</span> {String(tokenClaims.iss)}</div>
              <div><span className="text-gray-500">sub:</span> {String(tokenClaims.sub)}</div>
              <div><span className="text-gray-500">exp_id:</span> {String(tokenClaims.exp_id)}</div>
              <div className="col-span-2">
                <span className="text-gray-500">permisos:</span>{' '}
                <span className="text-xs">
                  {Array.isArray(tokenClaims.permisos) ? tokenClaims.permisos.join(', ') : ''}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

// Hook para usar el generador de tokens
export const useTokenGenerator = () => {
  const [token, setToken] = useState<string | null>(null);
  const [claims, setClaims] = useState<Record<string, unknown> | null>(null);

  const handleTokenGenerated = useCallback((result: TokenResult) => {
    setToken(result.token);
    setClaims(result.claims);
  }, []);

  const clearToken = useCallback(() => {
    setToken(null);
    setClaims(null);
  }, []);

  return {
    token,
    claims,
    handleTokenGenerated,
    clearToken,
    hasToken: !!token
  };
};
