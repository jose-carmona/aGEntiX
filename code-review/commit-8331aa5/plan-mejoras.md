# Plan de Mejoras - Frontend aGEntiX

**Fecha:** 2024-12-24
**Commit Base:** 8331aa5
**Estado:** Pendiente de implementación

---

## Resumen de Prioridades

| Prioridad | Descripción | Items | Esfuerzo |
|-----------|-------------|-------|----------|
| P1 - Crítica | Resolver antes de merge | 4 | 4-6h |
| P2 - Alta | Primera semana | 6 | 8-12h |
| P3 - Media | Próximo sprint | 4 | 16-24h |
| P4 - Baja | Mejoras futuras | 4 | 8-12h |

---

## P1 - CRÍTICA (Resolver Inmediatamente)

### P1.1 - Eliminar Tipos `any` en Código Crítico

**Estado:** ⬜ Pendiente

**Archivos:**
- `frontend/src/components/test-panel/IntegratedExecutionForm.tsx`
- `frontend/src/hooks/useAgentExecution.ts`
- `frontend/src/pages/TestPanel.tsx`
- `frontend/src/services/agentService.ts`
- `frontend/src/components/dashboard/AgentExecutionsChart.tsx`

**Cambios:**

```typescript
// ANTES (IntegratedExecutionForm.tsx:152)
const parseValidationError = (detail: any): string => { ... }

// DESPUÉS
interface ValidationErrorDetail {
  loc: string[];
  msg: string;
  type?: string;
}
const parseValidationError = (detail: ValidationErrorDetail[] | string): string => { ... }
```

```typescript
// ANTES (agentService.ts:167)
export const decodeJWT = (token: string): any => { ... }

// DESPUÉS
export const decodeJWT = (token: string): JWTClaims | null => { ... }
```

---

### P1.2 - Implementar Debounce en saveConfiguration

**Estado:** ⬜ Pendiente

**Archivo:** `frontend/src/components/test-panel/IntegratedExecutionForm.tsx`

**Cambio:**

```typescript
// Añadir import
import { useRef, useCallback } from 'react';

// Añadir ref para timeout
const saveTimeoutRef = useRef<number | null>(null);

// Crear función con debounce
const saveConfigurationDebounced = useCallback(() => {
  if (saveTimeoutRef.current) {
    clearTimeout(saveTimeoutRef.current);
  }
  saveTimeoutRef.current = window.setTimeout(() => {
    try {
      const config = {
        expedienteId,
        expTipo,
        tareaId,
        tareaNombre,
        permisos,
        expHours
      };
      localStorage.setItem(STORAGE_CONFIG_KEY, JSON.stringify(config));
    } catch (err) {
      console.error('Error saving configuration:', err);
    }
  }, 500);
}, [expedienteId, expTipo, tareaId, tareaNombre, permisos, expHours]);

// Usar en useEffect
useEffect(() => {
  saveConfigurationDebounced();
  return () => {
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }
  };
}, [saveConfigurationDebounced]);
```

---

### P1.3 - Corregir useEffect Dependencies

**Estado:** ⬜ Pendiente

**Archivo:** `frontend/src/components/test-panel/IntegratedExecutionForm.tsx`

**Cambio:**

```typescript
// ANTES (líneas 69-77)
useEffect(() => {
  if (localError) {
    setLocalError(null);
    setErrorType(null);
  }
  if (executionError && onResetError) {
    onResetError();
  }
}, [expedienteId, expTipo, tareaId, tareaNombre, permisos, selectedAgentId]);

// DESPUÉS
useEffect(() => {
  if (localError) {
    setLocalError(null);
    setErrorType(null);
  }
}, [expedienteId, expTipo, tareaId, tareaNombre, permisos, selectedAgentId, localError]);

useEffect(() => {
  if (executionError && onResetError) {
    onResetError();
  }
}, [executionError, onResetError]);
```

---

### P1.4 - Validar Prompt con Mensaje Visual

**Estado:** ⬜ Pendiente

**Archivo:** `frontend/src/components/test-panel/IntegratedExecutionForm.tsx`

**Cambio:** Agregar mensaje visual cuando prompt esté vacío

```tsx
{/* Después del textarea de prompt */}
{!prompt.trim() && selectedAgentId && (
  <p className="mt-1 text-sm text-amber-600">
    El prompt es requerido. Use el predeterminado o escriba instrucciones.
  </p>
)}
```

---

## P2 - ALTA (Primera Semana)

### P2.1 - Instalar Testing Framework

**Estado:** ⬜ Pendiente

```bash
cd frontend
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

**Configuración vitest.config.ts:**

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
});
```

---

### P2.2 - Implementar Code Splitting

**Estado:** ⬜ Pendiente

**Archivo:** `frontend/src/App.tsx`

```typescript
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Logs = lazy(() => import('./pages/Logs'));
const TestPanel = lazy(() => import('./pages/TestPanel'));

// En Routes
<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route path="/dashboard" element={<Dashboard />} />
    <Route path="/logs" element={<Logs />} />
    <Route path="/test-panel" element={<TestPanel />} />
  </Routes>
</Suspense>
```

