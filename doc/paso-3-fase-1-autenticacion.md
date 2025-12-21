# Paso 3 - Fase 1: Sistema de Autenticación Frontend

**Estado:** ✅ COMPLETADO
**Fecha:** 2025-12-21
**Objetivo:** Implementar sistema de autenticación para acceso al dashboard web de aGEntiX

---

## Resumen Ejecutivo

Se implementó correctamente el sistema de autenticación para el dashboard web, incluyendo:

- ✅ **Frontend React con TypeScript** - Configuración de Vite + TailwindCSS
- ✅ **Página de Login** - Interfaz de autenticación con validación
- ✅ **Contexto de Autenticación** - Gestión de estado con React Context
- ✅ **Rutas Protegidas** - Sistema de protección de rutas con redirección
- ✅ **Endpoint de Validación (Backend)** - `POST /api/v1/auth/validate-admin-token`
- ✅ **Configuración de CORS** - Soporte para desarrollo local y Codespaces
- ✅ **Componentes UI Base** - Card, Button, Input reutilizables

---

## Arquitectura de Autenticación

### Dos Sistemas Separados

El proyecto usa **DOS sistemas de autenticación diferentes**:

#### 1. Token de Admin (`API_ADMIN_TOKEN`)
- **Propósito:** Acceso al dashboard web (frontend)
- **Tipo:** String simple (NO es JWT)
- **Validación:** Comparación exacta con variable de entorno
- **Endpoints:**
  - `POST /api/v1/auth/validate-admin-token` - Validar token en login
  - Todos los endpoints del dashboard (`/api/v1/dashboard/*`, `/api/v1/logs/*`)
- **Flujo:**
  1. Usuario introduce token en página de login
  2. Frontend envía POST al endpoint de validación
  3. Backend compara con `API_ADMIN_TOKEN` en `.env`
  4. Si es válido, frontend guarda en `localStorage` y redirige a dashboard
  5. Todas las peticiones subsiguientes incluyen header `Authorization: Bearer <token>`

#### 2. JWT de Agente (Ya implementado en Paso 1)
- **Propósito:** Ejecutar agentes IA
- **Tipo:** JWT con 10 claims validados
- **Validación:** Firma, expiración, permisos, etc.
- **Endpoints:**
  - `POST /api/v1/agent/execute` - Ejecutar agente
  - `GET /api/v1/agent/status/{agent_run_id}` - Estado de ejecución

---

## Implementación

### Backend (Python/FastAPI)

#### 1. Variable de Entorno

**Archivo:** `src/backoffice/settings.py`

```python
# Admin Authentication (Paso 3 - Frontend Dashboard)
API_ADMIN_TOKEN: str = "change-me-in-production"
```

**Archivo:** `.env`

```bash
# Token de administración para acceso al dashboard web
API_ADMIN_TOKEN=agentix-admin-dev-token-2024
```

#### 2. Router de Autenticación

**Archivo:** `src/api/routers/auth.py`

```python
@router.post("/validate-admin-token")
async def validate_admin_token(request: TokenValidationRequest):
    if request.token == settings.API_ADMIN_TOKEN:
        return TokenValidationResponse(valid=True, message="Token válido")
    else:
        raise HTTPException(status_code=401, detail={"valid": False, "message": "Token inválido"})
```

**Registrado en:** `src/api/main.py`

```python
from .routers import agent, auth, health

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)
```

#### 3. Configuración de CORS

**Archivo:** `.env`

```bash
# CORS - Incluye puerto del frontend y wildcard para Codespaces
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080,*
```

**Archivo:** `src/api/main.py`

```python
cors_origins = settings.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Frontend (React/TypeScript)

#### 1. Configuración de Vite

**Archivo:** `frontend/vite.config.ts`

```typescript
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true, // Necesario para Codespaces
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
})
```

**Archivo:** `frontend/.env`

```bash
VITE_API_URL=http://localhost:8080
```

#### 2. Tipos TypeScript para Vite

**Archivo:** `frontend/src/vite-env.d.ts` (CRÍTICO)

```typescript
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

**Problema resuelto:** Sin este archivo, TypeScript no reconoce `import.meta.env` y la compilación falla.

#### 3. Servicio de Autenticación

**Archivo:** `frontend/src/services/authService.ts`

```typescript
export const authService = {
  validateAdminToken: async (token: string): Promise<boolean> => {
    const response = await api.post<TokenValidationResponse>(
      '/api/v1/auth/validate-admin-token',
      { token }
    );
    return response.data.valid;
  },
};
```

#### 4. Contexto de Autenticación

