# aGEntiX Dashboard - Frontend

Dashboard de administración para el sistema de agentes aGEntiX.

## Tecnologías

- **React 18** con **TypeScript**
- **Vite** como build tool
- **TailwindCSS** para estilos
- **React Router** para navegación
- **Axios** para peticiones HTTP
- **Recharts** para gráficos interactivos
- **date-fns** para formateo de fechas (locale español)

## Requisitos Previos

- Node.js >= 18.x
- npm >= 9.x

## Instalación

1. Instalar dependencias:

```bash
cd frontend
npm install
```

2. Configurar variables de entorno:

El archivo `.env` ya está creado con la configuración correcta:

```env
VITE_API_URL=http://localhost:8080
```

**IMPORTANTE:** El backend corre en puerto **8080**, no 8000.

Modifica este archivo si necesitas apuntar a una API diferente.

## Desarrollo

### Iniciar el servidor de desarrollo:

```bash
npm run dev
```

### Acceso a la aplicación:

- **GitHub Codespaces:**
  - Ve al panel **PORTS** en VS Code
  - Busca el puerto **5173**
  - Haz clic en el ícono de globo 🌐 para abrir en el navegador
  - O copia la URL forwarded

- **Local:**
  - `http://localhost:5173`

**Nota:** En Codespaces, es necesario que `vite.config.ts` tenga `host: true` para que el port forwarding funcione correctamente.

## Scripts Disponibles

- `npm run dev` - Inicia el servidor de desarrollo
- `npm run build` - Genera el build de producción
- `npm run preview` - Previsualiza el build de producción
- `npm run lint` - Ejecuta ESLint
- `npm run type-check` - Verifica tipos TypeScript

## Estructura del Proyecto

