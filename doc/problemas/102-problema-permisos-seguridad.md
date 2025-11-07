# Problemas en el Modelo de Permisos y Seguridad

## Contexto

La propuesta actual define un sistema de permisos basado en:
- Usuario "Automático" de GEX con permisos de Consulta/Gestión por tipo de expediente
- Acceso limitado a información de tarea específica
- Propagación mediante JWT: `BPMN → Agente → MCP → API → GEX`
- Principio de mínimo privilegio
- Modelo de amenazas documentado

Ver: [Sistema de permisos](../050-permisos-agente.md), [Propagación de permisos](../052-propagacion-permisos.md), [Mitigación Prompt Injection](../053-mitigacion-prompt-injection.md)

## Mejoras Recientes

**Avances positivos respecto a versión anterior**:
- ✅ Se ha añadido sección de modelo de amenazas
- ✅ Se ha especificado uso de JWT para propagación de permisos
- ✅ Se ha vinculado con sistema de permisos existente de GEX (usuario "Automático")
- ✅ Se ha creado documento específico sobre mitigación de Prompt Injection
- ✅ Se ha especificado separación de herramientas de lectura/escritura

**Valoración**: Las mejoras demuestran evolución hacia un modelo más robusto, pero siguen existiendo carencias críticas que impiden una implementación segura.

## Fortalezas Identificadas

- **Principio de mínimo privilegio**: Correctamente identificado y reforzado
- **Reutilización de infraestructura**: Aprovechar sistema de permisos de GEX es pragmático
- **Propagación explícita con JWT**: El modelo de propagación es más concreto
- **Separación lectura/escritura**: Distinción apropiada implementada a nivel de herramientas
- **Consciencia de amenazas**: Reconocimiento explícito de vectores de ataque principales

## Problemas Críticos Identificados

### 1. Granularidad Indefinida (PERSISTE)

**Estado**: Aunque se ha vinculado con el sistema de permisos de GEX (Consulta/Gestión), el problema de granularidad persiste.

**Problema**: Delegar en "permisos del usuario Automático" no resuelve la necesidad de especificar qué operaciones concretas puede realizar un agente.

**Preguntas críticas sin respuesta**:
- ¿Qué operaciones concretas implica "Gestión"? ¿Crear documentos? ¿Modificar metadatos? ¿Cambiar estados? ¿Ejecutar firmas?
- ¿Cómo se limitan las herramientas disponibles si el permiso de GEX es binario (Consulta/Gestión)?
- ¿Hay granularidad por tipo de documento? ¿Por campo específico?
- ¿Existe diferenciación entre "puede leer documento" y "puede incluir documento en contexto"?
- ¿Hay permisos condicionales? (ej: "puede crear documento solo si expediente está en estado X")

**Inconsistencia detectada**:
- El documento dice: "el agente sólo tendrá acceso a aquellas herramientas estríctamente necesarias"
- Pero GEX otorga permisos binarios: Consulta o Gestión
- **¿Cómo se reconcilian estos dos niveles de granularidad?**

**Impacto**:
- Imposible implementar control fino de acceso sobre herramientas MCP
- Riesgo de otorgar más permisos de los necesarios (violación de principio de mínimo privilegio)
- Dificulta auditoría de qué operaciones específicas realizó el agente

**Ejemplo de especificación necesaria**:
```yaml
# Mapeo entre permisos GEX y capacidades de agente
usuario_automatico:
  gex_permission: "Gestión"  # Permiso en GEX

  # Pero agente tiene subset específico:
  agent_capabilities:
    read:
      - document:metadata
      - document:content
      - expediente:estado
    write:
      - document:create:tipo=informe_extraccion
      - expediente:metadata:datos_extraidos
    deny:
      - document:delete
      - expediente:estado:change
      - signature:execute
```

### 2. Modelo de Amenazas Superficial (PARCIALMENTE RESUELTO)

**Estado**: Se ha añadido sección de modelo de amenazas en [050-permisos-agente.md](../050-permisos-agente.md), lo cual es una mejora significativa. Sin embargo, el análisis es superficial y delega aspectos críticos.

**Avances reconocidos**:
- ✅ Se identifican amenazas principales (privilege escalation, data exfiltration, injection, prompt injection, agente comprometido)
- ✅ Se documenta estrategia de mitigación para prompt injection
- ✅ Se reconoce limitación arquitectónica como defensa

**Problemas que persisten**:

