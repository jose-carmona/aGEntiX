# Fix: Validación Temprana de JWT en Servidor MCP HTTP

**Fecha:** 2025-11-30
**Prioridad:** CRÍTICA
**Relacionado con:** Corrección del CRÍTICO 2 en `step-1-critique.md`

---

## Problema Identificado

El servidor MCP HTTP actual (`/mcp-mock/mcp-expedientes/server_http.py`) **extrae** correctamente el token JWT del header `Authorization: Bearer <token>`, pero **NO lo valida inmediatamente**.

### Comportamiento Actual (Incorrecto)

```python
# server_http.py líneas 78-85
async def handle_sse(request: Request) -> Response:
    # Extraer token del header Authorization
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        context.set_token(token)
        logger.info(f"Token JWT recibido (primeros 20 chars): {token[:20]}...")
    else:
        logger.warning("No se recibió token JWT en el header Authorization")

    # ⚠️ PROBLEMA: Continúa procesando aunque no haya token o sea inválido
    # La validación ocurre después en cada handler de server.py
```

### Consecuencias del Defecto

1. **Fail-slow en lugar de fail-fast:**
   - Requests sin token se procesan parcialmente hasta que un handler intenta validar
   - Desperdicia recursos del servidor procesando requests que fallarán

2. **Mensajes de error inconsistentes:**
   - Error de autenticación puede aparecer en diferentes puntos del flujo
   - Dificulta debugging y logs de auditoría

3. **Seguridad:**
   - Aunque eventualmente se rechaza, permite que código no autorizado se ejecute parcialmente
   - El transporte SSE podría iniciarse antes de validar credenciales

4. **Incompatibilidad con clientes HTTP estándar:**
   - Clientes HTTP esperan recibir `401 Unauthorized` inmediatamente si el token es inválido
   - No después de establecer conexión SSE

---

## Solución Requerida

### 1. Validar JWT Inmediatamente en el Endpoint HTTP

Modificar `server_http.py` para validar el token **antes** de procesar la request MCP.

#### Código a Modificar

**Archivo:** `/mcp-mock/mcp-expedientes/server_http.py`

**Función:** `handle_sse()`

**Cambio requerido:**

```python
async def handle_sse(request: Request) -> Response:
    """
    Endpoint SSE para comunicación MCP.

    El token JWT se extrae del header Authorization y se valida
    INMEDIATAMENTE antes de procesar cualquier request MCP.

    Args:
        request: Petición HTTP

    Returns:
        Respuesta SSE o error 401/403

    Raises:
        HTTPException: Si el token es inválido o no está presente
    """
    from starlette.exceptions import HTTPException

    # 1. Extraer token del header Authorization
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        logger.warning("Request sin token JWT en header Authorization")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "AUTH_INVALID_TOKEN",
                "message": "Se requiere token JWT en header Authorization: Bearer <token>"
            }
        )

    token = auth_header[7:]  # Extraer token (quitar "Bearer ")

    # 2. VALIDAR TOKEN INMEDIATAMENTE (CAMBIO PRINCIPAL)
    try:
        from auth import validate_jwt

        # Validación básica del token (firma, expiración, claims obligatorios)
        # No validamos expediente_id ni tool específica aquí, eso se hace en cada handler
        await validate_jwt(token, server_id=context.server_id)

        logger.info(f"✅ Token JWT válido recibido (primeros 20 chars): {token[:20]}...")

    except AuthError as e:
        logger.warning(f"❌ Token JWT inválido: {e.message}")
        raise HTTPException(
            status_code=e.status_code,  # 401 o 403 según el error
            detail={
                "error": "AUTH_INVALID_TOKEN" if e.status_code == 401 else "AUTH_PERMISSION_DENIED",
                "message": e.message
            }
        )
    except Exception as e:
        logger.error(f"Error inesperado al validar token: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "Error interno al validar token JWT"
            }
        )

    # 3. Almacenar token en contexto (solo si es válido)
    context.set_token(token)

    # 4. Procesar request MCP (solo si token es válido)
    sse = SseServerTransport("/messages")

    async with sse.connect_sse(
        request.scope,
        request.receive,
        request._send
    ) as streams:
        await app_core.run(
            streams[0],
            streams[1],
            app_core.create_initialization_options()
        )

    return Response()
```

