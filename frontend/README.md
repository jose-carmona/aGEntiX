# aGEntiX Dashboard - Frontend

Dashboard de administración para el sistema de agentes aGEntiX.

## Tecnologías

- **React 18** con **TypeScript**
- **Vite** como build tool
- **TailwindCSS** para estilos
- **React Router** para navegación
- **Axios** para peticiones HTTP
- **React Query** para gestión de estado del servidor

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
│   │   ├── layout/        # Layout principal (Header, Sidebar)
│   │   └── ui/            # Componentes UI reutilizables
│   ├── contexts/          # Contextos de React (AuthContext)
│   ├── hooks/             # Custom hooks
│   ├── pages/             # Páginas de la aplicación
│   ├── services/          # Servicios API
│   ├── types/             # Tipos TypeScript
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
- Dashboard (placeholder)
- Logs (placeholder)
- TestPanel (placeholder)

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

### Fase 2: Dashboard de Métricas
- Gráficos interactivos
- KPIs del sistema
- Auto-refresh de métricas

### Fase 3: Visor de Logs
- Sistema de filtros
- Búsqueda de texto completo
- Streaming de logs en tiempo real

### Fase 4: Panel de Pruebas de Agentes
- Selector de agentes
- Generador de JWT
- Visualizador de resultados

### Fase 5: Refinamiento y Testing
- Tests unitarios
- Tests de componentes
- Optimización de performance

## Soporte

Para más información sobre el proyecto completo, consulta el README principal en la raíz del proyecto.