**2.1. Afirmaciones sin fundamento técnico**:
- Afirma: "El agente no tiene forma de acceder a información no privilegiada"
  - **Falta**: ¿Cómo se garantiza técnicamente? ¿Qué controles lo previenen?
- Afirma: "Sistema debe ser inmune a injection attacks a condición de que la API esté revisada"
  - **Crítica**: Delegar la seguridad a "si la API está bien hecha" no es aceptable. ¿Qué controles añade la capa de agentes?

**2.2. Análisis de Data Exfiltration insuficiente**:
- **Escenario no abordado**: Agente incluye información sensible en sus razonamientos/logs
- **Escenario no abordado**: Agente construye documento que mezcla datos de contexto con información externa
- **Escenario no abordado**: Agente expone información en errores/excepciones

**2.3. Análisis de Privilege Escalation incompleto**:
- ¿Puede un agente manipular el JWT que propaga?
- ¿Qué pasa si el servicio de agentes es comprometido y firma JWTs fraudulentos?
- ¿Hay validación de que el expediente en JWT coincide con expediente en contexto?

**2.4. Agente Comprometido - Riesgo subestimado**:
- Afirma que el riesgo es "reducido" por supervisión humana en BPMN
- **Crítica**: Esto asume que la supervisión detectará anomalías, pero:
  - ¿Qué pasa con acciones maliciosas sutiles?
  - ¿Cuánto daño puede hacer antes de que la supervisión actúe?
  - ¿Hay detección automática de comportamiento anómalo?

**Impacto**: Falsa sensación de seguridad por modelo de amenazas incompleto.

### 3. Validación de Salida No Especificada (SIN RESOLVER)

**Estado**: Este problema crítico no ha sido abordado en las actualizaciones recientes.

**Problema**: La documentación se enfoca en permisos de entrada (qué puede leer/escribir), pero **no especifica validación de salida** (qué puede exponer/generar).

**Escenarios problemáticos sin controles documentados**:

**3.1. Fuga en Logs y Trazas**:
- Documento [051-autoria-agente.md](../051-autoria-agente.md) especifica que se guardan:
  - Contexto completo
  - Prompts
  - Razonamientos del LLM
  - Respuestas
- **Riesgo**: Si logs son accesibles ampliamente, exposición masiva de datos personales
- **Pregunta**: ¿Se sanitizan/redactan automáticamente DNIs, emails, números de cuenta?

**3.2. Contaminación Cruzada de Expedientes**:
- Agente podría generar documento mezclando datos de:
  - Contexto actual (expediente A)
  - Información residual en memoria del modelo
  - Datos de ejemplos en prompts del sistema
- **Falta**: Validación de que outputs solo contienen información del expediente autorizado

**3.3. Exposición a APIs Externas**:
- Si el modelo LLM es externo (ej: API de OpenAI, Anthropic):
  - Todo el contexto se envía fuera de la infraestructura
  - **Pregunta**: ¿Está permitido? ¿Hay DPA (Data Processing Agreement)?
  - **Pregunta**: ¿Se anonimiza el contexto antes de envío?
- Si el modelo es local:
  - ¿Hay controles sobre dónde se almacenan logs del modelo?

**3.4. Generación de Documentos No Autorizados**:
- Agente con permiso de "Gestión" podría:
  - Crear documento de tipo no esperado
  - Generar documento con contenido malicioso (ej: script en campo de texto)
  - Crear número excesivo de documentos (DoS)
- **Falta**: Esquema de validación de outputs (tipo, formato, cantidad)

**3.5. Información en Errores**:
- Mensajes de error podrían exponer:
  - Estructura de base de datos
  - Rutas de archivos internos
  - Valores de datos sensibles
- **Falta**: Sanitización de mensajes de error antes de loguear/mostrar

**Impacto**:
- **CRÍTICO**: Violación potencial de GDPR/LOPD (Art. 32 - Seguridad del tratamiento)
- Imposibilidad de certificar cumplimiento del ENS (Esquema Nacional de Seguridad) sin controles de salida
- Riesgo reputacional por filtración accidental de datos

### 4. Gestión de Credenciales Incompleta (PARCIALMENTE RESUELTO)

**Estado**: Documento [052-propagacion-permisos.md](../052-propagacion-permisos.md) especifica uso de JWT, lo cual es positivo. Sin embargo, faltan aspectos críticos de gestión del ciclo de vida.

