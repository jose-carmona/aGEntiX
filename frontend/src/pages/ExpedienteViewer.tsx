// pages/ExpedienteViewer.tsx
// Visor de Expedientes y Documentos con renderizado de Markdown

import React, { useState, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import {
  checkMCPStatus,
  getExpedientes,
  getDocumentos,
  getDocumentoTexto,
  type ExpedienteResumen,
  type Documento
} from '@/services/expedientesService';

// ============================================================================
// Component
// ============================================================================

export const ExpedienteViewer: React.FC = () => {
  // Estado del servidor MCP
  const [mcpAvailable, setMcpAvailable] = useState<boolean | null>(null);
  const [isCheckingMCP, setIsCheckingMCP] = useState(true);

  // Estado de expedientes
  const [expedientes, setExpedientes] = useState<ExpedienteResumen[]>([]);
  const [selectedExpediente, setSelectedExpediente] = useState<ExpedienteResumen | null>(null);
  const [isLoadingExpedientes, setIsLoadingExpedientes] = useState(false);

  // Estado de documentos
  const [documentos, setDocumentos] = useState<Documento[]>([]);
  const [selectedDocumento, setSelectedDocumento] = useState<Documento | null>(null);
  const [isLoadingDocumentos, setIsLoadingDocumentos] = useState(false);

  // Estado del contenido markdown
  const [markdownContent, setMarkdownContent] = useState<string | null>(null);
  const [isLoadingContent, setIsLoadingContent] = useState(false);

  // Error general
  const [error, setError] = useState<string | null>(null);

  // ============================================================================
  // Effects
  // ============================================================================

  // Verificar MCP y cargar expedientes al montar
  useEffect(() => {
    initializeViewer();
  }, []);

  // ============================================================================
  // Handlers
  // ============================================================================

  const initializeViewer = async () => {
    setIsCheckingMCP(true);
    setError(null);

    try {
      // Verificar estado del MCP
      const status = await checkMCPStatus();
      setMcpAvailable(status.available);

      if (status.available) {
        // Cargar expedientes automáticamente
        await loadExpedientes();
      }
    } catch (err) {
      // Si falla el check, intentar cargar expedientes de todos modos
      // (el error podría ser de otra cosa)
      console.warn('Error checking MCP status:', err);
      setMcpAvailable(false);
    } finally {
      setIsCheckingMCP(false);
    }
  };

  const loadExpedientes = useCallback(async () => {
    setIsLoadingExpedientes(true);
    setError(null);

    try {
      const data = await getExpedientes();
      setExpedientes(data);
      setMcpAvailable(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error cargando expedientes';
      setError(message);
      setMcpAvailable(false);
    } finally {
      setIsLoadingExpedientes(false);
    }
  }, []);

  const handleSelectExpediente = async (expediente: ExpedienteResumen) => {
    setSelectedExpediente(expediente);
    setSelectedDocumento(null);
    setMarkdownContent(null);
    setIsLoadingDocumentos(true);
    setError(null);

    try {
      const docs = await getDocumentos(expediente.id);
      setDocumentos(docs);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error cargando documentos';
      setError(message);
      setDocumentos([]);
    } finally {
      setIsLoadingDocumentos(false);
    }
  };

  const handleSelectDocumento = async (documento: Documento) => {
    if (!selectedExpediente) return;

    setSelectedDocumento(documento);
    setIsLoadingContent(true);
    setError(null);

    try {
      const result = await getDocumentoTexto(selectedExpediente.id, documento.id);
      setMarkdownContent(result.texto_markdown || 'Sin contenido markdown disponible');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error cargando contenido';
      setError(message);
      setMarkdownContent(null);
    } finally {
      setIsLoadingContent(false);
    }
  };

  // ============================================================================
  // Render Helpers
  // ============================================================================

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getEstadoColor = (estado: string) => {
    switch (estado.toUpperCase()) {
      case 'EN_TRAMITE':
        return 'bg-blue-100 text-blue-800';
      case 'PENDIENTE_DOCUMENTACION':
        return 'bg-yellow-100 text-yellow-800';
      case 'ARCHIVADO':
        return 'bg-gray-100 text-gray-800';
      case 'COMPLETADO':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  const getTipoIcon = (tipo: string) => {
    switch (tipo.toUpperCase()) {
      case 'SOLICITUD':
        return '📝';
      case 'IDENTIFICACION':
        return '🪪';
      case 'BANCARIO':
        return '🏦';
      case 'PROYECTO':
        return '📐';
      case 'CERTIFICADO':
        return '📜';
      case 'INFORME':
        return '📊';
      default:
        return '📄';
    }
  };

  // ============================================================================
  // Render
  // ============================================================================

  // Estado: Verificando MCP
  if (isCheckingMCP) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Conectando con el servidor...</p>
        </div>
      </div>
    );
  }

  // Estado: MCP no disponible
  if (mcpAvailable === false && expedientes.length === 0) {
    return (
      <div className="p-6">
        <Card>
          <div className="text-center py-12">
            <div className="text-red-500 text-5xl mb-4">⚠️</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Servidor MCP no disponible
            </h2>
            <p className="text-gray-600 mb-4">
              El servidor MCP de expedientes no está respondiendo.
            </p>
            <p className="text-sm text-gray-500 mb-6">
              Ejecuta: <code className="bg-gray-100 px-2 py-1 rounded">./run-mcp.sh</code>
            </p>
            <Button onClick={initializeViewer}>
              Reintentar conexión
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // Estado: Visor completo
  return (
    <div className="p-6 h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">
            Visor de Expedientes
          </h1>
          <p className="text-gray-600 text-sm">
            Selecciona un expediente para ver sus documentos
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${mcpAvailable ? 'bg-green-500' : 'bg-red-500'}`}></span>
          <span className="text-sm text-gray-500">
            {mcpAvailable ? 'MCP Online' : 'MCP Offline'}
          </span>
        </div>
      </div>

      {/* Error global */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Layout de 3 paneles */}
      <div className="grid grid-cols-12 gap-4 h-[calc(100%-5rem)]">

        {/* Panel 1: Lista de Expedientes */}
        <div className="col-span-3 flex flex-col">
          <Card className="flex-1 flex flex-col overflow-hidden">
            <div className="flex-shrink-0 border-b border-gray-200 pb-3 mb-3">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-gray-900">
                  Expedientes
                  {expedientes.length > 0 && (
                    <span className="ml-2 text-sm font-normal text-gray-500">
                      ({expedientes.length})
                    </span>
                  )}
                </h2>
                <button
                  onClick={loadExpedientes}
                  disabled={isLoadingExpedientes}
                  className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
                  title="Recargar"
                >
                  <svg className={`w-4 h-4 ${isLoadingExpedientes ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto">
              {isLoadingExpedientes ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
                </div>
              ) : expedientes.length === 0 ? (
                <p className="text-gray-500 text-sm text-center py-8">
                  No hay expedientes disponibles
                </p>
              ) : (
                <div className="space-y-2">
                  {expedientes.map((exp) => (
                    <button
                      key={exp.id}
                      onClick={() => handleSelectExpediente(exp)}
                      className={`w-full text-left p-3 rounded-lg border transition-all ${
                        selectedExpediente?.id === exp.id
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="font-medium text-gray-900 text-sm">
                        {exp.id}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {exp.tipo.replace(/_/g, ' ')}
                      </div>
                      <div className="flex items-center justify-between mt-2">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${getEstadoColor(exp.estado)}`}>
                          {exp.estado.replace(/_/g, ' ')}
                        </span>
                        <span className="text-xs text-gray-400">
                          {formatDate(exp.fecha_inicio)}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Panel 2: Lista de Documentos */}
        <div className="col-span-3 flex flex-col">
          <Card className="flex-1 flex flex-col overflow-hidden">
            <div className="flex-shrink-0 border-b border-gray-200 pb-3 mb-3">
              <h2 className="font-semibold text-gray-900">
                Documentos
                {selectedExpediente && documentos.length > 0 && (
                  <span className="ml-2 text-sm font-normal text-gray-500">
                    ({documentos.length})
                  </span>
                )}
              </h2>
              {selectedExpediente && (
                <p className="text-xs text-gray-500 mt-1">
                  {selectedExpediente.id}
                </p>
              )}
            </div>

            <div className="flex-1 overflow-y-auto">
              {!selectedExpediente ? (
                <div className="flex flex-col items-center justify-center py-12 text-gray-400">
                  <span className="text-3xl mb-2">📂</span>
                  <p className="text-sm">Selecciona un expediente</p>
                </div>
              ) : isLoadingDocumentos ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
                </div>
              ) : documentos.length === 0 ? (
                <p className="text-gray-500 text-sm text-center py-8">
                  Sin documentos
                </p>
              ) : (
                <div className="space-y-2">
                  {documentos.map((doc) => (
                    <button
                      key={doc.id}
                      onClick={() => handleSelectDocumento(doc)}
                      className={`w-full text-left p-3 rounded-lg border transition-all ${
                        selectedDocumento?.id === doc.id
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        <span className="text-lg flex-shrink-0">
                          {getTipoIcon(doc.tipo)}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-gray-900 text-sm truncate">
                            {doc.nombre}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {doc.tipo} • {formatBytes(doc.tamano_bytes)}
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-gray-400">
                              {formatDate(doc.fecha)}
                            </span>
                            {doc.validado !== null && (
                              <span className={`text-xs ${doc.validado ? 'text-green-600' : 'text-orange-600'}`}>
                                {doc.validado ? '✓ Validado' : '○ Pendiente'}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Panel 3: Visor de Documento */}
        <div className="col-span-6 flex flex-col">
          <Card className="flex-1 flex flex-col overflow-hidden">
            <div className="flex-shrink-0 border-b border-gray-200 pb-3 mb-3">
              <h2 className="font-semibold text-gray-900">
                Contenido del Documento
              </h2>
              {selectedDocumento && (
                <p className="text-xs text-gray-500 mt-1">
                  {selectedDocumento.nombre}
                </p>
              )}
            </div>

            <div className="flex-1 overflow-y-auto">
              {!selectedDocumento ? (
                <div className="flex flex-col items-center justify-center py-12 text-gray-400">
                  <span className="text-4xl mb-3">📄</span>
                  <p className="text-sm">Selecciona un documento para ver su contenido</p>
                </div>
              ) : isLoadingContent ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                </div>
              ) : markdownContent ? (
                <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900 prose-table:text-sm">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {markdownContent}
                  </ReactMarkdown>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <p>No hay contenido disponible para este documento</p>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
