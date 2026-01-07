// components/jwt/index.ts
// Exportaciones del módulo JWT

// Componentes
export { JWTConfigCard, useJWTGenerator } from './JWTConfigCard';
export type { JWTConfigCardProps } from './JWTConfigCard';

export { ExpedienteSelector } from './ExpedienteSelector';
export { PermisosSelector } from './PermisosSelector';
export { TokenClaimsDisplay } from './TokenClaimsDisplay';

// Constantes y tipos
export {
  EXPEDIENTES_PRUEBA,
  PERMISOS_DISPONIBLES,
  DEFAULT_PERMISOS,
  getExpedienteTipo,
  getPermisosByModulo
} from './constants';

export type {
  TipoExpediente,
  ExpedientePrueba,
  ModuloPermiso,
  PermisoDefinition,
  JWTConfig,
  TokenResult
} from './constants';
