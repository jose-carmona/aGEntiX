// components/mcp/index.ts
// Exportaciones del módulo MCP

export { MCPServerStatus } from './MCPServerStatus';
export { MCPTokenGenerator, useTokenGenerator, EXPEDIENTES_PRUEBA, PERMISOS_DISPONIBLES } from './MCPTokenGenerator';
export type { TipoExpediente, TokenConfig, TokenResult } from './MCPTokenGenerator';
export { MCPTabs, MCP_TABS } from './MCPTabs';
export type { MCPTabId, MCPTab } from './MCPTabs';

// Panels
export { ExpedientesPanel } from './expedientes/ExpedientesPanel';
export { DocumentacionPanel } from './documentacion/DocumentacionPanel';
export { ExplorerPanel } from './explorer/ExplorerPanel';
