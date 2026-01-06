# Step 8: MCP Documentation - Documentación de Tipos de Expediente

## Objetivo

Crear herramientas MCP que permitan a los agentes acceder a la documentación asociada a cada **tipo de expediente**: normativa, instrucciones de tramitación y plantillas de documentos.

---

## Tipos de Expediente

| ID | Tipo | Directorio |
|----|------|------------|
| `subvenciones` | Subvenciones | `data/documentos/subvenciones/` |
| `licencias_obras` | Licencias de Obras | `data/documentos/licencias_obras/` |
| `certificado_empadronamiento` | Certificado de Empadronamiento | `data/documentos/certificado_empadronamiento/` |

---

## Estructura de Datos

```
src/mcp_mock/data/documentos/
├── subvenciones/
│   ├── normativa.json                           # Metadatos
│   ├── normativa.md                             # Contenido
│   ├── instrucciones_tramitacion.json / .md
│   ├── plantilla_propuesta_resolucion.json / .md
│   └── plantilla_requerimiento_documentacion.json / .md
│
├── licencias_obras/
│   ├── normativa.json / .md
│   ├── instrucciones_tramitacion.json / .md
│   ├── plantilla_propuesta_resolucion.json / .md
│   └── plantilla_requerimiento_documentacion.json / .md
│
└── certificado_empadronamiento/
    ├── normativa.json / .md
    ├── instrucciones_tramitacion.json / .md
    ├── plantilla_certificado.json / .md
    └── plantilla_requerimiento_documentacion.json / .md
```

### Esquema JSON de Documento

```json
{
  "id": "string",                    // ID único (ej: "SUB-NORM-001")
  "tipo": "string",                  // "normativa" | "instrucciones_tramitacion" | "plantilla"
  "subtipo": "string",               // Solo para plantillas (ej: "propuesta_resolucion")
  "tipo_expediente": "string",       // "subvenciones" | "licencias_obras" | "certificado_empadronamiento"
  "descripcion": "string",           // Descripción del documento y su uso
  "instrucciones_agente": "string",  // Instrucciones para el agente sobre cómo usar el documento
  "contenido": "string"              // Nombre del fichero .md con el contenido
}
```

---

## Herramientas MCP a Implementar

### 1. `listar_documentos`

Lista los documentos disponibles para un tipo de expediente.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "tipo_expediente": {
      "type": "string",
      "enum": ["subvenciones", "licencias_obras", "certificado_empadronamiento"],
      "description": "Tipo de expediente"
    }
  },
  "required": ["tipo_expediente"]
}
```

**Output:**
```json
{
  "tipo_expediente": "subvenciones",
  "documentos": [
    {
      "id": "SUB-NORM-001",
      "tipo": "normativa",
      "descripcion": "Normativa regulatoria aplicable..."
    },
    {
      "id": "SUB-INST-001",
      "tipo": "instrucciones_tramitacion",
      "descripcion": "Instrucciones detalladas..."
    }
  ]
}
```

---

### 2. `obtener_documento`

Obtiene el contenido completo de un documento.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "tipo_expediente": {
      "type": "string",
      "enum": ["subvenciones", "licencias_obras", "certificado_empadronamiento"]
    },
    "tipo_documento": {
      "type": "string",
      "enum": ["normativa", "instrucciones_tramitacion", "plantilla_propuesta_resolucion", "plantilla_requerimiento_documentacion", "plantilla_certificado"]
    }
  },
  "required": ["tipo_expediente", "tipo_documento"]
}
```

**Output:**
```json
{
  "id": "SUB-NORM-001",
  "tipo": "normativa",
  "tipo_expediente": "subvenciones",
  "descripcion": "Normativa regulatoria...",
  "instrucciones_agente": "Utiliza esta normativa para...",
  "contenido": "# Normativa Regulatoria de Subvenciones\n\n## 1. Ley 38/2003..."
}
```

---

### 3. `buscar_en_documentacion`

