# Propagación de Permisos en el Sistema

## Cadena de Propagación

Los permisos deben propagarse a través de toda la cadena de acceso:

```
Agente → MCP → API
```

## Funcionamiento

1. El **Agente** tiene permisos configurados
2. Estos permisos se propagan al **MCP**
3. El **MCP** los propaga a las llamadas al **API de GEX**

## Importancia

Esta propagación garantiza que:
- Los agentes no puedan realizar acciones no autorizadas
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
