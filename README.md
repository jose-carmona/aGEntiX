# aGEntiX
Sistema de Agentes IA para GEX

## Descripción

**aGEntiX** permite la integración de agentes de IA con GEX (Gestión de Expedientes) para automatizar tareas dentro de los flujos de trabajo administrativos, manteniendo límites estrictos en la autoridad de toma de decisiones.

GEX es el sistema de Gestión de Expedientes de Eprinsa, utilizado en la provincia de Córdoba como núcleo de la administración electrónica.

## Propuesta

La propuesta de aGEntiX introduce **acciones de tipo Agente** en el modelo BPMN de GEX, permitiendo que agentes IA:
- Automaticen tareas actualmente manuales (extracción de información, generación de documentos)
- Asistan en análisis de información (la toma de decisiones legales permanece exclusivamente humana)

## Principios de Diseño

1. **No acoplamiento**: Los agentes IA no están acoplados a GEX
2. **Modularidad**: Componentes independientemente desplegables
3. **Acceso vía MCP**: Información y herramientas accesibles mediante Model Context Protocol
4. **Enfoque conservador**: Las decisiones legales permanecen exclusivamente humanas
5. **Auditoría completa**: Todos los pasos del agente quedan registrados

## Documentación

La documentación completa del proyecto está organizada en un sistema **Zettelkasten** en el directorio `/doc`.

**Punto de entrada**: [doc/index.md](doc/index.md)

### Temas Principales

- **Sistema GEX**: Componentes, flujos de información e integraciones ([doc/001-gex-definicion.md](doc/001-gex-definicion.md))
- **Automatización de Tareas**: Tipos de tareas y candidatas para IA ([doc/010-tipos-tareas.md](doc/010-tipos-tareas.md))
- **Modelo BPMN**: Estructura de workflows y acciones de agente ([doc/020-bpmn-modelo.md](doc/020-bpmn-modelo.md))
- **Agentes IA**: Configuración, contexto y auditoría ([doc/030-propuesta-agentes.md](doc/030-propuesta-agentes.md))
- **Arquitectura**: Criterios de diseño y acceso MCP ([doc/040-criterios-diseño.md](doc/040-criterios-diseño.md))
- **Permisos**: Sistema de permisos y propagación ([doc/050-permisos-agente.md](doc/050-permisos-agente.md))

Cada nota representa un concepto individual e incluye referencias a notas relacionadas.

