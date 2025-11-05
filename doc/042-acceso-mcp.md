# Acceso a Información y Herramientas vía MCP

## Model Context Protocol (MCP)

El acceso a la información y las herramientas se realiza mediante el **Model Context Protocol**.

## Ventajas del Uso de MCP

- Desacoplamiento entre agentes y GEX
- Estandarización del acceso a información
- Facilita la seguridad y el control de permisos
- Permite evolución independiente de componentes

## Flujo de Acceso

```
Agente → MCP → API de GEX
```

## Relaciones

- Ver: [Principios arquitectónicos](040-criterios-diseño.md)
- Ver: [Información accesible](032-contexto-agente.md)
- Ver: [Propagación de permisos](052-propagacion-permisos.md)
- Ver: [Herramientas disponibles](031-configuracion-agente.md)
