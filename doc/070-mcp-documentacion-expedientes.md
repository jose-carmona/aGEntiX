# MCP Documentación de Tipos de Expediente (mock)

## Descripción

Servidor MCP que proporciona acceso a la documentación asociada a cada **tipo de expediente**: normativa regulatoria, instrucciones de tramitación y plantillas de documentos.

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

| Herramienta | Descripción |
|-------------|-------------|
| `listar_documentos` | Lista documentos disponibles por tipo de expediente |
| `obtener_documento` | Obtiene contenido completo de un documento |
| `buscar_en_documentacion` | Busca texto en la documentación |

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
    └── (misma estructura)
```

Cada documento tiene:
- **JSON**: Metadatos (id, tipo, descripción, instrucciones para el agente)
- **MD**: Contenido del documento en formato Markdown

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

- Relacionado con: [Acceso a información vía MCP](042-acceso-mcp.md)
- Relacionado con: [Contexto disponible para agentes](032-contexto-agente.md)
- Relacionado con: [Configuración de agentes](031-configuracion-agente.md)
- Relacionado con: [Sistema de permisos](050-permisos-agente.md)