### 2. Añadir Import Necesario

Al inicio del archivo `server_http.py`, añadir:

```python
from starlette.exceptions import HTTPException
from auth import validate_jwt, AuthError
```

### 3. Actualizar Comentarios de Uso

Actualizar los ejemplos de uso en el docstring del archivo para documentar los posibles errores:

```python
"""
...

Testing manual con curl:
    # Health check
    curl http://localhost:8000/health

    # Generar token
    TOKEN=$(python generate_token.py --exp-id EXP-2024-001 --formato raw)

    # Listar tools (con token válido)
    curl -X POST http://localhost:8000/sse \\
      -H "Authorization: Bearer $TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

    # Ejemplo de error 401 (sin token)
    curl -X POST http://localhost:8000/sse \\
      -H "Content-Type: application/json" \\
      -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
    # Respuesta: {"error": "AUTH_INVALID_TOKEN", "message": "Se requiere token JWT..."}

    # Ejemplo de error 401 (token expirado)
    curl -X POST http://localhost:8000/sse \\
      -H "Authorization: Bearer <token-expirado>" \\
      -H "Content-Type: application/json" \\
      -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
    # Respuesta: {"error": "AUTH_INVALID_TOKEN", "message": "Token expirado"}
"""
```

---

## Validación de la Corrección

### Tests a Realizar Después de la Corrección

1. **Test: Request sin header Authorization**
   ```bash
   curl -X POST http://localhost:8000/sse \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

   # Esperado: HTTP 401
   # {"error": "AUTH_INVALID_TOKEN", "message": "Se requiere token JWT en header Authorization: Bearer <token>"}
   ```

2. **Test: Token con firma inválida**
   ```bash
   curl -X POST http://localhost:8000/sse \
     -H "Authorization: Bearer token-falso" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

   # Esperado: HTTP 401
   # {"error": "AUTH_INVALID_TOKEN", "message": "Firma inválida"}
   ```

3. **Test: Token expirado**
   ```bash
   # Generar token expirado
   TOKEN_EXPIRADO=$(python generate_token.py --exp-id EXP-2024-001 --expired)

   curl -X POST http://localhost:8000/sse \
     -H "Authorization: Bearer $TOKEN_EXPIRADO" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

   # Esperado: HTTP 401
   # {"error": "AUTH_INVALID_TOKEN", "message": "Token expirado"}
   ```

4. **Test: Token válido funciona correctamente**
   ```bash
   TOKEN=$(python generate_token.py --exp-id EXP-2024-001 --formato raw)

   curl -X POST http://localhost:8000/sse \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

   # Esperado: HTTP 200
   # Lista de tools en formato JSON-RPC
   ```

5. **Test: Token sin claim obligatorio (ej: sin iss)**
   ```bash
   # Generar token sin claim iss
   TOKEN_SIN_ISS=$(python -c "
   import jwt
   import time
   claims = {
       'sub': 'Automático',
       'exp_id': 'EXP-2024-001',
       'exp': int(time.time()) + 3600,
       'permisos': ['consulta']
   }
   print(jwt.encode(claims, 'test-secret-key', algorithm='HS256'))
   ")

   curl -X POST http://localhost:8000/sse \
     -H "Authorization: Bearer $TOKEN_SIN_ISS" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

   # Esperado: HTTP 401
   # {"error": "AUTH_INVALID_TOKEN", "message": "Token JWT inválido: ..."}
   ```

### Tests Automatizados

Añadir test en `/mcp-mock/mcp-expedientes/tests/test_server_http.py`:

