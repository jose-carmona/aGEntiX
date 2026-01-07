# Servidor MCP Mock

## Propósito

Durante la fase de construcción de aGEntiX, se utiliza un **servidor MCP mock unificado** que simula el acceso a datos reales de GEX. Esto permite:

- Desarrollar y probar agentes sin depender del sistema GEX real
- Iterar rápidamente en la lógica de los agentes
- Validar la arquitectura MCP antes de la integración final
- Demostrar capacidades sin exponer datos reales

## Arquitectura Unificada

El servidor MCP mock unifica dos módulos en un único puerto (8000):

```
src/mcp_mock/
├── auth.py                     # Autenticación JWT compartida
├── models.py                   # Modelos Pydantic compartidos
├── README.md                   # Documentación del servidor
│
├── data/                       # Datos mock compartidos
│   ├── expedientes/            # Expedientes individuales (JSON)
│   │   ├── EXP-2024-001.json
│   │   ├── EXP-2024-002.json
│   │   └── EXP-2024-003.json
│   └── documentos/             # Documentación por tipo de expediente
│       ├── subvenciones/
│       ├── licencias_obras/
│       └── certificado_empadronamiento/
│
├── mcp_expedientes/            # Módulo de Expedientes
│   ├── server_http.py          # Servidor HTTP unificado
│   ├── tools.py                # Tools de expedientes
│   └── resources.py            # Resources de expedientes
│
└── mcp_documentacion/          # Módulo de Documentación
    ├── tools.py                # Tools de documentación
    ├── resources.py            # Resources de documentación
    └── data_loader.py          # Carga de documentos JSON/MD
```

## Módulos Disponibles

### Módulo: Expedientes

Gestión de expedientes administrativos individuales.

| Tool | Permiso | Descripción |
|------|---------|-------------|
| `consultar_expediente` | `consulta` | Información completa del expediente |
| `listar_documentos` | `consulta` | Lista de documentos del expediente |
| `obtener_documento` | `consulta` | Documento específico |
| `añadir_documento` | `gestion` | Añadir nuevo documento |
| `actualizar_datos` | `gestion` | Actualizar campos del expediente |
| `añadir_anotacion` | `gestion` | Añadir anotación al historial |

### Módulo: Documentación

Acceso a normativa, instrucciones y plantillas por tipo de expediente.

| Tool | Permiso | Descripción |
|------|---------|-------------|
| `listar_documentacion` | `documentacion:leer` | Lista documentos por tipo |
| `obtener_doc_documentacion` | `documentacion:leer` | Contenido completo del documento |
| `buscar_en_documentacion` | `documentacion:buscar` | Buscar texto en documentación |

## Diferencias con MCP Real

| Aspecto | MCP Mock | MCP Real (futuro) |
|---------|----------|-------------------|
| Datos | Ficticios, generados por LLM | Datos reales de GEX |
| Autenticación | JWT simplificado | Integración con SSO corporativo |
| Persistencia | Archivos JSON/MD | Base de datos GEX |
| Rendimiento | Sin optimizar | Optimizado para producción |
| Validaciones | Básicas | Completas según normativa |

## Uso en Desarrollo

```bash
# Configurar secreto JWT
export JWT_SECRET="test-secret-key"

# Iniciar servidor unificado (puerto 8000)
cd src/mcp_mock/mcp_expedientes
python -m uvicorn server_http:app --reload --port 8000

# Generar token de prueba (con todos los permisos)
python -m generate_token EXP-2024-001 \
  --permisos consulta gestion documentacion:leer documentacion:buscar

# Verificar health
curl http://localhost:8000/health
```

## Aviso Importante

> **Los datos mock son ficticios**, generados por LLM con fines de desarrollo.
> No deben utilizarse como referencia legal ni en producción.

## Relaciones

- Ver: [Acceso a información vía MCP](042-acceso-mcp.md)
- Ver: [Datos Mock disponibles](081-datos-mock.md)
- Ver: [MCP Documentación de Expedientes](070-mcp-documentacion-expedientes.md)
