# Plantilla: Propuesta de Resolución de Licencia de Obras

---

## PROPUESTA DE RESOLUCIÓN

**Expediente:** {{numero_expediente}}

**Tipo de obra:** {{tipo_obra}} (Mayor / Menor)

**Fecha:** {{fecha_propuesta}}

---

### DATOS DEL SOLICITANTE

| Campo | Valor |
|-------|-------|
| Nombre/Razón social | {{nombre_solicitante}} |
| {{tipo_documento}} | {{numero_documento}} |
| Domicilio a efectos de notificación | {{direccion_notificacion}} |

---

### DATOS DE LA OBRA

| Campo | Valor |
|-------|-------|
| Emplazamiento | {{direccion_obra}} |
| Referencia catastral | {{referencia_catastral}} |
| Descripción | {{descripcion_obra}} |
| Superficie parcela | {{superficie_parcela}} m² |
| Superficie construida | {{superficie_construida}} m² |
| Presupuesto Ejecución Material | {{pem}} € |

---

### ANTECEDENTES

**PRIMERO.-** Con fecha {{fecha_solicitud}}, {{nombre_solicitante}} presentó solicitud de licencia de obras para {{descripcion_obra}} en el emplazamiento indicado.

**SEGUNDO.-** {{antecedentes_adicionales}}

**TERCERO.-** El técnico municipal ha emitido informe urbanístico de fecha {{fecha_informe_tecnico}} con el siguiente resultado:

{{informe_tecnico}}

---

### PARÁMETROS URBANÍSTICOS

| Parámetro | Normativa PGOU | Proyecto | Cumple |
|-----------|---------------|----------|--------|
| Clasificación suelo | {{clasificacion_suelo}} | - | {{cumple_clasificacion}} |
| Uso | {{uso_permitido}} | {{uso_proyecto}} | {{cumple_uso}} |
| Edificabilidad | {{edificabilidad_max}} m²t/m²s | {{edificabilidad_proyecto}} m²t/m²s | {{cumple_edificabilidad}} |
| Ocupación | {{ocupacion_max}} % | {{ocupacion_proyecto}} % | {{cumple_ocupacion}} |
| Altura máxima | {{altura_max}} | {{altura_proyecto}} | {{cumple_altura}} |
| Retranqueo frontal | {{retranqueo_frontal_min}} m | {{retranqueo_frontal_proyecto}} m | {{cumple_retranqueo_f}} |
| Retranqueo lateral | {{retranqueo_lateral_min}} m | {{retranqueo_lateral_proyecto}} m | {{cumple_retranqueo_l}} |

---

### FUNDAMENTOS DE DERECHO

**PRIMERO.-** La Ley 7/2021, de 1 de diciembre, de Impulso para la Sostenibilidad del Territorio de Andalucía (LISTA), regula el régimen de licencias urbanísticas.

**SEGUNDO.-** El Plan General de Ordenación Urbana de {{municipio}}, aprobado definitivamente en fecha {{fecha_pgou}}, establece los parámetros urbanísticos aplicables.

**TERCERO.-** {{fundamentacion_adicional}}

---

### PROPUESTA

En virtud de lo expuesto, el/la técnico/a instructor/a que suscribe PROPONE:

{{#if concesion}}
**PRIMERO.-** CONCEDER licencia de obras a {{nombre_solicitante}} para {{descripcion_obra}} en {{direccion_obra}}, con sujeción al proyecto técnico presentado y a las siguientes condiciones:

**Condiciones generales:**
1. Plazo de inicio de las obras: 6 meses desde la notificación.
2. Plazo de finalización: {{plazo_finalizacion}} desde el inicio.
3. Comunicar el inicio de las obras con 15 días de antelación.
4. Nombrar dirección facultativa antes del inicio.
5. Colocar cartel de obra visible desde la vía pública.
6. Disponer de copia de la licencia en la obra.
7. Solicitar licencia de primera ocupación al finalizar.

**Condiciones particulares:**
{{condiciones_particulares}}

**SEGUNDO.-** La presente licencia no exime de la obtención de otras autorizaciones que pudieran ser necesarias (actividad, patrimonio, etc.).

**TERCERO.-** Las tasas e impuestos correspondientes son:
- Tasa licencia urbanística: {{tasa_licencia}} €
- Impuesto sobre Construcciones (ICIO): {{icio}} €
- TOTAL: {{total_tasas}} €
{{/if}}

{{#if denegacion}}
**ÚNICO.-** DENEGAR la licencia de obras solicitada por {{nombre_solicitante}} para {{descripcion_obra}} en {{direccion_obra}} por los siguientes motivos:

{{motivos_denegacion}}

La presente denegación se fundamenta en el incumplimiento de los siguientes preceptos:
{{preceptos_incumplidos}}
{{/if}}

---

### RECURSOS

Contra la presente resolución, que pone fin a la vía administrativa, podrá interponer:

- **Recurso potestativo de reposición** ante el mismo órgano, en el plazo de UN MES.
- **Recurso contencioso-administrativo** ante el Juzgado de lo Contencioso-Administrativo, en el plazo de DOS MESES.

Ambos plazos se computarán desde el día siguiente a la notificación.

---

En {{municipio}}, a {{fecha_propuesta}}

El/La Técnico/a Instructor/a



Fdo.: {{nombre_tecnico}}

---

## CAMPOS A RELLENAR:

### Datos básicos
- `{{numero_expediente}}`: Número del expediente (ej: LOB-2024-0001)
- `{{tipo_obra}}`: Mayor o Menor
- `{{fecha_propuesta}}`: Fecha de la propuesta
- `{{nombre_solicitante}}`: Nombre completo del solicitante
- `{{tipo_documento}}`: DNI, NIF o CIF
- `{{numero_documento}}`: Número del documento
- `{{direccion_notificacion}}`: Dirección para notificaciones

### Datos de la obra
- `{{direccion_obra}}`: Dirección completa del emplazamiento
- `{{referencia_catastral}}`: Referencia catastral de la parcela
- `{{descripcion_obra}}`: Descripción breve de la actuación
- `{{superficie_parcela}}`: Superficie de la parcela en m²
- `{{superficie_construida}}`: Superficie a construir en m²
- `{{pem}}`: Presupuesto de Ejecución Material

### Parámetros urbanísticos
- Valores de normativa PGOU y proyecto para cada parámetro
- `{{cumple_*}}`: SÍ o NO

### Resolución
- `{{plazo_finalizacion}}`: Plazo para terminar la obra
- `{{condiciones_particulares}}`: Condiciones específicas
- `{{tasa_licencia}}`: Importe tasa
- `{{icio}}`: Importe ICIO (4% del PEM)
- `{{motivos_denegacion}}`: Lista de motivos si denegación
- `{{preceptos_incumplidos}}`: Artículos específicos