```python
import pytest
from httpx import AsyncClient
from server_http import app


@pytest.mark.asyncio
async def test_sse_endpoint_sin_token():
    """Request sin token debe retornar 401 inmediatamente"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/sse",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
        )

        assert response.status_code == 401
        assert "AUTH_INVALID_TOKEN" in response.json()["error"]


@pytest.mark.asyncio
async def test_sse_endpoint_token_invalido():
    """Token con firma inválida debe retornar 401 inmediatamente"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/sse",
            headers={"Authorization": "Bearer token-falso"},
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
        )

        assert response.status_code == 401
        assert "AUTH_INVALID_TOKEN" in response.json()["error"]


@pytest.mark.asyncio
async def test_sse_endpoint_token_valido():
    """Token válido debe permitir procesamiento de request"""
    from generate_token import generate_token

    token = generate_token(
        usuario="Automático",
        expediente_id="EXP-2024-001",
        permisos=["consulta"]
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/sse",
            headers={"Authorization": f"Bearer {token}"},
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
        )

        # No debe ser 401/403
        assert response.status_code in [200, 201]
```

---

## Impacto de la Corrección

### Beneficios

1. ✅ **Fail-fast:** Rechaza inmediatamente requests no autorizadas
2. ✅ **Seguridad mejorada:** Ningún código se ejecuta sin validar credenciales
3. ✅ **Mensajes de error consistentes:** Siempre HTTP 401/403 en el mismo punto
4. ✅ **Compatibilidad con clientes HTTP estándar:** Comportamiento esperado
5. ✅ **Logs más claros:** Separación entre requests rechazadas y procesadas
6. ✅ **Performance:** No se desperdician recursos procesando requests no autorizadas

### Cambios de Comportamiento

- **Antes:** Request sin token se procesaba parcialmente hasta que un handler fallaba
- **Después:** Request sin token se rechaza inmediatamente con HTTP 401

### Compatibilidad

- ✅ **Compatible con clientes existentes:** Clientes que envían tokens válidos funcionarán igual
- ⚠️ **Incompatible con clientes sin token:** Ahora fallarán más rápido (esto es correcto)

---

## Checklist de Implementación

- [ ] Modificar función `handle_sse()` en `server_http.py`
- [ ] Añadir imports necesarios (`HTTPException`, `validate_jwt`, `AuthError`)
- [ ] Actualizar comentarios de uso en el docstring
- [ ] Ejecutar tests manuales (5 casos listados arriba)
- [ ] Crear/actualizar tests automatizados en `test_server_http.py`
- [ ] Verificar que todos los tests pasan
- [ ] Actualizar documentación en `/doc` si es necesario
- [ ] Probar integración con cliente MCP del back-office (cuando se implemente)

---

## Referencias

- **Archivo a modificar:** `/mcp-mock/mcp-expedientes/server_http.py`
- **Función de validación:** `/mcp-mock/mcp-expedientes/auth.py` → `validate_jwt()`
- **Modelo de claims:** `/mcp-mock/mcp-expedientes/models.py` → `JWTClaims`
- **Crítica original:** `/prompts/step-1-critique.md` → CRÍTICO 2
- **Especificación MCP:** https://modelcontextprotocol.io/

---

## Notas Adicionales

### ¿Por qué no validar expediente_id aquí?

La validación del token en el endpoint HTTP solo verifica:
- Firma válida
- Claims obligatorios presentes (`iss`, `sub`, `aud`, `exp`, `iat`, `nbf`, `jti`, `exp_id`, `permisos`)
- Token no expirado
- Audiencia correcta

**NO** valida:
- Que el `exp_id` del token coincida con el expediente solicitado en la tool
- Que los permisos incluyan la herramienta específica solicitada

Estas validaciones **más específicas** se realizan en cada handler (`read_resource`, `call_tool`, etc.) porque dependen del contexto de la operación.

### Separación de Responsabilidades

- **Endpoint HTTP (`handle_sse`):** Validación básica del token (autenticación)
- **Handlers MCP (`handle_call_tool`, etc.):** Validación específica de permisos (autorización)

Esto mantiene el principio de separación de responsabilidades y permite mensajes de error más específicos.

---

**Fin del documento de corrección**
