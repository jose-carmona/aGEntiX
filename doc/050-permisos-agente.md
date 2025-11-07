# Sistema de Permisos para Agentes IA

GEX dispone de un sistema de permisos a nivel de tipo de Expediente: Por tipo de expediente los usarios puede tener permisos de:
- Consulta (lectura)
- Gestión (lectura / escritura)

Las acciones que se realizan por la máquina (sin intervención de humanos) como parte de las tareas del flujo BPMN se hacen con un usuario especial denominado "Automatico". GEX permite asignarle permisos de igual manera que al resto de usuarios.

Independientemente de lo anterior, en GEX se limita por configuración la información a la que puede acceder el usuario para completar una tarea. Ésto se hace por dos motivos: por protección de datos y por eficacia.

Entonces, adoptaremos el mismo criterio ya establecido en GEX: el agente usará los permisos del usuario "Automático" accediendo únicamente a la información que se ha establecido a nivel de tarea.

## Principio de Mínimo Privilegio

Los agentes deben tener únicamente los permisos necesarios, según el tipo de Expediente/Tarea y acceso a las herramientas estrictamente necesarias para realizar su función específica.

El ámbito de lectura/escritura del agente queda restringido al expediente concreto sobre el que se está trabajando.

## Permisos de Lectura

**¿Qué información puede ver un agente?**

La información de la **Tarea de Expediente sobre el que se está trabajando** siempre y cuando el usuario "Automático" tenga permiso, al menos, de consulta.

## Permisos de Escritura

Los permisos de escritura estarán **limitados por la configuración del tipo de Expediente**: el Agente podrá escribir en el Expediente si el usuario "Automático" dispone de permisos de Gestión.

Las herramientas de lectura estará separadas de la herramientas de escritura y el agente sólo tendrá acceso a aquellas herramientas estríctamente necesarias. Este criterio también va a permitir optimizar la ventana de contexto del modelo LLM que puede ser muy limitada (más harramientas, mayor necesidad de contexto).

## Modelo de Amenazas

**Amenazas a considerar**:

El ámbito del acción del agente está limitado a una tarea/expediente concreta por arquitectura. El agente no tienen forma de acceder a información no privilegiada. Esto previene:
- **Privilege escalation**
- **Data exfiltration**

Dado que todas los accesos a datos se van a realizar mediante MCP propagando permisos, el sistema debe ser inmune a **Injection attacks** a condición de que la API de base se encuentre revisada contra ese tipo de vulnerabilidad.

Sin embargo, el sistema podría se susceptible a **Prompt injection** si se incluye en el contexto alguna información maliciosa. Se incluye una sección específica al respecto.

Por el diseño de privilegios y del BPMN de cada tipo de expediente dónde se limita la capacidad de toma de decisiones de los agentes y se establece puntos de supervisión humana, consideramos que el riesgo de que un **Agente comprometido** pueda generar un alto impacto en el Sistema es reducido.

## Relaciones

- Ver: [Información accesible](032-contexto-agente.md)
- Ver: [Autoría de acciones](051-autoria-agente.md)
- Ver: [Propagación en el sistema](052-propagacion-permisos.md)
- Ver: [Configuración del agente](031-configuracion-agente.md)
- Ver: [Mitigación de Prompt Injection](053-mitigacion-prompt-injection.md)
