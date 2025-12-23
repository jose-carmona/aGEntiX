# Configuración de un Agente IA

## Configuración General del Tipo de Agente

- **Nombre**: Identificador del tipo de agente
- **URL**: Endpoint del servicio del agente

Cada agente consistirá en un conjunto de pasos para resolver el objetivo. En cada paso se establecerá:

- **System prompt**: Instrucciones base para el modelo
- **Modelo LLM**: Modelo de lenguaje a utilizar

La configuración dependerá de si el agente está implementado en CrewAI o en LangChain.

## Configuración Específica para la acción GEX

- **Prompt**: Instrucciones específicas para la acción
- **Herramientas disponibles**: Capacidades que puede usar el agente

## Observaciones

La configuración permite tener un mismo tipo de agente que puede adaptarse a diferentes tareas mediante prompts y herramientas específicas.

## Relaciones

- Ver: [Propuesta general](030-propuesta-agentes.md)
- Ver: [Contexto disponible](032-contexto-agente.md)
- Ver: [Permisos del agente](050-permisos-agente.md)
