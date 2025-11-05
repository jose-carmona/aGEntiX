# Problemas en Auditoría y Trazabilidad

## Contexto

La propuesta actual establece que:
- El agente **debe dejar log de todos los pasos**
- Propósitos: depuración, comprobación, auditoría, cumplimiento
- La autoría usa el nombre del tipo de agente

Ver: [Requisitos de auditoría](../033-auditoria-agente.md), [Gestión de autoría](../051-autoria-agente.md)

## Fortalezas Identificadas

- **Requisito identificado correctamente**: El logging es fundamental en entornos administrativos
- **Propósitos claros**: Se entiende para qué sirve la auditoría
- **Trazabilidad de autoría**: Distinción entre acciones humanas y de agentes

## Problemas Críticos Identificados

### 1. Formato de Log No Especificado

**Problema**: No se define qué información debe contener cada log entry ni en qué formato.

**Preguntas sin respuesta**:
- ¿Texto libre o estructura JSON?
- ¿Qué campos son obligatorios?
- ¿Nivel de detalle (debug, info, warning, error)?
- ¿Se registra el razonamiento del agente o solo acciones?
- ¿Se incluye el contexto completo o resumen?

**Ejemplo de diferencia crítica**:

```
Log insuficiente (texto libre):
"El agente procesó el documento y extrajo los datos"

Log adecuado (estructurado):
{
  "timestamp": "2024-03-15T10:23:45.123Z",
  "execution_id": "exec_abc123",
  "agent_type": "document_extractor",
  "agent_version": "1.2.0",
  "expediente_id": "EXP-2024-001234",
  "tarea_id": "task_567",
  "accion": "extraer_datos",
  "input": {
    "documento_id": "doc_789",
    "documento_nombre": "solicitud.pdf",
    "documento_hash_sha256": "abc123..."
  },
  "reasoning": "Identifico 3 secciones en el documento. Sección 1 contiene datos personales...",
  "output": {
    "dni": "12345678A",
    "nombre": "Juan Pérez",
    "telefono": null
  },
  "confidence": 0.92,
  "duration_ms": 3450,
  "tokens_used": 1234,
  "cost_eur": 0.023,
  "warnings": [],
  "errors": []
}
```

**Impacto**: Logs inútiles para debugging, imposibilidad de auditoria automatizada.

### 2. Retención de Logs No Definida

**Problema**: No se especifica dónde se almacenan los logs ni por cuánto tiempo.

**Aspectos críticos**:
- **Ubicación**: ¿Base de datos? ¿Sistema de archivos? ¿Log aggregator externo?
- **Duración**: ¿Cuánto tiempo se guardan? (importante para GDPR y normativa administrativa)
- **Capacidad**: ¿Hay límite de tamaño? ¿Qué pasa si se llena?
- **Backup**: ¿Se hace backup de logs? ¿Con qué frecuencia?
- **Acceso**: ¿Quién puede acceder a logs? ¿Hay control de acceso?

**Contexto legal**:
- GDPR: datos personales en logs deben borrarse según política de retención
- Ley 39/2015: expedientes administrativos tienen períodos de conservación específicos
- ENS: logs de seguridad requieren protección especial

**Impacto**: Incumplimiento normativo, riesgo legal, costes de almacenamiento descontrolados.

### 3. Privacidad en Logs No Considerada

**Problema**: Los logs pueden contener datos personales sensibles que deben protegerse.

**Datos sensibles en logs**:
- DNI, nombre, dirección, teléfono, email
- Datos financieros (cuentas bancarias, ingresos)
- Datos de salud (en expedientes de servicios sociales)
- Datos de menores

**Riesgos**:
- Exposición de datos en logs accesibles por más personas que el expediente original
- Violación de GDPR/LOPD
- Logs en sistemas de monitorización externos (cloud) sin cifrado adecuado

**Ejemplo problemático**:
```json
{
  "agent": "document_extractor",
  "action": "extraer_datos",
  "reasoning": "Encontré el DNI 12345678A perteneciente a Juan Pérez García,
                con domicilio en Calle Falsa 123, y teléfono 666777888.
                Su cuenta bancaria ES12 3456 7890 1234..."
}
```

