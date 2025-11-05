# Aspectos Ausentes en la Documentación

## Contexto

Este documento cataloga aspectos críticos que no están mencionados en absoluto en la documentación actual, pero que son necesarios para un sistema en producción.

## 1. Gestión de Costes

### Problema

No se menciona control de costes de llamadas a LLMs, que pueden ser significativos.

### Aspectos Ausentes

**Control de presupuesto**:
```yaml
# No documentado: ¿Cómo se limita el gasto?
cost_controls:
  por_expediente:
    max_cost_eur: 5.00
    alerta_en: 3.00

  por_agente:
    budget_mensual_eur: 10000
    alerta_en_porcentaje: 80

  por_organizacion:
    budget_anual_eur: 100000
```

**Optimización de costes**:
- Caché de respuestas: si la misma pregunta se hace múltiples veces, reutilizar respuesta
- Prompt compression: reducir tamaño de prompts sin perder información
- Modelo tiering: usar modelos más baratos para tareas simples
- Batch processing: agrupar llamadas para descuentos

**Transparencia de costes**:
- Dashboard de costes por tipo de agente
- Atribución de costes por departamento/área
- Alertas de gasto anómalo

### Impacto

Sin control de costes, el sistema podría generar gastos inasumibles. Un solo expediente mal configurado podría consumir presupuesto de meses.

**Ejemplo real**:
```
Escenario: Agente mal configurado envía 500 páginas en cada llamada
Llamadas por expediente: 10
Coste por llamada: 2€
Expedientes al mes: 500
→ Coste mensual: 10,000€

Con control:
→ Alerta en la primera llamada cara
→ Bloqueo automático tras superar umbral
→ Investigación y corrección
```

### Recomendaciones

- Implementar límites de coste hard y soft
- Monitorización en tiempo real
- Optimizaciones automáticas (caché, compression)
- Revisión mensual de costes con justificación de ROI

## 2. Soporte Multimodal

### Problema

Los expedientes incluyen contenido no textual, pero no se especifica cómo los agentes lo procesan.

### Aspectos Ausentes

**Tipos de contenido**:
```
Formatos en expedientes reales:
- PDFs escaneados → Requiere OCR
- Planos arquitectónicos → Requiere visión + conocimiento técnico
- Fotos de obras → Requiere visión
- Mapas catastrales → Requiere interpretación geoespacial
- Hojas de cálculo complejas → Requiere ejecución de fórmulas
- Audio (declaraciones) → Requiere transcripción
- Video (inspecciones) → Requiere visión + temporal
```

**Preguntas sin respuesta**:
- ¿Los agentes tienen capacidad multimodal?
- ¿Hay pipeline de conversión automática (PDF→texto, imagen→descripción)?
- ¿Qué pasa con formatos no soportados?

**Caso de uso crítico**:
```
Tarea: "Verificar que las obras realizadas coinciden con planos aprobados"

Requiere:
1. OCR de planos originales (DWG/PDF)
2. Visión para interpretar fotos de obra
3. Comparación espacial 2D/3D

¿Puede el agente hacer esto? No está documentado.
```

### Impacto

Posible incapacidad de procesar información crítica en expedientes.

### Recomendaciones

- Evaluar capacidades multimodales de LLMs elegidos
- Implementar pipelines de conversión (OCR, transcripción)
- Documentar formatos soportados vs no soportados
- Crear fallback a revisión humana para formatos complejos

## 3. Internacionalización

### Problema

La documentación está en español, pero no se considera procesamiento de otros idiomas.

### Aspectos Ausentes

**Escenarios reales**:
- Documentación aportada por extranjeros en su idioma de origen
- Normativa europea en otros idiomas oficiales
- Documentos técnicos en inglés
- Traducción de resoluciones para notificación internacional

**Preguntas sin respuesta**:
- ¿Los agentes pueden procesar documentos en inglés, francés, etc.?
- ¿Hay traducción automática integrada?
- ¿Cómo se maneja mezcla de idiomas en un mismo expediente?

### Impacto

Posible exclusión de información relevante por barrera idiomática.

### Recomendaciones

- Declarar idiomas soportados
- Integrar traducción automática cuando necesario
- Validar que LLM elegido es multilingüe
- Considerar variaciones regionales (español de España vs Latinoamérica)

## 4. Cumplimiento Normativo Específico

### Problema

Se menciona "entornos regulados" genéricamente, pero sin análisis específico de normativa aplicable.

### Aspectos Ausentes

#### 4.1 GDPR / LOPD (Protección de Datos)

**Obligaciones no documentadas**:
- **Análisis de Impacto (DPIA)**: Requerido para procesamiento automatizado de datos personales
- **Base legal**: ¿Consentimiento? ¿Interés legítimo? ¿Obligación legal?
- **Derechos de los interesados**: Acceso, rectificación, supresión, portabilidad, oposición
- **Transferencias internacionales**: Si LLM está en cloud USA, hay transferencia
- **Delegado de Protección de Datos**: ¿Se ha consultado?

