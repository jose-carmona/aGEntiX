# Code Review: commit-5be9402

**Visor de Expedientes: Frontend + API con autenticación admin**

| Métrica | Valor |
|---------|-------|
| Fecha | 2026-01-04 |
| Archivos modificados | 9 |
| Líneas añadidas | +2,726 |
| Líneas eliminadas | -61 |
| Calidad General | 4.2/5 |

## Resumen Ejecutivo

Este commit implementa un **Visor de Expedientes** completo con arquitectura de 3 capas:

```
Frontend (React) → API REST (FastAPI) → MCP Server
     ↓                    ↓                  ↓
  Admin Token        JWT Interno         Mock Data
```

### Puntos Fuertes

1. **Arquitectura correcta**: El frontend no accede directamente al MCP
2. **Reutilización de autenticación**: Usa el mismo admin token del dashboard
3. **Separación de responsabilidades**: Backend genera JWT internos
4. **UI/UX bien diseñada**: Layout de 3 paneles con estados de carga
5. **Documentación OpenAPI**: Endpoints bien documentados con ejemplos

### Áreas de Mejora

1. **Imports no optimizados** en `mcp_client.py`
2. **Configuración MCP_BASE_URL** debería estar en settings
3. **Falta de tests** para los nuevos endpoints
4. **Warning en useEffect** por dependencias faltantes

## Análisis Detallado

### Backend: `src/api/services/mcp_client.py`

**Calidad: 4.0/5**

| Aspecto | Estado | Notas |
|---------|--------|-------|
| Manejo de errores | ✅ Bueno | MCPClientError con códigos HTTP |
| Async/await | ✅ Correcto | Uso apropiado de httpx |
| Logging | ✅ Adecuado | Logs en puntos clave |
| Seguridad | ✅ Bueno | JWT generados internamente |

**Issues encontrados:**

```python
# P1: Import dentro de funciones (líneas 178, 209, 244, 278)
# ACTUAL:
content = result.get("content", [])
if content and len(content) > 0:
    import json  # ❌ Import repetido dentro de función
    text = content[0].get("text", "{}")
    return json.loads(text)

# RECOMENDADO: Mover import al inicio del archivo
```

```python
# P2: MCP_BASE_URL como constante local
# ACTUAL:
MCP_BASE_URL = getattr(settings, 'MCP_BASE_URL', 'http://localhost:8000')

# RECOMENDADO: Añadir a settings.py
class Settings(BaseSettings):
    MCP_BASE_URL: str = "http://localhost:8000"
```

### Backend: `src/api/routers/expedientes.py`

**Calidad: 4.5/5**

| Aspecto | Estado | Notas |
|---------|--------|-------|
| Endpoints RESTful | ✅ Excelente | Rutas jerárquicas correctas |
| Autenticación | ✅ Correcto | Todos usan verify_admin_token |
| Modelos Pydantic | ✅ Completos | Con ejemplos para OpenAPI |
| Error handling | ✅ Robusto | Try/except con logs |

**Estructura de endpoints:**

| Método | Ruta | Propósito |
|--------|------|-----------|
| GET | `/mcp-status` | Estado del MCP |
| GET | `/` | Lista expedientes |
| GET | `/{id}` | Expediente completo |
| GET | `/{id}/documentos` | Lista documentos |
| GET | `/{id}/documentos/{doc_id}/texto` | Markdown |
| GET | `/{id}/documentos/{doc_id}/metadatos` | Metadatos |

### Frontend: `src/services/expedientesService.ts`

**Calidad: 4.5/5**

| Aspecto | Estado | Notas |
|---------|--------|-------|
| TypeScript types | ✅ Completos | Interfaces bien definidas |
| API client | ✅ Correcto | Usa cliente compartido |
| Funciones async | ✅ Limpias | Una función por endpoint |

### Frontend: `src/pages/ExpedienteViewer.tsx`

**Calidad: 4.0/5**

| Aspecto | Estado | Notas |
|---------|--------|-------|
| Layout | ✅ Excelente | 3 paneles responsivos |
| Estados de carga | ✅ Completos | Loading, error, empty |
| Markdown rendering | ✅ Correcto | react-markdown + remark-gfm |
| UX | ✅ Buena | Indicadores visuales claros |

**Issues encontrados:**

```tsx
// P3: useCallback sin incluir en dependencias de useEffect
// ACTUAL:
const loadExpedientes = useCallback(async () => { ... }, []);

useEffect(() => {
  initializeViewer();  // Llama a loadExpedientes internamente
}, []);  // ⚠️ Missing dependency warning

// RECOMENDADO: Refactorizar para evitar warning
useEffect(() => {
  const init = async () => {
    // ... lógica de inicialización
  };
  init();
}, []);
```

```tsx
// P4: initializeViewer no está memoizado
// Podría causar re-renders innecesarios si se pasa como prop
```

## Seguridad

| Check | Estado |
|-------|--------|
| Admin token requerido | ✅ |
| JWT internos con expiración | ✅ (1 hora) |
| No expone secretos al frontend | ✅ |
| Validación de inputs | ✅ (via Pydantic) |
| Rate limiting | ⚠️ No implementado |

## Tests Pendientes

Se recomienda añadir tests para:

```python
# tests/api/test_expedientes_router.py
def test_listar_expedientes_requires_auth():
    """Debe rechazar sin admin token"""

def test_listar_expedientes_success():
    """Debe retornar lista de expedientes"""

def test_mcp_status_offline():
    """Debe manejar MCP no disponible"""

def test_documento_texto_not_found():
    """Debe retornar 404 para documento inexistente"""
```

## Plan de Mejoras

### Prioridad 1 (Crítico)
- [ ] Mover `import json` al inicio de `mcp_client.py`
- [ ] Añadir `MCP_BASE_URL` a `settings.py`

### Prioridad 2 (Recomendado)
- [ ] Añadir tests para endpoints de expedientes
- [ ] Implementar cache para lista de expedientes (opcional)
- [ ] Corregir warnings de ESLint en useEffect

### Prioridad 3 (Nice-to-have)
- [ ] Rate limiting en endpoints
- [ ] Paginación para listas grandes
- [ ] Exportar documento a PDF

## Métricas de Código

| Archivo | Líneas | Complejidad |
|---------|--------|-------------|
| mcp_client.py | 295 | Media |
| expedientes.py | 332 | Baja |
| expedientesService.ts | 121 | Baja |
| ExpedienteViewer.tsx | 449 | Media-Alta |

## Conclusión

Implementación sólida que sigue las mejores prácticas de la arquitectura del proyecto. Los issues encontrados son menores y no afectan la funcionalidad. Se recomienda priorizar la adición de tests antes de considerar el código listo para producción.

**Recomendación:** Aprobar con mejoras menores.
