# Guión de Video - Presentación aGEntiX

**Duración estimada:** 10-12 minutos
**Formato:** Screencast con locución
**Tono:** Coloquial y didáctico

---

## PARTE 1: INTRODUCCIÓN (~2:00 min)

### [PANTALLA: aGEntiX - Sistema de Agentes IA para GEX]

> Hola, bienvenidos. En este video voy a presentaros aGEntiX, un sistema que he desarrollado como proyecto Capstone para integrar inteligencia artificial en la gestión de expedientes de la administración pública.

### [PANTALLA: Logo de Diputación de Córdoba + Mapa de la provincia]

> Pero antes de entrar en materia, dejadme que os ponga en contexto. GEX, o Gestión de Expedientes, es la aplicación desarrollada por Eprinsa, la empresa provincial de informática de la Diputación de Córdoba. Se utiliza tanto en la propia Diputación y sus organismos dependientes, como en prácticamente todos los ayuntamientos de la provincia para gestionar sus expedientes administrativos. Estamos hablando de miles de expedientes al año: expedientes del ámbito fiscal, recaudatorio, contrataciones, subvenciones...

### [PANTALLA: Foto concepto Expediente]

> Pero, ¿qué es un expediente? Simplificando mucho, no es más que una colección de documentos relacionados con un asunto concreto. El problema que nos encontramos es que muchas de las tareas administrativas necesarias para resolver esos expedientes son repetitivas y consumen mucho tiempo del personal. Me refiero a cosas como extraer información de documentos, validar que la documentación aportada está completa, o generar informes. Son tareas que no requieren tomar decisiones complejas, pero que tampoco se pueden automatizar con las herramientas tradicionales porque necesitan, de alguna manera, "entender" el contenido de los documentos.

### [PANTALLA: Foto concepto BPMN]

> Una de las funcionalidades más potentes de GEX es que permite anexar flujos BPMN a los expedientes, estandarizando así su tramitación. Y es precisamente aquí donde entra aGEntiX. La idea central es incorporar agentes de inteligencia artificial que puedan realizar estas tareas operativas, pero siempre, y esto es fundamental, manteniendo a las personas en el control de las decisiones importantes. Porque una cosa es que la IA extraiga datos de un documento o valide que está completo, y otra muy distinta es que decida si se aprueba o deniega una subvención. Eso sigue siendo, y debe seguir siendo, responsabilidad humana.

---

## PARTE 2: ARQUITECTURA DEL SISTEMA (~3:00 min)

### [PANTALLA: Arquitectura del Sistema]

> Vale, vamos a ver cómo funciona el sistema a vista de pájaro. Os voy a mostrar la arquitectura general y después entraremos en los detalles más relevantes.

### [PANTALLA: GEX + BPMN + aGEntiX]

> La integración de aGEntiX con GEX se inicia desde el propio flujo BPMN. Cuando el workflow llega a una tarea que requiere intervención de un agente IA, el motor BPMN genera un token JWT con los claims adecuados e invoca a aGEntiX mediante una API REST que hemos implementado con FastAPI.
>
> A continuación entra en juego el Back-Office, que es el cerebro del sistema. Es aquí donde realmente se ejecutan los agentes. Este componente recibe las peticiones, valida los permisos mediante los tokens JWT, orquesta la ejecución del agente correspondiente, y se asegura de que absolutamente todo quede registrado en el log de auditoría.
>
> Un aspecto fundamental de esta arquitectura es que está completamente desacoplada de GEX. Los agentes nunca tocan directamente la base de datos ni el código de GEX. Toda la comunicación pasa por el protocolo MCP, lo que nos da flexibilidad para evolucionar ambos sistemas de forma independiente. MCP, o Model Context Protocol, es un estándar que permite a los modelos de IA acceder a herramientas y datos de forma controlada y segura. En nuestro caso, el servidor MCP expone las operaciones que los agentes pueden realizar sobre los expedientes: leer documentos, consultar datos, crear anotaciones, y más.
>
> A efectos de desarrollo y para esta demostración, hemos construido un servidor MCP mock que simula la presencia de GEX. También hemos desarrollado un frontend en React para que la demo resulte más visual e intuitiva.

### [PANTALLA: aGEntiX en detalle]

