# Plantilla: Requerimiento de Subsanación - Licencia de Obras

---

## REQUERIMIENTO DE SUBSANACIÓN

**Expediente:** {{numero_expediente}}

**Tipo de obra:** {{tipo_obra}}

**Fecha:** {{fecha_requerimiento}}

---

### DESTINATARIO

**Nombre:** {{nombre_solicitante}}

**{{tipo_documento}}:** {{numero_documento}}

**Dirección:** {{direccion_notificacion}}

---

### ASUNTO: Requerimiento de subsanación - Expediente {{numero_expediente}}

Examinada la solicitud de licencia de obras presentada con fecha {{fecha_solicitud}} para {{descripcion_obra}} en {{direccion_obra}}, se ha observado que la documentación aportada presenta las siguientes deficiencias que deben ser subsanadas:

---

### A) DOCUMENTACIÓN ADMINISTRATIVA FALTANTE O DEFECTUOSA

{{#each documentos_admin_faltantes}}
- [ ] **{{nombre_documento}}**
  - Motivo: {{motivo}}
{{/each}}

---

### B) DOCUMENTACIÓN TÉCNICA FALTANTE

{{#each documentos_tecnicos_faltantes}}
- [ ] **{{nombre_documento}}**
  - Requerido según: {{normativa_referencia}}
{{/each}}

---

### C) DEFICIENCIAS DEL PROYECTO TÉCNICO

{{#if deficiencias_proyecto}}
El proyecto técnico presentado contiene las siguientes deficiencias que deben ser corregidas:

{{#each deficiencias_proyecto}}
**{{numero}}. {{titulo}}**
- Deficiencia: {{descripcion}}
- Documentación afectada: {{documento}}
- Normativa incumplida: {{normativa}}
- Corrección requerida: {{correccion}}

{{/each}}
{{/if}}

---

### D) INCUMPLIMIENTOS NORMATIVOS DETECTADOS

{{#if incumplimientos_normativos}}
| Parámetro | Normativa | Proyecto | Incumplimiento |
|-----------|-----------|----------|----------------|
{{#each incumplimientos_normativos}}
| {{parametro}} | {{valor_normativa}} | {{valor_proyecto}} | {{descripcion}} |
{{/each}}

**Nota:** Los incumplimientos normativos indicados requieren la presentación de proyecto modificado que se ajuste a la normativa urbanística vigente.
{{/if}}

---

### PLAZO DE SUBSANACIÓN

De conformidad con el artículo 68 de la Ley 39/2015, de 1 de octubre, del Procedimiento Administrativo Común de las Administraciones Públicas, se le requiere para que en el plazo de **DIEZ (10) DÍAS HÁBILES**, a contar desde el día siguiente a la recepción de esta notificación:

1. Aporte la documentación faltante indicada en los apartados A) y B).
2. Presente proyecto técnico corregido que subsane las deficiencias indicadas en el apartado C).
3. En su caso, presente proyecto modificado que cumpla la normativa urbanística.

---

### ADVERTENCIA

Transcurrido dicho plazo sin que se hubiera subsanado la falta o aportado los documentos preceptivos, se le tendrá por **DESISTIDO** de su solicitud, previa resolución que deberá ser dictada en los términos previstos en el artículo 21 de la citada Ley.

---

### FORMA DE PRESENTACIÓN

La documentación y/o proyecto corregido podrá presentarse:

1. **Electrónicamente:** A través de la sede electrónica {{url_sede_electronica}}
2. **Presencialmente:** En el registro general del Ayuntamiento.

**Importante:** 
- En toda la documentación debe constar el número de expediente: **{{numero_expediente}}**
- Los proyectos técnicos deben estar visados por el colegio profesional correspondiente.
- Las correcciones al proyecto deben venir firmadas por el técnico competente.

---

### INFORMACIÓN ADICIONAL

{{informacion_adicional}}

Para consultas técnicas puede contactar con el Servicio de Urbanismo:
- Teléfono: {{telefono_urbanismo}}
- Email: {{email_urbanismo}}
- Horario de atención: {{horario_atencion}}

---

Lo que se comunica a los efectos oportunos.

En {{municipio}}, a {{fecha_requerimiento}}

El/La Técnico/a Instructor/a



Fdo.: {{nombre_tecnico}}

---

## CAMPOS A RELLENAR:

### Datos básicos
- `{{numero_expediente}}`: Número del expediente
- `{{tipo_obra}}`: Mayor o Menor
- `{{fecha_requerimiento}}`: Fecha del requerimiento
- `{{nombre_solicitante}}`: Nombre del solicitante
- `{{direccion_obra}}`: Emplazamiento de la obra
- `{{descripcion_obra}}`: Descripción breve

### Documentación faltante
- `{{documentos_admin_faltantes}}`: Lista de documentos administrativos
- `{{documentos_tecnicos_faltantes}}`: Lista de documentos técnicos

### Deficiencias del proyecto
- `{{deficiencias_proyecto}}`: Lista detallada con:
  - numero, titulo, descripcion, documento, normativa, correccion

### Incumplimientos normativos
- `{{incumplimientos_normativos}}`: Tabla con parámetros incumplidos

### Contacto
- `{{telefono_urbanismo}}`: Teléfono del servicio
- `{{email_urbanismo}}`: Email de contacto
- `{{horario_atencion}}`: Horario de atención al público