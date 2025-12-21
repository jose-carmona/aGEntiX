# Paso 3: Frontend de Demostración para aGEntiX

## Contexto del Proyecto

Este es un proyecto Capstone de final de curso para **aGEntiX**, un sistema de agentes de IA que se integra con GEX (Gestión de Expedientes) utilizado en la administración pública de Córdoba, España.

**Estado actual:**
- ✅ Paso 1 completado: Back-office con arquitectura multi-MCP (119 tests passing)
- ✅ Funcionalidades core: JWT validation, PII redaction, audit logging, 3 agentes mock
- 🎯 Paso 2: API REST con FastAPI (a implementar antes del frontend)
- 🎯 Paso 3: Frontend de demostración (este paso)

## Objetivo del Paso 3

Crear un **frontend de demostración** con las siguientes funcionalidades principales:

### 0. Autenticación con Token de Administración

El acceso al dashboard estará protegido mediante un token de administración simple.

**Flujo de autenticación:**

1. **Variable de entorno en Backend:**
   - `API_ADMIN_TOKEN`: Token secreto configurado en `.env` del backend
   - Ejemplo: `API_ADMIN_TOKEN=agentix-admin-2024-secure-token-xyz`

2. **Endpoint de validación:**
   - `POST /api/v1/auth/validate-admin-token`
   - Request body: `{"token": "string"}`
   - Response exitosa (200): `{"valid": true, "message": "Token válido"}`
   - Response error (401): `{"valid": false, "message": "Token inválido"}`

3. **Protección de endpoints:**
   - **IMPORTANTE:** Existen DOS sistemas de autenticación:
     - **Token de Admin:** Para acceder al dashboard (métricas, logs, test panel)
     - **JWT de Agente:** Para ejecutar agentes (ya implementado en Paso 2)

   - **Endpoints públicos (sin autenticación):**
     - `GET /health`
     - `GET /metrics`
     - `POST /api/v1/auth/validate-admin-token`

   - **Endpoints que requieren Token de Admin (Paso 3):**
     - `GET /api/v1/dashboard/metrics`
     - `GET /api/v1/logs`
     - `GET /api/v1/logs/stream`
     - `POST /api/v1/auth/generate-jwt`
     - Header requerido: `Authorization: Bearer <API_ADMIN_TOKEN>`

   - **Endpoints que requieren JWT de Agente (ya implementados):**
     - `POST /api/v1/agent/execute`
     - `GET /api/v1/agent/status/{agent_run_id}`
     - Header requerido: `Authorization: Bearer <JWT_TOKEN>`
     - Validación: 10 claims JWT (ver Paso 1)

   - Middleware de FastAPI validará el token apropiado en cada request

4. **Página de Login:**
   - **Ruta:** `/login`
   - **Campos:**
     - Input tipo password para introducir el token
     - Botón "Acceder al Dashboard"
   - **Validación:**
     - Al hacer clic, llama a `POST /api/v1/auth/validate-admin-token`
     - Si es válido: almacena token en `localStorage` y redirige a `/dashboard`
     - Si es inválido: muestra mensaje de error "Token de administración inválido"
   - **Diseño:**
     - Centrado en pantalla con TailwindCSS
     - Logo de aGEntiX (opcional)
     - Card con sombra conteniendo el formulario

5. **Protección de rutas en Frontend:**
   - **ProtectedRoute component:** Envuelve todas las rutas del dashboard
   - Verifica presencia de token en `localStorage`
   - Si NO hay token → redirige a `/login`
   - Si HAY token → renderiza la ruta protegida

6. **Inclusión del token en todas las peticiones:**
   - Interceptor de Axios o configuración global de Fetch
   - Añade automáticamente header: `Authorization: Bearer <token>`
   - Si recibe 401 → borra token y redirige a `/login`

7. **Logout:**
   - Botón "Cerrar Sesión" en Header
   - Al hacer clic: borra token de `localStorage` y redirige a `/login`