**Archivo:** `frontend/src/contexts/AuthContext.tsx`

- Gestiona estado de autenticación (token, loading, isAuthenticated)
- Funciones: `login()`, `logout()`
- Almacenamiento en `localStorage`

#### 5. Componente ProtectedRoute

**Archivo:** `frontend/src/components/auth/ProtectedRoute.tsx`

- Verifica autenticación antes de renderizar rutas protegidas
- Redirige a `/login` si no hay token
- Muestra spinner durante carga

#### 6. Página de Login

**Archivo:** `frontend/src/pages/Login.tsx`

- Input de tipo password para token
- Validación con backend al submit
- Manejo de errores (token inválido)
- Redirección a `/dashboard` si éxito

---

## Estructura de Archivos (Frontend)

```
frontend/
├── public/
│   ├── test.html              # Página de prueba para debugging
│   └── vite.svg
├── src/
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx        # [NO USADO - Login es página]
│   │   │   ├── ProtectedRoute.tsx   # ✅ Protección de rutas
│   │   │   └── LogoutButton.tsx     # ✅ Botón de logout
│   │   ├── layout/
│   │   │   ├── Layout.tsx           # ✅ Layout con Header + Sidebar
│   │   │   ├── Header.tsx           # ✅ Header con logo y logout
│   │   │   └── Sidebar.tsx          # ✅ Navegación lateral
│   │   └── ui/
│   │       ├── Button.tsx           # ✅ Componente Button reutilizable
│   │       ├── Card.tsx             # ✅ Componente Card
│   │       ├── Input.tsx            # ✅ Input con label y error
│   │       ├── Select.tsx           # Componente Select (base)
│   │       └── Badge.tsx            # Componente Badge (base)
│   ├── contexts/
│   │   └── AuthContext.tsx          # ✅ Context de autenticación
│   ├── hooks/
│   │   └── useAuth.ts               # ✅ Hook para consumir AuthContext
│   ├── pages/
│   │   ├── Login.tsx                # ✅ Página de login
│   │   ├── Dashboard.tsx            # ✅ Dashboard (placeholders Fase 2)
│   │   ├── Logs.tsx                 # Placeholder (Fase 3)
│   │   └── TestPanel.tsx            # Placeholder (Fase 4)
│   ├── services/
│   │   ├── api.ts                   # ✅ Cliente Axios con interceptors
│   │   └── authService.ts           # ✅ Servicio de autenticación
│   ├── types/
│   │   ├── auth.ts                  # ✅ Tipos de autenticación
│   │   ├── agent.ts                 # Tipos de agentes (base)
│   │   ├── logs.ts                  # Tipos de logs (base)
│   │   ├── metrics.ts               # Tipos de métricas (base)
│   │   └── api.ts                   # Tipos de API (base)
│   ├── utils/
│   │   ├── storage.ts               # ✅ Helpers de localStorage
│   │   └── formatters.ts            # Helpers de formato (base)
│   ├── App.tsx                      # ✅ Routing y estructura
│   ├── main.tsx                     # ✅ Entry point
│   ├── index.css                    # ✅ Estilos base + Tailwind
│   └── vite-env.d.ts                # ✅ CRÍTICO: Tipos de Vite
├── .env                             # ✅ VITE_API_URL=http://localhost:8080
├── package.json                     # ✅ Dependencias
├── tsconfig.json                    # ✅ Config TypeScript
├── tailwind.config.js               # ✅ Config Tailwind (colores primary)
├── vite.config.ts                   # ✅ Config Vite (host: true)
└── README.md                        # Instrucciones de setup
```

---

## Problemas Encontrados y Soluciones

### 1. Pantalla en Blanco al Cargar

**Problema:**
- Navegador mostraba pantalla en blanco
- Título de la pestaña vacío
- Consola sin errores

**Causa:**
- Errores de compilación TypeScript bloqueaban la aplicación
- Faltaba `src/vite-env.d.ts` con definiciones de tipos

**Solución:**
```typescript
// frontend/src/vite-env.d.ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

### 2. No Renderiza en Codespaces

**Problema:**
- Intentando acceder a `http://localhost:5173` desde navegador local
- Servidor corriendo en contenedor de Codespaces

**Causa:**
- Vite no escuchaba en todas las interfaces de red
- Port forwarding de Codespaces no funcionaba

**Solución:**
```typescript
// vite.config.ts
server: {
  port: 5173,
  host: true, // ← Escuchar en todas las interfaces
}
```

Acceder mediante URL de Codespaces (panel PORTS en VS Code).

### 3. Error ECONNREFUSED al Hacer Login

