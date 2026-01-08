# Step 9: Agente Redactor de Propuesta de Resolución

## Objetivo

Crear un nuevo agente (`RedactorPropuestaResolucion`) capaz de generar automáticamente un documento de **Propuesta de Resolución** para expedientes de subvenciones, utilizando:

1. **Plantilla de documentación** leída via MCP Documentación
2. **Datos del expediente** leídos via MCP Expedientes
3. **Informe de situación** previo del expediente leído via MCP Expedientes
4. **Guardar el documento generado** en el expediente via MCP Expedientes

---

## Contexto del Sistema

### MCPs Disponibles

| MCP | Descripción | Permisos Requeridos |
|-----|-------------|---------------------|
| `agentix-mcp-expedientes` | Acceso a expedientes, documentos e historial | `consulta`, `gestion` |
| `agentix-mcp-documentacion` | Acceso a normativa, instrucciones y plantillas | `documentacion:leer`, `documentacion:buscar` |

### Flujo de Trabajo

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AGENTE: RedactorPropuestaResolucion                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. OBTENER PLANTILLA (MCP Documentación)                               │
│     └─> obtener_doc_documentacion(                                      │
│           tipo_expediente="subvenciones",                               │
│           tipo_documento="plantilla_propuesta_resolucion"               │
│         )                                                               │
│                                                                         │
│  2. CONSULTAR EXPEDIENTE (MCP Expedientes)                              │
│     └─> consultar_expediente(expediente_id)                             │
│         ├─> Extraer: datos solicitante, tipo, estado, fechas            │
│         └─> Identificar documento "informe_situacion.md"                │
│                                                                         │
│  3. LEER INFORME DE SITUACIÓN (MCP Expedientes)                         │
│     └─> obtener_texto_documento(expediente_id, doc_id_informe)          │
│         └─> Extraer: análisis previo, puntuaciones, observaciones       │
│                                                                         │
│  4. GENERAR PROPUESTA DE RESOLUCIÓN                                     │
│     └─> Rellenar plantilla con datos extraídos                          │
│         ├─> Campos del expediente (solicitante, proyecto, fechas)       │
│         ├─> Campos del informe (puntuaciones, análisis)                 │
│         └─> Generar fundamentación jurídica                             │
│                                                                         │
│  5. GUARDAR DOCUMENTO (MCP Expedientes)                                 │
│     └─> crear_documento_desde_markdown(                                 │
│           expediente_id,                                                │
│           nombre="propuesta_resolucion.md",                             │
│           tipo="PROPUESTA_RESOLUCION",                                  │
│           texto_markdown=<documento_generado>                           │
│         )                                                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Herramientas MCP Requeridas

### MCP Documentación

| Tool | Uso | Permisos |
|------|-----|----------|
| `listar_documentacion` | Ver documentos disponibles para el tipo de expediente | `documentacion:leer` |
| `obtener_doc_documentacion` | Obtener contenido de la plantilla | `documentacion:leer` |

### MCP Expedientes

| Tool | Uso | Permisos |
|------|-----|----------|
| `consultar_expediente` | Obtener datos completos del expediente | `consulta` |
| `listar_documentos` | Listar documentos para encontrar el informe de situación | `consulta` |
| `obtener_texto_documento` | Leer contenido del informe de situación | `consulta` |
| `crear_documento_desde_markdown` | Guardar la propuesta de resolución generada | `gestion` |
| `añadir_anotacion` | Registrar acción en historial | `gestion` |

---

## Plantilla de Propuesta de Resolución

La plantilla usa formato **Mustache** con placeholders `{{campo}}`:

### Campos de la Plantilla (Subvenciones)

#### Datos del Expediente
| Campo | Origen | Descripción |
|-------|--------|-------------|
| `{{numero_expediente}}` | expediente.id | Número del expediente |
| `{{nombre_convocatoria}}` | expediente.datos | Nombre de la convocatoria |
| `{{fecha_propuesta}}` | Generado | Fecha actual de la propuesta |
| `{{fecha_solicitud}}` | expediente.fecha_inicio | Fecha de la solicitud |
| `{{nombre_solicitante}}` | expediente.datos.solicitante | Nombre del solicitante |
| `{{tipo_documento}}` | expediente.datos | DNI/NIF/CIF |
| `{{numero_documento}}` | expediente.datos | Número del documento |
| `{{nombre_proyecto}}` | expediente.datos | Título del proyecto |

