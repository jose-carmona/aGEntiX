# Fixes Recomendados - commit-5be9402

## P1: Mover imports al inicio de mcp_client.py

**Archivo:** `src/api/services/mcp_client.py`

```python
# Al inicio del archivo, añadir:
import json  # Añadir esta línea

# Eliminar import json de las líneas 178, 209, 244, 278
```

**Impacto:** Mejora rendimiento (evita re-imports) y sigue convenciones Python.

---

## P2: Añadir MCP_BASE_URL a settings

**Archivo:** `src/backoffice/settings.py`

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # MCP Server
    MCP_BASE_URL: str = Field(
        default="http://localhost:8000",
        description="URL del servidor MCP"
    )
```

**Archivo:** `src/api/services/mcp_client.py`

```python
# Cambiar:
MCP_BASE_URL = getattr(settings, 'MCP_BASE_URL', 'http://localhost:8000')

# Por:
MCP_BASE_URL = settings.MCP_BASE_URL
```

**Impacto:** Configuración centralizada y documentada.

---

## P3: Refactorizar useEffect en ExpedienteViewer

**Archivo:** `frontend/src/pages/ExpedienteViewer.tsx`

```tsx
// Opción A: Añadir eslint-disable (rápido)
// eslint-disable-next-line react-hooks/exhaustive-deps
useEffect(() => {
  initializeViewer();
}, []);

// Opción B: Refactorizar (mejor)
useEffect(() => {
  const init = async () => {
    setIsCheckingMCP(true);
    setError(null);
    try {
      const status = await checkMCPStatus();
      setMcpAvailable(status.available);
      if (status.available) {
        const data = await getExpedientes();
        setExpedientes(data);
      }
    } catch (err) {
      console.warn('Error initializing:', err);
      setMcpAvailable(false);
    } finally {
      setIsCheckingMCP(false);
    }
  };
  init();
}, []);
```

**Impacto:** Elimina warning de linter, código más predecible.

---

## Comandos para aplicar fixes

```bash
# Después de aplicar cambios:
cd /workspaces/aGEntiX

# Verificar backend
python -c "from src.api.main import app; print('OK')"

# Verificar frontend
cd frontend && npm run build

# Ejecutar tests
./run-tests.sh
```
