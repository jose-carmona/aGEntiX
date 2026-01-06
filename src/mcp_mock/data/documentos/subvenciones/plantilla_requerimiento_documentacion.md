# Plantilla: Requerimiento de Subsanación de Documentación

---

## REQUERIMIENTO DE SUBSANACIÓN

**Expediente:** {{numero_expediente}}

**Convocatoria:** {{nombre_convocatoria}}

**Fecha:** {{fecha_requerimiento}}

---

### DESTINATARIO

**Nombre:** {{nombre_solicitante}}

**{{tipo_documento}}:** {{numero_documento}}

**Dirección:** {{direccion_notificacion}}

---

### ASUNTO: Requerimiento de subsanación de documentación - Expediente {{numero_expediente}}

Examinada la solicitud presentada con fecha {{fecha_solicitud}} para participar en la convocatoria {{nombre_convocatoria}}, se ha observado que la documentación aportada presenta las siguientes deficiencias:

---

### DOCUMENTACIÓN FALTANTE

{{#each documentos_faltantes}}
- [ ] **{{nombre_documento}}**: {{motivo}}
{{/each}}

---

### DOCUMENTACIÓN DEFECTUOSA

{{#each documentos_defectuosos}}
- [ ] **{{nombre_documento}}**: {{defecto}}
{{/each}}

---

### PLAZO DE SUBSANACIÓN

De conformidad con el artículo 68 de la Ley 39/2015, de 1 de octubre, del Procedimiento Administrativo Común de las Administraciones Públicas, se le requiere para que en el plazo de **DIEZ (10) DÍAS HÁBILES**, a contar desde el día siguiente a la recepción de esta notificación, subsane las deficiencias señaladas y/o aporte la documentación requerida.

---

### ADVERTENCIA

Transcurrido dicho plazo sin que se hubiera subsanado la falta o aportado los documentos preceptivos, se le tendrá por **DESISTIDO** de su solicitud, previa resolución que deberá ser dictada en los términos previstos en el artículo 21 de la citada Ley.

---

### FORMA DE PRESENTACIÓN

La documentación podrá presentarse:

1. **Electrónicamente:** A través de la sede electrónica {{url_sede_electronica}}
2. **Presencialmente:** En el registro general del Ayuntamiento o en cualquiera de los lugares previstos en el artículo 16.4 de la Ley 39/2015.

**Importante:** En toda la documentación que presente debe hacer constar el número de expediente: **{{numero_expediente}}**

---

### INFORMACIÓN ADICIONAL

{{informacion_adicional}}

---

Lo que se comunica a los efectos oportunos.

En {{localidad}}, a {{fecha_requerimiento}}

El/La Técnico/a Instructor/a



Fdo.: {{nombre_tecnico}}

---

### NOTIFICACIÓN

| Campo | Valor |
|-------|-------|
| Fecha de notificación | |
| Medio de notificación | [ ] Electrónica [ ] Postal [ ] Comparecencia |
| Fecha fin plazo subsanación | |

---

## CAMPOS A RELLENAR:

- `{{numero_expediente}}`: Número del expediente (ej: SUB-2024-0001)
- `{{nombre_convocatoria}}`: Nombre completo de la convocatoria
- `{{fecha_requerimiento}}`: Fecha de emisión del requerimiento
- `{{nombre_solicitante}}`: Nombre completo del solicitante
- `{{tipo_documento}}`: DNI, NIF o CIF
- `{{numero_documento}}`: Número del documento de identidad
- `{{direccion_notificacion}}`: Dirección completa para notificaciones
- `{{fecha_solicitud}}`: Fecha de presentación de la solicitud
- `{{documentos_faltantes}}`: Lista de documentos no aportados
  - `{{nombre_documento}}`: Nombre del documento
  - `{{motivo}}`: Por qué es necesario (ej: "Obligatorio según base 5.1")
- `{{documentos_defectuosos}}`: Lista de documentos con defectos
  - `{{nombre_documento}}`: Nombre del documento
  - `{{defecto}}`: Descripción del defecto (ej: "Firma ilegible", "Caducado")
- `{{url_sede_electronica}}`: URL de la sede electrónica municipal
- `{{informacion_adicional}}`: Cualquier otra información relevante
- `{{localidad}}`: Municipio donde se emite
- `{{nombre_tecnico}}`: Nombre del técnico instructor