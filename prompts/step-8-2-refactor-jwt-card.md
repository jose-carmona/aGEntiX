# Step 8.2: Unificar Componentes de Configuración JWT

## Problema

Existen dos componentes que generan tokens JWT con configuraciones inconsistentes:

| Componente | Ubicación | Uso |
|------------|-----------|-----|
| `MCPTokenGenerator` | `components/mcp/MCPTokenGenerator.tsx` | Panel MCP Mock |
| `SimpleExecutionForm` | `components/simple-execution/SimpleExecutionForm.tsx` | Ejecución de agentes |

### Discrepancias Detectadas

| Aspecto | MCPTokenGenerator | SimpleExecutionForm |
|---------|-------------------|---------------------|
| **Permisos** | Hardcoded: `consulta`, `gestion`, `documentacion:leer`, `documentacion:buscar` | Dinámico: `getAvailablePermissions()` API |
| **Categorías** | Por módulo: `expedientes`, `documentacion` | Por tipo: `lectura`, `escritura`, `admin` |
| **Expedientes** | Selector con 3 opciones predefinidas | Input libre |
| **Tarea ID** | Hardcoded `TAREA-MCP-TEST` | Input configurable |
| **Persistencia** | No | localStorage |
| **Campos extra** | No | `additionalGoal`, `callbackUrl` |

### Permisos Correctos (MCPTokenGenerator)

```typescript
const PERMISOS_DISPONIBLES = [
  { id: 'consulta', label: 'Consulta', modulo: 'expedientes', description: 'Lectura de expedientes y documentos' },
  { id: 'gestion', label: 'Gestión', modulo: 'expedientes', description: 'Escritura en expedientes' },
  { id: 'documentacion:leer', label: 'Leer Documentación', modulo: 'documentacion', description: 'Listar y obtener documentación' },
  { id: 'documentacion:buscar', label: 'Buscar', modulo: 'documentacion', description: 'Búsqueda en documentación' },
];
```

---

## Solución Propuesta

### Crear Componente Unificado: `JWTConfigCard`

Un componente reutilizable que:
1. Use los permisos correctos (hardcoded)
2. Soporte diferentes modos de uso
3. Sea configurable vía props

### Estructura de Archivos

```
frontend/src/components/
├── jwt/                              # NUEVO - Componentes JWT
│   ├── index.ts                      # Exportaciones
│   ├── JWTConfigCard.tsx             # Componente principal
│   ├── ExpedienteSelector.tsx        # Selector de expediente
│   ├── PermisosSelector.tsx          # Checkboxes de permisos
│   ├── TokenClaimsDisplay.tsx        # Visualización de claims
│   └── constants.ts                  # PERMISOS_DISPONIBLES, EXPEDIENTES_PRUEBA
│
├── mcp/
│   ├── MCPTokenGenerator.tsx         # MODIFICAR - usar JWTConfigCard
│   └── ...
│
└── simple-execution/
    └── SimpleExecutionForm.tsx       # MODIFICAR - usar JWTConfigCard
```

---

## API del Componente

### Props de `JWTConfigCard`

```typescript
interface JWTConfigCardProps {
  // Modo de operación
  mode: 'standalone' | 'embedded';

  // Configuración inicial
  defaultExpedienteId?: string;
  defaultTareaId?: string;
  defaultPermisos?: string[];

  // Callbacks
  onTokenGenerated?: (result: TokenResult) => void;
  onConfigChange?: (config: JWTConfig) => void;

  // Opciones de UI
  showTareaId?: boolean;           // Default: false para MCP, true para ejecución
  showExpedienteSelector?: boolean; // Default: true (selector) vs input libre
  showClaimsPreview?: boolean;      // Default: true
  compact?: boolean;                // Default: false

  // Estado externo
  disabled?: boolean;
  isGenerating?: boolean;
}

interface JWTConfig {
  expedienteId: string;
  tareaId: string;
  permisos: string[];
}

interface TokenResult {
  token: string;
  claims: Record<string, unknown>;
}
```

### Uso en MCPTokenGenerator (simplificado)

```tsx
// components/mcp/MCPTokenGenerator.tsx
import { JWTConfigCard, useTokenGenerator } from '@/components/jwt';

export const MCPTokenGenerator: React.FC<Props> = ({ onTokenGenerated, disabled }) => {
  return (
    <JWTConfigCard
      mode="standalone"
      showTareaId={false}
      showExpedienteSelector={true}
      onTokenGenerated={onTokenGenerated}
      disabled={disabled}
    />
  );
};
```

### Uso en SimpleExecutionForm (integrado)

