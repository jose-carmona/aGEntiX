// components/mcp/explorer/ExplorerPanel.tsx
// Panel explorador interactivo de tools y resources MCP

import React, { useState, useEffect, useCallback } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import {
  listTools,
  listResources,
  callTool,
  readResource,
  parseToolContent,
  parseResourceContent,
  type MCPTool,
  type MCPResource
} from '@/services/mcpService';

interface ExplorerPanelProps {
  token: string | null;
}

// Agrupar tools por módulo
const groupToolsByModule = (tools: MCPTool[]) => {
  const docTools = ['listar_documentacion', 'obtener_doc_documentacion', 'buscar_en_documentacion'];
  return {
    expedientes: tools.filter(t => !docTools.includes(t.name)),
    documentacion: tools.filter(t => docTools.includes(t.name))
  };
};

// Agrupar resources por tipo
const groupResourcesByType = (resources: MCPResource[]) => {
  return {
    expedientes: resources.filter(r => r.uri.startsWith('expediente://')),
    documentacion: resources.filter(r => r.uri.startsWith('documentacion://'))
  };
};

export const ExplorerPanel: React.FC<ExplorerPanelProps> = ({ token }) => {
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [resources, setResources] = useState<MCPResource[]>([]);
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
  const [selectedResource, setSelectedResource] = useState<MCPResource | null>(null);
  const [toolArgs, setToolArgs] = useState<Record<string, string>>({});
  const [result, setResult] = useState<unknown>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<'tools' | 'resources'>('tools');

  // Cargar tools y resources al tener token
  useEffect(() => {
    if (token) {
      loadToolsAndResources();
    }
  }, [token]);

  const loadToolsAndResources = async () => {
    if (!token) return;

    setIsLoading(true);
    setError(null);

    try {
      const [toolsData, resourcesData] = await Promise.all([
        listTools(token),
        listResources(token)
      ]);
      setTools(toolsData);
      setResources(resourcesData);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error cargando datos';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectTool = useCallback((tool: MCPTool) => {
    setSelectedTool(tool);
    setSelectedResource(null);
    setToolArgs({});
    setResult(null);
    setError(null);
  }, []);

  const handleSelectResource = useCallback((resource: MCPResource) => {
    setSelectedResource(resource);
    setSelectedTool(null);
    setResult(null);
    setError(null);
  }, []);

  const handleExecuteTool = async () => {
    if (!token || !selectedTool) return;

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      // Convertir strings a tipos correctos según schema
      const processedArgs: Record<string, unknown> = {};
      Object.entries(toolArgs).forEach(([key, value]) => {
        if (value === '') return;
        // Intentar parsear como JSON para objetos/arrays
        try {
          processedArgs[key] = JSON.parse(value);
        } catch {
          processedArgs[key] = value;
        }
      });

      const response = await callTool(token, selectedTool.name, processedArgs);
      setResult(parseToolContent(response));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error ejecutando tool';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReadResource = async () => {
    if (!token || !selectedResource) return;

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await readResource(token, selectedResource.uri);
      setResult(parseResourceContent(response));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error leyendo resource';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const groupedTools = groupToolsByModule(tools);
  const groupedResources = groupResourcesByType(resources);

  // Extraer propiedades del schema de la tool seleccionada
  const getToolProperties = (): { name: string; schema: Record<string, unknown> }[] => {
    if (!selectedTool?.inputSchema) return [];
    const schema = selectedTool.inputSchema as { properties?: Record<string, Record<string, unknown>> };
    if (!schema.properties) return [];
    return Object.entries(schema.properties).map(([name, propSchema]) => ({
      name,
      schema: propSchema
    }));
  };

  const renderJsonContent = (data: unknown): React.ReactNode => (
    <pre className="bg-gray-900 text-green-400 p-3 rounded text-xs overflow-auto font-mono max-h-96">
      {JSON.stringify(data, null, 2)}
    </pre>
  );

  return (
    <div className="space-y-6">
      {/* Header con toggle */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Explorador Interactivo</h2>
          {!token && (
            <span className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
              Genera un token primero
            </span>
          )}
        </div>

        {/* Toggle Tools/Resources */}
        <div className="flex gap-2">
          <button
            onClick={() => setActiveSection('tools')}
            className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
              activeSection === 'tools'
                ? 'bg-primary-100 text-primary-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Tools ({tools.length})
          </button>
          <button
            onClick={() => setActiveSection('resources')}
            className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
              activeSection === 'resources'
                ? 'bg-primary-100 text-primary-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Resources ({resources.length})
          </button>
        </div>
      </Card>

      {/* Error global */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Layout principal */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lista de Tools/Resources */}
        <Card className="lg:col-span-1 max-h-[600px] overflow-auto">
          {activeSection === 'tools' ? (
            <div className="space-y-4">
              {/* Expedientes Tools */}
              <div>
                <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                  Expedientes ({groupedTools.expedientes.length})
                </h4>
                <div className="space-y-1">
                  {groupedTools.expedientes.map(tool => (
                    <button
                      key={tool.name}
                      onClick={() => handleSelectTool(tool)}
                      className={`w-full text-left p-2 rounded text-sm transition-colors ${
                        selectedTool?.name === tool.name
                          ? 'bg-primary-100 text-primary-700'
                          : 'hover:bg-gray-100'
                      }`}
                    >
                      <span className="font-mono text-xs">{tool.name}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Documentación Tools */}
              <div>
                <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                  Documentación ({groupedTools.documentacion.length})
                </h4>
                <div className="space-y-1">
                  {groupedTools.documentacion.map(tool => (
                    <button
                      key={tool.name}
                      onClick={() => handleSelectTool(tool)}
                      className={`w-full text-left p-2 rounded text-sm transition-colors ${
                        selectedTool?.name === tool.name
                          ? 'bg-primary-100 text-primary-700'
                          : 'hover:bg-gray-100'
                      }`}
                    >
                      <span className="font-mono text-xs">{tool.name}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Expedientes Resources */}
              <div>
                <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                  Expedientes ({groupedResources.expedientes.length})
                </h4>
                <div className="space-y-1">
                  {groupedResources.expedientes.map(resource => (
                    <button
                      key={resource.uri}
                      onClick={() => handleSelectResource(resource)}
                      className={`w-full text-left p-2 rounded text-sm transition-colors ${
                        selectedResource?.uri === resource.uri
                          ? 'bg-primary-100 text-primary-700'
                          : 'hover:bg-gray-100'
                      }`}
                    >
                      <span className="font-mono text-xs break-all">{resource.uri}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Documentación Resources */}
              <div>
                <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                  Documentación ({groupedResources.documentacion.length})
                </h4>
                <div className="space-y-1">
                  {groupedResources.documentacion.map(resource => (
                    <button
                      key={resource.uri}
                      onClick={() => handleSelectResource(resource)}
                      className={`w-full text-left p-2 rounded text-sm transition-colors ${
                        selectedResource?.uri === resource.uri
                          ? 'bg-primary-100 text-primary-700'
                          : 'hover:bg-gray-100'
                      }`}
                    >
                      <span className="font-mono text-xs break-all">{resource.uri}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </Card>

        {/* Panel de Ejecución */}
        <Card className="lg:col-span-2">
          {selectedTool ? (
            <div className="space-y-4">
              <div>
                <h3 className="text-md font-semibold text-gray-900">{selectedTool.name}</h3>
                <p className="text-sm text-gray-600 mt-1">{selectedTool.description}</p>
              </div>

              {/* Formulario dinámico */}
              <div className="space-y-3">
                {getToolProperties().map(({ name, schema }) => (
                  <div key={name}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {name}
                      {(() => {
                        const inputSchema = selectedTool.inputSchema as Record<string, unknown> | undefined;
                        const required = inputSchema?.required;
                        if (Array.isArray(required) && required.includes(name)) {
                          return <span className="text-red-500 ml-1">*</span>;
                        }
                        return null;
                      })()}
                    </label>

                    {/* Formulario dinámico según tipo */}
                    {(() => {
                      const enumValues = schema.enum;
                      const schemaType = schema.type;
                      const description = schema.description as string | undefined;

                      if (Array.isArray(enumValues)) {
                        return (
                          <select
                            value={toolArgs[name] || ''}
                            onChange={(e) => setToolArgs(prev => ({ ...prev, [name]: e.target.value }))}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                            disabled={isLoading}
                          >
                            <option value="">Seleccionar...</option>
                            {enumValues.map((opt: unknown) => (
                              <option key={String(opt)} value={String(opt)}>{String(opt)}</option>
                            ))}
                          </select>
                        );
                      }

                      if (schemaType === 'boolean') {
                        return (
                          <select
                            value={toolArgs[name] || ''}
                            onChange={(e) => setToolArgs(prev => ({ ...prev, [name]: e.target.value }))}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                            disabled={isLoading}
                          >
                            <option value="">Seleccionar...</option>
                            <option value="true">true</option>
                            <option value="false">false</option>
                          </select>
                        );
                      }

                      if (schemaType === 'object') {
                        return (
                          <textarea
                            value={toolArgs[name] || ''}
                            onChange={(e) => setToolArgs(prev => ({ ...prev, [name]: e.target.value }))}
                            placeholder='{"key": "value"}'
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm font-mono"
                            rows={3}
                            disabled={isLoading}
                          />
                        );
                      }

                      return (
                        <input
                          type="text"
                          value={toolArgs[name] || ''}
                          onChange={(e) => setToolArgs(prev => ({ ...prev, [name]: e.target.value }))}
                          placeholder={description || name}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                          disabled={isLoading}
                        />
                      );
                    })()}

                    {typeof schema.description === 'string' && (
                      <p className="text-xs text-gray-500 mt-1">{schema.description}</p>
                    )}
                  </div>
                ))}
              </div>

              <Button
                onClick={handleExecuteTool}
                disabled={!token || isLoading}
                className="w-full"
              >
                {isLoading ? 'Ejecutando...' : 'Ejecutar Tool'}
              </Button>
            </div>
          ) : selectedResource ? (
            <div className="space-y-4">
              <div>
                <h3 className="text-md font-semibold text-gray-900 font-mono">{selectedResource.uri}</h3>
                {selectedResource.description && (
                  <p className="text-sm text-gray-600 mt-1">{selectedResource.description}</p>
                )}
                {selectedResource.mimeType && (
                  <p className="text-xs text-gray-500 mt-1">MIME: {selectedResource.mimeType}</p>
                )}
              </div>

              <Button
                onClick={handleReadResource}
                disabled={!token || isLoading}
                className="w-full"
              >
                {isLoading ? 'Leyendo...' : 'Leer Resource'}
              </Button>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>Selecciona una tool o resource de la lista</p>
            </div>
          )}

          {/* Resultado */}
          {result ? (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Resultado:</h4>
              {renderJsonContent(result)}
            </div>
          ) : null}
        </Card>
      </div>
    </div>
  );
};
