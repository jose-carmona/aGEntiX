import { LogEntry, LogLevel, LogComponent, AgentType } from '../types/logs';

// Mensajes de ejemplo para cada tipo de log
const LOG_MESSAGES = {
  INFO: [
    'Ejecución de agente iniciada correctamente',
    'Conexión establecida con servidor MCP',
    'Documento procesado exitosamente',
    'Token JWT validado correctamente',
    'Respuesta webhook enviada',
    'Herramienta MCP ejecutada correctamente',
    'Cache actualizado',
    'Sesión de usuario iniciada',
  ],
  WARNING: [
    'Timeout en llamada a MCP, reintentando...',
    'Campo opcional no encontrado en documento',
    'Rate limit próximo al límite',
    'Memoria del sistema al 85%',
    'Conexión lenta detectada',
    'Formato de fecha no estándar detectado',
  ],
  ERROR: [
    'Error al conectar con servidor MCP',
    'Token JWT expirado',
    'Documento no encontrado',
    'Validación de esquema fallida',
    'Error al redactar PII',
    'Timeout en ejecución de agente',
    'Error de permisos insuficientes',
  ],
  CRITICAL: [
    'Fallo total del sistema MCP',
    'Pérdida de conexión con base de datos',
    'Error irrecuperable en AgentExecutor',
    'Violación de seguridad detectada',
  ],
  DEBUG: [
    'Request headers: {...}',
    'Payload received: {...}',
    'Internal state: {...}',
    'Cache hit for key: ...',
  ],
};

const COMPONENTS: LogComponent[] = [
  'AgentExecutor',
  'MCPClient',
  'PIIRedactor',
  'AuditLogger',
  'JWTValidator',
  'APIServer',
  'WebhookService',
  'TaskTracker',
];

const AGENTS: AgentType[] = [
  'ValidadorDocumental',
  'AnalizadorSubvencion',
  'GeneradorInforme',
];

const EXPEDIENTES = [
  'EXP-2024-001',
  'EXP-2024-002',
  'EXP-2024-003',
  'EXP-2024-127',
  'EXP-2024-450',
  'EXP-2024-891',
];

// Genera un log aleatorio
function generateRandomLog(index: number, baseTime: Date): LogEntry {
  const levels: LogLevel[] = ['INFO', 'WARNING', 'ERROR', 'CRITICAL', 'DEBUG'];
  const level = levels[Math.floor(Math.random() * levels.length)];
  const component = COMPONENTS[Math.floor(Math.random() * COMPONENTS.length)];
  const messages = LOG_MESSAGES[level];
  const message = messages[Math.floor(Math.random() * messages.length)];

  // Timestamp: logs más recientes tienen timestamps más recientes
  const timestamp = new Date(baseTime.getTime() - index * 1000 * Math.random() * 10);

  const log: LogEntry = {
    id: `log-${timestamp.getTime()}-${index}`,
    timestamp: timestamp.toISOString(),
    level,
    component,
    message,
  };

  // 50% de probabilidad de tener agente
  if (Math.random() > 0.5) {
    log.agent = AGENTS[Math.floor(Math.random() * AGENTS.length)];
  }

  // 70% de probabilidad de tener expediente_id
  if (Math.random() > 0.3) {
    log.expediente_id = EXPEDIENTES[Math.floor(Math.random() * EXPEDIENTES.length)];
  }

  // 30% de probabilidad de tener contexto
  if (Math.random() > 0.7) {
    log.context = {
      request_id: `req-${Math.random().toString(36).substr(2, 9)}`,
      user_agent: 'aGEntiX-API/1.0',
      ip_address: `192.168.1.${Math.floor(Math.random() * 255)}`,
    };
  }

  // 20% de probabilidad de tener agent_run_id
  if (Math.random() > 0.8) {
    log.agent_run_id = `run-${Math.random().toString(36).substr(2, 9)}`;
  }

  // 40% de probabilidad de tener duration_ms
  if (Math.random() > 0.6) {
    log.duration_ms = Math.floor(Math.random() * 5000);
  }

  // Si es ERROR o CRITICAL, 80% de probabilidad de tener error details
  if ((level === 'ERROR' || level === 'CRITICAL') && Math.random() > 0.2) {
    log.error = {
      type: 'MCPConnectionError',
      message: 'Failed to connect to MCP server',
      stacktrace:
        '  File "src/backoffice/mcp/client.py", line 123, in connect\n    raise MCPConnectionError()\n',
    };
  }

  // Resaltar PII redactado en algunos mensajes
  if (Math.random() > 0.7) {
    log.message = log.message + ' - DNI: [DNI-REDACTED], Email: [EMAIL-REDACTED]';
  }

  return log;
}