Busca texto en la documentación de un tipo de expediente.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "tipo_expediente": {
      "type": "string",
      "enum": ["subvenciones", "licencias_obras", "certificado_empadronamiento"]
    },
    "query": {
      "type": "string",
      "description": "Texto a buscar"
    },
    "tipo_documento": {
      "type": "string",
      "description": "Filtrar por tipo de documento (opcional)"
    }
  },
  "required": ["tipo_expediente", "query"]
}
```

**Output:**
```json
{
  "resultados": [
    {
      "documento_id": "SUB-NORM-001",
      "tipo": "normativa",
      "coincidencias": [
        {
          "linea": 15,
          "contexto": "...el plazo máximo para resolver es de **6 meses**..."
        }
      ]
    }
  ],
  "total_coincidencias": 3
}
```

---

## Recursos MCP a Implementar

### `documentacion://{tipo_expediente}`

Recurso que expone la documentación como contexto.

**URI Pattern:** `documentacion://subvenciones`, `documentacion://licencias_obras`, etc.

**Contenido:** Lista de documentos con descripción e instrucciones (sin contenido completo).

---

## Implementación

### Ubicación

```
src/mcp_mock/mcp_documentacion/
├── __init__.py
├── server_http.py          # Servidor HTTP/SSE
├── tools.py                # Implementación de herramientas
├── resources.py            # Implementación de recursos
└── data_loader.py          # Carga de documentos JSON/MD
```

### Carga de Documentos

```python
# data_loader.py
import json
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "documentos"

def cargar_documento(tipo_expediente: str, tipo_documento: str) -> dict:
    """Carga un documento JSON y su contenido MD asociado."""
    json_path = DATA_PATH / tipo_expediente / f"{tipo_documento}.json"

    with open(json_path, 'r', encoding='utf-8') as f:
        doc = json.load(f)

    # Cargar contenido markdown
    md_path = DATA_PATH / tipo_expediente / doc["contenido"]
    with open(md_path, 'r', encoding='utf-8') as f:
        doc["contenido"] = f.read()

    return doc

def listar_documentos(tipo_expediente: str) -> list[dict]:
    """Lista todos los documentos de un tipo de expediente."""
    dir_path = DATA_PATH / tipo_expediente
    documentos = []

    for json_file in dir_path.glob("*.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            doc = json.load(f)
            documentos.append({
                "id": doc["id"],
                "tipo": doc["tipo"],
                "subtipo": doc.get("subtipo"),
                "descripcion": doc["descripcion"]
            })

    return documentos
```

---

## Configuración MCP

Añadir a `src/backoffice/config/mcp_servers.yaml`:

```yaml
mcp_servers:
  - id: documentacion
    name: "MCP Documentación de Expedientes"
    url: "http://localhost:8001"
    enabled: true
    description: "Documentación normativa, instrucciones y plantillas por tipo de expediente"
```

---

## Permisos JWT

Añadir permisos específicos para acceso a documentación:

| Permiso | Descripción |
|---------|-------------|
| `documentacion:leer` | Permite listar y obtener documentos |
| `documentacion:buscar` | Permite buscar en la documentación |

---

## Casos de Uso del Agente

1. **Obtener normativa**: El agente consulta la normativa aplicable antes de evaluar un expediente.
2. **Verificar documentación**: El agente consulta las instrucciones para saber qué documentos son obligatorios.
3. **Generar documentos**: El agente obtiene la plantilla y la rellena con los datos del expediente.
4. **Fundamentar decisiones**: El agente cita artículos específicos de la normativa en sus propuestas.

---

## Inventario de Documentos Creados

| Tipo Expediente | Documento | ID |
|-----------------|-----------|-----|
| subvenciones | normativa | SUB-NORM-001 |
| subvenciones | instrucciones_tramitacion | SUB-INST-001 |
| subvenciones | plantilla_propuesta_resolucion | SUB-TPL-001 |
| subvenciones | plantilla_requerimiento_documentacion | SUB-TPL-002 |
| licencias_obras | normativa | LOB-NORM-001 |
| licencias_obras | instrucciones_tramitacion | LOB-INST-001 |
| licencias_obras | plantilla_propuesta_resolucion | LOB-TPL-001 |
| licencias_obras | plantilla_requerimiento_documentacion | LOB-TPL-002 |
| certificado_empadronamiento | normativa | EMP-NORM-001 |
| certificado_empadronamiento | instrucciones_tramitacion | EMP-INST-001 |
| certificado_empadronamiento | plantilla_certificado | EMP-TPL-001 |
| certificado_empadronamiento | plantilla_requerimiento_documentacion | EMP-TPL-002 |

**Total: 12 documentos** (4 por tipo de expediente)
