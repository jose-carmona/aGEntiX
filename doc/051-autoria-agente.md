# Gestión de Autoría en Acciones de Agentes

## Autoría de las Acciones

**¿Qué autoría tienen las acciones del agente?**

El **nombre definido en el tipo de agente** se usa como autor de las acciones.

## Propósito

- **Trazabilidad**: Saber qué acciones fueron realizadas por agentes vs humanos
- **Responsabilidad**: Identificar qué agente realizó cada acción
- **Auditoría**: Facilitar la revisión de acciones automatizadas

## Transparencia

Es fundamental que quede claro en el sistema cuándo una acción fue realizada por un agente IA en lugar de por un humano. La traza quedará visible en el Expediente junto al resto de logs de tareas.

## ¿Qué trazas?

- Contexto
- Prompts
- Razonamientos del LLM
- Respuestas

## Relaciones

- Ver: [Requisitos de logging](033-auditoria-agente.md)
- Ver: [Nombre del agente](031-configuracion-agente.md)
- Ver: [Permisos del agente](050-permisos-agente.md)
