# Problemas en el Contexto de Agentes

## Contexto

La propuesta actual establece que el agente tiene acceso a:
- **Toda la información del Expediente** sobre el que está trabajando
- Datos, documentos, historial, metadatos
- Limitado al expediente específico (no acceso a otros expedientes)

Ver: [[../032-contexto-agente|Contexto disponible para agentes]]

## Fortalezas Identificadas

- **Alcance limitado apropiado**: Restricción a un solo expediente es correcta para seguridad
- **Acceso completo dentro del scope**: El agente tiene toda la información necesaria

## Problemas Críticos Identificados

### 1. Tamaño de Contexto (Context Window)

**Problema**: Los expedientes pueden ser extremadamente grandes y exceder el context window de los LLMs.

**Realidad de expedientes administrativos**:
```
Expediente típico de licencia de obras mayor:
- Solicitud inicial: 5 páginas
- Documentación técnica: 50 páginas
- Planos: 20 páginas
- Informes técnicos: 30 páginas
- Alegaciones: 15 páginas
- Resoluciones previas: 10 páginas
Total: ~130 páginas = ~200,000 tokens

Context window de Claude Sonnet: 200,000 tokens
→ En el límite, y esto es solo un expediente de complejidad media
```

**Casos problemáticos**:
- Expedientes urbanísticos complejos: 500+ páginas
- Expedientes con histórico largo (años): 1000+ páginas
- Documentos escaneados (OCR): mucho texto por página

**Impacto**: Imposibilidad de procesar expedientes grandes, errores de truncamiento, pérdida de información crítica.

### 2. Información Sensible Sin Sanitización

**Problema**: Los expedientes contienen datos personales sensibles que el agente no siempre necesita.

**Datos sensibles en expedientes**:
- **Categoría especial (GDPR Art. 9)**: salud, orientación sexual, religión, origen étnico
- **Identificadores**: DNI, NIE, pasaporte, nº Seguridad Social
- **Financieros**: cuentas bancarias, ingresos, deudas
- **Menores**: datos de hijos, permisos parentales
- **Víctimas**: en expedientes de violencia de género, acoso

**Principio de minimización (GDPR)**:
> Los datos deben ser "adecuados, pertinentes y limitados a lo necesario"

**Ejemplo problemático**:
```
Tarea del agente: "Verificar que solicitud incluye todos los documentos requeridos"

Información necesaria:
- Lista de documentos adjuntos
- Tipos de documento requeridos

Información NO necesaria (pero actualmente accesible):
- Contenido completo de cada documento
- Datos personales del solicitante
- Información financiera detallada
```

**Impacto**: Violación del principio de minimización, riesgo de data leakage, incumplimiento GDPR.

### 3. Sin Chunking Estratégico

**Problema**: No hay estrategia para priorizar información relevante vs menos relevante.

**Aspectos no contemplados**:
- ¿Qué documentos son más relevantes para cada tipo de tarea?
- ¿Cómo se seleccionan documentos cuando no caben todos en el contexto?
- ¿Se usa semantic search para encontrar secciones relevantes?
- ¿Hay metadatos que ayuden a priorizar?

**Ejemplo de mejora posible**:
```
Tarea: "Extraer datos del solicitante"

Estrategia naive (actual):
→ Enviar todo el expediente (130 páginas)

Estrategia inteligente (propuesta):
1. Identificar documentos relevantes: "solicitud_inicial.pdf"
2. Extraer secciones relevantes: "Datos del solicitante" (página 1-2)
3. Enviar solo 2 páginas al agente
→ Reduce tokens 98%, mejora latencia, aumenta precisión
```

**Impacto**: Latencia innecesaria, costes elevados, confusión del agente con información irrelevante.

### 4. Metadatos Insuficientes

**Problema**: No se especifica si el agente recibe solo documentos o también metadatos estructurados.

**Metadatos útiles para agentes**:
```json
{
  "expediente": {
    "id": "EXP-2024-001234",
    "tipo": "licencia_obras_mayores",
    "estado": "en_tramitacion",
    "fecha_inicio": "2024-01-15",
    "tramitador_asignado": "juan.perez@ejemplo.es",
    "prioridad": "normal",
    "plazo_resolucion": "2024-04-15"
  },
  "documentos": [
    {
      "id": "doc_789",
      "nombre": "solicitud.pdf",
      "tipo": "solicitud_inicial",
      "fecha_subida": "2024-01-15T10:23:45Z",
      "paginas": 5,
      "hash": "abc123...",
      "extracto_texto": "El abajo firmante solicita...",
      "embeddings_calculados": true
    }
  ],
  "historial": [
    {
      "fecha": "2024-01-15",
      "accion": "registro_entrada",
      "autor": "sistema",
      "descripcion": "Expediente creado"
    }
  ]
}
```

