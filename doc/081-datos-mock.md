# Datos Mock

## Descripción

Conjunto de datos ficticios utilizados por el servidor MCP mock durante el desarrollo. Todos los datos han sido **generados por LLM** y no representan información real.

## Ubicación

Todos los datos mock están centralizados en:

```
src/mcp_mock/data/
├── expedientes/                # Expedientes individuales
│   ├── EXP-2024-001.json       # Subvención (EN_TRAMITE)
│   ├── EXP-2024-002.json       # Licencia obra (PENDIENTE_DOCUMENTACION)
│   └── EXP-2024-003.json       # Certificado (ARCHIVADO)
│
└── documentos/                 # Documentación por tipo de expediente
    ├── subvenciones/
    ├── licencias_obras/
    └── certificado_empadronamiento/
```

## Inventario de Datos Mock

### Expedientes

| Archivo | Tipo | Estado | Descripción |
|---------|------|--------|-------------|
| `EXP-2024-001.json` | SUBVENCIONES | EN_TRAMITE | Solicitud de ayuda para local comercial |
| `EXP-2024-002.json` | LICENCIA_OBRA | PENDIENTE_DOCUMENTACION | Licencia de obra menor |
| `EXP-2024-003.json` | CERTIFICADO_EMPADRONAMIENTO | ARCHIVADO | Certificado emitido |

### Documentación por Tipo de Expediente

#### Subvenciones (`documentos/subvenciones/`)

| Archivo | Tipo | ID |
|---------|------|-----|
| `normativa.json` + `.md` | Normativa | SUB-NORM-001 |
| `instrucciones_tramitacion.json` + `.md` | Instrucciones | SUB-INST-001 |
| `plantilla_propuesta_resolucion.json` + `.md` | Plantilla | SUB-TPL-001 |
| `plantilla_requerimiento_documentacion.json` + `.md` | Plantilla | SUB-TPL-002 |

#### Licencias de Obras (`documentos/licencias_obras/`)

| Archivo | Tipo | ID |
|---------|------|-----|
| `normativa.json` + `.md` | Normativa | LOB-NORM-001 |
| `instrucciones_tramitacion.json` + `.md` | Instrucciones | LOB-INST-001 |
| `plantilla_propuesta_resolucion.json` + `.md` | Plantilla | LOB-TPL-001 |
| `plantilla_requerimiento_documentacion.json` + `.md` | Plantilla | LOB-TPL-002 |

#### Certificado de Empadronamiento (`documentos/certificado_empadronamiento/`)

| Archivo | Tipo | ID |
|---------|------|-----|
| `normativa.json` + `.md` | Normativa | EMP-NORM-001 |
| `instrucciones_tramitacion.json` + `.md` | Instrucciones | EMP-INST-001 |
| `plantilla_certificado.json` + `.md` | Plantilla | EMP-TPL-001 |
| `plantilla_requerimiento_documentacion.json` + `.md` | Plantilla | EMP-TPL-002 |

## Estructura de Documentos de Documentación

Cada documento tiene dos archivos:

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
| Expedientes | 3 |
| Tipos de expediente | 3 |
| Documentos por tipo | 4 |
| **Total documentos** | **12** |
| Archivos (JSON + MD) | 24 |

## Backups

Los datos de expedientes incluyen archivos `.json.backup` que permiten restaurar el estado original después de tests que modifican datos:

```
src/mcp_mock/data/expedientes/
├── EXP-2024-001.json
├── EXP-2024-001.json.backup    # Estado original
├── EXP-2024-002.json
├── EXP-2024-002.json.backup
└── ...
```

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