**Requisitos de seguridad:**
- Token almacenado en `localStorage` (alternativa: `sessionStorage` para mayor seguridad)
- NO mostrar el token en logs ni errores del frontend
- Token debe ser una cadena aleatoria de al menos 32 caracteres
- Validación del token en backend mediante comparación exacta (no JWT, token simple)
- Opcional: Implementar rate limiting en endpoint de validación (max 5 intentos/minuto)

### 1. Dashboard de Métricas
Mostrar las métricas más importantes del sistema en tiempo real o cuasi-real:

**Métricas a visualizar:**
- **Ejecuciones de agentes:**
  - Total de ejecuciones (hoy, última semana, último mes)
  - Ejecuciones por estado (success, error, in_progress)
  - Ejecuciones por tipo de agente (ValidadorDocumental, AnalizadorSubvencion, GeneradorInforme)
  - Tiempo promedio de ejecución
  - Tasa de éxito/error (%)

- **Recursos del sistema:**
  - Estado de los servidores MCP (activos/inactivos)
  - Número de herramientas MCP disponibles
  - Estado de conexión con servicios externos

- **Datos PII redactados:**
  - Total de campos PII redactados (por tipo: DNI, NIE, email, teléfono, IBAN, etc.)
  - Gráfico de distribución de tipos de PII encontrados

- **Performance:**
  - Tiempo de respuesta promedio de la API
  - Llamadas a MCP por segundo
  - Latencia P50, P95, P99

**Requisitos técnicos:**
- Gráficos interactivos (líneas de tiempo, barras, donuts, KPIs)
- Actualización automática cada 5-10 segundos (polling o websockets)
- Filtros por rango de fechas
- Exportación de datos a CSV/JSON

### 2. Visor de Logs en Tiempo Real
Mostrar los logs estructurados del sistema con capacidades de filtrado y búsqueda:

**Funcionalidades:**
- **Visualización:**
  - Lista de logs en orden cronológico (más reciente primero)
  - Formato expandible/colapsable para ver JSON completo
  - Colores por nivel de severidad (INFO=azul, WARNING=amarillo, ERROR=rojo)
  - Timestamp formateado en zona horaria local

- **Filtros:**
  - Por nivel de log (INFO, WARNING, ERROR, CRITICAL)
  - Por componente (AgentExecutor, MCPClient, PIIRedactor, etc.)
  - Por agente (ValidadorDocumental, AnalizadorSubvencion, GeneradorInforme)
  - Por expediente_id
  - Por rango de fechas/horas
  - Búsqueda de texto completo en mensaje y contexto

- **Características avanzadas:**
  - Auto-scroll al recibir nuevos logs
  - Resaltado de PII redactado (mostrar [DNI-REDACTED], etc.)
  - Descarga de logs filtrados en formato JSON Lines
  - Vista "tail -f" simulada

**Requisitos técnicos:**
- Streaming de logs desde la API (Server-Sent Events o WebSocket)
- Paginación infinita (infinite scroll) o paginación tradicional
- Rendimiento con miles de logs (virtualización de lista)
- Persistencia de filtros en sessionStorage

### 3. Panel de Pruebas de Agentes
Interfaz para invocar agentes de forma manual con propósitos de testing:

**Funcionalidades:**
- **Selector de agente:**
  - Dropdown con los 3 agentes disponibles
  - Descripción breve de cada agente
  - Indicador de estado (disponible/ocupado)

- **Configuración de ejecución:**
  - Campo `expediente_id` (ej: EXP-2024-001)
  - Selector de permisos a incluir en JWT de prueba
  - Campo opcional de contexto adicional (JSON)
  - Botón "Ejecutar Agente"

- **Visualización de resultados:**
  - Estado de la ejecución (pending → running → completed/error)
  - Barra de progreso o spinner durante ejecución
  - Resultado estructurado (JSON pretty-printed)
  - Logs específicos de esta ejecución
  - Métricas de esta ejecución (duración, herramientas llamadas, etc.)
  - Historial de ejecuciones recientes en sidebar