**Ejemplo de problema**:
```
Ciudadano ejerce derecho de supresión (derecho al olvido):
→ ¿Se borran sus datos de logs de agentes?
→ ¿Se borran embeddings generados?
→ ¿Se borran modelos fine-tuned con sus datos?

No documentado.
```

#### 4.2 Ley 39/2015 y 40/2015 (Procedimiento Administrativo)

**Obligaciones no documentadas**:
- **Motivación de decisiones**: Las resoluciones deben estar motivadas
  - Si un agente asiste en decisión, ¿se registra su razonamiento como parte de la motivación?
- **Notificaciones**: Requisitos específicos de notificación al interesado
  - ¿Se notifica que un agente IA participó en su expediente?
- **Recursos**: Derecho a recurrir decisiones
  - ¿El ciudadano puede solicitar revisión humana de acciones de agente?
- **Plazos**: Plazos máximos de resolución
  - ¿Los agentes ayudan a cumplir plazos o los complican?

#### 4.3 ENS (Esquema Nacional de Seguridad)

**Obligaciones no documentadas**:
- **Categorización del sistema**: ¿Nivel BAJO, MEDIO, ALTO?
- **Medidas de seguridad**: Según la categorización
- **Auditorías de seguridad**: Obligatorias cada X años
- **Gestión de incidentes**: Protocolo de respuesta
- **Continuidad de servicio**: Plan de contingencia

**Ejemplo de análisis necesario**:
```
Si el sistema procesa datos de categoría ALTA (ej: servicios sociales):
→ Cifrado obligatorio en tránsito y reposo
→ Auditoría de seguridad bienal
→ Registro de eventos de seguridad
→ Plan de continuidad de negocio
→ Segregación de funciones

¿Está contemplado?
```

#### 4.4 Directiva UE de IA (AI Act)

**Obligaciones potenciales**:
- Clasificación del sistema (riesgo inaceptable, alto, limitado, mínimo)
- Si es riesgo ALTO (probable en contexto administrativo):
  - Sistema de gestión de riesgos
  - Gobernanza y calidad de datos
  - Documentación técnica
  - Transparencia e información a usuarios
  - Supervisión humana
  - Robustez, precisión, ciberseguridad

### Impacto

Incumplimiento normativo puede resultar en:
- Multas cuantiosas (GDPR: hasta 20M€)
- Invalidación de resoluciones administrativas
- Responsabilidad penal en casos graves
- Daño reputacional severo

### Recomendaciones

1. **Contratar asesoría legal especializada** en:
   - Protección de datos
   - Derecho administrativo
   - Cumplimiento AI Act

2. **Realizar DPIA (Data Protection Impact Assessment)**
   - Obligatorio según GDPR
   - Involucrar al DPO

3. **Auditoría ENS**
   - Categorizar el sistema
   - Implementar medidas obligatorias
   - Plan de auditoría

4. **Transparencia con ciudadanos**
   - Informar de uso de IA en expedientes
   - Derecho a revisión humana
   - Explicación de decisiones

## 5. Sesgo y Fairness

### Problema

No hay consideración de sesgos del LLM en decisiones administrativas.

### Aspectos Ausentes

**Tipos de sesgo**:
```
Sesgo de género:
- Agente puede asumir que "arquitecto" = hombre
- Impacto en generación de documentos

Sesgo socioeconómico:
- Agente puede interpretar solicitudes de barrios desfavorecidos de forma diferente

Sesgo geográfico:
- Agente puede tener más dificultad con topónimos locales

Sesgo temporal:
- Datos de entrenamiento antiguos, normativa desactualizada en conocimiento del LLM
```

**Obligación de no discriminación**:
- Constitución Española Art. 14
- Ley 39/2015 Art. 3 (principio de objetividad)

**Ejemplo problemático**:
```
Dos solicitudes idénticas de licencia:
- Solicitante A: Nombre español, dirección barrio centro
- Solicitante B: Nombre extranjero, dirección barrio periférico

¿El agente las procesa de forma idéntica?
No hay validación documentada.
```

### Impacto

Discriminación algorítmica puede violar derechos fundamentales y generar responsabilidad legal.

### Recomendaciones

1. **Testing de sesgo**
   - Crear test suite con casos de diferentes demografías
   - Medir disparidad en outputs
   - Validar antes de cada actualización de agente

2. **Fairness metrics**
   - Demographic parity
   - Equalized odds
   - Monitorización continua

3. **Revisión ética**
   - Comité de ética que apruebe nuevos agentes
   - Análisis de impacto social

4. **Mitigación**
   - Prompts que enfaticen objetividad
   - Fine-tuning con datos balanceados
   - Human oversight en decisiones sensibles

## 6. Explicabilidad (Explainability)

### Problema

Los agentes deben poder explicar sus decisiones, especialmente en contexto administrativo.

### Aspectos Ausentes

**Obligación de motivación**:
- Ley 39/2015 exige que actos administrativos estén motivados
- Si un agente asiste, su razonamiento debe ser parte de la motivación