```
frontend/
├── src/
│   ├── components/
│   │   ├── auth/          # Componentes de autenticación
│   │   ├── dashboard/     # Componentes del dashboard (Fase 2)
│   │   │   ├── MetricsCard.tsx          # Tarjetas KPI
│   │   │   ├── AgentExecutionsChart.tsx # Gráficos de ejecuciones
│   │   │   ├── PIIRedactionChart.tsx    # Gráficos de PII
│   │   │   └── SystemHealthStatus.tsx   # Estado del sistema
│   │   ├── logs/          # Componentes de logs (Fase 3)
│   │   │   ├── LogEntry.tsx             # Entrada de log expandible
│   │   │   ├── LogFilters.tsx           # Panel de filtros
│   │   │   ├── LogSearch.tsx            # Búsqueda de texto
│   │   │   └── LogsViewer.tsx           # Contenedor principal
│   │   ├── layout/        # Layout principal (Header, Sidebar)
│   │   └── ui/            # Componentes UI reutilizables
│   ├── contexts/          # Contextos de React (AuthContext)
│   ├── hooks/             # Custom hooks
│   │   ├── useAuth.ts     # Hook de autenticación
│   │   ├── useMetrics.ts  # Hook de métricas con auto-refresh
│   │   ├── useLogs.ts     # Hook de logs con paginación (Fase 3)
│   │   └── useLogStream.ts # Hook de streaming SSE (Fase 3)
│   ├── mocks/             # Datos mock para desarrollo
│   │   ├── metrics.mock.ts # Datos mock de métricas
│   │   └── logs.mock.ts    # 2000 logs mock (Fase 3)
│   ├── pages/             # Páginas de la aplicación
│   │   ├── Login.tsx      # Página de login
│   │   ├── Dashboard.tsx  # Dashboard con métricas (Fase 2)
│   │   ├── Logs.tsx       # Visor de logs completo (Fase 3)
│   │   └── TestPanel.tsx  # Panel de pruebas (Fase 4)
│   ├── services/          # Servicios API
│   │   ├── api.ts         # Cliente HTTP con interceptors
│   │   ├── authService.ts # Servicio de autenticación
│   │   ├── metricsService.ts # Servicio de métricas
│   │   └── logsService.ts    # Servicio de logs con exportación (Fase 3)
│   ├── types/             # Tipos TypeScript
│   │   ├── auth.ts        # Tipos de autenticación
│   │   ├── metrics.ts     # Tipos de métricas
│   │   ├── logs.ts        # Tipos de logs (Fase 3)
│   │   └── ...
│   ├── utils/             # Utilidades
│   ├── App.tsx            # Componente principal
│   ├── main.tsx           # Entry point
│   └── index.css          # Estilos globales
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Fase 1: Setup y Autenticación ✅

La Fase 1 está completamente implementada e incluye:

### Sistema de Autenticación
- Página de login con validación de token
- AuthContext con gestión de estado de autenticación
- ProtectedRoute para proteger rutas privadas
- Interceptor HTTP para añadir token automáticamente
- Logout funcional

### Componentes UI Base
- Button (primario, secundario, danger)
- Card (contenedor con sombra)
- Input (con label y error)
- Select (dropdown)
- Badge (etiquetas de estado)

### Layout
- Header con logo y botón de logout
- Sidebar con navegación
- Layout principal con routing

### Páginas
- Login (funcional)
- Dashboard (con métricas completas - Fase 2)
- Logs (placeholder - Fase 3)
- TestPanel (placeholder - Fase 4)

## Fase 2: Dashboard de Métricas ✅

La Fase 2 está completamente implementada e incluye:

### Sistema de Métricas
- **8 KPIs Principales** (supera requisito de 6):
  - Total de Ejecuciones, Ejecuciones Hoy, Tasa de Éxito, Tiempo Promedio
  - PII Redactados, Servidores MCP, Latencia P95, Llamadas MCP/s

- **4 Gráficos Interactivos** (supera requisito de 3):
  - Histórico de Ejecuciones (24h) - Líneas/Barras seleccionable
  - Ejecuciones por Tipo de Agente - Barras
  - Distribución de PII - Donut/Circular seleccionable
  - Histórico de PII (24h) - Barras apiladas

- **Auto-Refresh**: Actualización automática cada 10 segundos
- **Exportación**: Descarga de métricas en formato CSV y JSON

### Componentes del Dashboard
- **MetricsCard**: Tarjetas KPI reutilizables con colores y tendencias
- **AgentExecutionsChart**: Gráfico de líneas/barras para histórico de ejecuciones
- **AgentTypeChart**: Gráfico de barras por tipo de agente
- **PIIRedactionChart**: Gráfico donut/circular de distribución de PII
- **PIIHistoryChart**: Gráfico de barras apiladas de histórico de PII
- **PIILegend**: Leyenda personalizada con valores y porcentajes
- **SystemHealthStatus**: Estado completo de servidores MCP y servicios externos

### Hook useMetrics
- Auto-refresh configurable (default: 10 segundos)
- Polling paralelo de: métricas, historial ejecuciones, historial PII
- Manejo de estados: loading, error, data
- Función `refetch()` para actualización manual

### Servicio de Métricas
- Abstracción mock/API con flag `USE_MOCK_DATA`
- Funciones de exportación CSV/JSON
- Datos mock con variaciones aleatorias
- Simulación de latencia de red

### Performance
- **Bundle gzipped**: 195KB (< 500KB requerido ✓)
- Gráficos responsivos con Recharts
- Formateo de fechas con date-fns (locale español)
- Compilación TypeScript sin errores

**Documentación completa**: Ver `/doc/paso-3-fase-2-dashboard-metricas.md`

## Fase 3: Visor de Logs en Tiempo Real ✅

La Fase 3 está completamente implementada e incluye:

### Sistema de Logs
- **Visualización Avanzada**:
  - Logs con colores por nivel de severidad (INFO=azul, WARNING=amarillo, ERROR=rojo, CRITICAL=rojo oscuro, DEBUG=gris)
  - Formato expandible/colapsable para ver detalles (error stacktrace, contexto JSON)
  - Timestamp formateado en zona horaria local (español)
  - Resaltado automático de PII redactado con badges morados
  - Metadata visible (agent_run_id, duration_ms)

- **Sistema de Filtros Avanzado** (5+ filtros):
  - Filtro por nivel de log (multi-selección)
  - Filtro por componente (multi-selección)
  - Filtro por agente (multi-selección)
  - Filtro por expediente_id (texto con debounce 500ms)
  - Filtro por rango de fechas (datetime-local)
  - Persistencia automática en sessionStorage
  - Panel colapsable/expandible con indicador de filtros activos

- **Búsqueda de Texto Completo**:
  - Búsqueda en mensaje, contexto JSON y errores
  - Debounce de 300ms
  - Indicador visual de búsqueda activa
  - Botón para limpiar búsqueda

- **Streaming en Tiempo Real**:
  - Conexión SSE para logs en tiempo real (simulado)
  - Toggle activar/desactivar streaming
  - Buffer limitado a 100 logs
  - Auto-scroll automático cuando está activo
  - Indicador visual de conexión activa (pulsante)

- **Paginación y Rendimiento**:
  - Infinite scroll con Intersection Observer
  - Botón "Cargar más" manual
  - Soporta 2000+ logs sin degradación
  - Estados de carga y error con reintentos
  - Contador de logs mostrados/totales

- **Exportación de Datos**:
  - Formato JSON (pretty-printed)
  - Formato JSON Lines (.jsonl - una línea por log)
  - Formato CSV (campos principales)
  - Respeta filtros activos
  - Descarga inmediata con timestamp en nombre

### Componentes de Logs
- **LogEntry**: Entrada de log individual con expand/collapse
- **LogFilters**: Panel completo de filtros con multi-selección
- **LogSearch**: Barra de búsqueda con debounce
- **LogsViewer**: Contenedor principal con infinite scroll

### Hooks de Logs
- **useLogs**: Gestión de estado con paginación y filtros
- **useLogStream**: Streaming SSE con buffer y auto-scroll

### Servicio de Logs
- Abstracción mock/API con flag `USE_MOCK_DATA`
- Funciones de filtrado y exportación (JSON/JSONL/CSV)
- Conexión SSE para streaming en tiempo real
- 2000 logs mock para testing de performance

**Documentación completa**: Ver `/doc/paso-3-fase-3-visor-logs.md`

## Autenticación

El sistema usa un token de administración simple para acceder al dashboard.

### Token de Desarrollo

```
agentix-admin-dev-token-2024
```

Este token está configurado en el backend (`.env` → `API_ADMIN_TOKEN`).

### Flujo de Login
1. Usuario introduce token en `/login`
2. Token se valida contra `POST /api/v1/auth/validate-admin-token`
3. Si es válido, se almacena en `localStorage`
4. Usuario es redirigido a `/dashboard`
5. Todas las peticiones incluyen el token en header `Authorization: Bearer <token>`

### Protección de Rutas
- Todas las rutas (excepto `/login`) están protegidas con `ProtectedRoute`
- Si no hay token válido, redirige automáticamente a `/login`
- Si una petición devuelve 401, limpia el token y redirige a `/login`

## Próximas Fases

### Fase 4: Panel de Pruebas de Agentes (Siguiente)
- Selector de agentes
- Generador de JWT
- Visualizador de resultados

### Fase 5: Refinamiento y Testing
- Tests unitarios
- Tests de componentes
- Optimización de performance

## Soporte

Para más información sobre el proyecto completo, consulta el README principal en la raíz del proyecto.