**Avances reconocidos**:
- ✅ Se especifica JWT como mecanismo de autenticación
- ✅ Se definen claims mínimos: usuario "Automático" + expediente concreto
- ✅ Se documenta flujo de validación en cada capa

**Aspectos críticos sin especificar**:

**4.1. Duración y Renovación de Tokens**:
- ¿Cuánto tiempo es válido el JWT? ¿1 hora? ¿1 día?
- ¿Cómo se renueva un token si la tarea tarda más que la expiración?
- ¿Hay tokens de refresh?
- **Recomendación estándar**: Tokens de corta duración (≤1h) con renovación automática

**4.2. Firma y Validación de JWT**:
- ¿Qué algoritmo de firma? ¿HS256? ¿RS256? ¿ES256?
- ¿Quién genera el JWT? ¿El sistema BPMN?
- ¿Dónde se almacena la clave de firma?
- ¿Hay rotación periódica de claves de firma?
- **Crítica**: Sin especificar algoritmo, imposible evaluar seguridad

**4.3. Claims del JWT - Insuficientes**:
- Claims documentados: `usuario`, `expediente`
- **Faltan claims críticos**:
  - `exp` (expiration): obligatorio para seguridad
  - `iat` (issued at): necesario para auditoría
  - `jti` (JWT ID): necesario para revocación
  - `aud` (audience): ¿quién puede usar este token?
  - `agent_type`: ¿qué tipo de agente está autorizado?
  - `allowed_tools`: ¿qué herramientas MCP puede usar?

**4.4. Almacenamiento de Secrets**:
- ¿Cómo se almacena la clave de firma del JWT?
- ¿Hay integración con secrets manager? (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault)
- ¿Cómo accede el sistema BPMN a la clave para firmar tokens?
- **Riesgo**: Clave hardcodeada en código o configuración sin cifrar

**4.5. Autenticación del Servicio de Agentes**:
- El JWT autentica el contexto de la tarea
- Pero, **¿cómo se autentica el servicio de agentes en sí ante MCP/GEX?**
- ¿TLS mutuo? ¿API keys? ¿Certificados?
- **Escenario**: Atacante podría suplantar servicio de agentes si no hay autenticación de servicio a servicio

**Impacto**:
- Tokens de larga duración aumentan ventana de exposición ante compromiso
- Sin rotación de claves, compromiso de clave de firma compromete todo el sistema permanentemente
- Falta de claims necesarios impide revocación efectiva

### 5. Sin Estrategia de Revocación (SIN RESOLVER)

**Estado**: Este problema crítico permanece sin abordar en la documentación.

**Problema**: No hay mecanismo documentado para responder a incidentes de seguridad relacionados con agentes.

**Escenarios de revocación necesarios**:

**5.1. Compromiso de Agente Individual**:
- Se detecta que un agente específico está comportándose de forma anómala
- **Falta**: ¿Cómo se desactiva inmediatamente ese agente?
- **Falta**: ¿Cómo se invalidan los JWTs ya emitidos para ese agente?

**5.2. Compromiso de Tipo de Agente**:
- Se descubre vulnerabilidad en todos los agentes de tipo "extractor"
- **Falta**: ¿Hay kill switch por tipo de agente?
- **Falta**: ¿Se pueden deshabilitar todos los agentes de un tipo sin afectar otros?

**5.3. Compromiso de Clave de Firma**:
- Se descubre que la clave de firma de JWT ha sido comprometida
- **Crítico**: Todos los JWTs son potencialmente falsos
- **Falta**: Plan de rotación de emergencia de claves

**5.4. Revocación de JWT Específico**:
- Se detecta JWT específico siendo usado maliciosamente
- **Falta**: Lista de revocación de JWTs (JTI blocklist)
- **Alternativa**: Redis con TTL de JWTs revocados
- **Problema**: Sin claim `jti` documentado, imposible implementar revocación granular

**5.5. Auditoría Post-Revocación**:
- Tras revocar agente comprometido, necesidad de investigar qué hizo
- **Falta**: ¿Cómo se consultan todas las acciones de ese agente?
- **Falta**: ¿Se pueden revertir acciones realizadas por agente comprometido?

**Tiempos de respuesta ante incidente**:

Sin estrategia de revocación:
- Detección de agente comprometido → T+0
- Localización de configuración → T+15min
- Modificación de configuración → T+30min
- Redeploy de servicios → T+45min
- Validación → T+60min
- **Ventana de exposición**: ~1 hora