#### Datos de Evaluación (del Informe de Situación)
| Campo | Origen | Descripción |
|-------|--------|-------------|
| `{{puntos_calidad}}` | informe | Puntuación calidad técnica (0-40) |
| `{{puntos_viabilidad}}` | informe | Puntuación viabilidad (0-25) |
| `{{puntos_impacto}}` | informe | Puntuación impacto social (0-20) |
| `{{puntos_experiencia}}` | informe | Puntuación experiencia (0-15) |
| `{{puntuacion_total}}` | Calculado | Suma de puntuaciones |

#### Datos de la Propuesta (Generados por el Agente)
| Campo | Origen | Descripción |
|-------|--------|-------------|
| `{{fundamentacion}}` | Generado | Artículos y normas aplicables |
| `{{antecedentes_adicionales}}` | informe | Hechos relevantes |
| `{{importe_concedido}}` | informe/datos | Importe si aprobación |
| `{{motivos_denegacion}}` | Generado | Motivos si denegación |
| `{{localidad}}` | Config | Municipio de emisión |
| `{{nombre_tecnico}}` | JWT.sub | Nombre del técnico |

---

## Configuración del Agente

### agents.yaml

```yaml
# ==========================================================================
# RedactorPropuestaResolucion - Genera Propuestas de Resolución (Paso 9)
# ==========================================================================

RedactorPropuestaResolucion:
  type: crewai
  enabled: true
  description: "Genera una Propuesta de Resolución basada en plantilla y datos del expediente"

  # Configuración del LLM
  llm:
    provider: anthropic
    model: claude-3-haiku-20240307
    max_tokens: 8192
    temperature: 0.1  # Baja para mayor consistencia en documentos formales
    num_retries: 5
    request_timeout: 180

  # Definición del agente CrewAI
  crewai_agent:
    role: "Redactor de Propuestas de Resolución Administrativa"
    goal: |
      Generar una Propuesta de Resolución formal y completa para el expediente {expediente_id},
      utilizando la plantilla oficial y los datos extraídos del expediente y su informe de situación.
      {additional_goal}
    backstory: |
      Eres un experto jurídico-administrativo de la administración pública española,
      especializado en la redacción de propuestas de resolución para expedientes de subvenciones.

      Tu experiencia incluye:
      - Conocimiento profundo de la Ley 38/2003 General de Subvenciones
      - Redacción de documentos administrativos siguiendo plantillas oficiales
      - Análisis de expedientes y valoración de solicitudes
      - Fundamentación jurídica de resoluciones

      Siempre sigues estrictamente la plantilla proporcionada, sustituyendo los campos
      marcados con {{campo}} por los valores correspondientes del expediente.

      Generas documentos formales, precisos y jurídicamente correctos.
    verbose: true
    allow_delegation: false
    max_rpm: 10

  # Tarea a ejecutar
  crewai_task:
    description: |
      Genera una Propuesta de Resolución para el expediente {expediente_id}.

      PASOS OBLIGATORIOS:

      1. OBTENER PLANTILLA
         - Usa 'obtener_doc_documentacion' con:
           * tipo_expediente = el tipo del expediente (subvenciones, licencias_obras, etc.)
           * tipo_documento = "plantilla_propuesta_resolucion"
         - Guarda la plantilla para usarla como base del documento
         - Lee las instrucciones del agente incluidas en el documento

      2. CONSULTAR EXPEDIENTE
         - Usa 'consultar_expediente' con expediente_id="{expediente_id}"
         - Extrae:
           * Datos del solicitante (nombre, NIF/CIF)
           * Datos del proyecto/solicitud
           * Estado actual y fechas
           * Tipo de expediente para determinar plantilla

      3. BUSCAR INFORME DE SITUACIÓN
         - Usa 'listar_documentos' con expediente_id="{expediente_id}"
         - Busca un documento de tipo "INFORME" con nombre similar a "informe_situacion"
         - Si existe, guarda su documento_id

      4. LEER INFORME DE SITUACIÓN
         - Si encontraste el informe, usa 'obtener_texto_documento' con:
           * expediente_id="{expediente_id}"
           * documento_id=<id del informe encontrado>
         - Extrae del informe:
           * Análisis y valoración de la solicitud
           * Puntuaciones si aplica
           * Observaciones relevantes
           * Recomendación (aprobar/denegar)

      5. DETERMINAR TIPO DE RESOLUCIÓN
         - Basándote en los datos y el informe, determina:
           * Si la propuesta es de APROBACIÓN o DENEGACIÓN
           * El importe a conceder (si aprobación)
           * Los motivos de denegación (si denegación)

      6. GENERAR PROPUESTA DE RESOLUCIÓN
         - Usa la plantilla obtenida en el paso 1
         - Sustituye TODOS los campos {{campo}} por los valores correspondientes:
           * Campos del expediente (paso 2)
           * Campos del informe (paso 4)
           * Campos generados (fecha actual, fundamentación)
         - IMPORTANTE: No dejes ningún {{campo}} sin sustituir
         - IMPORTANTE: La fundamentación jurídica debe ser coherente con el tipo de resolución

      7. GUARDAR DOCUMENTO
         - Usa 'crear_documento_desde_markdown' con:
           * expediente_id="{expediente_id}"
           * nombre="propuesta_resolucion.md"
           * tipo="PROPUESTA_RESOLUCION"
           * texto_markdown=<el documento generado>
           * metadatos={
               "tipo_resolucion": "aprobacion|denegacion",
               "importe": <si aplica>,
               "fecha_generacion": <fecha actual>,
               "generado_por": "RedactorPropuestaResolucion"
             }

      8. REGISTRAR ACCIÓN
         - Usa 'añadir_anotacion' para dejar constancia:
           * expediente_id="{expediente_id}"
           * texto="Generada propuesta de resolución de [aprobación/denegación] automática"

      IMPORTANTE: Responde siempre en Español.
      IMPORTANTE: El documento debe ser formalmente correcto y completo.
      IMPORTANTE: Debes completar TODOS los pasos antes de finalizar.

    expected_output: |
      Respuesta en formato JSON válido con estos campos:
      {
        "completado": true,
        "documento_id": "ID del documento creado",
        "tipo_resolucion": "aprobacion|denegacion",
        "importe_concedido": 5000.00,
        "resumen": "Breve resumen de la propuesta generada",
        "campos_rellenados": 15,
        "observaciones": "Notas adicionales si las hay"
      }

  # Herramientas MCP que puede usar el agente
  tools:
    # MCP Documentación
    - listar_documentacion
    - obtener_doc_documentacion
    # MCP Expedientes
    - consultar_expediente
    - listar_documentos
    - obtener_texto_documento
    - crear_documento_desde_markdown
    - añadir_anotacion

  required_permissions:
    - consulta
    - gestion
    - documentacion:leer

  timeout_seconds: 600
```

