# Problemas en la Integración BPMN

## Contexto

La propuesta integra agentes IA en workflows BPMN mediante **acciones de tipo Agente** dentro de tareas existentes. El modelo permite combinar acciones automáticas, manuales y de agente.

Ver: [[../020-bpmn-modelo|Modelo BPMN]], [[../023-acciones-agente|Acciones de agente]]

## Fortalezas Identificadas

- **Integración natural**: Las acciones de agente dentro de tareas BPMN es conceptualmente elegante
- **Composabilidad**: Permite combinar diferentes tipos de acciones en el mismo workflow
- **Reutilización**: Aprovecha motor BPMN existente sin reescribirlo

## Problemas Críticos Identificados

### 1. Gestión de Estado No Definida

**Problema**: No se especifica qué ocurre si un agente falla a mitad de una tarea.

**Escenarios no contemplados**:

```
Tarea: "Procesar solicitud de licencia"
Acciones:
  1. Acción humana: "Asignar a tramitador"
  2. Acción agente: "Extraer datos de documentos adjuntos"  ← FALLA aquí
  3. Acción automática: "Crear entrada en contabilidad"
  4. Acción humana: "Revisar y aprobar"

¿Qué ocurre?
- ¿Se revierten acciones 1 y 2?
- ¿La tarea queda en estado inconsistente?
- ¿Se marca para intervención manual?
- ¿Hay rollback automático?
```

**Aspectos críticos**:
- Transaccionalidad de tareas con múltiples acciones
- Compensación de acciones ya ejecutadas
- Idempotencia de acciones de agente (¿se pueden reintentar?)
- Estado persistente durante ejecución de agente

**Impacto**: Riesgo de corrupción de datos, expedientes en estados inconsistentes.

### 2. Timeouts en Agentes

**Problema**: Los LLMs pueden ser lentos. No se especifica cómo manejar timeouts.

**Aspectos no documentados**:
- ¿Cuál es el timeout por defecto de una acción de agente?
- ¿Es configurable por tipo de agente?
- ¿Qué ocurre al alcanzar timeout? ¿Se cancela? ¿Se reintenta?
- ¿Cómo interactúa con timeouts de tareas BPMN ya existentes?

**Ejemplo problemático**:
```
Tarea con timeout: 5 minutos
Acciones:
  1. Acción agente: "Analizar 50 documentos" (puede tardar 10 minutos)
  2. Acción automática: "Notificar resultado"

¿El timeout de la tarea aplica a toda la secuencia?
¿O cada acción tiene su propio timeout?
```

**Impacto**: Workflows bloqueados, experiencia de usuario degradada, escalado a tarea de fallback indeseado.

### 3. Paralelización No Especificada

**Problema**: No está claro si múltiples acciones de agente pueden ejecutarse en paralelo.

**Preguntas sin respuesta**:
- ¿Pueden dos acciones de agente ejecutarse concurrentemente en la misma tarea?
- ¿Hay límite de concurrencia?
- ¿Cómo se manejan condiciones de carrera? (ej: dos agentes intentan modificar el mismo documento)
- ¿Hay orden de ejecución garantizado?

**Ejemplo útil no contemplado**:
```
Tarea: "Analizar solicitud compleja"
Acciones (idealmente en paralelo para rapidez):
  - Agente A: "Extraer datos fiscales"
  - Agente B: "Verificar documentación técnica"
  - Agente C: "Validar requisitos urbanísticos"
  - Acción automática: "Consolidar resultados"

¿Esto es posible? ¿Cómo se modela en BPMN?
```

**Impacto**: Workflows más lentos de lo necesario, subutilización de recursos.

### 4. Condiciones de Transición

**Problema**: No se especifica cómo determina el BPMN si una acción de agente tuvo "éxito".

**Aspectos críticos**:
- ¿El agente devuelve código de éxito/error explícito?
- ¿Qué formato tiene la respuesta del agente?
- ¿Puede un agente indicar "necesito intervención humana"?
- ¿Las transiciones BPMN pueden evaluar la salida del agente?

**Ejemplo necesario**:
```bpmn
Tarea: "Evaluar admisibilidad"
  Acción agente: "Verificar cumplimiento de requisitos"
    Output esperado: {
      admisible: boolean,
      requisitos_faltantes: string[],
      confianza: float,
      requiere_revision_humana: boolean
    }

Siguiente tarea según:
  - Si admisible=true AND confianza>0.9 → "Pasar a tramitación"
  - Si admisible=false → "Notificar inadmisión"
  - Si requiere_revision_humana → "Revisión manual"

¿Cómo se modela esto en BPMN estándar?
```

**Impacto**: Imposible crear workflows que tomen decisiones basadas en output de agentes.

### 5. Orquestación vs Coreografía

**Problema**: No se especifica si habrá coordinación entre múltiples agentes.

**Preguntas arquitectónicas**:
- ¿Un agente puede invocar a otro agente?
- ¿Hay orquestador central?
- ¿O cada agente es independiente?
- ¿Puede haber pasaje de contexto entre agentes?

**Escenario no contemplado**:
```
Flujo deseado:
  Agente Extractor → genera datos estructurados
  ↓
  Agente Validador → valida consistencia de datos
  ↓
  Agente Generador → crea informe final

¿Esto requiere 3 tareas BPMN separadas?
¿O puede ser una tarea con 3 acciones de agente que se pasan contexto?
```

