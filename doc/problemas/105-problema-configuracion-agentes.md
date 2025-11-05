# Problemas en la Configuración de Agentes

## Contexto

La propuesta actual define configuración de agentes en dos niveles:
- **Configuración general del tipo**: nombre, system prompt, URL, modelo LLM
- **Configuración específica de tarea**: prompt específico, herramientas disponibles

Ver: [[../031-configuracion-agente|Configuración de agentes]]

## Fortalezas Identificadas

- **Separación tipo/instancia**: Permite reutilización de un tipo de agente en múltiples tareas
- **Herramientas configurables**: Flexibilidad en capacidades por tarea
- **Configuración por capas**: Herencia de configuración general con especialización

## Problemas Críticos Identificados

### 1. Modelo de Configuración Demasiado Simple

**Problema**: La especificación actual es un esqueleto mínimo, insuficiente para implementación.

**Aspectos faltantes**:
- Rate limits (llamadas por minuto, tokens por día)
- Retry policies (reintentos, backoff)
- Timeouts (por operación, total)
- Temperatura y otros parámetros del LLM
- Máximo de tokens de entrada/salida
- Estrategia de chunking para contextos grandes
- Fallback a otro modelo si el principal falla
- Configuración de logging (nivel, destino)
- Coste máximo permitido por ejecución
- Concurrencia máxima

**Impacto**: Cada implementador tendrá que inventar estos aspectos, generando inconsistencia.

### 2. Sin Gestión de Versiones

**Problema**: No hay estrategia para actualizar un agente sin romper workflows activos.

**Escenarios problemáticos**:
```
Situación:
- 50 workflows usan "document_extractor v1.0"
- Se desarrolla "document_extractor v2.0" con mejoras
- v2.0 cambia formato de output

¿Cómo se migra?
- ¿Se actualiza v1.0 in-place? (rompe workflows activos)
- ¿Se despliegan ambas versiones? (complejidad operacional)
- ¿Se fuerza migración de workflows? (requiere testing masivo)
```

**Aspectos no contemplados**:
- Versionado semántico (major.minor.patch)
- Compatibilidad hacia atrás
- Deprecation warnings
- Sunset policy
- Canary deployments
- Blue-green deployments

**Impacto**: Imposibilidad de evolucionar agentes sin causar disrupciones.

### 3. Ausencia de Testing y Validación

**Problema**: No hay estrategia para validar que un agente funciona correctamente antes de producción.

**Preguntas sin respuesta**:
- ¿Cómo se testea un agente antes de usarlo en workflows reales?
- ¿Hay entorno de staging?
- ¿Test cases obligatorios?
- ¿Métricas de quality gate (ej: tasa de éxito >95%)?
- ¿Cómo se detecta regression al actualizar?

**Impacto**: Agentes defectuosos en producción, errores en expedientes reales.

### 4. Prompt Engineering No Estructurado

**Problema**: Los prompts son texto libre sin estructura, validación ni versionado.

**Aspectos críticos**:
- No hay templates de prompts
- No se valida que prompts incluyan instrucciones críticas (ej: "siempre registra tu razonamiento")
- No hay versionado de prompts independiente de código
- No se documenta qué hace cada prompt
- No hay A/B testing de prompts

**Ejemplo de problema**:
```
System prompt actual (texto libre):
"Eres un asistente que extrae información de documentos."

System prompt necesario (estructurado):
role: document_extractor
instructions:
  - Extrae información de documentos administrativos
  - Usa SOLO información presente en el documento
  - Si un campo no está presente, devuelve null
  - Registra tu razonamiento en el campo 'reasoning'
  - Si confianza <0.7, marca 'requires_human_review': true
constraints:
  - No inventes información
  - No asumas valores por defecto
  - No uses conocimiento externo al documento
output_format: schemas/extraction_result.json
examples: [...]
```

**Impacto**: Comportamiento inconsistente, difícil depuración, imposibilidad de mejorar sistemáticamente.

### 5. Sin Monitorización

**Problema**: No hay métricas de rendimiento por agente.

**Aspectos ausentes**:
- Latencia (P50, P95, P99)
- Tasa de éxito/fallo
- Distribución de niveles de confianza
- Tasa de escalado a humano
- Coste por ejecución
- Tokens consumidos
- Versión del agente más usada
- Alertas automáticas (ej: tasa de error >5%)

**Impacto**: Imposibilidad de optimizar, detectar degradaciones, justificar costes.

## Recomendaciones

### Prioridad Crítica

1. **Ampliar modelo de configuración**
   ```yaml
   tipo_agente:
     # Identificación
     nombre: "document_extractor"
     version: "1.2.0"
     descripcion: "Extrae datos estructurados de documentos administrativos"
     autor: "equipo-ia@ejemplo.es"
     fecha_creacion: "2024-01-15"

     # LLM
     modelo_llm: "claude-sonnet-4"
     modelo_fallback: "claude-sonnet-3-5"
     temperatura: 0.1
     max_tokens_output: 4000

     # Prompts
     system_prompt_template: "prompts/document_extractor_system.j2"
     system_prompt_version: "2.1.0"

     # Límites
     timeout_default: 120s
     timeout_max: 600s
     rate_limit:
       llamadas_por_minuto: 30
       tokens_por_dia: 1000000
     costo_max_por_ejecucion: 0.50  # EUR
     concurrencia_max: 10

     # Resilencia
     retry_policy:
       max_intentos: 3
       backoff: "exponential"
       retry_on: ["timeout", "rate_limit", "server_error"]

     # Observabilidad
     logging_level: "INFO"
     trace_sampling: 0.1  # 10% de ejecuciones

     # Endpoint
     url: "https://agentes.ejemplo.es/document-extractor"
     health_check: "https://agentes.ejemplo.es/document-extractor/health"
   ```