- **Generación de JWT:**
  - Botón "Generar Token de Prueba"
  - Visualización del token generado
  - Copia al portapapeles
  - Decodificación visual de claims JWT

**Requisitos técnicos:**
- Validación de inputs antes de envío
- Manejo de errores con mensajes claros
- Cancelación de ejecuciones en progreso
- Guardado de últimas configuraciones en localStorage

## Stack Tecnológico

### Frontend
- **Framework:** React 18+ con TypeScript
- **Estilos:** TailwindCSS 3+ (utility-first)
- **Componentes UI:**
  - Headless UI (componentes accesibles)
  - Heroicons (iconografía)
  - Recharts o Chart.js (gráficos)
- **Gestión de estado:**
  - React Query / TanStack Query (server state)
  - Zustand o Context API (client state)
- **HTTP Client:** Axios o Fetch API
- **Tiempo real:** EventSource (SSE) o WebSocket
- **Build tool:** Vite

### Backend (ya existente)
- **API:** FastAPI (Python 3.11+)
- **Endpoints necesarios:**

  **✅ Ya implementados (Paso 2):**
  - `GET /health` - health check (público, no requiere autenticación)
  - `GET /metrics` - métricas Prometheus (público)
  - `POST /api/v1/agent/execute` - ejecutar agente (requiere JWT Bearer token)
  - `GET /api/v1/agent/status/{agent_run_id}` - estado de ejecución (requiere JWT Bearer token)

  **🎯 A implementar (Paso 3 - Frontend):**
  - **Autenticación admin:**
    - `POST /api/v1/auth/validate-admin-token` - validar token de admin dashboard
  - **Dashboard métricas:**
    - `GET /api/v1/dashboard/metrics` - métricas del sistema para dashboard
  - **Logs:**
    - `GET /api/v1/logs` - logs con filtros
    - `GET /api/v1/logs/stream` - SSE para logs en tiempo real
  - **Testing agentes:**
    - `POST /api/v1/auth/generate-jwt` - generar JWT de prueba para testing de agentes

## Estructura de Archivos Propuesta

```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── ProtectedRoute.tsx
│   │   │   └── LogoutButton.tsx
│   │   ├── layout/
│   │   │   ├── Layout.tsx
│   │   │   ├── Header.tsx
│   │   │   └── Sidebar.tsx
│   │   ├── dashboard/
│   │   │   ├── MetricsCard.tsx
│   │   │   ├── AgentExecutionsChart.tsx
│   │   │   ├── PIIRedactionChart.tsx
│   │   │   └── SystemHealthStatus.tsx
│   │   ├── logs/
│   │   │   ├── LogsViewer.tsx
│   │   │   ├── LogEntry.tsx
│   │   │   ├── LogFilters.tsx
│   │   │   └── LogSearch.tsx
│   │   ├── test-panel/
│   │   │   ├── AgentSelector.tsx
│   │   │   ├── ExecutionForm.tsx
│   │   │   ├── ResultsViewer.tsx
│   │   │   ├── JWTGenerator.tsx
│   │   │   └── ExecutionHistory.tsx
│   │   └── ui/
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── Input.tsx
│   │       ├── Select.tsx
│   │       └── Badge.tsx
│   ├── contexts/
│   │   └── AuthContext.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useMetrics.ts
│   │   ├── useLogs.ts
│   │   ├── useLogStream.ts
│   │   ├── useAgentExecution.ts
│   │   └── useWebSocket.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── authService.ts
│   │   ├── metricsService.ts
│   │   ├── logsService.ts
│   │   └── agentService.ts
│   ├── types/
│   │   ├── auth.ts
│   │   ├── metrics.ts
│   │   ├── logs.ts
│   │   ├── agent.ts
│   │   └── api.ts
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Logs.tsx
│   │   └── TestPanel.tsx
│   ├── utils/
│   │   ├── formatters.ts
│   │   ├── dateUtils.ts
│   │   ├── validators.ts
│   │   └── storage.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
└── README.md
```