**Niveles de explicabilidad**:
```
Nivel 1 - Resultado:
"Solicitud inadmisible"

Nivel 2 - Razón:
"Solicitud inadmisible por falta de documento X"

Nivel 3 - Razonamiento:
"He analizado los documentos aportados (A, B, C).
Según el art. 15.3, se requiere el documento X.
No he encontrado el documento X entre los aportados.
Por tanto, la solicitud es inadmisible."

Nivel 4 - Justificación legal:
"Art. 15.3 establece: '...'.
El documento X es obligatorio según interpretación consolidada.
Jurisprudencia: STS 123/2020.
No hay excepción aplicable en este caso."

¿Qué nivel proporciona el agente? No documentado.
```

**Derecho del ciudadano**:
- Entender por qué se tomó una decisión
- Poder impugnarla con argumentos
- Detectar errores

### Impacto

Resoluciones insuficientemente motivadas pueden ser anuladas en vía de recurso.

### Recomendaciones

1. **Configurar agentes para explicabilidad**
   - Prompts que requieran razonamiento paso a paso
   - Chain-of-thought prompting
   - Incluir razonamiento en logs

2. **Interfaz de explicación**
   - Mostrar razonamiento del agente al tramitador
   - Permitir revisión antes de notificar al ciudadano
   - Incluir referencias legales

3. **Testing de explicabilidad**
   - Validar que explicaciones son coherentes
   - Verificar que citan normativa correcta
   - Comprobar que son comprensibles

## 7. Continuidad de Negocio y Disaster Recovery

### Problema

No hay plan para mantener operación si el sistema de agentes falla.

### Aspectos Ausentes

**Escenarios de fallo**:
- Servidor MCP caído
- LLM provider (Anthropic, OpenAI) con outage
- Agente defectuoso desplegado en producción
- Ataque de seguridad

**Preguntas sin respuesta**:
- ¿Puede GEX funcionar sin agentes?
- ¿Hay fallback a procesamiento totalmente manual?
- ¿Cómo se recuperan expedientes en proceso cuando falla el sistema?
- ¿Hay backup de estado de ejecución de agentes?

### Impacto

Downtime puede paralizar administración, incumplir plazos legales, causar daños a ciudadanos.

### Recomendaciones

1. **Diseño resiliente**
   - GEX debe funcionar sin agentes (degradación graciosa)
   - Tareas de agente pueden marcarse para "hacer manualmente"

2. **Redundancia**
   - Múltiples servidores MCP
   - Múltiples LLM providers
   - Failover automático

3. **Plan de contingencia**
   - Procedimiento documentado para operar sin IA
   - Comunicación a usuarios
   - SLA con tiempos de recuperación

## 8. Formación y Change Management

### Problema

No se considera el impacto humano y organizacional de introducir IA.

### Aspectos Ausentes

**Formación necesaria**:
- Tramitadores: cómo trabajar con agentes, cuándo confiar, cuándo desconfiar
- Gestores: cómo interpretar métricas de agentes
- Auditores: cómo auditar decisiones asistidas por IA
- Ciudadanos: qué significa que IA participa en su expediente

**Resistencia al cambio**:
- Miedo a perder empleo
- Desconfianza en la tecnología
- Pérdida de autonomía profesional

**Gestión del cambio**:
- Plan de comunicación
- Programa de formación
- Apoyo psicológico si necesario
- Participación de trabajadores en diseño

### Impacto

Sin gestión del cambio adecuada, el sistema puede ser rechazado o mal utilizado por los usuarios.

### Recomendaciones

1. **Programa de formación**
   - Formación obligatoria antes de usar agentes
   - Certificación de usuarios
   - Formación continua en actualizaciones

2. **Participación**
   - Involucrar a tramitadores en diseño de agentes
   - Recoger feedback continuamente
   - Co-crear soluciones

3. **Transparencia**
   - Comunicar beneficios y limitaciones
   - Ser honesto sobre impacto laboral
   - Plan de recolocación si hay reducción de plantilla

## Resumen de Aspectos Críticos Ausentes

| Aspecto | Impacto si no se aborda | Prioridad |
|---------|-------------------------|-----------|
| Gestión de costes | Gastos inasumibles | Alta |
| Cumplimiento GDPR | Multas hasta 20M€ | Crítica |
| Cumplimiento Ley 39/2015 | Resoluciones anulables | Crítica |
| ENS | Incumplimiento legal | Crítica |
| Sesgo y fairness | Discriminación, responsabilidad legal | Alta |
| Explicabilidad | Resoluciones anulables | Alta |
| Soporte multimodal | Información inaccesible | Media |
| Internacionalización | Barrera idiomática | Baja |
| Business continuity | Downtime, incumplimiento plazos | Alta |
| Formación | Rechazo del sistema | Media |

## Relaciones

- Ver: [[100-problematica-general|Problemática general]]
- Ver: [[102-problema-permisos-seguridad|Seguridad]]
- Ver: [[103-problema-enfoque-conservador|Sesgo en automatización]]
- Ver: [[106-problema-auditoria-trazabilidad|Cumplimiento]]
- Ver: [[107-problema-contexto-agentes|Multimodal]]
- Ver: [[109-prioridades-mejora|Priorización]]
