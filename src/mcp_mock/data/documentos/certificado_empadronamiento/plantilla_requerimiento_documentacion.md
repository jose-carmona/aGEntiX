# Plantilla: Requerimiento de Documentación - Certificado de Empadronamiento

---

## REQUERIMIENTO DE SUBSANACIÓN

**Trámite:** {{numero_tramite}}

**Tipo de certificado solicitado:** {{tipo_certificado}}

**Fecha:** {{fecha_requerimiento}}

---

### DESTINATARIO

**Nombre:** {{nombre_solicitante}}

**{{tipo_documento}}:** {{numero_documento}}

**Dirección:** {{direccion_notificacion}}

**Email:** {{email_notificacion}}

---

### ASUNTO: Requerimiento de subsanación - Solicitud de certificado de empadronamiento

Examinada la solicitud de certificado de empadronamiento presentada con fecha {{fecha_solicitud}}, se ha observado que la documentación aportada presenta las siguientes deficiencias que impiden la expedición del certificado:

---

### DOCUMENTACIÓN FALTANTE O DEFECTUOSA

{{#each documentos_faltantes}}
- [ ] **{{nombre_documento}}**
  - Motivo: {{motivo}}
  - Requisito: {{requisito}}
{{/each}}

---

{{#if falta_autorizacion_convivientes}}
### AUTORIZACIONES PENDIENTES (CERTIFICADO COLECTIVO)

Para la expedición del certificado colectivo solicitado, se requiere la autorización expresa de todas las personas mayores de edad inscritas en el domicilio.

Faltan las autorizaciones de:

| Nombre | Relación |
|--------|----------|
{{#each convivientes_sin_autorizar}}
| {{nombre}} | {{relacion}} |
{{/each}}

Cada autorización debe incluir:
1. Nombre completo y firma del autorizante
2. Número de DNI/NIE
3. Declaración expresa autorizando la inclusión de sus datos en el certificado
4. Fecha de la autorización

---
{{/if}}

{{#if legitimacion_insuficiente}}
### DEFICIENCIA EN LA LEGITIMACIÓN

{{motivo_legitimacion}}

**Para subsanar esta deficiencia debe aportar:**
{{documentos_legitimacion}}

---
{{/if}}

### PLAZO DE SUBSANACIÓN

De conformidad con el artículo 68 de la Ley 39/2015, de 1 de octubre, del Procedimiento Administrativo Común de las Administraciones Públicas, se le requiere para que en el plazo de **DIEZ (10) DÍAS HÁBILES**, a contar desde el día siguiente a la recepción de esta notificación, aporte la documentación requerida.

---

### ADVERTENCIA

Transcurrido dicho plazo sin que se hubiera subsanado la falta o aportado los documentos preceptivos, se le tendrá por **DESISTIDO** de su solicitud, previa resolución que deberá ser dictada en los términos previstos en el artículo 21 de la citada Ley.

---

### FORMA DE PRESENTACIÓN

La documentación requerida podrá presentarse:

1. **Electrónicamente:** 
   - Sede electrónica: {{url_sede_electronica}}
   - Adjuntando documentos en formato PDF

2. **Presencialmente:**
   - Oficina de Atención al Ciudadano
   - Dirección: {{direccion_oficina}}
   - Horario: {{horario_oficina}}

**Importante:** En toda la documentación debe hacer constar el número de trámite: **{{numero_tramite}}**

---

### INFORMACIÓN ADICIONAL

**Teléfono de información:** {{telefono_informacion}}

**Email:** {{email_informacion}}

{{informacion_adicional}}

---

Lo que se comunica a los efectos oportunos.

En {{municipio}}, a {{fecha_requerimiento}}

El/La Funcionario/a



Fdo.: {{nombre_funcionario}}

---

## CAMPOS A RELLENAR:

### Datos del trámite
- `{{numero_tramite}}`: Número del trámite (ej: EMP-2024-00123)
- `{{tipo_certificado}}`: Individual, Colectivo o Histórico
- `{{fecha_requerimiento}}`: Fecha del requerimiento
- `{{fecha_solicitud}}`: Fecha de la solicitud original

### Datos del solicitante
- `{{nombre_solicitante}}`: Nombre completo
- `{{tipo_documento}}`: DNI, NIE o Pasaporte
- `{{numero_documento}}`: Número del documento
- `{{direccion_notificacion}}`: Dirección para notificaciones
- `{{email_notificacion}}`: Email del solicitante

### Documentación faltante
- `{{documentos_faltantes}}`: Array de documentos con:
  - `nombre_documento`: Nombre del documento
  - `motivo`: Por qué falta o está defectuoso
  - `requisito`: Normativa que lo exige

### Certificado colectivo
- `{{falta_autorizacion_convivientes}}`: true/false
- `{{convivientes_sin_autorizar}}`: Array con nombre y relación

### Legitimación
- `{{legitimacion_insuficiente}}`: true/false
- `{{motivo_legitimacion}}`: Descripción del problema
- `{{documentos_legitimacion}}`: Qué debe aportar

### Contacto
- `{{url_sede_electronica}}`: URL de la sede
- `{{direccion_oficina}}`: Dirección de la oficina
- `{{horario_oficina}}`: Horario de atención
- `{{telefono_informacion}}`: Teléfono de contacto
- `{{email_informacion}}`: Email de información

### Firma
- `{{municipio}}`: Nombre del municipio
- `{{nombre_funcionario}}`: Nombre del funcionario emisor