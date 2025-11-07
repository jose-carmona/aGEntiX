# Propagación de Permisos en el Sistema

## Cadena de Propagación

Los permisos deben propagarse a través de toda la cadena de acceso:

```
BPMN → Agente → MCP → API → GEX
```

## Funcionamiento

1. El sistema BPMN inicia un token JWT con los siguientes claims:
   1. Usuario "Automático"
   2. Expediente concreto
2. El API del sistema de agentes valida la integridad del token JWT y que tienen los claims obligatorios
3. El **Agente** tiene permisos configurados sobre herramientas concretas a las que accede por MCP
4. El token JWT se propaga al **MCP**
5. El **MCP**, a su vez, propaga el token a las llamadas al **API de GEX**
6. El **API de GEX** valida el JWT y llama a nucleo de **GEX** usando el usuario pasado ("Automático")
7. **GEX** comprueba los permisos del usuario para el Expediente concreto

## Importancia

Esta propagación garantiza que:
- Los agentes no puedan realizar acciones no autorizadas
- Los agentes no pueden acceder a otros expedientes
- El sistema de seguridad es coherente en todos los niveles
- Las restricciones se aplican de forma consistente

## Implementación

Cada capa del sistema debe:
- Recibir la información de permisos
- Validar que la acción solicitada está permitida
- Pasar la información de permisos a la siguiente capa

## Relaciones

- Ver: [Permisos del agente](050-permisos-agente.md)
- Ver: [Acceso vía MCP](042-acceso-mcp.md)
- Ver: [APIs integradas](004-integraciones.md)
