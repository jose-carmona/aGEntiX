# MCP Mock Unificado

Servidor MCP (Model Context Protocol) mock para el proyecto aGEntiX. Proporciona acceso simulado a expedientes y documentación de tipos de expediente.

## Arquitectura

El servidor unificado expone dos módulos en un único puerto (8000):

```
src/mcp_mock/
├── auth.py                     # Autenticación JWT compartida
├── models.py                   # Modelos de datos compartidos
├── data/                       # Datos compartidos
│   ├── expedientes/            # Datos de expedientes individuales
│   └── documentos/             # Documentación de tipos de expediente
│
├── mcp_expedientes/            # Módulo de Expedientes
│   ├── server_http.py          # Servidor HTTP unificado
│   ├── tools.py                # Tools de expedientes
│   └── resources.py            # Resources de expedientes
│
└── mcp_documentacion/          # Módulo de Documentación
    ├── tools.py                # Tools de documentación
    ├── resources.py            # Resources de documentación
    └── data_loader.py          # Carga de documentos
```

## Inicio Rápido

```bash
# Configurar secreto JWT
export JWT_SECRET="test-secret-key"

# Iniciar servidor (puerto 8000)
cd src/mcp_mock/mcp_expedientes
python -m uvicorn server_http:app --reload --port 8000

# Verificar que funciona
curl http://localhost:8000/health
```

## Módulos Disponibles

### 1. Expedientes (mcp_expedientes)

Gestión de expedientes administrativos individuales.

**Tools de Lectura** (requieren permiso `consulta`):
- `consultar_expediente(expediente_id)` - Información completa
- `listar_documentos(expediente_id)` - Lista de documentos
- `obtener_documento(expediente_id, documento_id)` - Documento específico
- `obtener_texto_documento(expediente_id, documento_id)` - Texto markdown
- `obtener_metadatos_documento(expediente_id, documento_id)` - Metadatos extraídos

**Tools de Escritura** (requieren permiso `gestion`):
- `añadir_documento(expediente_id, nombre, tipo, contenido)`
- `actualizar_datos(expediente_id, campo, valor)`
- `añadir_anotacion(expediente_id, texto)`
- `actualizar_metadatos_documento(expediente_id, documento_id, metadatos)`
- `crear_documento_desde_markdown(expediente_id, nombre, tipo, texto_markdown)`

**Resources**:
- `expediente://{id}` - Expediente completo
- `expediente://{id}/documentos` - Lista de documentos
- `expediente://{id}/historial` - Historial de acciones

### 2. Documentación (mcp_documentacion)

Acceso a normativa, instrucciones y plantillas por tipo de expediente.

**Tools de Lectura** (requieren permiso `documentacion:leer`):
- `listar_documentacion(tipo_expediente)` - Lista documentos disponibles
- `obtener_doc_documentacion(tipo_expediente, tipo_documento)` - Contenido completo

**Tools de Búsqueda** (requieren permiso `documentacion:buscar`):
- `buscar_en_documentacion(tipo_expediente, query, tipo_documento?)` - Buscar texto

**Resources**:
- `documentacion://subvenciones` - Documentación de subvenciones
- `documentacion://licencias_obras` - Documentación de licencias
- `documentacion://certificado_empadronamiento` - Documentación de certificados

**Tipos de Expediente Soportados**:
| ID | Descripción |
|----|-------------|
| `subvenciones` | Expedientes de ayudas y subvenciones |
| `licencias_obras` | Licencias de obras menores y mayores |
| `certificado_empadronamiento` | Certificados de empadronamiento |

**Tipos de Documento**:
| Tipo | Descripción |
|------|-------------|
| `normativa` | Normativa aplicable (leyes, reglamentos) |
| `instrucciones_tramitacion` | Guía paso a paso de tramitación |
| `plantilla_propuesta_resolucion` | Plantilla para propuestas |
| `plantilla_requerimiento_documentacion` | Plantilla para requerimientos |
| `plantilla_certificado` | Plantilla de certificado (solo empadronamiento) |

## Autenticación JWT

### Permisos Disponibles

| Permiso | Descripción |
|---------|-------------|
| `consulta` | Lectura de expedientes |
| `gestion` | Escritura de expedientes |
| `documentacion:leer` | Lectura de documentación de tipos |
| `documentacion:buscar` | Búsqueda en documentación |

### Generar Token

```bash
cd src/mcp_mock/mcp_expedientes

# Token con todos los permisos
python -m generate_token EXP-2024-001 \
  --permisos consulta gestion documentacion:leer documentacion:buscar

# Solo lectura de expedientes
python -m generate_token EXP-2024-001 --permisos consulta

# Solo documentación
python -m generate_token EXP-2024-001 \
  --permisos documentacion:leer documentacion:buscar
```

## Ejemplos de Uso

### Listar Tools Disponibles

```bash
TOKEN=$(python -m generate_token EXP-2024-001 --formato raw)

curl -X POST http://localhost:8000/rpc \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

### Consultar Expediente

```bash
curl -X POST http://localhost:8000/rpc \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "consultar_expediente",
      "arguments": {"expediente_id": "EXP-2024-001"}
    }
  }'
```

### Listar Documentación de Subvenciones

```bash
curl -X POST http://localhost:8000/rpc \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "listar_documentacion",
      "arguments": {"tipo_expediente": "subvenciones"}
    }
  }'
```

### Obtener Normativa

```bash
curl -X POST http://localhost:8000/rpc \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "obtener_doc_documentacion",
      "arguments": {
        "tipo_expediente": "subvenciones",
        "tipo_documento": "normativa"
      }
    }
  }'
```

### Buscar en Documentación

```bash
curl -X POST http://localhost:8000/rpc \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "buscar_en_documentacion",
      "arguments": {
        "tipo_expediente": "subvenciones",
        "query": "plazo"
      }
    }
  }'
```

## Tests

```bash
# Ejecutar todos los tests MCP
pytest tests/test_mcp/ -v

# Solo tests de documentación
pytest tests/test_mcp/test_documentacion.py -v

# Solo tests de expedientes
pytest tests/test_mcp/test_tools.py -v
```

## Expedientes de Prueba

| ID | Tipo | Estado |
|----|------|--------|
| `EXP-2024-001` | SUBVENCIONES | EN_TRAMITE |
| `EXP-2024-002` | LICENCIA_OBRA | PENDIENTE_DOCUMENTACION |
| `EXP-2024-003` | CERTIFICADO_EMPADRONAMIENTO | ARCHIVADO |

## Documentación de Tipos

Cada tipo de expediente incluye 4 documentos:
- Normativa aplicable
- Instrucciones de tramitación
- Plantilla de propuesta/certificado
- Plantilla de requerimiento de documentación

**Total: 12 documentos** (ver `data/documentos/`)