---

### P2.3 - Memoizar Componentes Dashboard

**Estado:** ⬜ Pendiente

**Archivos:**
- `frontend/src/components/dashboard/MetricsCard.tsx`
- `frontend/src/components/dashboard/AgentExecutionsChart.tsx`

```typescript
import { memo } from 'react';

export const MetricsCard = memo(({ title, value, ... }: MetricsCardProps) => {
  // ...
});
```

---

### P2.4 - Consolidar Estados en IntegratedExecutionForm

**Estado:** ⬜ Pendiente

**Cambio:** De 7+ useState a 1 objeto FormState

```typescript
interface FormState {
  expedienteId: string;
  expTipo: string;
  tareaId: string;
  tareaNombre: string;
  prompt: string;
  permisos: string[];
  expHours: number;
}

const [formState, setFormState] = useState<FormState>(initialFormState);

const updateField = <K extends keyof FormState>(
  field: K,
  value: FormState[K]
) => {
  setFormState(prev => ({ ...prev, [field]: value }));
};
```

---

### P2.5 - Crear Componente LoadingSpinner

**Estado:** ⬜ Pendiente

**Nuevo archivo:** `frontend/src/components/ui/LoadingSpinner.tsx`

```typescript
import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className = ''
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  };

  return (
    <svg
      className={`animate-spin ${sizeClasses[size]} ${className}`}
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
};
```

---

### P2.6 - Usar Constante para localStorage Key

**Estado:** ⬜ Pendiente

```typescript
// Añadir al inicio del archivo
const STORAGE_CONFIG_KEY = 'agentix_test_panel_config_v2';

// Reemplazar todas las ocurrencias
localStorage.getItem(STORAGE_CONFIG_KEY)
localStorage.setItem(STORAGE_CONFIG_KEY, ...)
```

---

## P3 - MEDIA (Próximo Sprint)

### P3.1 - Implementar Tests Unitarios

**Estado:** ⬜ Pendiente

**Meta:** 70% coverage

**Tests prioritarios:**
1. `src/components/auth/ProtectedRoute.test.tsx`
2. `src/hooks/useAuth.test.tsx`
3. `src/services/authService.test.ts`
4. `src/components/test-panel/IntegratedExecutionForm.test.tsx`

---

### P3.2 - Migrar Tokens a httpOnly Cookies

**Estado:** ⬜ Pendiente

**Cambios Backend:**
```python
# Set-Cookie: admin_token=...; HttpOnly; Secure; SameSite=Strict
```

**Cambios Frontend:**
- Eliminar `storage.ts`
- Configurar axios con `credentials: 'include'`

---

### P3.3 - Crear Documentación de Arquitectura

**Estado:** ⬜ Pendiente

**Nuevo archivo:** `frontend/ARCHITECTURE.md`

Contenido:
- Estructura de carpetas
- Patrones utilizados
- Flujos de datos
- Guía de componentes

---

### P3.4 - Mejorar Accesibilidad

**Estado:** ⬜ Pendiente

**Tareas:**
- [ ] Mejorar contraste de colores
- [ ] Agregar aria-labels a iconos
- [ ] Implementar focus management en Login
- [ ] Testing con screen readers

---

## P4 - BAJA (Mejoras Futuras)

### P4.1 - Implementar Storybook

**Estado:** ⬜ Pendiente

```bash
npx storybook@latest init
```

---

### P4.2 - Dark Mode

**Estado:** ⬜ Pendiente

---

### P4.3 - Internacionalización (i18n)

**Estado:** ⬜ Pendiente

---

### P4.4 - Performance Monitoring

**Estado:** ⬜ Pendiente

- Integrar Sentry
- Web Vitals monitoring

---

## Seguimiento

### Checklist de Implementación

**P1 - Crítica:**
- [ ] P1.1 - Eliminar tipos `any`
- [ ] P1.2 - Implementar debounce
- [ ] P1.3 - Corregir useEffect dependencies
- [ ] P1.4 - Validar prompt visualmente

**P2 - Alta:**
- [ ] P2.1 - Instalar testing framework
- [ ] P2.2 - Implementar code splitting
- [ ] P2.3 - Memoizar componentes
- [ ] P2.4 - Consolidar estados
- [ ] P2.5 - Crear LoadingSpinner
- [ ] P2.6 - Constante localStorage

**P3 - Media:**
- [ ] P3.1 - Tests unitarios (70%)
- [ ] P3.2 - Migrar tokens
- [ ] P3.3 - Documentación
- [ ] P3.4 - Accesibilidad

**P4 - Baja:**
- [ ] P4.1 - Storybook
- [ ] P4.2 - Dark mode
- [ ] P4.3 - i18n
- [ ] P4.4 - Monitoring

---

## Notas

- Las mejoras P1 deben completarse antes del próximo merge a main
- P2 debería completarse en la primera semana del próximo sprint
- P3 puede distribuirse a lo largo del sprint
- P4 son mejoras opcionales para cuando haya tiempo
