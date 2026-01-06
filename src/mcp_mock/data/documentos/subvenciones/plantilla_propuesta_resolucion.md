# Plantilla: Propuesta de Resolución de Subvención

---

## PROPUESTA DE RESOLUCIÓN

**Expediente:** {{numero_expediente}}

**Convocatoria:** {{nombre_convocatoria}}

**Fecha:** {{fecha_propuesta}}

---

### ANTECEDENTES

**PRIMERO.-** Con fecha {{fecha_solicitud}}, {{nombre_solicitante}}, con {{tipo_documento}} número {{numero_documento}}, presentó solicitud de subvención para el proyecto denominado "{{nombre_proyecto}}" al amparo de la convocatoria {{nombre_convocatoria}}, publicada en {{medio_publicacion}} de fecha {{fecha_publicacion}}.

**SEGUNDO.-** {{antecedentes_adicionales}}

**TERCERO.-** Examinada la documentación aportada y evaluado el proyecto conforme a los criterios establecidos en las bases reguladoras, se ha obtenido la siguiente puntuación:

| Criterio | Puntuación máxima | Puntuación obtenida |
|----------|-------------------|---------------------|
| Calidad técnica del proyecto | 40 | {{puntos_calidad}} |
| Viabilidad económica | 25 | {{puntos_viabilidad}} |
| Impacto social | 20 | {{puntos_impacto}} |
| Experiencia del solicitante | 15 | {{puntos_experiencia}} |
| **TOTAL** | **100** | **{{puntuacion_total}}** |

---

### FUNDAMENTOS DE DERECHO

**PRIMERO.-** La Ley 38/2003, de 17 de noviembre, General de Subvenciones, regula el régimen jurídico general de las subvenciones otorgadas por las Administraciones Públicas.

**SEGUNDO.-** {{fundamentacion}}

**TERCERO.-** Las bases reguladoras de la convocatoria establecen los requisitos, criterios de valoración y procedimiento aplicables.

---

### PROPUESTA

En virtud de lo expuesto, el/la técnico/a instructor/a que suscribe PROPONE:

{{#if aprobacion}}
**PRIMERO.-** CONCEDER a {{nombre_solicitante}} una subvención por importe de {{importe_concedido}} euros para la realización del proyecto "{{nombre_proyecto}}".

**SEGUNDO.-** El plazo de ejecución del proyecto será desde {{fecha_inicio_proyecto}} hasta {{fecha_fin_proyecto}}.

**TERCERO.-** El plazo para la presentación de la justificación será de 3 meses desde la finalización del proyecto.

**CUARTO.-** El beneficiario deberá cumplir las obligaciones establecidas en el artículo 14 de la Ley General de Subvenciones.
{{/if}}

{{#if denegacion}}
**ÚNICO.-** DENEGAR la subvención solicitada por {{nombre_solicitante}} para el proyecto "{{nombre_proyecto}}" por los siguientes motivos:

{{motivos_denegacion}}
{{/if}}

---

**Contra esta propuesta provisional podrá formular alegaciones en el plazo de 10 días hábiles a contar desde el día siguiente a su notificación.**

---

En {{localidad}}, a {{fecha_propuesta}}

El/La Técnico/a Instructor/a



Fdo.: {{nombre_tecnico}}

---

## CAMPOS A RELLENAR:

- `{{numero_expediente}}`: Número del expediente (ej: SUB-2024-0001)
- `{{nombre_convocatoria}}`: Nombre completo de la convocatoria
- `{{fecha_propuesta}}`: Fecha de la propuesta (DD de MES de AAAA)
- `{{fecha_solicitud}}`: Fecha de presentación de la solicitud
- `{{nombre_solicitante}}`: Nombre completo del solicitante
- `{{tipo_documento}}`: DNI, NIF o CIF
- `{{numero_documento}}`: Número del documento de identidad
- `{{nombre_proyecto}}`: Título del proyecto
- `{{medio_publicacion}}`: BOP, BOJA, tablón de anuncios, etc.
- `{{fecha_publicacion}}`: Fecha de publicación de la convocatoria
- `{{antecedentes_adicionales}}`: Otros hechos relevantes (requerimientos, subsanaciones...)
- `{{puntos_calidad}}`: Puntuación criterio calidad técnica (0-40)
- `{{puntos_viabilidad}}`: Puntuación criterio viabilidad (0-25)
- `{{puntos_impacto}}`: Puntuación criterio impacto social (0-20)
- `{{puntos_experiencia}}`: Puntuación criterio experiencia (0-15)
- `{{puntuacion_total}}`: Suma total de puntuación
- `{{fundamentacion}}`: Artículos y normas que fundamentan la decisión
- `{{importe_concedido}}`: Importe de la subvención (solo si aprobación)
- `{{fecha_inicio_proyecto}}`: Fecha inicio ejecución proyecto
- `{{fecha_fin_proyecto}}`: Fecha fin ejecución proyecto
- `{{motivos_denegacion}}`: Lista numerada de motivos (solo si denegación)
- `{{localidad}}`: Municipio donde se emite
- `{{nombre_tecnico}}`: Nombre del técnico instructor