```tsx
// components/simple-execution/SimpleExecutionForm.tsx
import { JWTConfigCard } from '@/components/jwt';

export const SimpleExecutionForm: React.FC<Props> = ({ ... }) => {
  const [jwtConfig, setJwtConfig] = useState<JWTConfig | null>(null);

  return (
    <Card>
      {/* Configuración JWT embebida */}
      <JWTConfigCard
        mode="embedded"
        showTareaId={true}
        showExpedienteSelector={false}  // Input libre
        onConfigChange={setJwtConfig}
        compact={true}
      />

      {/* Campos adicionales de ejecución */}
      <div>
        <textarea placeholder="Objetivo adicional..." />
        <input placeholder="URL Callback..." />
      </div>

      <Button onClick={handleExecute}>Ejecutar</Button>
    </Card>
  );
};
```

---

## Plan de Implementación

### Fase 1: Crear módulo `jwt/` ✅

- [x] Crear `constants.ts` con permisos y expedientes
- [x] Crear `ExpedienteSelector.tsx`
- [x] Crear `PermisosSelector.tsx`
- [x] Crear `TokenClaimsDisplay.tsx`
- [x] Crear `JWTConfigCard.tsx`
- [x] Crear `index.ts` con exportaciones

### Fase 2: Migrar MCPTokenGenerator ✅

- [x] Importar `JWTConfigCard` desde `@/components/jwt`
- [x] Reemplazar implementación por wrapper de `JWTConfigCard`
- [x] Mantener exportaciones existentes para compatibilidad
- [x] Verificar funcionamiento en panel MCP

### Fase 3: Migrar SimpleExecutionForm ✅

- [x] Eliminar carga dinámica de permisos (`getAvailablePermissions`)
- [x] Reemplazar sección de permisos por componentes JWT compartidos
- [x] Mantener campos adicionales (additionalGoal, callbackUrl)
- [x] Verificar funcionamiento en panel de ejecución

### Fase 4: Limpieza ✅

- [x] Eliminar `getAvailablePermissions` del API (`agentService.ts`)
- [x] Eliminar tipo `Permission` (`types/agent.ts`)
- [x] Build verificado exitosamente

---

## Componentes Detallados

### `constants.ts`

```typescript
export type TipoExpediente = 'subvenciones' | 'licencias_obras' | 'certificado_empadronamiento';

export const EXPEDIENTES_PRUEBA = [
  { id: 'EXP-2024-001', tipo: 'subvenciones' as TipoExpediente, label: 'Subvención Asociación Cultural' },
  { id: 'EXP-2024-002', tipo: 'licencias_obras' as TipoExpediente, label: 'Licencia Obra Menor' },
  { id: 'EXP-2024-003', tipo: 'certificado_empadronamiento' as TipoExpediente, label: 'Certificado Empadronamiento' },
] as const;

export type ModuloPermiso = 'expedientes' | 'documentacion';

export interface PermisoDefinition {
  id: string;
  label: string;
  modulo: ModuloPermiso;
  description: string;
}

export const PERMISOS_DISPONIBLES: PermisoDefinition[] = [
  { id: 'consulta', label: 'Consulta', modulo: 'expedientes', description: 'Lectura de expedientes y documentos' },
  { id: 'gestion', label: 'Gestión', modulo: 'expedientes', description: 'Escritura en expedientes' },
  { id: 'documentacion:leer', label: 'Leer Documentación', modulo: 'documentacion', description: 'Listar y obtener documentación' },
  { id: 'documentacion:buscar', label: 'Buscar', modulo: 'documentacion', description: 'Búsqueda en documentación' },
];

export const DEFAULT_PERMISOS = ['consulta', 'gestion', 'documentacion:leer', 'documentacion:buscar'];
```

### `PermisosSelector.tsx`

```typescript
interface PermisosSelectorProps {
  selected: string[];
  onChange: (permisos: string[]) => void;
  disabled?: boolean;
  layout?: 'grid' | 'compact';
}
```

### `ExpedienteSelector.tsx`

```typescript
interface ExpedienteSelectorProps {
  value: string;
  onChange: (id: string) => void;
  mode: 'select' | 'input';  // select = dropdown, input = texto libre
  disabled?: boolean;
  showTipo?: boolean;
}
```

---

## Criterios de Aceptación ✅

1. **Funcional**
   - [x] JWTConfigCard funciona en modo standalone (MCP)
   - [x] JWTConfigCard funciona en modo embedded (Ejecución)
   - [x] Los 4 permisos correctos se muestran en ambos sitios
   - [x] Token generado incluye permisos seleccionados

2. **UX**
   - [x] UI consistente en ambos paneles
   - [x] Checkboxes organizados por módulo
   - [x] Feedback de loading/error

3. **Código**
   - [x] Sin duplicación de lógica de permisos
   - [x] Tipos compartidos desde constants.ts
   - [x] Componentes pequeños y enfocados

---

## Impacto

| Archivo | Acción | Líneas |
|---------|--------|--------|
| `components/jwt/*` | Crear | ~400 |
| `components/mcp/MCPTokenGenerator.tsx` | Simplificar | -150 |
| `components/simple-execution/SimpleExecutionForm.tsx` | Simplificar | -80 |
| `services/agentService.ts` | Eliminar `getAvailablePermissions` | -10 |

**Resultado neto:** +160 líneas, pero código más mantenible y consistente.
