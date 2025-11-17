# MCP Mock de Expedientes

Servidor MCP (Model Context Protocol) mock para simular el acceso a expedientes de GEX en el proyecto aGEntiX.

## Descripción

Este servidor implementa el protocolo MCP oficial para proporcionar acceso simulado a expedientes administrativos, permitiendo:

- Desarrollo y testing de agentes IA sin necesidad del sistema GEX real
- Validación del modelo de permisos basado en JWT
- Pruebas de integración con múltiples transportes (stdio y HTTP/SSE)
- Persistencia en JSON para simplicidad y transparencia

## Características

✅ Protocolo MCP 1.0 oficial
✅ Doble transporte: stdio y HTTP/SSE
✅ Autenticación JWT con validación completa
✅ Modelo de permisos de lectura/escritura
✅ Resources MCP (lectura pasiva)
✅ Tools MCP (acciones con efectos secundarios)
✅ Persistencia en JSON
✅ Suite completa de tests
✅ Compatibilidad con Claude Desktop

## Instalación

### Requisitos

- Python 3.10 o superior
- pip (gestor de paquetes Python)

### Pasos

1. **Clonar el repositorio** (si aún no lo has hecho):
   ```bash
   git clone <repo-url>
   cd aGEntiX/mcp-mock/mcp-expedientes
   ```