**Impacto**: Violación de privacidad, multas GDPR (hasta 20M€ o 4% facturación), pérdida de confianza.

### 4. Sin Estrategia de Análisis de Logs

**Problema**: No hay plan para utilizar los logs de forma proactiva.

**Oportunidades perdidas**:
- Detectar patrones de error recurrentes
- Identificar expedientes problemáticos antes de que escalen
- Mejorar agentes basándose en casos fallidos
- Alertas automáticas de comportamiento anómalo
- Métricas agregadas de rendimiento

**Ejemplo de análisis útil**:
```
Análisis detecta:
- El agente "document_extractor" tiene tasa de error 15% en documentos
  de tipo "certificado_catastral" (vs 2% en otros documentos)
→ Acción: Mejorar prompts específicos para ese tipo de documento
```

**Impacto**: Subutilización de datos valiosos, problemas no detectados hasta que causan impacto.

### 5. Autoría Nominal Insuficiente

**Problema**: Usar solo "nombre del agente" como autor es insuficiente para trazabilidad completa.

**Información adicional necesaria**:
- **Versión del agente**: ¿Fue "document_extractor v1.0" o "v2.0"?
- **Timestamp**: ¿Cuándo exactamente?
- **Execution ID**: Para correlacionar múltiples logs de la misma ejecución
- **Usuario humano responsable**: ¿Quién configuró/desplegó el agente?
- **Contexto**: ¿Qué expediente, tarea, workflow?

**Ejemplo de autoría mejorada**:
```json
{
  "autoria": {
    "tipo": "agente",
    "agente_tipo": "document_extractor",
    "agente_version": "1.2.0",
    "agente_instancia_id": "inst_xyz789",
    "execution_id": "exec_abc123",
    "timestamp": "2024-03-15T10:23:45.123Z",
    "responsable_humano": "admin@ejemplo.es",
    "expediente_id": "EXP-2024-001234",
    "tarea_id": "task_567",
    "workflow_id": "wf_licencias_obras_v3"
  }
}
```

**Impacto**: Imposibilidad de debugging efectivo, atribución de responsabilidad confusa.

### 6. Sin Garantía de Inmutabilidad

**Problema**: No se especifica cómo prevenir manipulación de logs.

**Riesgos**:
- Modificación de logs para ocultar errores
- Borrado de logs comprometedores
- Inserción de logs falsos

**Técnicas necesarias**:
- Firma criptográfica de logs
- Append-only log storage
- Blockchain o similar para cadena de custodia
- Write-Once-Read-Many (WORM) storage

**Impacto**: Logs no confiables para auditoría legal, problemas en litigios.

## Recomendaciones

### Prioridad Crítica

1. **Definir esquema estructurado de logs**
   ```json
   {
     "$schema": "https://agentix.ejemplo.es/schemas/agent_log_v1.json",
     "version": "1.0",
     "timestamp": "ISO8601",
     "trace_id": "string",
     "span_id": "string",
     "execution_id": "string",

     "agent": {
       "type": "string",
       "version": "semver",
       "instance_id": "string"
     },

     "context": {
       "expediente_id": "string",
       "tarea_id": "string",
       "workflow_id": "string",
       "workflow_version": "string"
     },

     "action": {
       "name": "string",
       "input_hash": "sha256",  // hash del input, no el input completo
       "output_hash": "sha256",
       "confidence": "float[0-1]",
       "duration_ms": "integer",
       "status": "success|failure|partial|needs_review"
     },

     "reasoning": "string",  // PII redacted

     "resources": {
       "tokens_used": "integer",
       "cost_eur": "float",
       "model_used": "string"
     },

     "warnings": ["string"],
     "errors": [{"code": "string", "message": "string"}],

     "responsible_human": "email",
     "signature": "base64"  // firma criptográfica del log
   }
   ```

