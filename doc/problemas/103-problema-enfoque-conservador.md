# Problemas con el Enfoque Conservador

## Contexto

La estrategia actual adopta un **enfoque conservador** donde:
- Análisis legal y toma de decisiones permanecen exclusivamente humanos
- IA puede automatizar extracción de información y generación de documentos
- IA puede asistir (pero no decidir) en análisis

Ver: [Estrategia conservadora](../041-enfoque-conservador.md), [Tareas candidatas para IA](../013-tareas-ia-candidatas.md)

## Fortalezas Identificadas

- **Apropiado para contexto público**: La cautela es correcta dado el entorno regulado
- **Límites éticos claros**: Mantener decisiones legales en humanos es prudente
- **Evolución gradual**: Permite aprendizaje iterativo sin riesgo excesivo

## Problemas Críticos Identificados

### 1. Línea Difusa en la Práctica

**Problema**: La distinción entre "análisis de información" (asistencia IA permitida) y "toma de decisiones" (solo humanos) es conceptualmente clara pero prácticamente ambigua.

**Ejemplos problemáticos**:

| Tarea | ¿IA puede? | Ambigüedad |
|-------|------------|------------|
| "Verificar que solicitud cumple requisitos normativos X, Y, Z" | ¿? | ¿Es verificación (IA) o decisión de validez (humano)? |
| "Determinar si expediente debe enviarse a área fiscal" | ¿? | ¿Es clasificación (IA) o decisión administrativa (humano)? |
| "Calcular plazo de respuesta según art. 21 Ley 39/2015" | ¿? | ¿Es cálculo (IA) o interpretación legal (humano)? |
| "Identificar si solicitud es urgente" | ¿? | ¿Es extracción de dato (IA) o juicio de urgencia (humano)? |

**Impacto**: Equipos de implementación tendrán interpretaciones inconsistentes. Riesgo de que agentes de facto tomen decisiones sin supervisión adecuada.

### 2. Riesgo de Automatización Sesgada

**Problema**: Al clasificar solo ciertas tareas como "automatizables", se pueden perpetuar o amplificar sesgos existentes.

**Consideraciones no documentadas**:
- ¿Se automatizarán primero tareas de bajo valor (liberando poco tiempo)?
- ¿O tareas de alto volumen (maximizando impacto)?
- ¿Hay riesgo de que trabajadores afectados por automatización sean de perfiles específicos?
- ¿Se considera el impacto social y laboral?

**Impacto**: Resistencia organizacional, problemas éticos, subutilización del sistema.

### 3. Ausencia de Métricas de Éxito

**Problema**: No hay KPIs definidos para evaluar si el enfoque conservador está funcionando.

**Preguntas sin respuesta**:
- ¿Cómo se mide "éxito"? ¿Tiempo ahorrado? ¿Errores reducidos? ¿Satisfacción del usuario?
- ¿Qué tasa de error es aceptable para agentes?
- ¿Cuándo se considera que un tipo de tarea está "lista" para automatización?
- ¿Qué métricas determinarían ampliar el alcance de IA?

**Impacto**: Imposible evaluar objetivamente si se debe expandir, mantener o reducir el uso de agentes.

### 4. Sin Estrategia de Escalabilidad

**Problema**: No hay criterios documentados para decidir cuándo ampliar el alcance de automatización.

**Aspectos críticos**:
- ¿Quién decide qué nuevas tareas pueden automatizarse?
- ¿Qué proceso de aprobación existe?
- ¿Hay piloto obligatorio antes de producción?
- ¿Criterios de "graduación" de una tarea de piloto a producción?

**Impacto**: Parálisis por análisis o expansión descontrolada sin governance.

### 5. Ambigüedad en "Asistencia"

**Problema**: Cuando IA "asiste" pero humano "decide", la responsabilidad legal puede diluirse.

**Escenario problemático**:
```
1. Agente analiza expediente y recomienda: "Denegar solicitud por incumplimiento art. 15.3"
2. Humano revisa brevemente y confirma la recomendación
3. Solicitud denegada
4. Ciudadano recurre y gana: la denegación fue incorrecta

¿Quién es responsable? ¿El humano que "decidió"?
¿El agente que "recomendó erróneamente"?
¿El diseñador del agente?
```

**Impacto**: Confusión en accountability, problemas legales en caso de error.

## Recomendaciones

### Prioridad Crítica