2. **Crear entorno virtual** (recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**:
   ```bash
   export JWT_SECRET="test-secret-key"
   ```

## Uso

### 1. Transporte stdio (para Claude Desktop)

El transporte stdio es ideal para desarrollo con Claude Desktop:

```bash
# Generar token JWT
export MCP_JWT_TOKEN=$(python generate_token.py --exp-id EXP-2024-001 --formato raw)
export JWT_SECRET="test-secret-key"

# Ejecutar servidor
python server_stdio.py
```

**Configuración para Claude Desktop** (`~/.config/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "gex-expedientes": {
      "command": "python",
      "args": ["/ruta/absoluta/a/server_stdio.py"],
      "env": {
        "MCP_JWT_TOKEN": "eyJhbGc...",
        "JWT_SECRET": "test-secret-key"
      }
    }
  }
}
```

### 2. Transporte HTTP/SSE (para testing manual)

El transporte HTTP es ideal para pruebas manuales con curl/Postman:

```bash
# Ejecutar servidor HTTP
uvicorn server_http:app --reload --host 0.0.0.0 --port 8000
```

**Testing con curl**:

```bash
# Health check
curl http://localhost:8000/health

# Generar token
TOKEN=$(python generate_token.py --exp-id EXP-2024-001 --formato raw)

# Listar tools
curl -X POST http://localhost:8000/sse \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'

# Ejecutar tool
curl -X POST http://localhost:8000/sse \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "consultar_expediente",
      "arguments": {"expediente_id": "EXP-2024-001"}
    }
  }'
```

### 3. Simulador BPMN

Para simular la invocación desde el motor BPMN:

```bash
# Simulación básica
python simulate_bpmn.py --exp-id EXP-2024-001

# Con permisos específicos
python simulate_bpmn.py --exp-id EXP-2024-001 --permisos consulta

# Para múltiples MCP servers
python simulate_bpmn.py --exp-id EXP-2024-001 \
  --mcp-servers agentix-mcp-expedientes agentix-mcp-normativa
```

## Expedientes de Prueba

El servidor incluye 3 expedientes de ejemplo:

| ID | Tipo | Estado | Descripción |
|----|------|--------|-------------|
| `EXP-2024-001` | SUBVENCIONES | EN_TRAMITE | Solicitud de ayuda para local comercial |
| `EXP-2024-002` | LICENCIA_OBRA | PENDIENTE_DOCUMENTACION | Licencia de obra menor |
| `EXP-2024-003` | CERTIFICADO_EMPADRONAMIENTO | ARCHIVADO | Certificado emitido |

## Resources MCP

Los resources exponen información para lectura pasiva:

| URI | Descripción |
|-----|-------------|
| `expediente://{id}` | Información completa del expediente |
| `expediente://{id}/documentos` | Lista de documentos |
| `expediente://{id}/documento/{doc_id}` | Documento específico |
| `expediente://{id}/historial` | Historial de acciones |

## Tools MCP

### Tools de Lectura (requieren permiso `consulta`)

- **`consultar_expediente(expediente_id)`**: Obtiene información completa del expediente
- **`listar_documentos(expediente_id)`**: Lista todos los documentos
- **`obtener_documento(expediente_id, documento_id)`**: Obtiene un documento específico

### Tools de Escritura (requieren permiso `gestion`)

- **`añadir_documento(expediente_id, nombre, tipo, contenido)`**: Añade un nuevo documento
- **`actualizar_datos(expediente_id, campo, valor)`**: Actualiza un campo del expediente
- **`añadir_anotacion(expediente_id, texto)`**: Añade una anotación al historial

## Autenticación y Permisos

### Generación de Tokens

```bash
# Token con permisos de lectura
python generate_token.py --exp-id EXP-2024-001 --permisos consulta

# Token con permisos de lectura y escritura
python generate_token.py --exp-id EXP-2024-001 --permisos consulta gestion

# Token con expiración personalizada (24 horas)
python generate_token.py --exp-id EXP-2024-001 --exp-hours 24

# Solo el token (útil para scripts)
python generate_token.py --exp-id EXP-2024-001 --formato raw
```

### Claims JWT

El token JWT incluye los siguientes claims:

```json
{
  "sub": "Automático",
  "iss": "agentix-bpmn",
  "aud": ["agentix-mcp-expedientes"],
  "exp_id": "EXP-2024-001",
  "exp_tipo": "SUBVENCIONES",
  "tarea_id": "TAREA-VALIDAR-DOC-001",
  "tarea_nombre": "VALIDAR_DOCUMENTACION",
  "permisos": ["consulta", "gestion"]
}
```

### Validación

El servidor valida:

1. ✅ Firma JWT correcta
2. ✅ Token no expirado
3. ✅ Not before válido
4. ✅ Audiencia correcta (soporta multi-MCP)
5. ✅ Subject = "Automático"
6. ✅ Acceso al expediente autorizado
7. ✅ Permisos suficientes para la operación

## Testing

### Ejecutar tests

```bash
# Todos los tests
pytest

# Tests específicos
pytest tests/test_auth.py
pytest tests/test_tools.py
pytest tests/test_resources.py

# Con verbose
pytest -v

# Con coverage
pytest --cov=. --cov-report=html
```

### Test Cases Implementados

**Autenticación (TC-AUTH-001 a TC-AUTH-006)**:
- Token válido con permisos consulta
- Token válido con permisos gestión
- Token expirado
- Firma inválida
- Acceso a expediente no autorizado
- Usuario no automático

**Permisos (TC-PERM-001 a TC-PERM-002)**:
- Escritura sin permiso gestión
- Lectura con solo permiso consulta

**Resources (TC-RES-001 a TC-RES-003)**:
- Expediente completo
- Lista de documentos
- Historial

**Tools (TC-TOOL-001 a TC-TOOL-007)**:
- Consultar expediente
- Listar documentos
- Obtener documento específico
- Obtener documento inexistente
- Añadir documento
- Actualizar datos
- Añadir anotación

## Estructura del Proyecto

```
mcp-expedientes/
├── server.py              # Servidor core (agnóstico de transporte)
├── server_stdio.py        # Transporte stdio
├── server_http.py         # Transporte HTTP/SSE
├── auth.py                # Validación JWT
├── models.py              # Modelos de datos Pydantic
├── resources.py           # Implementación de resources MCP
├── tools.py               # Implementación de tools MCP
├── generate_token.py      # Generador de tokens JWT
├── simulate_bpmn.py       # Simulador BPMN
├── requirements.txt       # Dependencias Python
├── data/
│   └── expedientes/       # Expedientes JSON
│       ├── EXP-2024-001.json
│       ├── EXP-2024-002.json
│       └── EXP-2024-003.json
└── tests/
    ├── conftest.py        # Configuración de pytest
    ├── test_auth.py       # Tests de autenticación
    ├── test_tools.py      # Tests de tools
    ├── test_resources.py  # Tests de resources
    └── fixtures/
        └── tokens.py      # Fixtures de tokens JWT
```

## Troubleshooting

### Error: "Token JWT no proporcionado"

Asegúrate de configurar la variable de entorno `MCP_JWT_TOKEN`:

```bash
export MCP_JWT_TOKEN=$(python generate_token.py --exp-id EXP-2024-001 --formato raw)
```

### Error: "JWT_SECRET no configurado"

Configura la variable de entorno `JWT_SECRET`:

```bash
export JWT_SECRET="test-secret-key"
```

### Error: "Expediente no encontrado"

Verifica que el expediente existe en `data/expedientes/`:

```bash
ls data/expedientes/
```

### Tests fallan

Asegúrate de que el directorio de trabajo es correcto y que todas las dependencias están instaladas:

```bash
cd mcp-mock/mcp-expedientes
pip install -r requirements.txt
pytest
```

## Próximos Pasos

Este es el primer servidor MCP del proyecto aGEntiX. Próximos servidores planificados:

- **MCP de Normativa**: Acceso a normativa (BOE, BOJA, ordenanzas)
- **MCP de Generación de Documentos**: Generación de PDFs desde plantillas

## Referencias

- [Especificación MCP](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Documentación aGEntiX](../../doc/index.md)
- [Acceso vía MCP](../../doc/042-acceso-mcp.md)
- [Permisos de agente](../../doc/050-permisos-agente.md)

## Licencia

Este proyecto forma parte de aGEntiX y está sujeto a la misma licencia.
