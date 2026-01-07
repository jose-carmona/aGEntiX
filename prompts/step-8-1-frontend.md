# Step 8.1: Mejoras Frontend - Panel MCP Unificado

## Objetivo

Mejorar la página `MCPServerMock.tsx` para demostrar los dos módulos MCP disponibles:
- **mcp_expedientes**: Gestión de expedientes (10 tools)
- **mcp_documentacion**: Documentación de tipos de expediente (3 tools)

---

## Estado Actual

### Limitaciones del Panel Actual

| Aspecto | Problema |
|---------|----------|
| **Cobertura** | Solo prueba tools de expedientes, ignora documentación |
| **Interactividad** | Secuencia de tests fija, no permite exploración |
| **Permisos** | Genera token con permisos hardcodeados (`consulta`, `gestion`) |
| **Visualización** | Todo en JSON crudo, sin renderizado de markdown |
| **UX** | Lista larga de resultados sin organización por módulo |

### Tools NO Probadas Actualmente

```
listar_documentacion        # Lista docs por tipo expediente
obtener_doc_documentacion   # Obtiene contenido completo
buscar_en_documentacion     # Búsqueda de texto
```

---

## Propuesta de Mejoras

### 1. Diseño con Tabs por Módulo

```
┌─────────────────────────────────────────────────────────────────┐
│  MCP Server Mock                                    [🔄 Refresh] │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Expedientes  │  │ Documentación│  │  Explorador  │           │
│  │   (10 tools) │  │   (3 tools)  │  │  Interactivo │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Contenido del tab activo]                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Estructura de Componentes

```
frontend/src/
├── pages/
│   └── MCPServerMock.tsx              # Página principal (refactorizada)
│
└── components/
    └── mcp/
        ├── MCPTabs.tsx                # Navegación por tabs
        ├── MCPTokenGenerator.tsx      # Generador de tokens configurable
        ├── MCPServerStatus.tsx        # Health + Info (existente, extraído)
        │
        ├── expedientes/
        │   ├── ExpedientesPanel.tsx   # Panel de pruebas expedientes
        │   ├── ExpedienteSelector.tsx # Selector de expediente
        │   └── ExpedienteViewer.tsx   # Visualización de expediente
        │
        ├── documentacion/
        │   ├── DocumentacionPanel.tsx # Panel de pruebas documentación
        │   ├── TipoExpedienteSelector.tsx  # Selector: subvenciones, licencias, etc.
        │   ├── DocumentacionList.tsx  # Lista de documentos disponibles
        │   └── DocumentacionViewer.tsx # Visualización con markdown
        │
        └── explorer/
            ├── ToolExplorer.tsx       # Explorador interactivo de tools
            ├── ToolForm.tsx           # Formulario dinámico según schema
            └── ResourceExplorer.tsx   # Explorador de resources
```

---

## Tab 1: Expedientes

### Funcionalidades

1. **Selector de Expediente**
   - Dropdown con expedientes disponibles: `EXP-2024-001`, `EXP-2024-002`, `EXP-2024-003`
   - Mostrar tipo de expediente junto al ID

2. **Acciones Rápidas** (botones)
   - `Consultar Expediente` → `consultar_expediente`
   - `Listar Documentos` → `listar_documentos`
   - `Ver Historial` → resource `expediente://{id}/historial`

3. **Sección Documentos del Expediente**
   - Lista de documentos con acciones:
     - `Ver Texto` → `obtener_texto_documento`
     - `Ver Metadatos` → `obtener_metadatos_documento`
   - Visualización markdown para textos

4. **Acciones de Escritura** (colapsable)
   - Formulario para `añadir_anotacion`
   - Formulario para `actualizar_datos`
   - Formulario para `crear_documento_desde_markdown`

### Wireframe Tab Expedientes

