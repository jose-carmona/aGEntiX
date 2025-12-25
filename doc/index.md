# Índice de Notas - aGEntiX

## Sistema GEX

- [Qué es GEX y su rol en la administración electrónica](001-gex-definicion.md)
- [Componentes principales del sistema GEX](002-componentes-gex.md)
- [Flujo de información en el sistema](003-flujo-informacion.md)
- [Sistemas integrados con GEX](004-integraciones.md)

## Automatización y Tareas

- [Tipos de tareas: automáticas vs manuales](010-tipos-tareas.md)
- [Tareas que ya están automatizadas](011-tareas-automatizadas.md)
- [Tareas que requieren intervención humana](012-tareas-humanas.md)
- [Tareas candidatas para automatización con IA](013-tareas-ia-candidatas.md)

## BPMN

- [Modelo de workflow BPMN en GEX](020-bpmn-modelo.md)
- [Estructura y composición de una Tarea](021-estructura-tarea.md)
- [Tareas de inicio y fin](022-tareas-especiales.md)
- [Acciones de tipo Agente en tareas](023-acciones-agente.md)

## Agentes IA

- [Propuesta de incorporación de agentes IA](030-propuesta-agentes.md)
- [Configuración de un agente IA](031-configuracion-agente.md)
- [Contexto disponible para los agentes](032-contexto-agente.md)
- [Requisitos de auditoría y logging](033-auditoria-agente.md)

## Arquitectura y Diseño

- [Principios arquitectónicos del sistema](040-criterios-diseño.md)
- [Estrategia conservadora en automatización](041-enfoque-conservador.md)
- [Acceso a información y herramientas vía MCP](042-acceso-mcp.md)

## Permisos y Seguridad

- [Sistema de permisos para agentes IA](050-permisos-agente.md)
- [Gestión de autoría en acciones de agentes](051-autoria-agente.md)
- [Propagación de permisos: BPMN → Agente → MCP → API](052-propagacion-permisos.md)
- [Mitigación de Prompt Injection](053-mitigacion-prompt-injection.md)

## Autenticación

- [Sistema de Autenticación Dual](060-autenticacion-dual.md)
- [Token Administrativo](061-token-admin.md)
- [Token JWT de Ejecución](062-token-jwt.md)

## Análisis Crítico y Problemas Identificados

- [Introducción a la problemática general](problemas/100-problematica-general.md)
- [Problemas en la arquitectura MCP](problemas/101-problema-arquitectura-mcp.md)
- [Problemas en el modelo de permisos y seguridad](problemas/102-problema-permisos-seguridad.md)
- [Problemas con el enfoque conservador](problemas/103-problema-enfoque-conservador.md)
- [Problemas en la integración BPMN](problemas/104-problema-integracion-bpmn.md)
- [Problemas en la configuración de agentes](problemas/105-problema-configuracion-agentes.md)
- [Problemas en auditoría y trazabilidad](problemas/106-problema-auditoria-trazabilidad.md)
- [Problemas en el contexto de agentes](problemas/107-problema-contexto-agentes.md)
- [Aspectos ausentes en la documentación](problemas/108-aspectos-ausentes.md)
- [Prioridades de mejora y roadmap](problemas/109-prioridades-mejora.md)

## Meta

- [Método de documentación utilizado](zettelkasten.md)
