# Datos Mock

## Descripción

Conjunto de datos ficticios utilizados por los servidores MCP mock durante el desarrollo. Todos los datos han sido **generados por LLM** y no representan información real.

## Inventario de Datos Mock

### Expedientes (`mcp_expedientes`)

| Ubicación | Contenido |
|-----------|-----------|
| `src/mcp_mock/mcp_expedientes/data/expedientes.json` | Expedientes de ejemplo |

### Documentación por Tipo de Expediente (`mcp_documentacion`)

| Ubicación | Contenido |
|-----------|-----------|
| `src/mcp_mock/data/documentos/` | Documentación de tipos de expediente |

#### Subvenciones

| Archivo | Tipo | ID |
|---------|------|-----|
| `normativa.json` + `.md` | Normativa | SUB-NORM-001 |
| `instrucciones_tramitacion.json` + `.md` | Instrucciones | SUB-INST-001 |
| `plantilla_propuesta_resolucion.json` + `.md` | Plantilla | SUB-TPL-001 |
| `plantilla_requerimiento_documentacion.json` + `.md` | Plantilla | SUB-TPL-002 |

#### Licencias de Obras

| Archivo | Tipo | ID |
|---------|------|-----|
| `normativa.json` + `.md` | Normativa | LOB-NORM-001 |
| `instrucciones_tramitacion.json` + `.md` | Instrucciones | LOB-INST-001 |
| `plantilla_propuesta_resolucion.json` + `.md` | Plantilla | LOB-TPL-001 |
| `plantilla_requerimiento_documentacion.json` + `.md` | Plantilla | LOB-TPL-002 |

#### Certificado de Empadronamiento

| Archivo | Tipo | ID |
|---------|------|-----|
| `normativa.json` + `.md` | Normativa | EMP-NORM-001 |
| `instrucciones_tramitacion.json` + `.md` | Instrucciones | EMP-INST-001 |
| `plantilla_certificado.json` + `.md` | Plantilla | EMP-TPL-001 |
| `plantilla_requerimiento_documentacion.json` + `.md` | Plantilla | EMP-TPL-002 |

## Estructura de Documentos

Cada documento de documentación tiene dos archivos:

- **JSON**: Metadatos (id, tipo, descripción, instrucciones para agente)
- **MD**: Contenido en Markdown (facilita edición humana)

```json
{
  "id": "SUB-NORM-001",
  "tipo": "normativa",
  "tipo_expediente": "subvenciones",
  "descripcion": "Normativa regulatoria...",
  "instrucciones_agente": "Utiliza esta normativa para...",
  "contenido": "normativa.md"
}
```

## Resumen

| Categoría | Cantidad |
|-----------|----------|
| Tipos de expediente | 3 |
| Documentos por tipo | 4 |
| **Total documentos** | **12** |
| Archivos (JSON + MD) | 24 |

## Aviso Legal

> **IMPORTANTE**: Todos los datos bajo `/src/mcp_mock/data/` son **ficticios**.
>
> - Generados por LLM (Large Language Model)
> - Solo para desarrollo y pruebas
> - La normativa citada es orientativa
> - Las plantillas son ejemplos ilustrativos
>
> **No usar como referencia legal ni en producción.**

## Relaciones

- Ver: [Servidor MCP Mock](080-mock-mcp.md)
- Ver: [MCP Documentación de Expedientes](070-mcp-documentacion-expedientes.md)
