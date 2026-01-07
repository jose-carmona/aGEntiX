// components/jwt/JWTConfigCard.tsx
// Componente principal para configuración y generación de tokens JWT

import React, { useState, useCallback, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { generateJWT } from '@/services/agentService';
import { ExpedienteSelector } from './ExpedienteSelector';
import { PermisosSelector } from './PermisosSelector';
import { TokenClaimsDisplay } from './TokenClaimsDisplay';
import {
  EXPEDIENTES_PRUEBA,
  DEFAULT_PERMISOS,
  type JWTConfig,
  type TokenResult
} from './constants';

export interface JWTConfigCardProps {
  // Modo de operación
  mode?: 'standalone' | 'embedded';

  // Configuración inicial
  defaultExpedienteId?: string;
  defaultTareaId?: string;
  defaultPermisos?: string[];

  // Callbacks
  onTokenGenerated?: (result: TokenResult) => void;
  onConfigChange?: (config: JWTConfig) => void;

  // Opciones de UI
  title?: string;
  showTareaId?: boolean;
  expedienteMode?: 'select' | 'input';
  permisosLayout?: 'grid' | 'compact' | 'list';
  showClaimsPreview?: boolean;
  showGenerateButton?: boolean;
  generateButtonText?: string;

  // Estado externo
  disabled?: boolean;
  isGenerating?: boolean;
}

export const JWTConfigCard: React.FC<JWTConfigCardProps> = ({
  mode = 'standalone',
  defaultExpedienteId = EXPEDIENTES_PRUEBA[0].id,
  defaultTareaId = 'TAREA-001',
  defaultPermisos = [...DEFAULT_PERMISOS],
  onTokenGenerated,
  onConfigChange,
  title = 'Configuración del Token JWT',
  showTareaId = false,
  expedienteMode = 'select',
  permisosLayout = 'grid',
  showClaimsPreview = true,
  showGenerateButton = true,
  generateButtonText = 'Generar Token',
  disabled = false,
  isGenerating: externalIsGenerating
}) => {
  // Estado interno
  const [expedienteId, setExpedienteId] = useState(defaultExpedienteId);
  const [tareaId, setTareaId] = useState(defaultTareaId);
  const [permisos, setPermisos] = useState<string[]>(defaultPermisos);
  const [internalIsGenerating, setInternalIsGenerating] = useState(false);
  const [tokenClaims, setTokenClaims] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isGenerating = externalIsGenerating ?? internalIsGenerating;

  // Notificar cambios de configuración
  useEffect(() => {
    onConfigChange?.({
      expedienteId,
      tareaId,
      permisos
    });
  }, [expedienteId, tareaId, permisos, onConfigChange]);

  // Decodificar payload del JWT
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

  // Generar token
  const handleGenerate = useCallback(async () => {
    setInternalIsGenerating(true);
    setError(null);

    try {
      const response = await generateJWT({
        exp_id: expedienteId,
        tarea_id: tareaId,
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
      setInternalIsGenerating(false);
    }
  }, [expedienteId, tareaId, permisos, onTokenGenerated]);

  // Handlers
  const handleExpedienteChange = useCallback((id: string) => {
    setExpedienteId(id);
    setError(null);
  }, []);

  const handleTareaChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setTareaId(e.target.value);
    setError(null);
  }, []);

  const handlePermisosChange = useCallback((newPermisos: string[]) => {
    setPermisos(newPermisos);
    setError(null);
  }, []);

  const canGenerate = expedienteId && permisos.length > 0 && !isGenerating && !disabled;

  // Contenido del componente
  const content = (
    <div className="space-y-4">
      {/* Expediente y Tarea */}
      <div className={showTareaId ? 'grid grid-cols-2 gap-4' : ''}>
        <ExpedienteSelector
          value={expedienteId}
          onChange={handleExpedienteChange}
          mode={expedienteMode}
          disabled={disabled || isGenerating}
          showTipo={expedienteMode === 'select'}
        />

        {showTareaId && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ID Tarea
            </label>
            <input
              type="text"
              value={tareaId}
              onChange={handleTareaChange}
              placeholder="TAREA-001"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-50 disabled:text-gray-500"
              disabled={disabled || isGenerating}
            />
          </div>
        )}
      </div>

      {/* Permisos */}
      <PermisosSelector
        selected={permisos}
        onChange={handlePermisosChange}
        disabled={disabled || isGenerating}
        layout={permisosLayout}
      />

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Botón Generar */}
      {showGenerateButton && (
        <Button
          onClick={handleGenerate}
          disabled={!canGenerate}
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
            generateButtonText
          )}
        </Button>
      )}

      {/* Claims Preview */}
      {showClaimsPreview && tokenClaims && (
        <TokenClaimsDisplay claims={tokenClaims} />
      )}
    </div>
  );

  // Modo standalone: con Card
  if (mode === 'standalone') {
    return (
      <Card>
        {title && (
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            {title}
          </h2>
        )}
        {content}
      </Card>
    );
  }

  // Modo embedded: sin Card
  return content;
};

// Hook para usar el generador de tokens
export const useJWTGenerator = () => {
  const [token, setToken] = useState<string | null>(null);
  const [claims, setClaims] = useState<Record<string, unknown> | null>(null);
  const [config, setConfig] = useState<JWTConfig | null>(null);

  const handleTokenGenerated = useCallback((result: TokenResult) => {
    setToken(result.token);
    setClaims(result.claims);
  }, []);

  const handleConfigChange = useCallback((newConfig: JWTConfig) => {
    setConfig(newConfig);
  }, []);

  const clearToken = useCallback(() => {
    setToken(null);
    setClaims(null);
  }, []);

  return {
    token,
    claims,
    config,
    handleTokenGenerated,
    handleConfigChange,
    clearToken,
    hasToken: !!token
  };
};