```
┌─────────────────────────────────────────────────────────────────┐
│ EXPEDIENTES                                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Expediente: [EXP-2024-001 ▼] (SUBVENCIONES - EN_TRAMITE)       │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ 📋 Consultar    │  │ 📄 Documentos   │  │ 📜 Historial    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│ Documentos del Expediente                                [4]     │
├─────────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ DOC-001 | solicitud.pdf | SOLICITUD                        │  │
│ │ [Ver Texto] [Ver Metadatos]                                │  │
│ ├────────────────────────────────────────────────────────────┤  │
│ │ DOC-002 | dni_solicitante.pdf | IDENTIFICACION             │  │
│ │ [Ver Texto] [Ver Metadatos]                                │  │
│ └────────────────────────────────────────────────────────────┘  │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│ ▶ Acciones de Escritura                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tab 2: Documentación

### Funcionalidades

1. **Selector de Tipo de Expediente**
   - `subvenciones` | `licencias_obras` | `certificado_empadronamiento`
   - Mostrar descripción del tipo seleccionado

2. **Lista de Documentación Disponible**
   - Cargar automáticamente al seleccionar tipo → `listar_documentacion`
   - Mostrar: ID, tipo (normativa/instrucciones/plantilla), descripción

3. **Visor de Documento**
   - Seleccionar documento de la lista → `obtener_doc_documentacion`
   - Renderizar contenido markdown con estilos
   - Mostrar `instrucciones_agente` destacadas

4. **Búsqueda en Documentación**
   - Input de búsqueda → `buscar_en_documentacion`
   - Mostrar resultados con contexto y línea
   - Filtro opcional por tipo de documento

### Wireframe Tab Documentación

```
┌─────────────────────────────────────────────────────────────────┐
│ DOCUMENTACIÓN                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Tipo Expediente: [Subvenciones ▼]                              │
│  Descripción: Gestión de solicitudes de ayudas y subvenciones   │
│                                                                  │
├──────────────────────────┬──────────────────────────────────────┤
│ Documentos Disponibles   │  Contenido del Documento              │
├──────────────────────────┼──────────────────────────────────────┤
│                          │                                       │
│ ○ SUB-NORM-001          │  # Normativa Regulatoria              │
│   normativa              │                                       │
│   "Normativa aplicable"  │  ## Instrucciones para el Agente     │
│                          │  ┌─────────────────────────────────┐ │
│ ● SUB-INST-001          │  │ Utiliza esta normativa para...   │ │
│   instrucciones          │  └─────────────────────────────────┘ │
│   "Instrucciones de..."  │                                       │
│                          │  ## 1. Ley General de Subvenciones   │
│ ○ SUB-TPL-001           │                                       │
│   plantilla              │  La Ley 38/2003, de 17 de noviembre │
│   "Plantilla propuesta"  │  establece el régimen jurídico...   │
│                          │                                       │
├──────────────────────────┴──────────────────────────────────────┤
│ 🔍 Buscar en documentación                                       │
├─────────────────────────────────────────────────────────────────┤
│ [                        ] [Buscar]  Filtro: [Todos ▼]          │
│                                                                  │
│ Resultados:                                                      │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ SUB-NORM-001 (línea 15): "...plazo máximo de 6 meses..."   │  │
│ │ SUB-INST-001 (línea 42): "...verificar plazo según art..." │  │
│ └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tab 3: Explorador Interactivo

### Funcionalidades

1. **Lista de Tools** (dinámico desde `tools/list`)
   - Agrupar por módulo (expedientes vs documentación)
   - Mostrar descripción e inputSchema

2. **Formulario Dinámico**
   - Generar inputs según `inputSchema` de cada tool
   - Validación de campos requeridos
   - Soporte para enums (dropdown)

