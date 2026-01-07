# Servidor MCP Mock

## Propósito

Durante la fase de construcción de aGEntiX, se utiliza un **servidor MCP mockeado** que simula el acceso a datos reales de GEX. Esto permite:

- Desarrollar y probar agentes sin depender del sistema GEX real
- Iterar rápidamente en la lógica de los agentes
- Validar la arquitectura MCP antes de la integración final
- Demostrar capacidades sin exponer datos reales

## Ubicación

```
src/mcp_mock/
├── mcp_expedientes/        # MCP de expedientes (existente)
│   ├── server_http.py
│   ├── auth.py
│   └── data/
│       └── expedientes.json
│
├── mcp_documentacion/      # MCP de documentación (por implementar)
│   ├── server_http.py
│   ├── tools.py
│   └── resources.py
│
└── data/                   # Datos mock compartidos
    └── documentos/         # Documentación por tipo de expediente
        ├── subvenciones/
        ├── licencias_obras/
        └── certificado_empadronamiento/
```

## Diferencias con MCP Real

| Aspecto | MCP Mock | MCP Real (futuro) |
|---------|----------|-------------------|
| Datos | Ficticios, generados por LLM | Datos reales de GEX |
| Autenticación | JWT simplificado | Integración con SSO corporativo |
| Persistencia | Archivos JSON/MD | Base de datos GEX |
| Rendimiento | Sin optimizar | Optimizado para producción |
| Validaciones | Básicas | Completas según normativa |

## Servidores MCP Mock Disponibles

| ID | Puerto | Descripción | Estado |
|----|--------|-------------|--------|
| `expedientes` | 8000 | Datos de expedientes | ✅ Implementado |
| `documentacion` | 8001 | Normativa, instrucciones, plantillas | 🚧 Por implementar |

## Uso en Desarrollo

```bash
# Iniciar MCP de expedientes
cd src/mcp_mock/mcp_expedientes
python -m uvicorn server_http:app --reload --port 8000

# Generar token de prueba
python -m generate_token EXP-2024-001
```

## Aviso Importante

> **Los datos mock son ficticios**, generados por LLM con fines de desarrollo.
> No deben utilizarse como referencia legal ni en producción.

## Relaciones

- Ver: [Acceso a información vía MCP](042-acceso-mcp.md)
- Ver: [Datos Mock disponibles](081-datos-mock.md)
- Ver: [MCP Documentación de Expedientes](070-mcp-documentacion-expedientes.md)