Con estrategia de revocación:
- Detección → T+0
- Revocación vía API/Dashboard → T+2min
- Propagación a todos los servicios → T+5min
- **Ventana de exposición**: ~5 minutos

**Impacto**:
- **CRÍTICO**: Incapacidad de respuesta rápida ante incidente de seguridad
- Ventana de exposición extendida permite mayor daño
- Incumplimiento potencial de Art. 33 GDPR (notificación de brechas en 72h requiere capacidad de contención rápida)

## Recomendaciones Actualizadas

### Resumen de Prioridades

**Estado actual**: El proyecto ha avanzado en consciencia de seguridad (modelo de amenazas, JWT, mitigación de prompt injection), pero **faltan especificaciones técnicas concretas** para implementación segura.

**Enfoque recomendado**: Completar especificaciones antes de iniciar implementación para evitar refactorizaciones costosas por decisiones de seguridad tardías.

### Prioridad Crítica (Bloqueantes para producción)

#### 1. Definir catálogo explícito de permisos y su mapeo con GEX

**Acción**: Documentar qué implica "Consulta" y "Gestión" en términos de operaciones concretas.

```yaml
# Especificación necesaria:
gex_permission_mapping:
  Consulta:
    implies:
      - read:expediente:all_metadata
      - read:document:content
      - read:document:metadata
      - read:expediente:historial
    denies:
      - write:*
      - execute:*

  Gestión:
    implies:
      - read:*  # Todo lo de Consulta
      - write:document:create
      - write:document:update
      - write:expediente:metadata
      - execute:template:render
    denies:
      - write:document:delete
      - write:expediente:estado:change
      - execute:signature
      - execute:notification:send

# Luego, mapeo por tipo de agente:
agent_types:
  extractor:
    gex_base: Gestión
    restrict_to:  # Subset de Gestión
      - read:document:content
      - write:expediente:metadata:datos_extraidos
      - write:document:create:tipo=informe_extraccion
```

**Justificación**: Sin esto, imposible implementar control de acceso fino que cumpla principio de mínimo privilegio.

#### 2. Implementar validación de salida (Output Validation)

**Acciones concretas**:

```python
# Ejemplo de especificación necesaria:
output_validation:
  log_sanitization:
    enabled: true
    pii_patterns:
      - type: dni
        regex: '\d{8}[A-Z]'
        replacement: '[DNI-REDACTED]'
      - type: email
        regex: '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        replacement: '[EMAIL-REDACTED]'
      - type: iban
        regex: 'ES\d{22}'
        replacement: '[IBAN-REDACTED]'

  document_validation:
    schema_enforcement: true
    allowed_document_types:
      - informe_extraccion
      - borrador_respuesta
    max_documents_per_expediente: 5

  cross_expediente_check:
    enabled: true
    # Validar que IDs en documento generado coinciden con expediente actual
```

**Justificación**: CRÍTICO para cumplimiento GDPR/LOPD. Sin esto, el sistema no es deployable en producción.

#### 3. Completar especificación de JWT

**Acciones**:

```json
{
  "jwt_specification": {
    "algorithm": "RS256",
    "token_duration": "1h",
    "refresh_enabled": true,
    "required_claims": {
      "iss": "gex-bpmn",
      "sub": "usuario_automatico",
      "aud": ["agentix-service", "mcp-server", "gex-api"],
      "exp": "timestamp",
      "iat": "timestamp",
      "jti": "unique-token-id",
      "expediente_id": "string",
      "agent_type": "string",
      "allowed_tools": ["array"]
    }
  },
  "key_management": {
    "storage": "HashiCorp Vault",
    "rotation_schedule": "quarterly",
    "emergency_rotation_procedure": "documented"
  }
}
```

**Justificación**: Necesario para implementar revocación y auditoría efectiva.

#### 4. Implementar estrategia de revocación

**Arquitectura propuesta**:

```
Revocation Service (Redis/PostgreSQL)
  ├─ JTI Blocklist (TTL = token expiration)
  ├─ Agent Type Disablement
  └─ Emergency Kill Switch

API Endpoints:
  POST /revoke/token/{jti}
  POST /revoke/agent/{agent_id}
  POST /revoke/agent-type/{type}
  POST /emergency/kill-all-agents

Validation Flow:
  Cada servicio (Agente, MCP, API) verifica:
  1. JWT válido (firma, exp)
  2. JTI not in blocklist
  3. Agent type not disabled
  4. Emergency kill switch not active
```

