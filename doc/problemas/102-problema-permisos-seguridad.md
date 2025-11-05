# Problemas en el Modelo de Permisos y Seguridad

## Contexto

La propuesta actual define un sistema de permisos basado en:
- Lectura: acceso completo al expediente en proceso
- Escritura: limitada por configuración del agente
- Propagación: `Agente → MCP → API`
- Principio de mínimo privilegio

Ver: [Sistema de permisos](../050-permisos-agente.md), [Propagación de permisos](../052-propagacion-permisos.md)

## Fortalezas Identificadas

- **Principio de mínimo privilegio**: Correctamente identificado
- **Propagación explícita**: El modelo de propagación es conceptualmente claro
- **Separación lectura/escritura**: Distinción apropiada entre capacidades

## Problemas Críticos Identificados

### 1. Granularidad Indefinida

**Problema**: La frase "permisos limitados por configuración" es demasiado vaga.

**Preguntas sin respuesta**:
- ¿Qué acciones concretas pueden autorizarse?
- ¿Cuál es la taxonomía de permisos?
- ¿Granularidad por tipo de documento? ¿Por campo?
- ¿Hay permisos condicionales? (ej: "puede crear documento solo si expediente está en estado X")

**Impacto**: Imposible implementar sistema de autorización sin catálogo explícito.

**Ejemplo de lo que falta**:
```
Permisos de escritura posibles:
- write:document:create
- write:document:update
- write:document:delete
- write:expediente:metadata
- execute:signature
- execute:notification
- etc.
```

### 2. Ausencia de Modelo de Amenazas

**Problema**: No se identifica qué ataques se quieren prevenir.

**Amenazas no consideradas**:
- **Privilege escalation**: ¿Puede un agente otorgarse más permisos?
- **Data exfiltration**: ¿Cómo se previene que un agente filtre información sensible?
- **Injection attacks**: ¿Se validan inputs del agente contra SQL/command injection?
- **Prompt injection**: ¿Cómo se previene que datos del expediente manipulen el comportamiento del agente?
- **Agente comprometido**: ¿Qué daño puede hacer un agente malicioso con permisos válidos?

**Impacto**: Sistema vulnerable a ataques no contemplados.

### 3. Validación de Salida No Especificada

**Problema**: Solo se mencionan permisos de entrada (qué puede hacer), pero no validación de salida (qué puede exponer).

**Escenarios problemáticos**:
- Agente incluye datos personales sensibles en logs públicos
- Agente genera documento con información de otros expedientes mezclada
- Agente envía contexto completo a API externa no autorizada

**Impacto**: Riesgo de violación de GDPR/LOPD por data leakage.

### 4. Gestión de Credenciales No Especificada

**Problema**: No se describe cómo se autentican los agentes.

**Aspectos críticos**:
- ¿Tokens de acceso? ¿JWT? ¿API keys?
- ¿Certificados X.509?
- ¿Rotación automática de credenciales?
- ¿Almacenamiento seguro (secrets management)?
- ¿Scope por expediente individual?

**Impacto**: Riesgo de credenciales comprometidas con acceso persistente.

### 5. Sin Estrategia de Revocación

**Problema**: No hay mecanismo documentado para revocar permisos de agente comprometido.

**Preguntas sin respuesta**:
- ¿Cómo se desactiva un agente problemático?
- ¿Hay kill switch global?
- ¿Se pueden revocar permisos sin redeploy?
- ¿Cómo se audita qué hizo el agente antes de revocación?

**Impacto**: Tiempo de respuesta lento ante incidente de seguridad.

## Recomendaciones

### Prioridad Crítica

1. **Definir catálogo explícito de permisos**
   ```
   Formato: <action>:<resource>:<operation>
   Ejemplos:
   - read:expediente:metadata
   - write:document:create
   - execute:signature:request
   - delete:document:draft
   ```

2. **Implementar RBAC (Role-Based Access Control)**
   ```
   Roles predefinidos:
   - agent:extractor (read:*, write:document:create)
   - agent:generator (read:*, write:document:create, execute:template)
   - agent:analyst (read:*, write:expediente:metadata)
   ```

3. **Crear modelo de amenazas documentado**
   - Identificar actores maliciosos (agente comprometido, insider, atacante externo)
   - Documentar vectores de ataque
   - Definir controles para cada amenaza

### Prioridad Alta

4. **Añadir validación de salida (output validation)**
   - Sanitización de logs (redacción automática de PII)
   - Validación de que documentos generados no contienen datos de otros expedientes
   - Rate limiting en llamadas externas

5. **Diseñar sistema de autenticación robusto**
   - Usar tokens JWT de corta duración (1 hora)
   - Incluir claims: `agent_id`, `expediente_id`, `permissions[]`, `exp`
   - Rotación automática de secrets
   - Integración con secrets manager (HashiCorp Vault, AWS Secrets Manager)

6. **Implementar capacidad de revocación**
   - Lista de revocación de tokens
   - Kill switch por tipo de agente
   - API de emergencia para deshabilitar agentes
   - Logs de auditoría previos a revocación

### Prioridad Media

7. **Permisos condicionales**
   - Permitir reglas como: "puede firmar solo si monto < 1000€"
   - Policy as code (ej: usando OPA - Open Policy Agent)

8. **Defense in depth**
   - Validación en múltiples capas (Agente, MCP, API)
   - Rate limiting por agente
   - Anomaly detection en patrones de acceso

## Ejemplo de Especificación Necesaria

```yaml
# Definición de rol de agente
agent_role:
  name: "document_extractor"
  permissions:
    read:
      - "expediente:*"
      - "document:*"
    write:
      - "expediente:metadata:extracted_data"
      - "document:create:tipo=informe_extraccion"
    deny:
      - "document:delete:*"
      - "expediente:estado:*"

  rate_limits:
    api_calls_per_minute: 60
    documents_created_per_expediente: 1

  output_validation:
    log_redaction:
      - dni
      - email
      - telefono
    prevent_cross_expediente_data: true
```

## Relaciones

- Ver: [Problemática general](100-problematica-general.md)
- Ver: [Sistema de permisos actual](../050-permisos-agente.md)
- Ver: [Propagación en arquitectura](../052-propagacion-permisos.md)
- Ver: [Implementación en MCP](101-problema-arquitectura-mcp.md)
- Ver: [Aspectos de cumplimiento normativo](108-aspectos-ausentes.md)
- Ver: [Prioridades de mejora](109-prioridades-mejora.md)