**Problema:**
```
Error: connect ECONNREFUSED 127.0.0.1:8000
```

**Causa:**
- Frontend apuntaba a puerto incorrecto
- `.env` tenía `VITE_API_URL=http://localhost:5173` (a sí mismo)
- Backend corre en puerto **8080**, no 8000

**Solución:**
```bash
# frontend/.env
VITE_API_URL=http://localhost:8080
```

### 4. Error de CORS

**Problema:**
```
Access to XMLHttpRequest blocked by CORS policy
```

**Causa:**
- CORS configurado solo para puertos 3000 y 8080
- Frontend corre en puerto 5173

**Solución:**
```bash
# .env (backend)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080,*
```

El `*` permite cualquier origen (útil para URLs dinámicas de Codespaces).

**Importante:** Reiniciar backend después de cambiar `.env` (no hot-reload).

---

## Testing Manual

### 1. Verificar Backend

```bash
# Backend debe estar corriendo en puerto 8080
curl http://localhost:8080/health

# Probar endpoint de autenticación
curl -X POST http://localhost:8080/api/v1/auth/validate-admin-token \
  -H "Content-Type: application/json" \
  -d '{"token": "agentix-admin-dev-token-2024"}'

# Respuesta esperada:
# {"valid":true,"message":"Token válido"}
```

### 2. Verificar Frontend

1. **Acceder a la aplicación:**
   - Codespaces: Panel PORTS → Puerto 5173 → Abrir en navegador
   - Local: `http://localhost:5173`

2. **Página de login:**
   - Debe mostrar título "aGEntiX"
   - Input de password para token
   - Botón "Acceder al Dashboard"

3. **Login exitoso:**
   - Token: `agentix-admin-dev-token-2024`
   - Debe redirigir a `/dashboard`
   - Header debe mostrar botón "Cerrar Sesión"

4. **Protección de rutas:**
   - Cerrar sesión
   - Intentar acceder a `/dashboard` directamente
   - Debe redirigir a `/login`

---

## Configuración para Desarrollo

### Iniciar Backend

```bash
cd /workspaces/aGEntiX

# Asegurarse de que .env tiene API_ADMIN_TOKEN
grep API_ADMIN_TOKEN .env

# Iniciar servidor
python -m uvicorn src.api.main:app --reload --port 8080
```

### Iniciar Frontend

```bash
cd /workspaces/aGEntiX/frontend

# Asegurarse de que .env apunta al backend correcto
grep VITE_API_URL .env

# Iniciar Vite
npm run dev
```

### Configuración Mínima Requerida

**Backend `.env`:**
```bash
JWT_SECRET=change-me-in-production-use-openssl-rand
API_ADMIN_TOKEN=agentix-admin-dev-token-2024
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080,*
```

**Frontend `.env`:**
```bash
VITE_API_URL=http://localhost:8080
```

---

## Token de Admin en Producción

**IMPORTANTE:** En producción, generar token seguro:

```bash
# Opción 1: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Opción 2: OpenSSL
openssl rand -base64 32

# Opción 3: Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

Actualizar `.env`:
```bash
API_ADMIN_TOKEN=<token-generado-seguro>
```

**Política de seguridad:**
- Mínimo 32 caracteres
- Rotación cada 90 días
- No compartir en repositorio (`.env` en `.gitignore`)
- Usar gestor de secretos (AWS Secrets Manager, Vault, etc.)

---

## Próximos Pasos (Fase 2)

- [ ] Implementar Dashboard de Métricas
  - Endpoint `GET /api/v1/dashboard/metrics`
  - Gráficos con Recharts
  - KPIs en tiempo real
  - Auto-refresh cada 10 segundos

- [ ] Implementar Visor de Logs
  - Endpoint `GET /api/v1/logs`
  - Endpoint `GET /api/v1/logs/stream` (SSE)
  - Filtros por nivel, componente, agente, fecha
  - Resaltado de PII redactado

- [ ] Implementar Panel de Pruebas de Agentes
  - Endpoint `POST /api/v1/auth/generate-jwt`
  - Selector de agentes
  - Generador de JWT de prueba
  - Visualización de resultados en tiempo real

---

## Referencias

- **Prompt original:** `/prompts/step-3-frontend.md`
- **Backend (Paso 2):** `/src/api/`
- **Back-office (Paso 1):** `/src/backoffice/`
- **Code review Paso 1:** `/code-review/commit-c039abe/`
- **Documentación Zettelkasten:** `/doc/index.md`

---

**Documentado por:** Claude Code
**Fecha:** 2025-12-21