3. **Lista de Resources** (dinámico desde `resources/list`)
   - Agrupar por tipo (expediente:// vs documentacion://)
   - Botón para leer cada resource

4. **Historial de Ejecuciones**
   - Log de llamadas realizadas en la sesión
   - Tiempo de respuesta
   - Request/Response colapsables

### Wireframe Tab Explorador

```
┌─────────────────────────────────────────────────────────────────┐
│ EXPLORADOR INTERACTIVO                                           │
├──────────────────────────┬──────────────────────────────────────┤
│ Tools Disponibles        │  Ejecutar Tool                        │
├──────────────────────────┼──────────────────────────────────────┤
│                          │                                       │
│ ▼ Expedientes (10)       │  Tool: obtener_doc_documentacion      │
│   ○ consultar_expediente │  ─────────────────────────────────── │
│   ○ listar_documentos    │                                       │
│   ○ obtener_documento    │  tipo_expediente: [subvenciones ▼]   │
│   ...                    │                                       │
│                          │  tipo_documento: [normativa ▼]        │
│ ▼ Documentación (3)      │                                       │
│   ● listar_documentacion │          [Ejecutar Tool]              │
│   ○ obtener_doc_documen..│                                       │
│   ○ buscar_en_documen... │  ─────────────────────────────────── │
│                          │  Resultado:                           │
├──────────────────────────┤  ┌─────────────────────────────────┐ │
│ Resources Disponibles    │  │ {                               │ │
├──────────────────────────┤  │   "id": "SUB-NORM-001",         │ │
│                          │  │   "tipo": "normativa",          │ │
│ ▼ Expedientes (9)        │  │   "contenido": "# Normativa..." │ │
│   expediente://EXP-2024..│  │ }                               │ │
│   ...                    │  └─────────────────────────────────┘ │
│                          │                                       │
│ ▼ Documentación (3)      │                                       │
│   documentacion://subven.│                                       │
│   ...                    │                                       │
└──────────────────────────┴──────────────────────────────────────┘
```

---

## Generador de Token Mejorado

### Configuración Actual (limitada)

```typescript
// Solo genera con permisos fijos
permisos: ['consulta', 'gestion']
```

### Configuración Propuesta

```typescript
interface TokenConfig {
  exp_id: string;                    // Expediente ID
  exp_tipo: TipoExpediente;          // Tipo (para documentación)
  permisos: string[];                // Checkboxes seleccionables
  mcp_servers: string[];             // Servidores autorizados
}

// Permisos seleccionables:
const PERMISOS_DISPONIBLES = [
  { id: 'consulta', label: 'Consulta', modulo: 'expedientes' },
  { id: 'gestion', label: 'Gestión', modulo: 'expedientes' },
  { id: 'documentacion:leer', label: 'Leer Documentación', modulo: 'documentacion' },
  { id: 'documentacion:buscar', label: 'Buscar en Documentación', modulo: 'documentacion' },
];
```

### Wireframe Generador Token

```
┌─────────────────────────────────────────────────────────────────┐
│ Configuración del Token JWT                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Expediente: [EXP-2024-001 ▼]   Tipo: SUBVENCIONES              │
│                                                                  │
│  Permisos:                                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Expedientes           │ Documentación                       ││
│  │ ☑ consulta            │ ☑ documentacion:leer                ││
│  │ ☑ gestion             │ ☑ documentacion:buscar              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│                    [Generar Token]                               │
│                                                                  │
│  Token Claims:                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ iss: agentix-bpmn     │ exp_id: EXP-2024-001                ││
│  │ sub: Automático       │ exp_tipo: subvenciones              ││
│  │ permisos: consulta, gestion, documentacion:leer, ...        ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Cambios en Backend (API)

### Modificar `/api/v1/generate-jwt`

Añadir soporte para `exp_tipo` en el payload:

```python
# src/api/routers/agent.py

class GenerateJWTRequest(BaseModel):
    exp_id: str
    exp_tipo: Optional[str] = None  # NUEVO: subvenciones, licencias_obras, etc.
    tarea_id: str
    permisos: List[str]
    mcp_servers: List[str]
```

El backend debe inferir `exp_tipo` del expediente si no se proporciona.

---

## Visualización de Markdown

### Componente MarkdownViewer

```typescript
// components/ui/MarkdownViewer.tsx

interface MarkdownViewerProps {
  content: string;
  className?: string;
}

// Usar react-markdown con plugins:
// - remark-gfm (tablas, checkboxes)
// - rehype-highlight (syntax highlighting)
```

### Estilos para Documentación

```css
.doc-viewer {
  /* Tipografía legible */
  font-family: 'Inter', sans-serif;
  line-height: 1.6;
}

.doc-viewer h1, .doc-viewer h2 {
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 0.5rem;
}

.doc-viewer table {
  /* Tablas estilizadas para plantillas */
  border-collapse: collapse;
  width: 100%;
}

.instrucciones-agente {
  /* Destacar instrucciones para el agente */
  background: #fef3c7;
  border-left: 4px solid #f59e0b;
  padding: 1rem;
  margin: 1rem 0;
}
```

---

## Dependencias a Añadir

```json
{
  "dependencies": {
    "react-markdown": "^9.0.1",
    "remark-gfm": "^4.0.0",
    "rehype-highlight": "^7.0.0"
  }
}
```

---

## Plan de Implementación

### Fase 1: Refactorización Base ✅ COMPLETADA
- [x] Extraer componentes existentes (`MCPServerStatus`, `MCPTokenGenerator`)
- [x] Crear estructura de carpetas `components/mcp/`
- [x] Implementar sistema de tabs (`MCPTabs`)

### Fase 2: Tab Documentación ✅ COMPLETADA
- [x] `TipoExpedienteSelector` con los 3 tipos
- [x] `DocumentacionList` llamando a `listar_documentacion`
- [x] `DocumentacionViewer` con visualización de contenido
- [x] Integrar búsqueda con `buscar_en_documentacion`

### Fase 3: Mejoras Tab Expedientes ✅ COMPLETADA
- [x] `ExpedienteSelector` con los 3 expedientes de prueba
- [x] Acciones rápidas (Consultar, Documentos, Historial)
- [x] Suite de pruebas completa (6 tests)

### Fase 4: Explorador Interactivo ✅ COMPLETADA
- [x] `ToolExplorer` con agrupación por módulo (expedientes/documentación)
- [x] `ToolForm` dinámico según inputSchema (enum, boolean, object, string)
- [x] `ResourceExplorer` con lectura inline

### Fase 5: Token Mejorado ✅ COMPLETADA
- [x] Checkboxes de permisos (consulta, gestion, documentacion:leer, documentacion:buscar)
- [x] Inferencia de tipo expediente según ID seleccionado
- [ ] Actualizar backend para `exp_tipo` (opcional, no requerido)

---

## Criterios de Aceptación

1. **Funcional**
   - [x] Se pueden probar las 13 tools disponibles
   - [x] Se pueden leer todos los resources
   - [x] El contenido de documentación se visualiza correctamente
   - [x] La búsqueda en documentación funciona

2. **UX**
   - [x] Navegación clara por tabs
   - [x] Feedback visual de loading/success/error
   - [x] Resultados organizados por módulo

3. **Técnico**
   - [x] Componentes reutilizables
   - [x] TypeScript strict (build sin errores)
   - [x] No hay código duplicado entre tabs

---

## Notas de Implementación

### Permisos del Token

Para que las tools de documentación funcionen, el token debe incluir:

```typescript
permisos: [
  'consulta',              // Para tools de expedientes (lectura)
  'gestion',               // Para tools de expedientes (escritura)
  'documentacion:leer',    // Para listar_documentacion, obtener_doc_documentacion
  'documentacion:buscar'   // Para buscar_en_documentacion
]
```

### Mapeo Tipo Expediente

| ID Expediente | Tipo Expediente |
|---------------|-----------------|
| EXP-2024-001 | subvenciones |
| EXP-2024-002 | licencias_obras |
| EXP-2024-003 | certificado_empadronamiento |

El frontend debe conocer este mapeo para auto-seleccionar el tipo de documentación relevante.

### Documentos por Tipo

| Tipo | Documentos |
|------|------------|
| subvenciones | normativa, instrucciones_tramitacion, plantilla_propuesta_resolucion, plantilla_requerimiento_documentacion |
| licencias_obras | normativa, instrucciones_tramitacion, plantilla_propuesta_resolucion, plantilla_requerimiento_documentacion |
| certificado_empadronamiento | normativa, instrucciones_tramitacion, plantilla_certificado, plantilla_requerimiento_documentacion |

---

## Resumen de Cambios Implementados

| Archivo | Estado | Descripción |
|---------|--------|-------------|
| `pages/MCPServerMock.tsx` | ✅ Refactorizado | 76 líneas → usa componentes modulares |
| `components/mcp/index.ts` | ✅ Nuevo | Exportaciones del módulo |
| `components/mcp/MCPServerStatus.tsx` | ✅ Nuevo | Health + Info + Endpoints |
| `components/mcp/MCPTokenGenerator.tsx` | ✅ Nuevo | Token con checkboxes de permisos |
| `components/mcp/MCPTabs.tsx` | ✅ Nuevo | Navegación por tabs con badges |
| `components/mcp/expedientes/ExpedientesPanel.tsx` | ✅ Nuevo | 6 tests de tools expedientes |
| `components/mcp/documentacion/DocumentacionPanel.tsx` | ✅ Nuevo | Lista, visualiza y busca docs |
| `components/mcp/explorer/ExplorerPanel.tsx` | ✅ Nuevo | Formularios dinámicos para 13 tools |
| `services/mcpService.ts` | Sin cambios | Ya soportaba todas las operaciones |

### Build Final

```
dist/assets/index.css   27.66 kB │ gzip:   5.39 kB
dist/assets/index.js  1009.12 kB │ gzip: 288.92 kB
```

### Componentes Creados

```
frontend/src/components/mcp/
├── index.ts                          # Exportaciones
├── MCPServerStatus.tsx               # 170 líneas
├── MCPTokenGenerator.tsx             # 240 líneas
├── MCPTabs.tsx                       # 110 líneas
├── expedientes/
│   └── ExpedientesPanel.tsx          # 300 líneas
├── documentacion/
│   └── DocumentacionPanel.tsx        # 230 líneas
└── explorer/
    └── ExplorerPanel.tsx             # 430 líneas
```