2. **Implementar versionado y deployment strategies**
   ```yaml
   deployment:
     strategy: "blue-green"
     versions_activas:
       - version: "1.2.0"
         traffic_percentage: 90
         workflows_pinned: ["workflow_critical_1", "workflow_critical_2"]
       - version: "1.3.0"
         traffic_percentage: 10  # canary
         workflows_pinned: []

     deprecation:
       version: "1.0.0"
       deprecated_since: "2024-03-01"
       sunset_date: "2024-06-01"
       migration_guide: "docs/migration_1.0_to_1.2.md"
   ```

3. **Crear framework de testing**
   ```yaml
   test_suite:
     tipo_agente: "document_extractor"

     unit_tests:
       - nombre: "extrae_dni_correcto"
         input: "test_data/solicitud_con_dni.pdf"
         expected_output:
           dni: "12345678A"
         assertion: "output.dni == expected.dni"

       - nombre: "detecta_campo_ausente"
         input: "test_data/solicitud_sin_telefono.pdf"
         expected_output:
           telefono: null
         assertion: "output.telefono is null"

     integration_tests:
       - nombre: "workflow_completo_licencia_obras"
         expediente_test: "test_expedientes/licencia_001"

     performance_tests:
       - nombre: "latencia_documento_grande"
         input: "test_data/documento_50_paginas.pdf"
         max_latency: 30s

     quality_gates:
       tasa_exito_minima: 0.95
       latencia_p95_maxima: 10s
       confianza_promedio_minima: 0.85
   ```

### Prioridad Alta

4. **Estructurar prompts**
   - Usar templates (Jinja2, Liquid)
   - Versionar prompts separadamente del código
   - Validar que incluyen instrucciones críticas
   - Documentar propósito y ejemplos

   ```jinja2
   {# prompts/document_extractor_system.j2 v2.1.0 #}
   Eres un asistente especializado en extracción de información.

   ## Tu Rol
   {{ role_description }}

   ## Instrucciones Obligatorias
   {% for instruction in mandatory_instructions %}
   - {{ instruction }}
   {% endfor %}

   ## Formato de Salida
   Devuelve JSON siguiendo este esquema:
   {{ output_schema | tojson }}

   ## Ejemplos
   {% for example in examples %}
   Input: {{ example.input }}
   Output: {{ example.output }}
   {% endfor %}
   ```

5. **Implementar telemetría completa**
   ```python
   # Instrumentación con OpenTelemetry
   from opentelemetry import trace, metrics

   tracer = trace.get_tracer("agentix.agents")
   meter = metrics.get_meter("agentix.agents")

   # Métricas
   latency_histogram = meter.create_histogram(
       "agent.execution.duration",
       unit="ms",
       description="Duración de ejecución del agente"
   )

   success_counter = meter.create_counter(
       "agent.execution.success",
       description="Ejecuciones exitosas"
   )

   cost_counter = meter.create_counter(
       "agent.execution.cost",
       unit="EUR",
       description="Coste de ejecuciones"
   )

   # En cada ejecución
   with tracer.start_as_current_span("agent.execute") as span:
       span.set_attributes({
           "agent.type": "document_extractor",
           "agent.version": "1.2.0",
           "expediente.id": expediente_id
       })
       # ... ejecución ...
       latency_histogram.record(duration_ms, {"agent.type": "document_extractor"})
       cost_counter.add(execution_cost, {"agent.type": "document_extractor"})
   ```

### Prioridad Media

6. **A/B testing de prompts**
   - Desplegar múltiples variantes de prompts
   - Medir impacto en tasa de éxito, confianza, latencia
   - Seleccionar ganador automáticamente

7. **Configuration as Code**
   - Todas las configuraciones en Git
   - Revisión por pares de cambios
   - CI/CD para desplegar cambios de configuración
   - Rollback automático si degradación detectada

8. **Catálogo de agentes**
   - Portal web con todos los tipos de agentes
   - Documentación, ejemplos, métricas
   - Permite a diseñadores de workflows descubrir agentes disponibles

## Ejemplo Completo de Configuración Necesaria

Ver archivo aparte: `examples/agent_config_complete.yaml`

## Relaciones

- Ver: [[100-problematica-general|Problemática general]]
- Ver: [[../031-configuracion-agente|Configuración actual]]
- Ver: [[101-problema-arquitectura-mcp|Versionado de MCP]]
- Ver: [[104-problema-integracion-bpmn|Timeouts en workflows]]
- Ver: [[106-problema-auditoria-trazabilidad|Logging y telemetría]]
- Ver: [[109-prioridades-mejora|Prioridades]]
