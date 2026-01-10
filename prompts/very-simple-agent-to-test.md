# Agente Simple de Prueba E2E

## Objetivo

Crear un agente extremadamente simple que sirva para pruebas E2E (end-to-end) del sistema.

El agente debe probar que:
1. Funciona el API REST
2. Funciona la carga de agentes desde `agents.yaml`
3. Se invoca correctamente el agente CrewAI
4. El agente responde y devuelve un resultado

## Comportamiento del Agente

**Acción:** El agente simplemente responde "OK".

No realiza ninguna tarea compleja, no llama a herramientas MCP, no analiza datos. Solo devuelve la respuesta "OK" para confirmar que todo el pipeline funciona correctamente.

## Configuración

Añadir al archivo `src/backoffice/config/agents.yaml`:

```yaml
  # ==========================================================================
  # AgenteTestSimple - Agente de prueba E2E (solo responde OK)
  # ==========================================================================

  AgenteTestSimple:
    type: crewai
    enabled: true
    description: "Agente de prueba E2E - solo responde OK"

    llm:
      provider: anthropic
      model: claude-3-haiku-20240307
      max_tokens: 100
      temperature: 0

    crewai_agent:
      role: "Agente de Prueba"
      goal: "Responder OK para confirmar que el sistema funciona"
      backstory: |
        Eres un agente de prueba. Tu única función es responder "OK"
        para verificar que el sistema de ejecución de agentes funciona correctamente.
      verbose: false
      allow_delegation: false

    crewai_task:
      description: |
        Responde exactamente "OK" para confirmar que el sistema funciona.
        No hagas nada más. Solo responde OK.
      expected_output: |
        OK

    tools: []

    required_permissions: []
    timeout_seconds: 30
```

## Uso con test-agent.sh

```bash
# Ejecutar el agente de prueba
./test-agent.sh EXP-2024-001 AgenteTestSimple

# O con valores personalizados
./test-agent.sh MI-EXPEDIENTE AgenteTestSimple MI-TAREA
```

## Resultado Esperado

```json
{
  "status": "completed",
  "success": true,
  "result": {
    "raw": "OK",
    "pydantic": null
  }
}
```

## Casos de Uso

- **Prueba de despliegue:** Verificar que el sistema arranca correctamente
- **Prueba de conectividad:** Confirmar que API y agentes se comunican
- **Prueba de pipeline:** Validar el flujo completo sin dependencias externas
- **Health check avanzado:** Verificación más completa que `/health`
- **Debugging:** Aislar problemas de infraestructura vs. lógica de agentes

## Ventajas

| Característica | Beneficio |
|----------------|-----------|
| Sin herramientas MCP | No requiere servidores MCP activos |
| Sin permisos | No requiere JWT con permisos específicos |
| Respuesta inmediata | Timeout muy bajo (30s) |
| Modelo pequeño | Usa Haiku para mínimo coste/latencia |
| Determinístico | Temperature 0 para respuesta consistente |
