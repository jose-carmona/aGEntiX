# Construcción de Servicios MCP Mock para aGEntiX

## Contexto

El proyecto se centra en la ejecución de agentes IA.

Los agentes interactúan con GEX mediante MCP (Model Context Protocol).

Para construir dichos agentes necesitamos servicios MCP.

Vamos a construir una serie de servicios mock en los que nos apoyaremos más adelante en la construcción de los agentes y en las pruebas.

## Tecnologías

Para la construcción de los servicios MCP mock nos vamos a basar en **Python**.

Simularemos los expedientes mediante **ficheros JSON**.

El MCP no será más que una capa sobre un API construido sobre **Python Flask**.

## Objetivos

Crear un servidor MCP mock que:

1. **Simule el acceso a GEX** sin necesidad de conectar con el sistema real
2. **Permita pruebas** de agentes IA durante el desarrollo
3. **Implemente el modelo de permisos** basado en JWT
4. **Proporcione herramientas (tools)** de lectura y escritura sobre expedientes
5. **Valide la propagación de permisos** según la arquitectura del sistema

## Arquitectura

```
BPMN (simulado) → Agente → MCP Mock → Datos JSON
```

El MCP Mock debe:
- Validar tokens JWT con los claims: usuario "Automático" y ID de expediente
- Verificar permisos antes de cada operación
- Exponer resources y tools según la especificación MCP
- Mantener el estado en ficheros JSON

## Modelo de Datos

Cada expediente será un fichero JSON que contenga:

### Estructura del Expediente

```json
{
  "id": "EXP-2024-001",
  "tipo": "SUBVENCIONES",
  "estado": "EN_TRAMITE",
  "fecha_inicio": "2024-01-15",
  "datos": {
    "solicitante": {
      "nombre": "...",
      "nif": "...",
      "direccion": "..."
    },
    "importe_solicitado": 5000.00,
    "concepto": "..."
  },
  "documentos": [
    {
      "id": "DOC-001",
      "nombre": "solicitud.pdf",
      "fecha": "2024-01-15",
      "tipo": "SOLICITUD",
      "ruta": "path/to/file.pdf"
    }
  ],
  "historial": [
    {
      "fecha": "2024-01-15",
      "usuario": "Automático",
      "accion": "INICIAR_EXPEDIENTE",
      "detalles": "..."
    }
  ],
  "metadatos": {
    "tarea_actual": "VALIDAR_DOCUMENTACION",
    "responsable": "Automático"
  }
}
```

## Recursos MCP (Resources)

El servidor MCP debe exponer:

1. **expediente://{id}** - Información completa del expediente
2. **expediente://{id}/documentos** - Lista de documentos
3. **expediente://{id}/documento/{doc_id}** - Documento específico
4. **expediente://{id}/historial** - Historial de acciones

## Herramientas MCP (Tools)

### Herramientas de Lectura

1. **consultar_expediente(expediente_id)**
   - Retorna toda la información del expediente
   - Requiere: permiso de consulta

2. **obtener_documento(expediente_id, documento_id)**
   - Retorna un documento específico
   - Requiere: permiso de consulta

3. **listar_documentos(expediente_id)**
   - Lista todos los documentos del expediente
   - Requiere: permiso de consulta

### Herramientas de Escritura

1. **añadir_documento(expediente_id, nombre, tipo, contenido)**
   - Añade un nuevo documento al expediente
   - Requiere: permiso de gestión
   - Registra en historial

2. **actualizar_datos(expediente_id, campo, valor)**
   - Actualiza un campo de datos del expediente
   - Requiere: permiso de gestión
   - Registra en historial

3. **añadir_anotacion(expediente_id, texto)**
   - Añade una anotación al historial
   - Requiere: permiso de gestión
   - Registra en historial

## Sistema de Permisos

### JWT Claims Requeridos

```json
{
  "sub": "Automático",
  "exp_id": "EXP-2024-001",
  "permisos": ["consulta"] // o ["consulta", "gestion"]
}
```

### Validación

El MCP debe:
1. Validar la firma del JWT
2. Verificar que el expediente solicitado coincide con `exp_id`
3. Verificar que el usuario es "Automático"
4. Comprobar que el permiso requerido está presente

### Respuestas de Error

- **401**: Token inválido o expirado
- **403**: Permiso insuficiente
- **404**: Expediente o documento no encontrado
- **422**: Operación no válida en el estado actual

## Implementación Técnica

### Estructura del Proyecto

```
mcp-mock/
├── server.py           # Servidor Flask + MCP
├── auth.py             # Validación de JWT
├── models.py           # Modelos de datos
├── tools.py            # Implementación de tools
├── resources.py        # Implementación de resources
├── data/
│   └── expedientes/    # Ficheros JSON de expedientes
└── tests/
    └── test_*.py       # Tests unitarios
```

### Dependencias Python

- `flask` - API REST
- `pyjwt` - Validación de tokens
- `mcp` - Librería oficial del Model Context Protocol
- `pytest` - Testing

### Generación de Tokens de Prueba

Crear un script `generate_token.py` que permita generar tokens JWT válidos para testing con diferentes permisos y expedientes.

## Datos de Prueba

Crear al menos 3 expedientes de ejemplo:

1. **EXP-2024-001**: Expediente de subvenciones (estado: en trámite)
2. **EXP-2024-002**: Expediente de licencia (estado: pendiente documentación)
3. **EXP-2024-003**: Expediente completado (estado: archivado)

Cada uno con:
- Datos completos
- Al menos 3 documentos
- Historial de acciones
- Diferentes tipos de datos para probar extracción

## Criterios de Aceptación

El MCP mock debe:

- [ ] Implementar la especificación MCP correctamente
- [ ] Validar tokens JWT en cada petición
- [ ] Exponer todos los resources definidos
- [ ] Implementar todas las tools (lectura y escritura)
- [ ] Rechazar accesos a expedientes no autorizados
- [ ] Registrar todas las acciones en el historial
- [ ] Incluir tests unitarios para cada tool
- [ ] Proporcionar documentación de uso
- [ ] Incluir script de generación de tokens
- [ ] Mantener persistencia en JSON entre reinicios

## Referencias

- [Especificación MCP](https://modelcontextprotocol.io/)
- [Acceso vía MCP](../042-acceso-mcp.md)
- [Permisos de agente](../050-permisos-agente.md)
- [Propagación de permisos](../052-propagacion-permisos.md)
- [Contexto del agente](../032-contexto-agente.md)