---

## Ejemplo de Ejecución

### Input

```json
{
  "agent": "RedactorPropuestaResolucion",
  "context": {
    "expediente_id": "EXP-2024-001",
    "tarea_id": "TAREA-PROPUESTA-001"
  },
  "additional_goal": "La propuesta debe enfatizar el impacto social del proyecto"
}
```

### Output Esperado

```json
{
  "completado": true,
  "documento_id": "DOC-123456",
  "tipo_resolucion": "aprobacion",
  "importe_concedido": 5000.00,
  "resumen": "Propuesta de resolución favorable para subvención de 5.000€ a la Asociación Cultural Sol Naciente para el proyecto Festival de Primavera 2024. Puntuación total: 78/100.",
  "campos_rellenados": 18,
  "observaciones": null
}
```

### Documento Generado (Ejemplo)

```markdown
# PROPUESTA DE RESOLUCIÓN

**Expediente:** EXP-2024-001

**Convocatoria:** Subvenciones Culturales 2024

**Fecha:** 8 de enero de 2026

---

### ANTECEDENTES

**PRIMERO.-** Con fecha 15 de enero de 2024, Asociación Cultural Sol Naciente, con NIF número G14123456, presentó solicitud de subvención para el proyecto denominado "Festival de Primavera 2024"...

[... documento completo con todos los campos rellenados ...]
```

---

## Validaciones y Manejo de Errores

### Prerrequisitos

