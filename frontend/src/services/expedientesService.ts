// services/expedientesService.ts
// Servicio para acceso a expedientes y documentos via API REST

import { api } from './api';

// ============================================================================
// Types
// ============================================================================

export interface ExpedienteResumen {
  id: string;
  tipo: string;
  estado: string;
  fecha_inicio: string;
}

export interface Expediente extends ExpedienteResumen {
  datos?: Record<string, unknown>;
  documentos?: Documento[];
  historial?: HistorialEntry[];
  metadatos?: Record<string, unknown>;
}

export interface Documento {
  id: string;
  nombre: string;
  tipo: string;
  fecha: string;
  validado: boolean | null;
  tamano_bytes: number;
  ruta?: string;
  hash_sha256?: string;
  metadatos_extraidos?: Record<string, unknown>;
  texto_markdown?: string;
}

export interface HistorialEntry {
  id: string;
  fecha: string;
  usuario: string;
  tipo: string;
  accion: string;
  detalles: string;
}

export interface DocumentoTexto {
  documento_id: string;
  texto_markdown: string | null;
}

export interface DocumentoMetadatos {
  documento_id: string;
  metadatos_extraidos: Record<string, unknown> | null;
}

export interface MCPStatus {
  available: boolean;
  message: string;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Verifica el estado del servidor MCP
 */
export const checkMCPStatus = async (): Promise<MCPStatus> => {
  const response = await api.get<MCPStatus>('/api/v1/expedientes/mcp-status');
  return response.data;
};

/**
 * Obtiene la lista de todos los expedientes
 */
export const getExpedientes = async (): Promise<ExpedienteResumen[]> => {
  const response = await api.get<ExpedienteResumen[]>('/api/v1/expedientes/');
  return response.data;
};

/**
 * Obtiene los datos completos de un expediente
 */
export const getExpediente = async (expedienteId: string): Promise<Expediente> => {
  const response = await api.get<Expediente>(`/api/v1/expedientes/${expedienteId}`);
  return response.data;
};

/**
 * Obtiene la lista de documentos de un expediente
 */
export const getDocumentos = async (expedienteId: string): Promise<Documento[]> => {
  const response = await api.get<Documento[]>(`/api/v1/expedientes/${expedienteId}/documentos`);
  return response.data;
};

/**
 * Obtiene el texto markdown de un documento
 */
export const getDocumentoTexto = async (
  expedienteId: string,
  documentoId: string
): Promise<DocumentoTexto> => {
  const response = await api.get<DocumentoTexto>(
    `/api/v1/expedientes/${expedienteId}/documentos/${documentoId}/texto`
  );
  return response.data;
};

/**
 * Obtiene los metadatos extraídos de un documento
 */
export const getDocumentoMetadatos = async (
  expedienteId: string,
  documentoId: string
): Promise<DocumentoMetadatos> => {
  const response = await api.get<DocumentoMetadatos>(
    `/api/v1/expedientes/${expedienteId}/documentos/${documentoId}/metadatos`
  );
  return response.data;
};
