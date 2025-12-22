# Paso 3 - Fase 3: Visor de Logs en Tiempo Real

## Estado

✅ **COMPLETADO** - 2024-12-22

## Resumen

Implementación completa del visor de logs en tiempo real para el dashboard de aGEntiX. Sistema de visualización, filtrado y búsqueda de logs del sistema con soporte para streaming en tiempo real (SSE), exportación de datos y persistencia de filtros.

## Funcionalidades Implementadas

### 1. Visualización de Logs

- **LogEntry Component** (`src/components/logs/LogEntry.tsx`)
  - Lista de logs en orden cronológico (más reciente primero)
  - Formato expandible/colapsable para ver JSON completo
  - Colores por nivel de severidad:
    - INFO: Azul
    - WARNING: Amarillo
    - ERROR: Rojo
    - CRITICAL: Rojo oscuro
    - DEBUG: Gris
  - Timestamp formateado en zona horaria local (español)
  - Resaltado de PII redactado con badges morados
  - Visualización de metadata (agent_run_id, duration_ms)
  - Detalles expandidos: error stacktrace y contexto JSON

### 2. Sistema de Filtros

- **LogFilters Component** (`src/components/logs/LogFilters.tsx`)
  - Filtro por nivel de log (multi-selección)
  - Filtro por componente (multi-selección)
  - Filtro por agente (multi-selección)
  - Filtro por expediente_id (texto con debounce)
  - Filtro por rango de fechas (datetime-local)
  - Botón "Limpiar filtros"
  - Estado visual de "Filtros Activos"
  - Colapsable/expandible

### 3. Búsqueda de Texto Completo

- **LogSearch Component** (`src/components/logs/LogSearch.tsx`)
  - Búsqueda en mensaje
  - Búsqueda en contexto JSON
  - Búsqueda en errores
  - Debounce de 300ms
  - Indicador visual de búsqueda activa
  - Botón para limpiar búsqueda

### 4. Streaming en Tiempo Real

- **useLogStream Hook** (`src/hooks/useLogStream.ts`)
  - Conexión SSE para logs en tiempo real
  - Toggle activar/desactivar streaming
  - Buffer limitado a 100 logs
  - Auto-scroll cuando está activo
  - Indicador visual de conexión activa
  - Manejo de errores y reconexión

### 5. Paginación y Rendimiento

- **LogsViewer Component** (`src/components/logs/LogsViewer.tsx`)
  - Infinite scroll con Intersection Observer
  - Botón "Cargar más" manual
  - Estado de carga visual
  - Mensaje de error con opción de reintentar
  - Contador de logs mostrados/totales
  - Soporta miles de logs sin degradación

### 6. Exportación de Datos

- **Formatos soportados:**
  - JSON (`.json`) - Pretty-printed
  - JSON Lines (`.jsonl`) - Una línea por log
  - CSV (`.csv`) - Campos principales
- Descarga inmediata con nombre de archivo con timestamp
- Respeta filtros activos

### 7. Persistencia de Estado

- Filtros guardados en `sessionStorage`
- Clave: `agentix_logs_filters`
- Se recuperan al recargar la página
- Se limpian con el botón "Limpiar filtros"

## Arquitectura

### Estructura de Archivos

```
frontend/src/
├── types/
│   └── logs.ts                    # Tipos TypeScript completos
├── mocks/
│   └── logs.mock.ts               # 2000 logs mock para testing
├── services/
│   └── logsService.ts             # API client con mock/real toggle
├── hooks/
│   ├── useLogs.ts                 # Gestión de estado de logs
│   └── useLogStream.ts            # Streaming SSE
├── components/logs/
│   ├── LogEntry.tsx               # Entrada individual
│   ├── LogFilters.tsx             # Panel de filtros
│   ├── LogSearch.tsx              # Búsqueda de texto
│   └── LogsViewer.tsx             # Contenedor principal
└── pages/
    └── Logs.tsx                   # Página completa integrada
```

### Tipos de Datos

```typescript
export type LogLevel = 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL' | 'DEBUG';

export type LogComponent =
  | 'AgentExecutor'
  | 'MCPClient'
  | 'PIIRedactor'
  | 'AuditLogger'
  | 'JWTValidator'
  | 'APIServer'
  | 'WebhookService'
  | 'TaskTracker'
  | 'Unknown';

export interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  component: LogComponent;
  agent?: AgentType;
  expediente_id?: string;
  message: string;
  context?: Record<string, any>;
  user_id?: string;
  agent_run_id?: string;
  duration_ms?: number;
  error?: {
    type: string;
    message: string;
    stacktrace?: string;
  };
}
```

## Datos Mock

### Dataset Grande

- **largeMockDataset**: 2000 logs generados aleatoriamente
- Distribución realista de niveles de log
- Componentes variados
- 50% incluyen agente
- 70% incluyen expediente_id
- 30% incluyen contexto
- Errores con stacktrace
- PII redactado en algunos mensajes

### Dataset Estático

- **mockLogs**: 8 logs predefinidos para desarrollo consistente
- Ejemplos de cada nivel de log
- Casos de error con stacktrace
- PII redactado visible
- Metadata completa

## Características Técnicas

### Performance

