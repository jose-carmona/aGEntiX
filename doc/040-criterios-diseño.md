# Criterios de Diseño Arquitectónico

Los principios fundamentales del diseño de aGEntiX son:

## 1. No Acoplamiento, No Intrusión
Los agentes IA no deben estar acoplados a GEX. El sistema debe poder funcionar sin los agentes y los agentes deben poder actualizarse independientemente.

## 2. Modularidad
Los componentes deben ser modulares e independientemente desplegables.

## 3. Acceso vía MCP
La información y las herramientas se acceden mediante el **Model Context Protocol (MCP)**.

## Implicaciones

Estos criterios garantizan:
- Flexibilidad en la evolución del sistema
- Facilidad de mantenimiento
- Posibilidad de reemplazar o actualizar componentes
- Independencia entre GEX y el sistema de agentes

## Relaciones

- Ver: [Acceso mediante MCP](042-acceso-mcp.md)
- Ver: [Propuesta de agentes](030-propuesta-agentes.md)