**Impacto**: Diseño de workflows ineficiente o imposibilidad de implementar casos de uso complejos.

## Recomendaciones

### Prioridad Crítica

1. **Definir semántica de transacciones**
   - Adoptar patrón **Saga** para tareas con múltiples acciones
   - Cada acción de agente debe declarar acción compensatoria
   - Implementar estado de tarea: `pending`, `executing`, `compensating`, `completed`, `failed`

   **Ejemplo**:
   ```yaml
   accion_agente:
     nombre: "extraer_datos"
     compensacion: "eliminar_datos_extraidos"
     idempotente: true
   ```

2. **Establecer timeouts configurables**
   ```yaml
   tipo_agente:
     nombre: "document_extractor"
     timeout_default: 120s
     timeout_max: 600s

   accion_agente:
     tipo: "document_extractor"
     timeout_override: 300s  # para este caso específico
     on_timeout:
       action: "retry"
       max_retries: 2
       backoff: "exponential"
       fallback: "escalate_to_human"
   ```

3. **Diseñar protocolo de respuesta del agente**
   ```json
   {
     "status": "success" | "failure" | "needs_human" | "partial",
     "result": {
       "data": {...},
       "confidence": 0.95,
       "execution_time_ms": 1234
     },
     "errors": [],
     "metadata": {
       "agent_version": "1.2.3",
       "model_used": "claude-sonnet-4"
     },
     "next_action_recommendation": "continue" | "halt" | "branch_to:task_id"
   }
   ```

### Prioridad Alta

4. **Soportar paralelización**
   - Permitir marcado de acciones como `parallel: true`
   - Implementar barrera de sincronización al final
   - Gestionar conflictos con locking optimista

   **Ejemplo BPMN extendido**:
   ```xml
   <task id="analizar_solicitud">
     <parallelActions>
       <agentAction id="agente_fiscal" />
       <agentAction id="agente_tecnico" />
       <agentAction id="agente_urbanistico" />
     </parallelActions>
     <action id="consolidar_resultados" dependsOn="all_parallel" />
   </task>
   ```

5. **Implementar evaluación de condiciones**
   - Permitir que transiciones BPMN evalúen output de agentes
   - Usar JSONPath o similar para extraer valores
   - Soportar expresiones complejas

   **Ejemplo**:
   ```xml
   <sequenceFlow sourceRef="evaluar" targetRef="tramitar">
     <conditionExpression>
       ${agent_output.admisible == true && agent_output.confianza > 0.9}
     </conditionExpression>
   </sequenceFlow>
   ```

6. **Considerar patrón Saga**
   - Para workflows largos con múltiples agentes
   - Implementar Saga Execution Coordinator
   - Registrar progreso para recuperación ante fallos

### Prioridad Media

7. **Especificar modelo de coordinación**
   - Decisión arquitectónica: ¿Orquestación centralizada o agentes independientes?
   - Si hay coordinación: diseñar API de comunicación inter-agente
   - Prevenir deadlocks en coordinación compleja

8. **Monitorización de workflows con agentes**
   - Dashboard de estado de acciones de agente en tiempo real
   - Alertas cuando acciones de agente exceden tiempo esperado
   - Métricas: tiempo de ejecución por tipo de agente, tasa de éxito, etc.

## Ejemplo de Especificación Necesaria

```yaml
# Definición completa de tarea BPMN con acciones de agente
tarea_bpmn:
  id: "procesar_solicitud_licencia"
  nombre: "Procesar solicitud de licencia de obras"
  timeout_total: 600s

  acciones:
    - tipo: "manual"
      id: "asignar_tramitador"
      actor: "role:tramitador"

    - tipo: "agente"
      id: "extraer_datos"
      agente: "document_extractor"
      input:
        documentos: "${expediente.documentos}"
        esquema: "schemas/licencia_obras.json"
      timeout: 180s
      on_failure:
        action: "escalate_to_human"
        assign_to: "${tramitador_asignado}"
      compensacion: "eliminar_datos_temp"
      idempotente: true

    - tipo: "agente"
      id: "validar_datos"
      agente: "data_validator"
      depends_on: "extraer_datos"
      input:
        datos: "${extraer_datos.result.data}"

    - tipo: "automatica"
      id: "crear_asiento_contable"
      depends_on: "validar_datos"
      condition: "${validar_datos.result.valido == true}"
      compensacion: "anular_asiento_contable"

  transiciones:
    - condition: "${validar_datos.result.valido == true}"
      siguiente_tarea: "revision_tecnica"
    - condition: "${validar_datos.result.valido == false}"
      siguiente_tarea: "requiere_subsanacion"
    - condition: "${extraer_datos.status == 'needs_human'}"
      siguiente_tarea: "extraccion_manual"
```

## Relaciones

- Ver: [[100-problematica-general|Problemática general]]
- Ver: [[../020-bpmn-modelo|Modelo BPMN actual]]
- Ver: [[../023-acciones-agente|Acciones de agente]]
- Ver: [[101-problema-arquitectura-mcp|Latencia y fallos MCP]]
- Ver: [[105-problema-configuracion-agentes|Configuración de timeouts]]
- Ver: [[109-prioridades-mejora|Prioridades]]