- **Infinite scroll** con Intersection Observer
- **Debounce** de 300ms en búsqueda y expediente_id
- **Renderizado optimizado** sin virtualización compleja
- **Buffer limitado** en streaming (100 logs)
- Soporta **2000+ logs** sin problemas de rendimiento

### Accesibilidad

- Labels en todos los inputs
- Aria-labels en botones
- Focus visible
- Navegación por teclado
- Contraste de colores WCAG AA

### Responsive

- Grid adaptable en filtros de fechas
- Flex wrapping en filtros multi-selección
- Mobile-friendly (>= 640px)

## Integración con API

### Endpoints Esperados (Backend - Paso 3)

```
GET /api/v1/logs
  - Query params: level, component, agent, expediente_id, date_from, date_to, search, page, page_size
  - Response: LogsResponse { logs, total, page, page_size, has_more }
  - Requiere: Authorization: Bearer <API_ADMIN_TOKEN>

GET /api/v1/logs/stream
  - Server-Sent Events (SSE)
  - Eventos: { type: 'log', data: LogEntry }
  - Requiere: Authorization: Bearer <API_ADMIN_TOKEN>
```

### Toggle Mock/Real

```typescript
// src/services/logsService.ts
const USE_MOCK_DATA = true; // Cambiar a false cuando API esté lista
```

## Criterios de Aceptación

### ✅ Cumplidos

- [x] Streaming de logs en tiempo real (SSE simulado)
- [x] 5+ filtros funcionales (nivel, componente, agente, expediente_id, fecha, búsqueda)
- [x] Renderizado de 2000+ logs sin degradación de performance
- [x] Resaltado de PII redactado visible con badges
- [x] Descarga de logs filtrados (JSON, JSONL, CSV)
- [x] Persistencia de filtros en sessionStorage
- [x] Auto-scroll en modo streaming
- [x] Infinite scroll con Intersection Observer
- [x] Colores por nivel de severidad
- [x] Formato expandible/colapsable para detalles

## Testing Manual

### Caso 1: Filtrado Básico

1. Navegar a `/logs`
2. Expandir panel de filtros
3. Seleccionar nivel "ERROR"
4. Verificar que solo se muestran logs de nivel ERROR

### Caso 2: Búsqueda de Texto

1. Escribir "MCP" en barra de búsqueda
2. Verificar que se filtran logs que contengan "MCP" en mensaje, contexto o error
3. Limpiar búsqueda con el botón X

### Caso 3: Streaming en Tiempo Real

1. Hacer clic en "Activar Streaming"
2. Verificar indicador verde pulsante
3. Observar nuevos logs apareciendo cada 2-5 segundos
4. Verificar auto-scroll al final
5. Desactivar streaming

### Caso 4: Exportación

1. Filtrar logs (ej: solo ERRORs)
2. Hacer clic en "Exportar"
3. Seleccionar formato (JSON/JSONL/CSV)
4. Verificar descarga automática
5. Abrir archivo y verificar contenido

### Caso 5: Persistencia de Filtros

1. Aplicar filtros (nivel, componente, fechas)
2. Recargar página (F5)
3. Verificar que filtros se mantienen

### Caso 6: Infinite Scroll

1. Scroll hasta el final de la lista
2. Verificar que se carga automáticamente la siguiente página
3. O hacer clic en "Cargar más"

### Caso 7: Expandir Detalles

1. Buscar un log con error (nivel ERROR o CRITICAL)
2. Hacer clic en icono de expandir (>)
3. Verificar que se muestra stacktrace y contexto JSON
4. Hacer clic de nuevo para colapsar

## Próximos Pasos

### Fase 4: Panel de Pruebas de Agentes

- Selector de agentes
- Formulario de ejecución
- Generador de JWT de prueba
- Visualizador de resultados
- Historial de ejecuciones

## Notas de Implementación

### Decisiones de Diseño

1. **No se usó react-window**: La lista simple con infinite scroll es suficiente para 2000+ logs
2. **Streaming mock**: Se simula con setInterval + logs aleatorios
3. **Debounce centralizado**: En los componentes de input, no en el hook
4. **Persistencia en sessionStorage**: Se pierde al cerrar tab (más seguro que localStorage)
5. **Colores semánticos**: TailwindCSS utility classes para consistencia

### Mejoras Futuras (Opcionales)

- [ ] React-window para >10000 logs
- [ ] WebSocket en lugar de SSE para streaming bidireccional
- [ ] Filtros avanzados: regex, operadores lógicos (AND/OR)
- [ ] Bookmarks de búsquedas frecuentes
- [ ] Alertas/notificaciones cuando llega log CRITICAL
- [ ] Modo dark

## Referencias

- **Especificación**: `/prompts/step-3-frontend.md` - Sección 2
- **Tipos**: `/frontend/src/types/logs.ts`
- **Datos Mock**: `/frontend/src/mocks/logs.mock.ts`
- **date-fns**: https://date-fns.org/ (formateo de fechas)

## Changelog

### 2024-12-22

- ✅ Implementación completa de Fase 3: Visor de Logs
- ✅ 8 componentes/hooks/servicios creados
- ✅ 2000 logs mock para testing de performance
- ✅ Streaming SSE simulado
- ✅ Exportación CSV/JSON/JSONL
- ✅ Persistencia de filtros en sessionStorage
- ✅ TypeScript types completos
- ✅ Documentación completa