> Entrando un poco más en detalle, como os decía, el punto de entrada a aGEntiX es un endpoint REST implementado con FastAPI. El sistema soporta dos frameworks de agentes: CrewAI y LangGraph, lo que nos da flexibilidad para elegir el más adecuado según el caso de uso. Toda la configuración de los agentes se realiza mediante ficheros YAML, lo que facilita su mantenimiento sin tocar código. Y para entornos de producción con alta carga, el sistema está preparado para escalar horizontalmente gracias a Celery.
>
> Hay un tema que en administración pública es absolutamente crítico: la seguridad. El sistema valida múltiples claims en cada token JWT: quién emitió el token, para qué expediente concreto es válido, qué permisos tiene el agente, cuándo expira el token...
>
> Además, todos los logs pasan por un sistema de redacción automática de datos personales. Si un agente procesa un documento que contiene un DNI, un email o un número de teléfono, esos datos se redactan automáticamente antes de escribirse en el log. Esto es fundamental para cumplir las normativas de protección de datos.
>
> En concreto, el sistema detecta y redacta ocho tipos de datos personales: DNI/NIF, NIE, direcciones de email, teléfonos móviles y fijos, números IBAN, tarjetas de crédito y cuentas bancarias.

### [PANTALLA: VSCode + Claude Code]

> Un apunte sobre el entorno de desarrollo. Todo el proyecto se ha desarrollado utilizando Visual Studio Code con Dev Containers, lo que garantiza un entorno reproducible y consistente. Y quiero destacar especialmente el uso de Claude Code, que ha acelerado enormemente la ejecución del proyecto, tanto en la escritura de código como en la documentación y los tests.

---

## PARTE 3: DEMOSTRACIÓN - MOCK MCP (~2:00 min)

### [PANTALLA: DEMO: MOCK MCP]

> Pasemos a la demostración...

### [PANTALLA: VSCode - datos mock]

> Para el desarrollo hemos creado un conjunto de datos mock. Tenemos expedientes de subvenciones con toda su documentación asociada: solicitudes, memorias de proyecto, justificantes bancarios, certificados... Todo simulando casos más o menos reales.
>
> También hemos incluido la documentación asociada a cada tipo de expediente: la normativa aplicable, las instrucciones de tramitación, y las plantillas de documentos que se utilizan habitualmente.

### [PANTALLA: Terminal]

> Vamos a verlo funcionando. Para arrancar el sistema completo necesitamos levantar varios servicios en diferentes terminales.
>
> Primero hemos arrancamos el servidor MCP mock en el puerto 8000. En otro terminal arrancamos Celery. El sistema puede funcionar ejecutando directamente los agentes desde el backend, pero está preparado para escalar tanto vertical como horizontalmente gracias a Celery. En nuestra configuración, Celery utiliza Redis tanto como broker de mensajes como backend de resultados.
>
> También hemos arrancamos la API REST en el puerto 8080 y, por último, el frontend React en el puerto de desarrollo.

### [PANTALLA: Frontend + MOCK MCP]

> Vamos a acceder al frontend. Lo primero que nos encontramos es una pantalla de login. El frontend está protegido con un token de administración que se configura mediante una variable de entorno. Introducimos el token y accedemos al dashboard principal, que nos muestra de un vistazo la situación general del sistema: ejecuciones totales, tasa de éxito, tiempos medios...
>
> En la parte izquierda tenemos el sidebar de navegación que nos da acceso a las diferentes secciones de la aplicación.
>
> Vamos a explorar el servidor MCP mock. Generamos un token JWT con todos los claims para un expediente determinado y esto nos da la posibilidad de acceder a todos los recurso de ese expediente. Podemos ver sus datos: (revisión rápida punto por punto)
> 
> Por operatividad en la demostración, el frontend incluye también un visor de expedientes. Podemos ver los diferentes expedientes disponibles, la relación de documentos de cada uno, y el detalle de cualquier documento. Esto nos permite verificar que los datos mock están correctamente configurados antes de probar los agentes así como el resultado final de la ejecución de un agente.
---

## PARTE 4: DEMOSTRACIÓN - EJECUCIÓN DE AGENTE (~4:00 min)

### [PANTALLA: DEMO: AGENTES]

> Entramos ahora en lo realmente importante del proyecto

### [PANTALLA: API REST]

> Aunque estamos usando el frontend React en la demos, quiero recordar que el acceso en producción se realizará a través del API REST. Podemos ver la documentación de los diferentes endpoints en Swagger ui y redocs.

### [PANTALLA: Agente mínimo de test e2e]

> Vamos a ejecutar nuestro primer agente. Empezaremos con un agente mínimo de prueba que nos permite verificar que toda la cadena funciona correctamente de extremo a extremo: desde la petición REST, pasando por la validación JWT, la ejecución del agente, hasta el registro en el log de auditoría. El objetivo de éste agente es responder simplemente "OK". Para ello necesita permisos mínimos. Ejecutamos... Tenemos el resultado esperado: OK.
>
> Si nos vamos al terminal, vemos que la petición ha llegado hasta el worker Celery.