2. **Implementar PII redaction automática**
   ```python
   import re
   from presidio_analyzer import AnalyzerEngine
   from presidio_anonymizer import AnonymizerEngine

   analyzer = AnalyzerEngine()
   anonymizer = AnonymizerEngine()

   def redact_pii(text):
       """Elimina datos personales de logs"""
       results = analyzer.analyze(
           text=text,
           language='es',
           entities=["DNI", "EMAIL", "PHONE_NUMBER", "IBAN", "PERSON"]
       )
       return anonymizer.anonymize(
           text=text,
           analyzer_results=results,
           operators={"DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"})}
       )

   # Usar en todos los logs
   log_entry["reasoning"] = redact_pii(original_reasoning)
   ```

3. **Definir política de retención**
   ```yaml
   log_retention_policy:
     # Logs de operaciones normales
     operational_logs:
       duration: "90_days"
       location: "elasticsearch_cluster"
       backup: "daily"
       backup_retention: "1_year"

     # Logs de auditoría (requieren conservación extendida)
     audit_logs:
       duration: "7_years"  # según normativa administrativa
       location: "worm_storage"
       encrypted: true
       access_control: "audit_team_only"

     # Logs con datos personales (GDPR)
     pii_logs:
       duration: "30_days"
       auto_deletion: true
       legal_hold_support: true  # para casos legales activos

     # Logs de errores/incidentes
     incident_logs:
       duration: "3_years"
       location: "incident_db"
       immutable: true
   ```

### Prioridad Alta

4. **Implementar log aggregation**
   - Usar ELK Stack (Elasticsearch, Logstash, Kibana) o similar
   - Centralizar logs de todos los agentes
   - Permitir búsqueda y análisis
   - Crear dashboards

5. **Firmar logs criptográficamente**
   ```python
   import hmac
   import hashlib
   import json

   def sign_log_entry(log_entry, secret_key):
       """Firma criptográficamente un log entry"""
       log_bytes = json.dumps(log_entry, sort_keys=True).encode('utf-8')
       signature = hmac.new(
           key=secret_key.encode('utf-8'),
           msg=log_bytes,
           digestmod=hashlib.sha256
       ).hexdigest()
       log_entry['signature'] = signature
       return log_entry

   def verify_log_entry(log_entry, secret_key):
       """Verifica que un log no ha sido manipulado"""
       signature = log_entry.pop('signature')
       expected_signature = sign_log_entry(log_entry, secret_key)['signature']
       return hmac.compare_digest(signature, expected_signature)
   ```

6. **Implementar análisis automatizado**
   ```python
   # Detección de anomalías
   from sklearn.ensemble import IsolationForest

   def detect_anomalies(logs):
       """Detecta comportamientos anómalos en logs de agentes"""
       features = extract_features(logs)  # latencia, tasa error, confianza
       model = IsolationForest(contamination=0.05)
       anomalies = model.fit_predict(features)
       return logs[anomalies == -1]

   # Alertas automáticas
   def check_alert_conditions(logs):
       if logs.filter(status='failure').count() > 5:
           send_alert("Tasa de error elevada en agente X")

       if logs.filter(confidence < 0.7).count() > 10:
           send_alert("Baja confianza detectada, revisar expedientes")
   ```

### Prioridad Media

7. **Crear herramienta de auditoría**
   - Portal web para auditores
   - Filtrado por expediente, agente, fecha, etc.
   - Visualización de razonamiento del agente
   - Exportación para auditorías externas

8. **Compliance automatizado**
   - Verificación automática de retención según normativa
   - Alertas de logs próximos a caducar
   - Generación de reportes de cumplimiento

## Ejemplo de Implementación

Ver: `examples/logging_implementation.py`

## Relaciones

- Ver: [Problemática general](100-problematica-general.md)
- Ver: [Requisitos actuales](../033-auditoria-agente.md)
- Ver: [Autoría de acciones](../051-autoria-agente.md)
- Ver: [Protección de datos](102-problema-permisos-seguridad.md)
- Ver: [Cumplimiento normativo](108-aspectos-ausentes.md)
- Ver: [Prioridades](109-prioridades-mejora.md)
