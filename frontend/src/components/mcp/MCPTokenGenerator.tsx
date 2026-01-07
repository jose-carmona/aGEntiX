// components/mcp/MCPTokenGenerator.tsx
// Generador de tokens JWT para el panel MCP
// Wrapper sobre JWTConfigCard para mantener compatibilidad

import React from 'react';
import {
  JWTConfigCard,
  useJWTGenerator,
  // Re-exportar tipos y constantes para compatibilidad
  EXPEDIENTES_PRUEBA,
  PERMISOS_DISPONIBLES,
  DEFAULT_PERMISOS,
  type TipoExpediente,
  type TokenResult,
  type JWTConfig
} from '@/components/jwt';

// Re-exportar para compatibilidad con código existente
export { EXPEDIENTES_PRUEBA, PERMISOS_DISPONIBLES, DEFAULT_PERMISOS };
export type { TipoExpediente, TokenResult };

// Mantener TokenConfig como alias de JWTConfig para compatibilidad
export type TokenConfig = JWTConfig;

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
  return (
    <JWTConfigCard
      mode="standalone"
      title="Configuración del Token JWT"
      expedienteMode="select"
      permisosLayout={compact ? 'compact' : 'grid'}
      showTareaId={false}
      showClaimsPreview={true}
      showGenerateButton={true}
      generateButtonText="Generar Token"
      onTokenGenerated={onTokenGenerated}
      disabled={disabled}
    />
  );
};

// Re-exportar hook con nombre original para compatibilidad
export const useTokenGenerator = useJWTGenerator;
