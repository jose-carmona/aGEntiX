# Plantilla: Certificado de Empadronamiento

---

## CERTIFICADO DE EMPADRONAMIENTO {{tipo_certificado}}

**Nº Certificado:** {{numero_certificado}}

**Fecha de expedición:** {{fecha_expedicion}}

---

### AYUNTAMIENTO DE {{municipio}}

**Provincia de {{provincia}}**

---

{{nombre_secretario}}, Secretario/a General del Ayuntamiento de {{municipio}},

**CERTIFICO:**

{{#if certificado_individual}}
Que consultados los datos obrantes en el Padrón Municipal de Habitantes de este Ayuntamiento, **{{nombre_completo}}**, con **{{tipo_documento}} {{numero_documento}}**, figura inscrito/a en el mismo con los siguientes datos:

| Dato | Valor |
|------|-------|
| Nombre y apellidos | {{nombre_completo}} |
| Fecha de nacimiento | {{fecha_nacimiento}} |
| Lugar de nacimiento | {{lugar_nacimiento}} |
| Nacionalidad | {{nacionalidad}} |
| Domicilio | {{domicilio_completo}} |
| Fecha de alta | {{fecha_alta_padron}} |
| {{tipo_documento}} | {{numero_documento}} |
{{/if}}

{{#if certificado_colectivo}}
Que consultados los datos obrantes en el Padrón Municipal de Habitantes de este Ayuntamiento, en el domicilio sito en **{{domicilio_completo}}**, figuran inscritas las siguientes personas:

| Nombre y apellidos | Fecha nacimiento | {{tipo_documento}} | Fecha alta | Parentesco |
|-------------------|------------------|---------------------|------------|------------|
{{#each personas_domicilio}}
| {{nombre_completo}} | {{fecha_nacimiento}} | {{numero_documento}} | {{fecha_alta}} | {{parentesco}} |
{{/each}}

**Total de personas inscritas en el domicilio:** {{total_personas}}
{{/if}}

{{#if certificado_historico}}
Que consultados los datos obrantes en el Padrón Municipal de Habitantes de este Ayuntamiento, **{{nombre_completo}}**, con **{{tipo_documento}} {{numero_documento}}**, presenta el siguiente historial de inscripciones:

| Fecha alta | Fecha baja | Domicilio | Motivo alta | Motivo baja |
|------------|------------|-----------|-------------|-------------|
{{#each movimientos_padronales}}
| {{fecha_alta}} | {{fecha_baja}} | {{domicilio}} | {{motivo_alta}} | {{motivo_baja}} |
{{/each}}

**Periodo certificado:** Desde {{fecha_inicio_periodo}} hasta {{fecha_fin_periodo}}
{{/if}}

---

Y para que conste y surta los efectos oportunos{{#if finalidad}}, a los efectos de **{{finalidad}}**{{/if}}, expido el presente certificado.

---

En {{municipio}}, a {{fecha_expedicion}}

El/La Secretario/a General



Fdo.: {{nombre_secretario}}

---

### CÓDIGO SEGURO DE VERIFICACIÓN (CSV)

**{{codigo_csv}}**

Este documento es copia auténtica de un documento electrónico.
Puede verificar su autenticidad en: {{url_verificacion}}

---

### NOTAS

1. Este certificado refleja la situación padronal en el momento de su expedición.
2. Los datos personales están protegidos conforme al Reglamento (UE) 2016/679 (RGPD).
3. El uso fraudulento de este documento puede constituir delito.
4. Validez del documento: 3 meses desde su expedición (recomendado).

---

## CAMPOS A RELLENAR:

### Datos del certificado
- `{{numero_certificado}}`: Número único del certificado (ej: EMP-2024-00123)
- `{{fecha_expedicion}}`: Fecha de expedición (DD de MES de AAAA)
- `{{tipo_certificado}}`: INDIVIDUAL / COLECTIVO / HISTÓRICO

### Datos del municipio
- `{{municipio}}`: Nombre del municipio
- `{{provincia}}`: Nombre de la provincia
- `{{nombre_secretario}}`: Nombre del Secretario/a General

### Datos del interesado (individual/histórico)
- `{{nombre_completo}}`: Nombre y apellidos completos
- `{{tipo_documento}}`: DNI, NIE o Pasaporte
- `{{numero_documento}}`: Número del documento
- `{{fecha_nacimiento}}`: Fecha de nacimiento (DD/MM/AAAA)
- `{{lugar_nacimiento}}`: Localidad y país de nacimiento
- `{{nacionalidad}}`: Nacionalidad
- `{{domicilio_completo}}`: Dirección completa
- `{{fecha_alta_padron}}`: Fecha de inscripción en el Padrón

### Datos del domicilio (colectivo)
- `{{domicilio_completo}}`: Dirección completa del domicilio
- `{{personas_domicilio}}`: Array de personas con sus datos
- `{{total_personas}}`: Número total de inscritos

### Datos históricos
- `{{movimientos_padronales}}`: Array de altas/bajas
- `{{fecha_inicio_periodo}}`: Inicio del periodo certificado
- `{{fecha_fin_periodo}}`: Fin del periodo certificado

### Verificación
- `{{codigo_csv}}`: Código Seguro de Verificación (generado automáticamente)
- `{{url_verificacion}}`: URL de la sede electrónica para verificación

### Opcional
- `{{finalidad}}`: Finalidad específica del certificado (si se indica)