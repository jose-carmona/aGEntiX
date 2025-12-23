# Paso 4: Refactorización de la Invocación de Agentes

## Objetivo

Simplificar la invocación de agentes para que sea más intuitiva y fácil de usar desde el sistema BPMN.

---

## Estado Actual: Cómo se Invoca un Agente

### Endpoint Actual

```http
POST /api/v1/agent/execute
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

### Request Body Actual (Complejo)

```json
{
  "expediente_id": "EXP-2024-001",
  "tarea_id": "TAREA-VALIDAR-DOC",
  "agent_config": {
    "nombre": "ValidadorDocumental",
    "system_prompt": "Eres un validador de documentación administrativa...",
    "modelo": "claude-3-5-sonnet-20241022",
    "prompt_tarea": "Valida que todos los documentos estén presentes y sean válidos",
    "herramientas": ["consultar_expediente", "actualizar_datos", "añadir_anotacion"]
  },
  "webhook_url": "https://bpmn.example.com/api/v1/tasks/callback",
  "timeout_seconds": 300
}
```

### Problemas del Enfoque Actual

1. **Demasiados parámetros obligatorios**: El BPMN debe conocer detalles internos del sistema
2. **system_prompt redundante**: Cada invocación repite el mismo prompt para el mismo tipo de agente
3. **modelo hardcodeado**: El cliente decide el modelo, cuando debería ser configuración del servidor
4. **herramientas explícitas**: El cliente debe saber qué herramientas puede usar cada agente
5. **Acoplamiento fuerte**: El BPMN necesita saber demasiado sobre la implementación interna

### Archivos Involucrados Actualmente

| Archivo                              | Responsabilidad                                              |
| ------------------------------------ | ------------------------------------------------------------ |
| `src/api/routers/agent.py`           | Endpoint HTTP, validación de request                         |
| `src/api/models.py`                  | Modelos Pydantic (ExecuteAgentRequest, AgentConfigRequest)   |
| `src/backoffice/executor.py`         | Orquestador principal (AgentExecutor)                        |
| `src/backoffice/models.py`           | Modelos internos (AgentConfig, AgentExecutionResult)         |
| `src/backoffice/agents/registry.py`  | Registro de agentes disponibles                              |
| `src/backoffice/agents/base.py`      | Clase base AgentMock                                         |

---

## Propuesta: Invocación Simplificada

### Endpoint Modificado

```http
POST /api/v1/agent/execute
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

### Nuevo Request Body (Simplificado)

```json
{
  "agent": "ValidadorDocumental",
  "prompt": "Valida los documentos del expediente EXP-2024-001 y verifica que el NIF del solicitante coincida con los documentos adjuntos",
  "context": {
    "expediente_id": "EXP-2024-001",
    "tarea_id": "TAREA-VALIDAR-DOC"
  },
  "callback_url": "https://bpmn.example.com/callback"
}
```

### Parámetros Simplificados

| Parámetro      | Tipo   | Obligatorio | Descripción                                    |
| -------------- | ------ | ----------- | ---------------------------------------------- |
| `agent`        | string | Sí          | Identificador del tipo de agente               |
| `prompt`       | string | Sí          | Instrucciones específicas para esta ejecución  |
| `context`      | object | Sí          | Contexto mínimo (expediente_id, tarea_id)      |
| `callback_url` | string | No          | URL para notificar el resultado (opcional)     |

### Configuración del Agente (Lado Servidor)

Los detalles de configuración se mueven a un fichero YAML en el servidor:

```yaml
# src/backoffice/config/agents.yaml
agents:
  ValidadorDocumental:
    description: "Valida documentación administrativa"
    model: "claude-3-5-sonnet-20241022"
    system_prompt: |
      Eres un agente especializado en validar documentación administrativa.
      Tu trabajo es verificar que todos los documentos requeridos están presentes,
      son válidos y cumplen con los requisitos legales.
    tools:
      - consultar_expediente
      - actualizar_datos
      - añadir_anotacion
    timeout_seconds: 300

  AnalizadorSubvencion:
    description: "Analiza solicitudes de subvención"
    model: "claude-3-5-sonnet-20241022"
    system_prompt: |
      Eres un agente especializado en analizar solicitudes de subvención.
      Tu trabajo es evaluar si la solicitud cumple los requisitos formales.
    tools:
      - consultar_expediente
      - calcular_puntuacion
      - generar_informe
    timeout_seconds: 600

  GeneradorInforme:
    description: "Genera informes técnicos"
    model: "claude-3-5-sonnet-20241022"
    system_prompt: |
      Eres un agente especializado en generar informes técnicos.
    tools:
      - consultar_expediente
      - generar_documento
    timeout_seconds: 300
```

---

## Comparativa: Antes vs Después

### Antes (Invocación Actual)