### [PANTALLA: Logs]

> Aquí podemos ver los logs generados durante la ejecución. Fijaos cómo cada entrada incluye el identificador del expediente, el subsistema, el agente, el identificador único de la ejecución, y cómo los datos personales que pudieran aparecer están correctamente redactados. Esto nos da trazabilidad completa de lo que ha hecho el agente, respetando la privacidad de los datos. Disponemos de filtros que faciliten la búsqueda en los logs.

### [PANTALLA: Configuración de Agentes]

> La configuración de los agentes se realiza mediante ficheros YAML. Aquí definimos el nombre del agente, qué proveedor y modelo de lenguaje utiliza, su prompt de sistema, las herramientas MCP a las que tiene acceso, y los permisos que requiere. Esta aproximación declarativa facilita crear nuevos agentes o modificar los existentes sin necesidad de tocar código Python.

### [PANTALLA: Agente con CrewAI]

> Veamos ahora un agente más complejo implementado con CrewAI. En este ejemplo ejecutamos "RedactorSituacion", que genera un informe de situación del expediente. El agente consulta los datos del expediente, lee cada documento, analiza el historial de tramitación, y finalmente genera un informe en Markdown que guarda como nuevo documento. Podéis ver en los logs cómo va invocando las distintas herramientas MCP: primero consultar_expediente, después listar_documentos, luego obtener_texto_documento para cada uno... y finalmente crear_documento_desde_markdown con el informe generado.
>
> Vamos a ejecutarlo con el Expediente EXP-2024-001. Solo necesita acceder al Expediente, no es necesario que acceda a la documentación asociada al tipo de Expediente. (tarda un poco por rate limits)... ya lo tenemos. Vemos que el expediente tiene un nuevo documento Informe de sitaución.

### [PANTALLA: Agente con LangGraph]

> Por último, veamos un agente implementado con LangGraph. LangGraph nos da más control sobre el flujo de ejecución mediante un grafo de estados. Como ejemplo, tenemos el agente "RedactorResolución" que accede a Expediente, lee el documento de propuesta de resolución y genera el documento de resolución. El agente va pasando por diferentes nodos del grafo: primero recopila información, después la analiza, y finalmente genera el documento de salida.
>
> Vamos a lanzar el agente sobre el expediente EXP-2026-004 imaginando que la propuesta de resolución ha sido firmada y se ha decidido aceptar en su integridad. Según el BPMN ahora corresponde crear el documento de Resolución para ser puesto en firma de la persona competente en la resolución del Expediente. (de nuevo rate limits... un poco de paciencia). Ya tenemos el documento en el Expediente.

---

## PARTE 5: CONCLUSIONES (~1:30 min)

### [PANTALLA: Conclusiones]

> Para terminar, permitidme que resuma lo que hemos visto. aGEntiX es un sistema que permite incorporar agentes de inteligencia artificial en flujos de trabajo administrativos de forma segura, controlada y completamente auditable.

### [PANTALLA: Bullets con características principales]

> Las claves del sistema son: una arquitectura completamente desacoplada de GEX que permite evolución independiente; comunicación estandarizada mediante el protocolo MCP; soporte para agentes CrewAI y LangGraph según las necesidades; configuración declarativa mediante ficheros YAML; un sistema de permisos granular basado en tokens JWT; redacción automática de datos personales para cumplimiento normativo; trazabilidad completa de todas las acciones mediante logs estructurados; y escalabilidad para entornos de producción gracias a Celery y Redis.

### [PANTALLA: Diagrama de lo que hacen los agentes vs lo que hacen las personas]

> Pero si hay algo que quiero que os llevéis de este video es esto: los agentes automatizan las tareas operativas y repetitivas, pero las decisiones que implican responsabilidad legal siguen siendo exclusivamente humanas. La inteligencia artificial asiste y agiliza, pero no decide. Y ese es exactamente el equilibrio que buscábamos.

### [PANTALLA: "Gracias" + enlaces al repositorio]

> Y eso es todo. Muchísimas gracias. El código completo del proyecto está disponible en GitHub, así que si os animo a echarle un vistazo y probarlo vosotros mismos. ¡Hasta la próxima!

---

## NOTAS DE PRODUCCIÓN

| Aspecto                  | Indicación                                     |
| ------------------------ | ---------------------------------------------- |
| Velocidad de locución    | Pausada, ~130 palabras/minuto                  |
| Transiciones             | Suaves entre secciones, sin efectos excesivos  |
| Pausas                   | 2-3 segundos entre secciones                   |