**Beneficios de metadatos estructurados**:
- Agente puede razonar sobre estructura sin procesar todo
- Facilita selección de documentos relevantes
- Permite validaciones (ej: "¿hay documento tipo X?")

**Impacto**: Agentes menos efectivos, necesidad de procesar más información de la necesaria.

### 5. Versionado de Documentos

**Problema**: Los documentos pueden tener múltiples versiones. No se especifica cuál ve el agente.

**Escenarios complejos**:
```
Documento: "informe_tecnico.pdf"
Versiones:
- v1: subida 2024-01-15, estado: borrador
- v2: subida 2024-01-20, estado: borrador
- v3: subida 2024-01-25, estado: definitivo

Tarea del agente: "Extraer conclusiones del informe técnico"
¿Qué versión debe usar el agente?
- ¿La última? (puede ser borrador)
- ¿La marcada como definitiva?
- ¿Todas?
```

**Impacto**: Agente puede usar información desactualizada o no oficial, inconsistencias.

### 6. Información Multimodal

**Problema**: Los expedientes no son solo texto.

**Tipos de contenido en expedientes**:
- **PDF**: Pueden ser nativos (texto seleccionable) o escaneados (requieren OCR)
- **Imágenes**: Fotos de obras, planos, mapas, firmas
- **Formularios**: Datos estructurados en XML/JSON
- **Planos CAD**: DWG, DXF
- **Hojas de cálculo**: Excel con cálculos
- **Audio/Video**: En algunos procedimientos

**Preguntas sin respuesta**:
- ¿Qué formatos puede procesar el agente?
- ¿Hay conversión automática (ej: OCR para PDFs escaneados)?
- ¿Los agentes tienen capacidad multimodal (visión)?
- ¿Cómo se manejan formatos no soportados?

**Impacto**: Información crítica inaccesible para el agente (ej: plano con medidas).

## Recomendaciones

### Prioridad Crítica

1. **Implementar chunking inteligente**
   ```python
   from typing import List
   from semantic_search import find_relevant_chunks

   def prepare_context_for_agent(expediente, task_description, max_tokens=50000):
       """
       Selecciona información relevante del expediente para la tarea específica
       """
       # 1. Siempre incluir metadatos estructurados (bajo coste en tokens)
       context = {
           "metadata": expediente.get_metadata(),
           "documentos": []
       }

       # 2. Identificar documentos relevantes usando embeddings
       relevant_docs = find_relevant_chunks(
           query=task_description,
           documents=expediente.documentos,
           top_k=5
       )

       # 3. Extraer secciones relevantes de cada documento
       token_budget = max_tokens - count_tokens(context["metadata"])

       for doc in relevant_docs:
           if token_budget <= 0:
               break

           # Búsqueda semántica dentro del documento
           relevant_sections = find_relevant_sections(
               doc=doc,
               query=task_description,
               max_tokens=min(10000, token_budget)
           )

           context["documentos"].append({
               "id": doc.id,
               "nombre": doc.nombre,
               "tipo": doc.tipo,
               "secciones": relevant_sections,
               "nota": f"Secciones más relevantes (documento completo: {doc.paginas} páginas)"
           })

           token_budget -= count_tokens(relevant_sections)

       return context
   ```

2. **Aplicar minimización de datos (GDPR)**
   ```python
   def sanitize_context(context, task_permissions):
       """
       Elimina información sensible que el agente no necesita
       """
       # Definir qué datos necesita cada tipo de tarea
       if task_permissions.task_type == "verificar_documentacion":
           # Solo necesita lista de documentos, no contenido
           return {
               "metadata": context["metadata"],
               "documentos": [
                   {"id": d["id"], "tipo": d["tipo"], "nombre": d["nombre"]}
                   for d in context["documentos"]
               ]
           }

       elif task_permissions.task_type == "extraer_datos_solicitante":
           # Necesita datos personales, pero no financieros
           return redact_fields(
               context,
               redact=["datos_bancarios", "ingresos", "deudas"]
           )

       return context
   ```