```bash
curl -X POST http://localhost:8080/api/v1/agent/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "expediente_id": "EXP-2024-001",
    "tarea_id": "TAREA-VALIDAR-DOC",
    "agent_config": {
      "nombre": "ValidadorDocumental",
      "system_prompt": "Eres un validador de documentación administrativa...",
      "modelo": "claude-3-5-sonnet-20241022",
      "prompt_tarea": "Valida que todos los documentos estén presentes",
      "herramientas": ["consultar_expediente", "actualizar_datos", "añadir_anotacion"]
    },
    "webhook_url": "https://bpmn.example.com/callback",
    "timeout_seconds": 300
  }'
```

### Después (Invocación Simplificada)

```bash
curl -X POST http://localhost:8080/api/v1/agent/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "ValidadorDocumental",
    "prompt": "Valida los documentos del expediente y verifica el NIF del solicitante",
    "context": {
      "expediente_id": "EXP-2024-001",
      "tarea_id": "TAREA-VALIDAR-DOC"
    },
    "callback_url": "https://bpmn.example.com/callback"
  }'
```

---

## Beneficios de la Simplificación

| Aspecto                    | Antes                                          | Después                              |
| -------------------------- | ---------------------------------------------- | ------------------------------------ |
| **Campos obligatorios**    | 7 campos anidados                              | 3 campos principales                 |
| **Conocimiento requerido** | BPMN debe conocer modelo, tools, system_prompt | BPMN solo conoce nombre del agente   |
| **Configuración**          | En cada invocación                             | Centralizada en YAML                 |
| **Mantenimiento**          | Cambiar modelo requiere modificar BPMN         | Cambiar modelo es transparente       |
| **Acoplamiento**           | Alto (BPMN ↔ Implementación)                   | Bajo (BPMN → Contrato)               |

---

## Cambios Necesarios

### 1. Nuevo Modelo de Request (API)

```python
# src/api/models.py
class ExecuteAgentRequest(BaseModel):
    """Request simplificado para invocar un agente"""
    agent: str = Field(..., description="Nombre del agente a ejecutar")
    prompt: str = Field(..., description="Instrucciones específicas para esta ejecución")
    context: AgentContext = Field(..., description="Contexto de ejecución")
    callback_url: Optional[HttpUrl] = Field(None, description="URL de callback opcional")

class AgentContext(BaseModel):
    """Contexto mínimo para la ejecución"""
    expediente_id: str = Field(..., description="ID del expediente")
    tarea_id: str = Field(..., description="ID de la tarea BPMN")
```

### 2. Cargador de Configuración de Agentes

```python
# src/backoffice/config/agent_config_loader.py
class AgentConfigLoader:
    """Carga configuración de agentes desde YAML"""

    def load(self, agent_name: str) -> AgentDefinition:
        """Carga la definición de un agente por nombre"""
        pass

    def list_agents(self) -> List[str]:
        """Lista los agentes disponibles"""
        pass
```

### 3. Modificar Endpoint Existente

```python
# src/api/routers/agent.py
@router.post("/execute", response_model=ExecuteAgentResponse)
async def execute_agent(request: ExecuteAgentRequest, ...):
    """Endpoint simplificado para invocar agentes"""
    # Cargar configuración del agente desde YAML
    agent_config = agent_config_loader.load(request.agent)

    # Combinar prompt del usuario con system_prompt del YAML
    # Ejecutar agente con la configuración cargada
    pass
```

### 4. Endpoint para Listar Agentes Disponibles

```python
# src/api/routers/agent.py
@router.get("/agents", response_model=ListAgentsResponse)
async def list_agents():
    """Lista los agentes disponibles y sus descripciones"""
    pass
```

---

## Endpoint Adicional: Descubrimiento de Agentes

### GET /api/v1/agent/agents

Permite al BPMN descubrir qué agentes están disponibles:

```json
{
  "agents": [
    {
      "name": "ValidadorDocumental",
      "description": "Valida documentación administrativa",
      "required_permissions": ["expediente.lectura", "expediente.escritura"]
    },
    {
      "name": "AnalizadorSubvencion",
      "description": "Analiza solicitudes de subvención",
      "required_permissions": ["expediente.lectura", "subvencion.analisis"]
    },
    {
      "name": "GeneradorInforme",
      "description": "Genera informes técnicos",
      "required_permissions": ["expediente.lectura", "documento.escritura"]
    }
  ]
}
```

---

## Plan de Implementación

### Fase 1: Preparación

- [ ] Crear fichero `agents.yaml` con configuración de agentes
- [ ] Implementar `AgentConfigLoader` para leer el YAML
- [ ] Añadir tests unitarios para el loader

### Fase 2: Modificar API

- [ ] Modificar modelos Pydantic (`ExecuteAgentRequest`, `AgentContext`)
- [ ] Actualizar endpoint `POST /api/v1/agent/execute`
- [ ] Implementar endpoint `GET /api/v1/agent/agents`
- [ ] Añadir tests de integración

### Fase 3: Integración

- [ ] Modificar `AgentExecutor` para usar la nueva configuración
- [ ] Actualizar el Panel de Pruebas del frontend
- [ ] Actualizar documentación

### Fase 4: Validación

- [ ] Tests E2E con el nuevo flujo
- [ ] Verificar que el frontend del dashboard funciona correctamente
- [ ] Actualizar ejemplos en documentación
