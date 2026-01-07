// components/mcp/documentacion/DocumentacionPanel.tsx
// Panel de pruebas para el módulo de Documentación

import React, { useState, useCallback, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { TipoExpediente } from '../MCPTokenGenerator';
import { callTool, parseToolContent } from '@/services/mcpService';

// Tipos de expediente para documentación
const TIPOS_EXPEDIENTE: { id: TipoExpediente; label: string; description: string }[] = [
  { id: 'subvenciones', label: 'Subvenciones', description: 'Gestión de solicitudes de ayudas y subvenciones' },
  { id: 'licencias_obras', label: 'Licencias de Obras', description: 'Tramitación de licencias urbanísticas' },
  { id: 'certificado_empadronamiento', label: 'Certificado Empadronamiento', description: 'Emisión de certificados de residencia' },
];

interface DocumentoInfo {
  id: string;
  tipo: string;
  subtipo?: string;
  descripcion: string;
}

interface SearchResult {
  documento_id: string;
  tipo: string;
  coincidencias: Array<{
    linea: number;
    contexto: string;
  }>;
}

interface DocumentacionPanelProps {
  token: string | null;
}

export const DocumentacionPanel: React.FC<DocumentacionPanelProps> = ({ token }) => {
  const [tipoExpediente, setTipoExpediente] = useState<TipoExpediente>('subvenciones');
  const [documentos, setDocumentos] = useState<DocumentoInfo[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null);
  const [docContent, setDocContent] = useState<{
    contenido: string;
    instrucciones_agente: string;
    descripcion: string;
  } | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Cargar lista de documentos al cambiar tipo de expediente
  useEffect(() => {
    if (token) {
      loadDocumentos();
    }
  }, [tipoExpediente, token]);

  const loadDocumentos = async () => {
    if (!token) return;

    setIsLoading(true);
    setError(null);
    setDocumentos([]);
    setSelectedDoc(null);
    setDocContent(null);

    try {
      const result = await callTool(token, 'listar_documentacion', {
        tipo_expediente: tipoExpediente
      });
      const parsed = parseToolContent(result) as { documentos: DocumentoInfo[] };
      setDocumentos(parsed.documentos || []);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error cargando documentación';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const loadDocumento = useCallback(async (tipoDocumento: string) => {
    if (!token) return;

    setIsLoading(true);
    setError(null);
    setSelectedDoc(tipoDocumento);

    try {
      const result = await callTool(token, 'obtener_doc_documentacion', {
        tipo_expediente: tipoExpediente,
        tipo_documento: tipoDocumento
      });
      const parsed = parseToolContent(result) as {
        contenido: string;
        instrucciones_agente: string;
        descripcion: string;
      };
      setDocContent(parsed);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error cargando documento';
      setError(message);
      setDocContent(null);
    } finally {
      setIsLoading(false);
    }
  }, [token, tipoExpediente]);

  const handleSearch = async () => {
    if (!token || !searchQuery.trim()) return;

    setIsLoading(true);
    setError(null);
    setSearchResults([]);

    try {
      const result = await callTool(token, 'buscar_en_documentacion', {
        tipo_expediente: tipoExpediente,
        query: searchQuery
      });
      const parsed = parseToolContent(result) as { resultados: SearchResult[] };
      setSearchResults(parsed.resultados || []);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error en búsqueda';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const tipoSeleccionado = TIPOS_EXPEDIENTE.find(t => t.id === tipoExpediente);

  return (
    <div className="space-y-6">
      {/* Selector de Tipo de Expediente */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Documentación</h2>
          {!token && (
            <span className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
              Genera un token primero
            </span>
          )}
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tipo de Expediente
            </label>
            <select
              value={tipoExpediente}
              onChange={(e) => setTipoExpediente(e.target.value as TipoExpediente)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              disabled={!token || isLoading}
            >
              {TIPOS_EXPEDIENTE.map(tipo => (
                <option key={tipo.id} value={tipo.id}>
                  {tipo.label}
                </option>
              ))}
            </select>
            {tipoSeleccionado && (
              <p className="text-xs text-gray-500 mt-1">{tipoSeleccionado.description}</p>
            )}
          </div>
        </div>
      </Card>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Layout de 2 columnas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lista de Documentos */}
        <Card className="lg:col-span-1">
          <h3 className="text-md font-semibold text-gray-900 mb-3">
            Documentos Disponibles
            {documentos.length > 0 && (
              <span className="ml-2 text-xs font-normal text-gray-500">
                ({documentos.length})
              </span>
            )}
          </h3>

          {isLoading && documentos.length === 0 ? (
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Cargando...
            </div>
          ) : documentos.length === 0 ? (
            <p className="text-gray-500 text-sm">
              {token ? 'No hay documentos disponibles' : 'Genera un token para ver documentos'}
            </p>
          ) : (
            <div className="space-y-2">
              {documentos.map(doc => {
                // Extraer tipo de documento del ID para usar como key de carga
                const tipoDoc = doc.tipo === 'plantilla' && doc.subtipo
                  ? `plantilla_${doc.subtipo}`
                  : doc.tipo;

                return (
                  <button
                    key={doc.id}
                    onClick={() => loadDocumento(tipoDoc)}
                    disabled={isLoading}
                    className={`
                      w-full text-left p-3 rounded-lg border transition-colors
                      ${selectedDoc === tipoDoc
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }
                    `}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${selectedDoc === tipoDoc ? 'bg-primary-500' : 'bg-gray-300'}`} />
                      <span className="font-medium text-sm text-gray-900">{doc.id}</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1 ml-4">{doc.tipo}</p>
                    <p className="text-xs text-gray-600 mt-1 ml-4 line-clamp-2">{doc.descripcion}</p>
                  </button>
                );
              })}
            </div>
          )}
        </Card>

        {/* Contenido del Documento */}
        <Card className="lg:col-span-2">
          <h3 className="text-md font-semibold text-gray-900 mb-3">
            Contenido del Documento
          </h3>

          {isLoading && selectedDoc ? (
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Cargando documento...
            </div>
          ) : docContent ? (
            <div className="space-y-4">
              {/* Instrucciones para el Agente */}
              {docContent.instrucciones_agente && (
                <div className="bg-amber-50 border-l-4 border-amber-400 p-4 rounded-r">
                  <h4 className="text-sm font-semibold text-amber-800 mb-1">
                    Instrucciones para el Agente
                  </h4>
                  <p className="text-sm text-amber-700">{docContent.instrucciones_agente}</p>
                </div>
              )}

              {/* Contenido Markdown */}
              <div className="bg-white rounded-lg p-4 max-h-96 overflow-auto prose prose-sm max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ children }) => <h1 className="text-xl font-bold text-gray-900 border-b pb-2 mb-4">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-lg font-semibold text-gray-800 border-b pb-1 mb-3 mt-4">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-md font-semibold text-gray-700 mb-2 mt-3">{children}</h3>,
                    p: ({ children }) => <p className="text-sm text-gray-700 mb-2 leading-relaxed">{children}</p>,
                    ul: ({ children }) => <ul className="list-disc list-inside text-sm text-gray-700 mb-2 space-y-1">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal list-inside text-sm text-gray-700 mb-2 space-y-1">{children}</ol>,
                    li: ({ children }) => <li className="text-sm text-gray-700">{children}</li>,
                    strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
                    code: ({ children }) => <code className="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono text-gray-800">{children}</code>,
                    pre: ({ children }) => <pre className="bg-gray-900 text-green-400 p-3 rounded text-xs overflow-auto font-mono my-2">{children}</pre>,
                    table: ({ children }) => <table className="min-w-full border-collapse border border-gray-300 my-2">{children}</table>,
                    th: ({ children }) => <th className="border border-gray-300 bg-gray-100 px-3 py-2 text-left text-sm font-semibold">{children}</th>,
                    td: ({ children }) => <td className="border border-gray-300 px-3 py-2 text-sm">{children}</td>,
                    blockquote: ({ children }) => <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-600 my-2">{children}</blockquote>,
                  }}
                >
                  {docContent.contenido}
                </ReactMarkdown>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-sm">
              Selecciona un documento de la lista para ver su contenido
            </p>
          )}
        </Card>
      </div>

      {/* Búsqueda en Documentación */}
      <Card>
        <h3 className="text-md font-semibold text-gray-900 mb-3">
          Buscar en Documentación
        </h3>

        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Buscar texto en documentación..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            disabled={!token || isLoading}
          />
          <Button
            onClick={handleSearch}
            disabled={!token || isLoading || !searchQuery.trim()}
          >
            Buscar
          </Button>
        </div>

        {/* Resultados de búsqueda */}
        {searchResults.length > 0 && (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">
              {searchResults.reduce((acc, r) => acc + r.coincidencias.length, 0)} coincidencias encontradas
            </p>
            {searchResults.map((result, idx) => (
              <div key={idx} className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm font-medium text-gray-900">{result.documento_id}</span>
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                    {result.tipo}
                  </span>
                </div>
                <div className="space-y-2">
                  {result.coincidencias.map((match, matchIdx) => (
                    <div key={matchIdx} className="bg-gray-50 rounded p-2">
                      <span className="text-xs text-gray-500">Línea {match.linea}:</span>
                      <p className="text-sm text-gray-700 mt-1">{match.contexto}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};