1. **Crear matriz de decisión clara**
   - Desarrollar taxonomía detallada con ejemplos concretos
   - Incluir casos grises con su resolución
   - Publicar como guía oficial para implementadores

   **Ejemplo de formato**:
   ```
   | Tarea | Categoría | Puede IA | Justificación |
   |-------|-----------|----------|---------------|
   | Extraer DNI de documento | Extracción | Sí | Dato objetivo |
   | Verificar formato de DNI | Validación | Sí | Regla determinista |
   | Determinar si DNI es válido para trámite | Decisión | No | Requiere contexto legal |
   ```

2. **Implementar human-in-the-loop obligatorio**
   - Para tareas de "asistencia", diseñar interfaz que fuerce revisión activa (no solo confirmación pasiva)
   - Requerir justificación humana adicional a la del agente
   - Registrar tiempo de revisión humana (detectar "rubber stamping")

3. **Definir métricas de éxito**
   ```yaml
   kpis:
     eficiencia:
       - tiempo_procesamiento_expediente: {objetivo: "-30%", limite_minimo: "-10%"}
       - volumen_automatizado: {objetivo: "40% tareas candidatas", primera_fase: "15%"}
     calidad:
       - tasa_error_agente: {objetivo: "<2%", bloqueante: ">5%"}
       - recursos_ciudadano: {objetivo: "<1%", bloqueante: ">3%"}
     satisfaccion:
       - satisfaccion_usuario_interno: {objetivo: ">4/5"}
       - aceptacion_automatizacion: {objetivo: ">70%"}
   ```

### Prioridad Alta

4. **Establecer governance de expansión**
   - Crear comité revisor: técnico + legal + ético + representación trabajadores
   - Definir proceso de propuesta → evaluación → piloto → producción
   - Criterios de aprobación:
     - Tasa de éxito en piloto >95%
     - Satisfacción usuarios internos >70%
     - Revisión legal sin objeciones
     - Impacto laboral evaluado y mitigado

5. **Clarificar cadena de responsabilidad**
   - Documentar que decisiones asistidas por IA tienen responsabilidad 100% humana
   - Formar a usuarios en "revisión crítica" vs "confirmación pasiva"
   - Registrar metadatos: tiempo de revisión, si humano modificó recomendación, justificación

6. **Considerar impacto social y laboral**
   - Realizar evaluación de impacto en puestos de trabajo
   - Plan de reentrenamiento/recolocación
   - Comunicación transparente con trabajadores
   - Priorizar automatización de tareas de bajo valor añadido (libera tiempo para trabajo de mayor valor)

### Prioridad Media

7. **Crear ciclo de feedback**
   - Cuando ciudadano recurre una decisión asistida por IA, analizar si IA contribuyó al error
   - Feed back loop para mejorar agentes
   - Publicar estadísticas de errores de forma transparente

8. **Definir "niveles de autonomía"**
   - Nivel 0: Solo humano (análisis legal complejo)
   - Nivel 1: IA asiste, humano decide con revisión profunda
   - Nivel 2: IA asiste, humano confirma con revisión ligera
   - Nivel 3: IA ejecuta, humano revisa por muestreo
   - Nivel 4: IA totalmente autónoma (tareas deterministas)

## Ejemplo de Mejora Necesaria

**Situación actual**:
> "Análisis de información para ayuda en la toma de decisiones (pero la decisión final sigue siendo humana)"

**Propuesta mejorada**:
```yaml
tarea: "Verificar cumplimiento de requisitos de subvención"
categoria: "asistencia_ia_nivel_1"

agente:
  input: {expediente, normativa_subvencion}
  output:
    cumplimiento: boolean
    requisitos_evaluados: list
    justificacion: string
    confianza: float[0-1]

humano:
  recibe: output_agente
  debe:
    - Revisar justificacion completamente
    - Verificar contra normativa original
    - Documentar acuerdo/desacuerdo con analisis IA
    - Si desacuerdo: documentar razonamiento propio
  no_puede:
    - Confirmar sin revisar (sistema detecta confirmaciones <30s)
  responsabilidad: 100% del resultado final

auditoria:
  registrar:
    - tiempo_revision_humana
    - humano_modifico_conclusion: boolean
    - fundamentacion_humana: string
```

## Relaciones

- Ver: [Problemática general](100-problematica-general.md)
- Ver: [Estrategia actual](../041-enfoque-conservador.md)
- Ver: [Tareas candidatas](../013-tareas-ia-candidatas.md)
- Ver: [Tareas que requieren humanos](../012-tareas-humanas.md)
- Ver: [Auditoría de decisiones](106-problema-auditoria-trazabilidad.md)
- Ver: [Fairness y sesgo](108-aspectos-ausentes.md)
- Ver: [Prioridades](109-prioridades-mejora.md)