| Verificación | Acción si falla |
|--------------|-----------------|
| Expediente existe | Error: "Expediente no encontrado" |
| Tipo expediente soporta plantilla | Error: "No existe plantilla para tipo X" |
| Informe de situación existe | Warning: Generar sin datos de informe |
| Todos los campos obligatorios tienen valor | Error: "Campos faltantes: X, Y, Z" |

### Errores Esperados

```python
# Si no existe informe de situación previo
{
  "completado": false,
  "error": "prerequisite_missing",
  "mensaje": "No se encontró informe de situación previo. Ejecute primero RedactorSituacion.",
  "documento_id": null
}

# Si faltan datos obligatorios
{
  "completado": false,
  "error": "missing_data",
  "mensaje": "Faltan datos obligatorios: nombre_solicitante, importe_solicitado",
  "documento_id": null
}
```

---

## Dependencias con Otros Agentes

### Flujo Recomendado

```
1. ClasificadorExpediente    (clasificar tipo/urgencia)
         ↓
2. RedactorSituacion         (generar informe de situación)
         ↓
3. RedactorPropuestaResolucion   (generar propuesta basada en informe)
```

### Prerequisito: RedactorSituacion

El agente `RedactorPropuestaResolucion` asume que existe un documento `informe_situacion.md` previo generado por `RedactorSituacion`. Este informe contiene:

- Análisis de la documentación
- Valoración de la solicitud
- Puntuaciones (si aplica)
- Recomendación de resolución

Si el informe no existe, el agente puede:
1. **Modo estricto**: Fallar con error `prerequisite_missing`
2. **Modo flexible**: Generar propuesta solo con datos del expediente (con advertencia)

---

## JWT Requerido

```json
{
  "iss": "agentix-bpmn",
  "sub": "Automático",
  "aud": ["agentix-mcp-expedientes", "agentix-mcp-documentacion"],
  "exp_id": "EXP-2024-001",
  "permisos": ["consulta", "gestion", "documentacion:leer"],
  "tarea_id": "TAREA-PROPUESTA-001"
}
```

---

## Plan de Implementación

### Fase 1: Configuración del Agente
- [ ] Añadir configuración a `agents.yaml`
- [ ] Verificar que las tools de MCP documentación están disponibles
- [ ] Probar acceso a plantillas via MCP documentación

### Fase 2: Integración MCP Multi-Server
- [ ] Verificar routing de tools a MCPs correctos
- [ ] Probar flujo completo: documentación → expedientes → documentación
- [ ] Validar permisos JWT para ambos MCPs

### Fase 3: Generación de Documento
- [ ] Implementar sustitución de campos {{campo}}
- [ ] Validar que no queden campos sin sustituir
- [ ] Probar con diferentes tipos de expediente

### Fase 4: Pruebas End-to-End
- [ ] Test con expediente completo (informe previo)
- [ ] Test con expediente sin informe (modo flexible)
- [ ] Test de error (expediente inexistente)
- [ ] Test de permisos insuficientes

---

## Notas de Diseño

### Por qué leer la plantilla via MCP

1. **Consistencia**: La misma plantilla para humanos y agentes
2. **Mantenibilidad**: Cambios en plantilla se reflejan automáticamente
3. **Auditoría**: Registro de qué versión de plantilla se usó
4. **Flexibilidad**: Diferentes plantillas por tipo de expediente

### Por qué depender del Informe de Situación

1. **Calidad**: El informe ya analizó los documentos
2. **Eficiencia**: No repetir análisis ya realizado
3. **Consistencia**: Propuesta coherente con análisis previo
4. **Trazabilidad**: Cadena de documentos relacionados

### Decisiones de IA vs Humanas

| Aspecto | Decisión | Motivo |
|---------|----------|--------|
| Tipo de resolución (aprobar/denegar) | **Humano** | Decisión final legal |
| Importe exacto | **Humano** | Decisión presupuestaria |
| Redacción del documento | **IA** | Tarea mecánica basada en plantilla |
| Fundamentación jurídica | **IA** | Basada en normativa predefinida |
| Revisión final | **Humano** | Control de calidad obligatorio |

El agente genera una **PROPUESTA** que debe ser revisada y aprobada por un humano antes de convertirse en RESOLUCIÓN definitiva.
