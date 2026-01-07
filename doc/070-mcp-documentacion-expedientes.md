# MCP Documentación de Tipos de Expediente

## Estado

**Implementado** - Integrado en el servidor MCP unificado (puerto 8000).

## Descripción

Módulo MCP que proporciona acceso a la documentación asociada a cada **tipo de expediente**: normativa regulatoria, instrucciones de tramitación y plantillas de documentos.

Esta documentación es esencial para que los agentes puedan:
- Fundamentar sus decisiones citando normativa específica
- Verificar requisitos de documentación obligatoria
- Generar documentos usando plantillas predefinidas

## Tipos de Expediente Soportados

| ID | Tipo | Descripción |
|----|------|-------------|
| `subvenciones` | Subvenciones | Ayudas y subvenciones públicas |
| `licencias_obras` | Licencias de Obras | Licencias urbanísticas |
| `certificado_empadronamiento` | Certificado de Empadronamiento | Certificados del Padrón Municipal |

## Herramientas MCP

| Herramienta | Permiso | Descripción |
|-------------|---------|-------------|
| `listar_documentacion` | `documentacion:leer` | Lista documentos disponibles por tipo de expediente |
| `obtener_doc_documentacion` | `documentacion:leer` | Obtiene contenido completo de un documento |
| `buscar_en_documentacion` | `documentacion:buscar` | Busca texto en la documentación |

## Resources MCP

| URI | Descripción |
|-----|-------------|
| `documentacion://subvenciones` | Documentación de subvenciones |
| `documentacion://licencias_obras` | Documentación de licencias de obras |
| `documentacion://certificado_empadronamiento` | Documentación de certificados |

## Tipos de Documento

| Tipo | Descripción |
|------|-------------|
| `normativa` | Normativa regulatoria aplicable |
| `instrucciones_tramitacion` | Guía paso a paso de tramitación |
| `plantilla_propuesta_resolucion` | Plantilla para propuestas de resolución |
| `plantilla_requerimiento_documentacion` | Plantilla para requerimientos |
| `plantilla_certificado` | Plantilla de certificado (solo empadronamiento) |

## Estructura de Datos

```
src/mcp_mock/data/documentos/
├── subvenciones/
│   ├── normativa.json + .md
│   ├── instrucciones_tramitacion.json + .md
│   ├── plantilla_propuesta_resolucion.json + .md
│   └── plantilla_requerimiento_documentacion.json + .md
├── licencias_obras/
│   └── (misma estructura)
└── certificado_empadronamiento/
    ├── normativa.json + .md
    ├── instrucciones_tramitacion.json + .md
    ├── plantilla_certificado.json + .md
    └── plantilla_requerimiento_documentacion.json + .md
```

Cada documento tiene:
- **JSON**: Metadatos (id, tipo, descripción, instrucciones para el agente)
- **MD**: Contenido del documento en formato Markdown

## Ejemplo de Uso

```bash
# Generar token con permisos de documentación
TOKEN=$(python -m generate_token EXP-2024-001 \
  --permisos documentacion:leer documentacion:buscar --formato raw)

# Listar documentación de subvenciones
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

# Obtener normativa completa
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

## Datos Mock - Aviso Importante

> **AVISO**: Todos los documentos bajo `/src/mcp_mock/data/` son **datos ficticios** generados por un LLM (Large Language Model) con fines de desarrollo y pruebas.
>
> - La normativa citada es **orientativa** y puede no reflejar el texto legal vigente exacto.
> - Las plantillas son **ejemplos ilustrativos**, no documentos oficiales.
> - Los plazos, requisitos y procedimientos son **aproximaciones** basadas en normativa real pero simplificadas.
>
> **No deben utilizarse como referencia legal ni en entornos de producción sin validación por expertos en la materia.**

## Especificación Técnica

Ver: `/prompts/step-8-mcp-documentation.md`

## Relaciones

- Relacionado con: [Servidor MCP Mock](080-mock-mcp.md)
- Relacionado con: [Datos Mock disponibles](081-datos-mock.md)
- Relacionado con: [Acceso a información vía MCP](042-acceso-mcp.md)
- Relacionado con: [Contexto disponible para agentes](032-contexto-agente.md)
- Relacionado con: [Sistema de permisos](050-permisos-agente.md)
