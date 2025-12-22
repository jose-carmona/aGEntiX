// components/test-panel/JWTGenerator.tsx

import React, { useState } from 'react';
import { generateJWT, formatTimestamp } from '../../services/agentService';
import type { GenerateJWTRequest, JWTClaims } from '../../types/agent';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

interface JWTGeneratorProps {
  expedienteId: string;
  permisos: string[];
  onTokenGenerated: (token: string, claims: JWTClaims) => void;
}

export const JWTGenerator: React.FC<JWTGeneratorProps> = ({
  expedienteId,
  permisos,
  onTokenGenerated
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedToken, setGeneratedToken] = useState<string | null>(null);
  const [claims, setClaims] = useState<JWTClaims | null>(null);
  const [showClaims, setShowClaims] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleGenerateToken = async () => {
    setLoading(true);
    setError(null);
    setCopied(false);

    try {
      const request: GenerateJWTRequest = {
        exp_id: expedienteId,
        permisos: permisos.length > 0 ? permisos : ['consulta'],
        exp_hours: 1
      };

      const response = await generateJWT(request);

      setGeneratedToken(response.token);
      setClaims(response.claims);
      onTokenGenerated(response.token, response.claims);

    } catch (err: any) {
      console.error('Error generating JWT:', err);

      let errorMessage = 'Error al generar el token JWT';

      if (err.response?.status === 401) {
        errorMessage = 'No autorizado. Por favor, inicia sesión nuevamente.';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyToken = async () => {
    if (!generatedToken) return;

    try {
      await navigator.clipboard.writeText(generatedToken);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Error copying token:', err);
    }
  };

  return (
    <Card className="p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Generador de JWT de Prueba
        </h3>
        <p className="text-sm text-gray-600">
          Genera un token JWT válido para ejecutar agentes en modo testing.
        </p>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Parámetros del token */}
      <div className="mb-4 space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Expediente:</span>
          <span className="font-mono text-gray-900">{expedienteId || 'No especificado'}</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Permisos:</span>
          <span className="font-mono text-gray-900">
            {permisos.length > 0 ? permisos.join(', ') : 'consulta (default)'}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Expiración:</span>
          <span className="font-mono text-gray-900">1 hora</span>
        </div>
      </div>

      {/* Botón generar */}
      <Button
        onClick={handleGenerateToken}
        disabled={loading || !expedienteId}
        className="w-full mb-4"
      >
        {loading ? 'Generando...' : 'Generar Token JWT'}
      </Button>

      {/* Token generado */}
      {generatedToken && (
        <div className="space-y-4">
          <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
            <div className="flex items-start justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">
                Token generado:
              </label>
              <button
                onClick={handleCopyToken}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                {copied ? '✓ Copiado' : 'Copiar'}
              </button>
            </div>
            <div className="font-mono text-xs text-gray-800 break-all bg-white p-2 rounded border border-gray-200">
              {generatedToken}
            </div>
          </div>

          {/* Claims decodificados */}
          {claims && (
            <div>
              <button
                onClick={() => setShowClaims(!showClaims)}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium mb-2"
              >
                {showClaims ? '▼ Ocultar claims' : '▶ Ver claims decodificados'}
              </button>

              {showClaims && (
                <div className="border border-gray-200 rounded-lg p-4 bg-white">
                  <div className="space-y-2 text-sm">
                    <div className="grid grid-cols-2 gap-2">
                      <span className="text-gray-600">Subject (sub):</span>
                      <span className="font-mono text-gray-900">{claims.sub}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <span className="text-gray-600">Emisor (iss):</span>
                      <span className="font-mono text-gray-900">{claims.iss}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <span className="text-gray-600">Audiencia (aud):</span>
                      <span className="font-mono text-gray-900 break-all">
                        {Array.isArray(claims.aud) ? claims.aud.join(', ') : claims.aud}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <span className="text-gray-600">Token ID (jti):</span>
                      <span className="font-mono text-xs text-gray-900 break-all">{claims.jti}</span>
                    </div>
                    <div className="border-t border-gray-200 my-2"></div>
                    <div className="grid grid-cols-2 gap-2">
                      <span className="text-gray-600">Expediente ID:</span>
                      <span className="font-mono text-gray-900">{claims.exp_id}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <span className="text-gray-600">Tipo:</span>
                      <span className="font-mono text-gray-900">{claims.exp_tipo}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <span className="text-gray-600">Tarea ID:</span>
                      <span className="font-mono text-gray-900">{claims.tarea_id}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <span className="text-gray-600">Tarea Nombre:</span>
                      <span className="font-mono text-gray-900">{claims.tarea_nombre}</span>
                    </div>
                    <div className="border-t border-gray-200 my-2"></div>
                    <div className="grid grid-cols-2 gap-2">
                      <span className="text-gray-600">Permisos:</span>
                      <span className="font-mono text-gray-900">{claims.permisos.join(', ')}</span>
                    </div>
                    <div className="border-t border-gray-200 my-2"></div>
                    <div className="grid grid-cols-2 gap-2">
                      <span className="text-gray-600">Emitido (iat):</span>
                      <span className="font-mono text-xs text-gray-900">{formatTimestamp(claims.iat)}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <span className="text-gray-600">Válido desde (nbf):</span>
                      <span className="font-mono text-xs text-gray-900">{formatTimestamp(claims.nbf)}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <span className="text-gray-600">Expira (exp):</span>
                      <span className="font-mono text-xs text-gray-900">{formatTimestamp(claims.exp)}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </Card>
  );
};
