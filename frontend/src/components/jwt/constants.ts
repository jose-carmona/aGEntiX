// components/jwt/constants.ts
// Constantes compartidas para configuración JWT

// Tipos de expediente disponibles
export type TipoExpediente = 'subvenciones' | 'licencias_obras' | 'certificado_empadronamiento';

// Expedientes de prueba disponibles
export interface ExpedientePrueba {
  id: string;
  tipo: TipoExpediente;
  label: string;
}

export const EXPEDIENTES_PRUEBA: readonly ExpedientePrueba[] = [
  { id: 'EXP-2024-001', tipo: 'subvenciones', label: 'Subvención Asociación Cultural' },
  { id: 'EXP-2024-002', tipo: 'licencias_obras', label: 'Licencia Obra Menor' },
  { id: 'EXP-2024-003', tipo: 'certificado_empadronamiento', label: 'Certificado Empadronamiento' },
] as const;

// Módulos de permisos
export type ModuloPermiso = 'expedientes' | 'documentacion';

// Definición de un permiso
export interface PermisoDefinition {
  id: string;
  label: string;
  modulo: ModuloPermiso;
  description: string;
}

// Permisos disponibles (fuente única de verdad)
export const PERMISOS_DISPONIBLES: readonly PermisoDefinition[] = [
  { id: 'consulta', label: 'Consulta', modulo: 'expedientes', description: 'Lectura de expedientes y documentos' },
  { id: 'gestion', label: 'Gestión', modulo: 'expedientes', description: 'Escritura en expedientes' },
  { id: 'documentacion:leer', label: 'Leer Documentación', modulo: 'documentacion', description: 'Listar y obtener documentación' },
  { id: 'documentacion:buscar', label: 'Buscar', modulo: 'documentacion', description: 'Búsqueda en documentación' },
] as const;

// Permisos por defecto (todos activos)
export const DEFAULT_PERMISOS: readonly string[] = [
  'consulta',
  'gestion',
  'documentacion:leer',
  'documentacion:buscar'
] as const;

// Configuración JWT
export interface JWTConfig {
  expedienteId: string;
  tareaId: string;
  permisos: string[];
}

// Resultado de generación de token
export interface TokenResult {
  token: string;
  claims: Record<string, unknown>;
}

// Helpers
export const getExpedienteTipo = (expedienteId: string): TipoExpediente | undefined => {
  return EXPEDIENTES_PRUEBA.find(e => e.id === expedienteId)?.tipo;
};

export const getPermisosByModulo = (modulo: ModuloPermiso): PermisoDefinition[] => {
  return PERMISOS_DISPONIBLES.filter(p => p.modulo === modulo);
};