## Requisitos de Diseño UI/UX

### Paleta de Colores
- **Primario:** Azul oscuro (#1e40af) - confianza, institucional
- **Secundario:** Verde (#10b981) - éxito, positivo
- **Acento:** Naranja (#f59e0b) - advertencia, atención
- **Error:** Rojo (#ef4444) - errores, fallos
- **Fondo:** Gris claro (#f9fafb) - neutro, limpio
- **Texto:** Gris oscuro (#111827) - legibilidad

### Tipografía
- **Familia:** Inter o System UI (profesional, legible)
- **Tamaños:** Escala modular TailwindCSS (text-sm, text-base, text-lg, etc.)

### Responsividad
- **Desktop first:** Optimizado para 1920x1080 (presentación)
- **Breakpoints:** lg (1024px), md (768px), sm (640px)
- **Mínimo soportado:** Tablet landscape (768px)

### Accesibilidad
- **WCAG 2.1 AA:**
  - Contraste de color adecuado
  - Navegación por teclado
  - Etiquetas ARIA
  - Focus visible
  - Textos alternativos

## Casos de Uso Principales

### UC-0: Autenticarse en el Sistema
**Actor:** Administrador del sistema
**Flujo:**
1. Usuario navega a la URL del frontend (ej: http://localhost:5173)
2. Sistema detecta que no hay token en localStorage
3. Sistema redirige automáticamente a `/login`
4. Usuario visualiza página de login con input de token
5. Usuario introduce el token de administración
6. Usuario hace clic en "Acceder al Dashboard"
7. Sistema envía POST a `/api/v1/auth/validate-admin-token`
8. Backend valida el token contra `API_ADMIN_TOKEN`
9. Sistema recibe respuesta exitosa (200)
10. Sistema almacena token en localStorage
11. Sistema redirige a `/dashboard`
12. Usuario visualiza el dashboard con métricas

**Flujo alternativo (token inválido):**
- Paso 9a: Backend responde con 401 Unauthorized
- Sistema muestra mensaje de error: "Token de administración inválido"
- Usuario permanece en página de login
- Usuario puede reintentar con token correcto

### UC-1: Monitorizar Salud del Sistema
**Actor:** Administrador del sistema
**Precondición:** Usuario autenticado (token válido en localStorage)
**Flujo:**
1. Usuario accede al dashboard
2. Sistema incluye token en header de peticiones
3. Sistema muestra métricas en tiempo real
4. Usuario observa gráficos de ejecuciones
5. Usuario detecta anomalía (pico de errores)
6. Usuario hace clic en métrica para ver detalles
7. Sistema redirige a logs filtrados por ese período

**Flujo alternativo (sesión expirada):**
- Sistema recibe 401 en cualquier petición
- Sistema borra token de localStorage
- Sistema redirige a `/login`

### UC-2: Depurar Error en Ejecución
**Actor:** Desarrollador
**Precondición:** Usuario autenticado (token válido en localStorage)
**Flujo:**
1. Usuario accede a visor de logs
2. Usuario filtra por nivel ERROR
3. Usuario filtra por agente específico
4. Sistema muestra logs relevantes
5. Usuario expande log para ver stacktrace
6. Usuario copia log completo para análisis

### UC-3: Probar Agente Manualmente
**Actor:** QA / Desarrollador
**Precondición:** Usuario autenticado (token válido en localStorage)
**Flujo:**
1. Usuario accede a panel de pruebas
2. Usuario selecciona "ValidadorDocumental"
3. Usuario introduce expediente_id "EXP-2024-001"
4. Usuario selecciona permisos: ["leer_expediente", "leer_documentos"]
5. Usuario hace clic en "Ejecutar Agente"
6. Sistema muestra progreso en tiempo real
7. Sistema muestra resultado: documentos validados correctamente
8. Usuario revisa logs específicos de esta ejecución

### UC-4: Cerrar Sesión
**Actor:** Administrador del sistema
**Precondición:** Usuario autenticado (token válido en localStorage)
**Flujo:**
1. Usuario hace clic en botón "Cerrar Sesión" en Header
2. Sistema borra token de localStorage
3. Sistema redirige a `/login`
4. Usuario visualiza página de login
5. Sistema no permite acceso a rutas protegidas sin nuevo login

## Criterios de Aceptación

### Generales
- [ ] Aplicación funciona sin errores en Chrome, Firefox, Safari, Edge
- [ ] Todos los componentes usan TypeScript con tipos estrictos
- [ ] No hay warnings de ESLint o TypeScript
- [ ] Bundle optimizado < 500KB (gzipped)
- [ ] Lighthouse score > 90 en Performance y Accessibility
- [ ] README con instrucciones de instalación y desarrollo

### Autenticación
- [ ] Página de login renderiza correctamente con diseño centrado
- [ ] Input de token es tipo password (oculta caracteres)
- [ ] Validación de token funciona correctamente con backend
- [ ] Token válido almacena en localStorage y redirige a /dashboard
- [ ] Token inválido muestra mensaje de error sin redirección
- [ ] Rutas protegidas redirigen a /login si no hay token
- [ ] Todas las peticiones incluyen header Authorization: Bearer <token>
- [ ] Respuestas 401 borran token y redirigen a /login
- [ ] Botón "Cerrar Sesión" funcional en Header
- [ ] Logout borra token y redirige a /login
- [ ] No se puede acceder a rutas protegidas sin autenticación

### Dashboard de Métricas
- [ ] Muestra al menos 6 KPIs principales
- [ ] 3+ gráficos interactivos (hover, click, zoom)
- [ ] Actualización automática cada 10 segundos
- [ ] Filtro por rango de fechas funcional
- [ ] Exportación de datos a CSV

### Visor de Logs
- [ ] Streaming de logs en tiempo real (SSE o WS)
- [ ] 5+ filtros funcionales (nivel, componente, agente, fecha, búsqueda)
- [ ] Renderizado de 1000+ logs sin degradación de performance
- [ ] Resaltado de PII redactado visible
- [ ] Descarga de logs filtrados

### Panel de Pruebas
- [ ] Selector de 3 agentes funcional
- [ ] Generación de JWT de prueba
- [ ] Validación de expediente_id con regex
- [ ] Estado de ejecución en tiempo real
- [ ] Historial de últimas 10 ejecuciones
- [ ] Cancelación de ejecuciones

## Consideraciones de Implementación

### Performance
- **Code splitting:** Lazy loading de rutas con React.lazy()
- **Memoización:** useMemo/useCallback para componentes pesados
- **Virtualización:** react-window para listas largas de logs
- **Debouncing:** Búsquedas y filtros con debounce de 300ms
- **Optimistic updates:** Actualización optimista de UI antes de respuesta

### Seguridad
- **Autenticación:**
  - Token de admin almacenado en `API_ADMIN_TOKEN` en .env del backend
  - Middleware de FastAPI valida token en header Authorization
  - Frontend almacena token en localStorage (o sessionStorage para mayor seguridad)
  - Interceptor HTTP añade automáticamente header Bearer
  - Logout seguro: borra token y limpia estado
- **CORS:** Configurar correctamente en FastAPI (permitir origen del frontend)
- **XSS:** Sanitización de inputs con DOMPurify
- **CSRF:** Tokens CSRF en requests de modificación (opcional para API stateless)
- **Rate Limiting:** Limitar intentos de validación de token (backend)
- **Secrets:**
  - NO hardcodear API URLs, usar .env (VITE_API_URL)
  - NO exponer API_ADMIN_TOKEN en código frontend
  - NO loguear tokens en consola o errores

### Testing
- **Unit tests:** Vitest para lógica de negocio
- **Component tests:** React Testing Library
- **E2E tests (opcional):** Playwright o Cypress
- **Cobertura mínima:** 70%

### Logging Frontend
- **Console.log:** Solo en desarrollo
- **Error tracking:** Sentry o similar (opcional)
- **Analytics:** Ninguno (proyecto académico)

## Datos Mock para Desarrollo

Mientras se implementa la API (Paso 2), usar datos mock en el frontend:

```typescript
// src/mocks/metrics.mock.ts
export const mockMetrics = {
  total_executions: 1247,
  executions_today: 34,
  success_rate: 94.2,
  avg_execution_time: 2.3,
  executions_by_agent: {
    ValidadorDocumental: 512,
    AnalizadorSubvencion: 423,
    GeneradorInforme: 312
  },
  executions_by_status: {
    success: 1175,
    error: 62,
    in_progress: 10
  },
  mcp_servers_status: {
    expedientes: "active",
    firma: "inactive"
  },
  pii_redacted: {
    DNI: 3421,
    email: 2134,
    telefono: 1876,
    // ...
  }
}

// src/mocks/logs.mock.ts
export const mockLogs = [
  {
    timestamp: "2025-12-21T10:30:45.123Z",
    level: "INFO",
    component: "AgentExecutor",
    agent: "ValidadorDocumental",
    expediente_id: "EXP-2024-001",
    message: "Ejecución iniciada",
    context: { /* ... */ }
  },
  // ...
]
```

## Ejemplos de Código - Sistema de Autenticación

### Backend: Endpoint de Validación (FastAPI)

```python
# src/api/routes/auth.py
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from src.backoffice.settings import settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

class TokenValidationRequest(BaseModel):
    token: str

class TokenValidationResponse(BaseModel):
    valid: bool
    message: str

@router.post("/validate-admin-token", response_model=TokenValidationResponse)
async def validate_admin_token(request: TokenValidationRequest):
    """Valida el token de administración."""
    if request.token == settings.API_ADMIN_TOKEN:
        return TokenValidationResponse(valid=True, message="Token válido")
    else:
        raise HTTPException(
            status_code=401,
            detail={"valid": False, "message": "Token inválido"}
        )

# Dependency para validar token en endpoints protegidos
async def verify_admin_token(authorization: str = Header(...)):
    """Verifica que el header Authorization contenga un Bearer token válido."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autorización requerido")

    token = authorization.replace("Bearer ", "")
    if token != settings.API_ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido")

    return token
```

### Backend: Middleware de Autenticación

```python
# src/api/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Rutas públicas que no requieren autenticación admin
# NOTA: Los endpoints de agente (/api/v1/agent/*) requieren JWT de agente, no token admin
PUBLIC_PATHS = [
    "/",                                      # Root
    "/health",                                # Health check
    "/metrics",                               # Prometheus metrics
    "/api/v1/auth/validate-admin-token",     # Validación de token admin
    "/docs",                                  # Swagger docs
    "/redoc",                                 # ReDoc
    "/openapi.json",                          # OpenAPI schema
    "/api/v1/agent/execute",                 # Ya tiene validación JWT propia
    "/api/v1/agent/status"                   # Ya tiene validación JWT propia
]

@app.middleware("http")
async def validate_admin_token_middleware(request: Request, call_next):
    """
    Middleware que valida el token de administración para endpoints del dashboard.

    Los endpoints de agente (/api/v1/agent/*) tienen su propia validación JWT
    y no usan el token de admin.
    """
    # Permitir rutas públicas
    if any(request.url.path.startswith(path) for path in PUBLIC_PATHS):
        return await call_next(request)

    # Para endpoints del dashboard (/api/v1/dashboard/*, /api/v1/logs/*, etc.)
    # verificar token de admin
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autorización requerido")

    token = auth_header.replace("Bearer ", "")
    if token != settings.API_ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido")

    # Token válido, continuar
    return await call_next(request)
```

### Frontend: AuthContext

```typescript
// src/contexts/AuthContext.tsx
import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { validateAdminToken } from '../services/authService';

interface AuthContextType {
  isAuthenticated: boolean;
  token: string | null;
  login: (token: string) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'agentix_admin_token';

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Cargar token al iniciar
    const savedToken = localStorage.getItem(TOKEN_KEY);
    if (savedToken) {
      setToken(savedToken);
    }
    setLoading(false);
  }, []);

  const login = async (adminToken: string): Promise<boolean> => {
    try {
      const isValid = await validateAdminToken(adminToken);
      if (isValid) {
        localStorage.setItem(TOKEN_KEY, adminToken);
        setToken(adminToken);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error validating token:', error);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{
      isAuthenticated: !!token,
      token,
      login,
      logout,
      loading
    }}>
      {children}
    </AuthContext.Provider>
  );
};
```

### Frontend: Hook useAuth

```typescript
// src/hooks/useAuth.ts
import { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe usarse dentro de AuthProvider');
  }
  return context;
};
```

### Frontend: ProtectedRoute Component

```typescript
// src/components/auth/ProtectedRoute.tsx
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div className="flex items-center justify-center h-screen">
      <div className="text-gray-600">Cargando...</div>
    </div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};
```

### Frontend: Login Page

```typescript
// src/pages/Login.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export const Login = () => {
  const [token, setToken] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const success = await login(token);

    if (success) {
      navigate('/dashboard');
    } else {
      setError('Token de administración inválido');
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="bg-white shadow-lg rounded-lg p-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            aGEntiX Dashboard
          </h1>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="token" className="block text-sm font-medium text-gray-700 mb-2">
                Token de Administración
              </label>
              <input
                id="token"
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Introduce el token"
                required
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-700 hover:bg-blue-800 text-white font-medium py-2 px-4 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Validando...' : 'Acceder al Dashboard'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
```

### Frontend: API Service con Interceptor

```typescript
// src/services/api.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para añadir token a todas las peticiones
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('agentix_admin_token');
    if (token && config.url !== '/api/v1/auth/validate-admin-token') {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token inválido o expirado
      localStorage.removeItem('agentix_admin_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// src/services/authService.ts
import { api } from './api';

export const validateAdminToken = async (token: string): Promise<boolean> => {
  try {
    const response = await api.post('/api/v1/auth/validate-admin-token', { token });
    return response.data.valid;
  } catch (error) {
    return false;
  }
};
```

### Frontend: App.tsx con Routing

```typescript
// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Logs } from './pages/Logs';
import { TestPanel } from './pages/TestPanel';
import { Layout } from './components/layout/Layout';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          <Route path="/" element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="logs" element={<Logs />} />
            <Route path="test-panel" element={<TestPanel />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
```

### Backend: Settings (.env)

```bash
# .env
API_ADMIN_TOKEN=agentix-admin-2024-secure-token-xyz123
JWT_SECRET=your-jwt-secret-here
# ... otras variables
```

### Frontend: Environment Variables

```bash
# .env
VITE_API_URL=http://localhost:8000
```

## Entregables

1. **Código fuente:** Repositorio Git con commits semánticos
2. **Documentación:**
   - README.md con setup instructions
   - Comentarios JSDoc en funciones principales
   - Storybook (opcional pero recomendado)
3. **Tests:** Suite de tests con >70% cobertura
4. **Deployment:**
   - Build de producción funcionando
   - Docker Compose con frontend + backend (opcional)
   - Instrucciones de despliegue

## Plan de Implementación

### Fase 1: Setup y Autenticación
- Setup del proyecto (Vite + React + TypeScript + TailwindCSS)
- Estructura de carpetas y routing
- **Sistema de autenticación:**
  - Página de login con TailwindCSS
  - AuthContext y useAuth hook
  - ProtectedRoute component
  - Interceptor HTTP para Bearer token
- Componentes UI base (Button, Card, Input, etc.)
- Layout general (Header con logout, Sidebar, páginas vacías)

### Fase 2: Dashboard de Métricas
- Dashboard de métricas con datos mock
- Gráficos interactivos (líneas, barras, donuts)
- KPIs principales (ejecuciones, tasa de éxito, performance)
- Auto-refresh de métricas
- Exportación de datos a CSV

### Fase 3: Visor de Logs
- Visor de logs con datos mock
- Sistema de filtros (nivel, componente, agente, fecha)
- Búsqueda de texto completo
- Infinite scroll o paginación
- Resaltado de PII redactado
- Descarga de logs filtrados

### Fase 4: Panel de Pruebas de Agentes
- Selector de agentes disponibles
- Formulario de ejecución (expediente_id, permisos, contexto)
- Generador de JWT de prueba
- Visualizador de resultados en tiempo real
- Historial de ejecuciones recientes
- Decodificación visual de JWT claims

### Fase 5: Refinamiento y Testing
- Testing completo (unit, component, E2E)
- Refinamiento UI/UX basado en feedback
- Optimización de performance
- Documentación técnica (README, JSDoc)
- Fixes de bugs y mejoras de estabilidad

## Referencias

### Documentación del Proyecto
- `/doc/index.md` - Índice Zettelkasten
- `/doc/001-gex-definicion.md` - Sistema GEX
- `CLAUDE.md` - Guía completa del proyecto
- `code-review/commit-c039abe/` - Review del Paso 1

### Tecnologías
- [TailwindCSS](https://tailwindcss.com/docs)
- [React Query](https://tanstack.com/query/latest)
- [Recharts](https://recharts.org/)
- [Headless UI](https://headlessui.com/)
- [Vite](https://vitejs.dev/)

### Inspiración UI
- Vercel Dashboard
- Railway.app
- Supabase Dashboard
- Linear.app (diseño minimalista)

## Preguntas Frecuentes

**Q: ¿Qué hacer si la API (Paso 2) no está lista?**
A: Usar datos mock definidos en `/src/mocks/`. Diseñar interfaces TypeScript que coincidan con el contrato esperado de la API. Para desarrollo, puedes mockear el endpoint de validación para que siempre retorne `{valid: true}`.

**Q: ¿Cómo funciona la autenticación?**
A: Hay DOS tipos de tokens diferentes en el sistema:
1. **Token de Administración (API_ADMIN_TOKEN):** Token simple para acceder al dashboard del frontend. Se valida comparando strings en el backend. NO es JWT.
2. **JWT de agentes:** Tokens JWT que se generan desde el panel de pruebas para ejecutar agentes. Estos tienen claims y se validan según el sistema del Paso 1.

El token de admin protege el acceso al dashboard. Los JWT protegen la ejecución de agentes.

**Q: ¿Qué hacer con logs sensibles?**
A: Mostrar los PII ya redactados (ej: `[DNI-REDACTED]`). No intentar desredactar. Resaltar visualmente con badges.

**Q: ¿Soporte mobile?**
A: No prioritario. Enfocarse en desktop/tablet landscape (768px+). Opcionalmente, se puede hacer responsive hasta 640px.

**Q: ¿Internacionalización (i18n)?**
A: No necesario. Todo en **español** (idioma del proyecto).

**Q: ¿Cómo generar un token de administración seguro?**
A: Para desarrollo, puedes usar cualquier string. Para producción, genera un token aleatorio:

```bash
# Opción 1: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Opción 2: OpenSSL
openssl rand -base64 32

# Opción 3: Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

Añade el resultado a `.env` como `API_ADMIN_TOKEN=<token-generado>`.

---

**¡Éxito con la implementación del frontend! 🚀**
