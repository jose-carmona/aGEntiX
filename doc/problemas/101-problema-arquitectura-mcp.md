# Problemas en la Arquitectura MCP

## Contexto

La propuesta actual define el uso de **Model Context Protocol (MCP)** como mecanismo de desacoplamiento entre agentes y GEX, siguiendo el flujo: `BPMN → Agente → MCP → API de GEX`

Ver: [Propuesta de acceso MCP](../042-acceso-mcp.md)

## Fortalezas Identificadas

- **Principio arquitectónico correcto**: El desacoplamiento mediante protocolo estándar es una decisión sólida
- **Flexibilidad**: Permite evolución independiente de componentes
- **Estandarización**: MCP es un protocolo establecido y documentado

## Problemas Críticos Identificados

### 1. Documentación Insuficiente de Implementación

**Problema**: No se especifica CÓMO se implementará MCP concretamente.

**Preguntas sin respuesta**:
- ¿Será un servidor MCP personalizado?
- ¿Qué recursos expondrá? (en terminología MCP)
- ¿Qué herramientas (tools) estarán disponibles?
- ¿Qué prompts estarán predefinidos?
- ¿Habrá sampling? ¿Roots?

**Impacto**: Imposible estimar esfuerzo de implementación o evaluar viabilidad técnica.

### 2. Latencia No Considerada

**Problema**: La cadena `Agente → MCP → API GEX` introduce latencia adicional.

**Aspectos no documentados**:
- Requisitos de rendimiento (ej: "respuesta en < 2s")
- Impacto en workflows con timeouts BPMN
- Estrategias de optimización (caching, batching)
- Métricas de SLA

**Impacto**: Riesgo de timeouts en workflows, experiencia de usuario degradada.

### 3. Ausencia de Arquitectura de Fallos

**Problema**: No hay estrategia para manejar fallos del servidor MCP.

**Escenarios no contemplados**:
- ¿Qué ocurre si el servidor MCP está caído?
- ¿Hay reintentos automáticos?
- ¿Circuit breakers?
- ¿Fallback a modo degradado?
- ¿Cómo se notifica al workflow BPMN?

**Impacto**: Workflows bloqueados sin path de recuperación.

### 4. Versionado No Definido

**Problema**: No se menciona cómo gestionar evolución del protocolo.

**Aspectos críticos**:
- ¿Cómo se versionan los recursos/herramientas MCP?
- ¿Compatibilidad hacia atrás?
- ¿Cómo se coordinan upgrades de agentes vs servidor MCP?
- ¿Deprecation policy?

**Impacto**: Riesgo de breaking changes que rompan workflows en producción.

## Recomendaciones

### Prioridad Crítica

1. **Definir esquema concreto MCP**
   - Catálogo de recursos (ej: `expediente://{id}`, `documento://{id}`)
   - Catálogo de herramientas (ej: `create_document`, `sign_document`)
   - Esquemas JSON para cada recurso/herramienta

2. **Establecer SLAs y requisitos de latencia**
   - P50, P95, P99 de tiempo de respuesta
   - Timeout por tipo de operación
   - Budget de latencia para workflows críticos

3. **Diseñar estrategia de resiliencia**
   - Implementar circuit breaker pattern
   - Definir política de reintentos (exponential backoff)
   - Crear fallback strategy (ej: marcar tarea para revisión manual)

### Prioridad Alta

4. **Implementar versionado semántico**
   - Versionar servidor MCP: `v1.0.0`, `v1.1.0`, `v2.0.0`
   - Agents declaran versión MCP soportada
   - Mantener compatibilidad en minor versions
   - Documentar migration path para major versions

5. **Monitorización**
   - Métricas: latencia, tasa de error, throughput
   - Alertas automáticas
   - Dashboards de observabilidad

## Ejemplo Concreto de Especificación Necesaria

```json
{
  "mcp_version": "1.0.0",
  "resources": [
    {
      "uri": "expediente://{expediente_id}",
      "name": "Expediente",
      "description": "Acceso completo a un expediente",
      "mimeType": "application/json",
      "schema": "schemas/expediente.json"
    }
  ],
  "tools": [
    {
      "name": "create_document",
      "description": "Crea un documento en el expediente",
      "inputSchema": "schemas/create_document_input.json",
      "permissions": ["write:document"]
    }
  ]
}
```

## Relaciones

- Ver: [Problemática general](100-problematica-general.md)
- Ver: [Propuesta actual de MCP](../042-acceso-mcp.md)
- Ver: [Criterios de diseño](../040-criterios-diseño.md)
- Ver: [Propagación de permisos vía MCP](102-problema-permisos-seguridad.md)
- Ver: [Prioridades de mejora](109-prioridades-mejora.md)