**Justificación**: Sin esto, tiempo de respuesta ante incidentes es inaceptable (>1h vs 5min).

### Prioridad Alta (Necesario para despliegue seguro)

#### 5. Profundizar modelo de amenazas con controles técnicos específicos

**Acción**: Para cada amenaza identificada, documentar control técnico específico.

Ejemplo:
```markdown
| Amenaza | Control Arquitectónico | Control Técnico | Testing |
|---------|----------------------|-----------------|---------|
| Privilege Escalation | Scope JWT por expediente | Validación de expediente_id en cada operación | Intentar acceder expediente no autorizado |
| Data Exfiltration | Logs con PII redactada | Regex-based sanitization pre-logging | Verificar logs no contienen DNIs |
| Agente Comprometido | Rate limiting | Max 100 req/min por agente | Stress test con 1000 req/min |
```

#### 6. Definir estrategia de deployment de modelos LLM

**Decisión necesaria**:
- ¿Modelos externos (API) o locales?
- Si externos: DPA, anonimización, residencia de datos
- Si locales: requisitos de infraestructura, actualización

### Prioridad Media (Mejoras progresivas)

#### 7. Permisos condicionales con Policy as Code

Usar OPA (Open Policy Agent) para reglas complejas:
```rego
allow {
  input.action == "execute:signature"
  input.expediente.importe < 1000
  input.agent.type == "gestor_automatico"
}
```

#### 8. Detección de anomalías en comportamiento de agentes

- Establecer baseline por tipo de agente
- Alertar desviaciones significativas
- Machine learning para detección de patrones anómalos

## Ejemplo Integrado de Especificación Necesaria

```yaml
# Especificación completa para un tipo de agente
agent_type_specification:
  name: "document_extractor"
  version: "1.0"

  # Permisos base en GEX
  gex_permission: "Gestión"

  # Permisos específicos del agente (subset de Gestión)
  permissions:
    read:
      - "expediente:metadata"
      - "document:content"
      - "document:metadata"
    write:
      - "expediente:metadata:extracted_data"
      - "document:create:tipo=informe_extraccion"
    deny:
      - "document:delete:*"
      - "expediente:estado:*"
      - "signature:*"
      - "notification:*"

  # Herramientas MCP disponibles
  mcp_tools:
    - "read_document"
    - "write_metadata"
    - "create_document"

  # JWT claims adicionales
  jwt_claims:
    agent_type: "document_extractor"
    allowed_tools: ["read_document", "write_metadata", "create_document"]

  # Límites operacionales
  rate_limits:
    api_calls_per_minute: 60
    documents_created_per_expediente: 1
    max_context_size_mb: 10

  # Validación de salida
  output_validation:
    log_redaction:
      enabled: true
      patterns: [dni, email, telefono, iban, tarjeta_credito]
    document_validation:
      enforce_schema: true
      allowed_types: ["informe_extraccion"]
      max_size_mb: 5
    prevent_cross_expediente_data: true

  # Auditoría
  audit:
    log_level: "detailed"
    retention_days: 365
    pii_handling: "redacted"

  # Revocación
  revocation:
    supports_immediate: true
    invalidates_existing_tokens: true
```

## Conclusión

**Valoración general**: El proyecto ha evolucionado positivamente en consciencia de seguridad. Las mejoras en documentación de modelo de amenazas, uso de JWT y mitigación de prompt injection son pasos en la dirección correcta.

**Crítica constructiva**: Sin embargo, el diseño sigue en fase **conceptual** sin suficiente detalle técnico para implementación segura. Los problemas identificados (granularidad indefinida, validación de salida ausente, revocación no especificada) son **bloqueantes para producción** en un entorno que maneja datos personales sensibles bajo GDPR/LOPD.

**Recomendación**: Priorizar completar especificaciones técnicas de seguridad **antes** de iniciar implementación. Es más eficiente diseñar seguridad desde el inicio que refactorizar después.

## Relaciones

- Ver: [Problemática general](100-problematica-general.md)
- Ver: [Sistema de permisos actual](../050-permisos-agente.md)
- Ver: [Propagación en arquitectura](../052-propagacion-permisos.md)
- Ver: [Mitigación de Prompt Injection](../053-mitigacion-prompt-injection.md)
- Ver: [Implementación en MCP](101-problema-arquitectura-mcp.md)
- Ver: [Aspectos de cumplimiento normativo](108-aspectos-ausentes.md)
- Ver: [Prioridades de mejora](109-prioridades-mejora.md)