// Genera un conjunto de logs mock
export function generateMockLogs(count: number): LogEntry[] {
  const now = new Date();
  const logs: LogEntry[] = [];

  for (let i = 0; i < count; i++) {
    logs.push(generateRandomLog(i, now));
  }

  // Ordenar por timestamp descendente (más reciente primero)
  logs.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  return logs;
}

// Dataset estático para desarrollo consistente
export const mockLogs: LogEntry[] = [
  {
    id: 'log-001',
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(), // hace 5 min
    level: 'INFO',
    component: 'AgentExecutor',
    agent: 'ValidadorDocumental',
    expediente_id: 'EXP-2024-001',
    message: 'Ejecución de agente ValidadorDocumental iniciada para EXP-2024-001',
    agent_run_id: 'run-abc123',
    context: {
      user_id: 'user-001',
      permissions: ['leer_expediente', 'leer_documentos'],
    },
  },
  {
    id: 'log-002',
    timestamp: new Date(Date.now() - 1000 * 60 * 4).toISOString(), // hace 4 min
    level: 'INFO',
    component: 'MCPClient',
    message: 'Conectado a servidor MCP expedientes',
    context: {
      server_url: 'http://localhost:8000',
      server_id: 'mcp-expedientes',
    },
  },
  {
    id: 'log-003',
    timestamp: new Date(Date.now() - 1000 * 60 * 3).toISOString(), // hace 3 min
    level: 'WARNING',
    component: 'PIIRedactor',
    expediente_id: 'EXP-2024-001',
    message: 'PII detectado y redactado en logs: DNI: [DNI-REDACTED], Email: [EMAIL-REDACTED]',
    context: {
      pii_types_found: ['DNI', 'EMAIL'],
      original_message_length: 256,
      redacted_message_length: 198,
    },
  },
  {
    id: 'log-004',
    timestamp: new Date(Date.now() - 1000 * 60 * 2).toISOString(), // hace 2 min
    level: 'ERROR',
    component: 'MCPClient',
    agent: 'ValidadorDocumental',
    expediente_id: 'EXP-2024-001',
    message: 'Error al ejecutar herramienta MCP: validar_documentos',
    agent_run_id: 'run-abc123',
    duration_ms: 5234,
    error: {
      type: 'MCPToolError',
      message: 'Tool execution failed: Connection timeout',
      stacktrace:
        '  File "src/backoffice/mcp/client.py", line 187, in call_tool\n    response = await self._request(...)\nTimeoutError: Request timed out after 5s',
    },
  },
  {
    id: 'log-005',
    timestamp: new Date(Date.now() - 1000 * 60 * 1).toISOString(), // hace 1 min
    level: 'INFO',
    component: 'AgentExecutor',
    agent: 'ValidadorDocumental',
    expediente_id: 'EXP-2024-001',
    message: 'Ejecución completada con errores recuperables',
    agent_run_id: 'run-abc123',
    duration_ms: 12456,
    context: {
      status: 'completed_with_warnings',
      warnings: 1,
      errors: 1,
    },
  },
  {
    id: 'log-006',
    timestamp: new Date(Date.now() - 1000 * 30).toISOString(), // hace 30 seg
    level: 'CRITICAL',
    component: 'APIServer',
    message: 'Fallo total del sistema MCP - Todos los servidores inaccesibles',
    error: {
      type: 'SystemFailure',
      message: 'All MCP servers are down',
      stacktrace: '  No servers responding to health checks',
    },
  },
  {
    id: 'log-007',
    timestamp: new Date(Date.now() - 1000 * 15).toISOString(), // hace 15 seg
    level: 'INFO',
    component: 'JWTValidator',
    message: 'Token JWT validado correctamente - Teléfono: [TELEFONO_MOVIL-REDACTED]',
    context: {
      issuer: 'agentix-bpmn',
      subject: 'Automático',
      audience: 'agentix-mcp-expedientes',
    },
  },
  {
    id: 'log-008',
    timestamp: new Date(Date.now() - 1000 * 5).toISOString(), // hace 5 seg
    level: 'DEBUG',
    component: 'TaskTracker',
    message: 'Task status updated: run-xyz789 -> completed',
    agent_run_id: 'run-xyz789',
    context: {
      previous_status: 'running',
      new_status: 'completed',
      execution_time_ms: 3421,
    },
  },
];

// Generar dataset grande para testing de performance
export const largeMockDataset = generateMockLogs(2000);
