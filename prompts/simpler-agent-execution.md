# Simplificación de la Ejecución de Agentes

## Objetivo

Simplificar la interfaz de ejecución de agentes reduciendo los parámetros necesarios al mínimo imprescindible.

## Parámetros de Entrada

Para ejecutar un agente solo serán necesarios:

| Parámetro | Descripción | Obligatorio |
|-----------|-------------|-------------|
| **Agente** | Selector del agente a ejecutar | Sí |
| **ID Expediente** | Identificador del expediente GEX | Sí |
| **ID Tarea** | Identificador de la tarea BPMN | Sí |
| **Permisos JWT** | Permisos a incluir en el token | Sí |
| **Objetivo adicional** | Instrucciones específicas para esta ejecución | No |
| **URL Callback** | URL para notificación de finalización | No |

## Restricciones

- No es necesaria retrocompatibilidad con la interfaz actual
- No se requieren cambios en el backend existente

## Flujo de Usuario

1. El usuario selecciona el agente a ejecutar
2. Introduce el ID de Expediente y el ID de Tarea
3. Configura los permisos para el token JWT
4. (Opcional) Añade un objetivo adicional
5. (Opcional) Indica la URL de callback
6. Pulsa el botón "Ejecutar"

## Interfaz de Resultados

### Panel Principal (izquierda)
- Selección de agente
- ID de Expediente e ID de Tarea
- Permisos para el token JWT
- Botón de ejecución del agente
- Panel de resultado inmediatamente debajo del botón
- Muestra el estado y resultado de la ejecución actual

### Panel Lateral (derecha)
- Historial de ejecuciones anteriores