3. **Proporcionar contexto estructurado**
   - Crear JSON schema del expediente
   - Incluir metadatos ricos antes de documentos completos
   - Permitir que agente "solicite" documentos adicionales si necesita

   **Ejemplo de contexto estructurado**:
   ```json
   {
     "expediente_metadata": {
       "id": "EXP-2024-001234",
       "tipo": "licencia_obras_mayores",
       "resumen_generado_por_ia": "Solicitud de licencia para construcción de vivienda unifamiliar de 150m2...",
       "tags": ["urbanismo", "nueva_construccion", "uso_residencial"],
       "estado_actual": "pendiente_informe_tecnico",
       "documentos_count": 12,
       "documentos_por_tipo": {
         "solicitud": 1,
         "proyecto_tecnico": 1,
         "planos": 8,
         "justificante_pago": 1,
         "certificado_catastral": 1
       }
     },
     "documentos_disponibles": [
       {
         "id": "doc_001",
         "tipo": "solicitud_inicial",
         "resumen": "Solicitud de D. Juan Pérez para construir vivienda...",
         "embeddings_available": true
       }
     ],
     "documentos_incluidos_en_contexto": [
       // Solo los más relevantes para esta tarea
     ],
     "nota": "Hay 9 documentos adicionales disponibles. Usa herramienta 'request_document' si necesitas alguno."
   }
   ```

### Prioridad Alta

4. **Implementar semantic search**
   ```python
   from sentence_transformers import SentenceTransformer
   import faiss

   # Precompute embeddings de todos los documentos
   model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

   def index_expediente(expediente):
       """Crea índice de embeddings para búsqueda semántica"""
       chunks = split_documents_into_chunks(expediente.documentos)

       embeddings = model.encode([c.text for c in chunks])

       index = faiss.IndexFlatL2(embeddings.shape[1])
       index.add(embeddings)

       return index, chunks

   def find_relevant_chunks(query, expediente_index, top_k=5):
       """Encuentra chunks más relevantes para la query"""
       index, chunks = expediente_index

       query_embedding = model.encode([query])
       distances, indices = index.search(query_embedding, top_k)

       return [chunks[i] for i in indices[0]]
   ```

5. **Gestionar versionado de documentos**
   ```yaml
   document_versioning_policy:
     # Por defecto, usar versión "oficial" más reciente
     default_version: "latest_official"

     # Para cada tipo de tarea, especificar política
     task_policies:
       extraccion_datos:
         version: "latest_official"
         fallback: "latest_any_status"

       verificacion_cumplimiento:
         version: "all_official"  # ver todas las versiones oficiales

       analisis_cambios:
         version: "all"  # incluyendo borradores
   ```

6. **Soportar formatos múltiples**
   ```yaml
   document_processing:
     pdf:
       native: "extract_text"
       scanned: "ocr_with_tesseract"

     images:
       processing: "multimodal_llm"  # usar visión del LLM
       fallback: "ocr"

     office:
       docx: "extract_text"
       xlsx: "parse_to_json"

     cad:
       dwg: "convert_to_pdf_then_ocr"  # o "skip_with_warning"

     unsupported:
       action: "log_warning_and_skip"
       notify: "agent_in_response"
   ```

### Prioridad Media

7. **Implementar "agente solicita más contexto"**
   - Agente recibe contexto inicial limitado
   - Si necesita más información, puede solicitar documentos específicos
   - Patrón de "function calling" para ampliar contexto

8. **Caché de embeddings**
   - Precalcular embeddings de todos los documentos al subirse
   - Almacenar en base de datos vectorial
   - Reduce latencia de búsqueda semántica

9. **Resúmenes automáticos**
   - Generar resumen de cada documento al subirse
   - Incluir resúmenes en contexto inicial
   - Agente puede solicitar documento completo si el resumen es insuficiente

## Ejemplo de Flujo Mejorado

```python
# Cuando se ejecuta una acción de agente
def execute_agent_action(agent, task, expediente):
    # 1. Preparar contexto optimizado
    context = prepare_context_for_agent(
        expediente=expediente,
        task_description=task.description,
        max_tokens=50000
    )

    # 2. Aplicar minimización de datos
    context = sanitize_context(
        context=context,
        task_permissions=task.permissions
    )

    # 3. Proporcionar herramienta para solicitar más contexto
    tools = [
        {
            "name": "request_document",
            "description": "Solicita el contenido completo de un documento específico",
            "parameters": {
                "document_id": "string",
                "reason": "string"
            }
        }
    ]

    # 4. Ejecutar agente con contexto optimizado
    result = agent.execute(
        context=context,
        tools=tools
    )

    return result
```

## Relaciones

- Ver: [[100-problematica-general|Problemática general]]
- Ver: [[../032-contexto-agente|Propuesta de contexto actual]]
- Ver: [[102-problema-permisos-seguridad|Minimización de datos]]
- Ver: [[108-aspectos-ausentes|Procesamiento multimodal]]
- Ver: [[105-problema-configuracion-agentes|Configuración de chunking]]
- Ver: [[109-prioridades-mejora|Prioridades]]
