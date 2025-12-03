# Code Review: Validación Temprana de JWT en Servidor HTTP MCP

**Fecha**: 2025-12-01
**Revisor**: Claude Code
**Cambios**: Implementación de validación fail-fast de tokens JWT en servidor HTTP/SSE

---

## Resumen Ejecutivo

Este code review analiza los cambios implementados para agregar validación temprana (fail-fast) de tokens JWT en el servidor HTTP del sistema MCP de expedientes. El cambio principal mueve la validación JWT al inicio del procesamiento de la request, antes de iniciar el transporte SSE o procesar cualquier operación MCP.

### Archivos Modificados

1. `server_http.py` - Servidor HTTP con transporte SSE (cambios principales)
2. `tests/test_server_http.py` - Suite de tests para validación JWT (archivo nuevo)
3. `data/expedientes/EXP-2024-001.json` - Datos de prueba (cambios menores)

---

## Análisis Detallado

### 1. Cambios en `server_http.py`

#### ✅ Fortalezas

**1.1 Validación Fail-Fast Correctamente Implementada**
```python
# Líneas 120-146
# 2. VALIDAR TOKEN INMEDIATAMENTE (CAMBIO PRINCIPAL)
try:
    await validate_jwt(token, server_id=context.server_id)
    logger.info(f"✅ Token JWT válido recibido (primeros 20 chars): {token[:20]}...")
except AuthError as e:
    logger.warning(f"❌ Token JWT inválido: {e.message}")
    raise HTTPException(status_code=e.status_code, ...)
```

**Positivo**:
- La validación ocurre **antes** de crear el transporte SSE y procesar requests MCP
- El flujo de control es claro: extraer → validar → almacenar → procesar
- Uso correcto de excepciones para control de flujo

**1.2 Manejo de Errores Estructurado**
```python
# Líneas 197-211: http_exception_handler
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )
```

**Positivo**:
- Exception handler personalizado para HTTPException
- Respuestas JSON consistentes con estructura `{"error": ..., "message": ...}`
- Códigos de estado HTTP apropiados (401 para auth, 403 para permisos)

**1.3 Documentación Mejorada**

La documentación del módulo ahora incluye ejemplos de uso con curl que cubren:
- Requests exitosas con token válido
- Error 401 sin token
- Error 401 con token expirado
- Error 401 con token con firma inválida

**Positivo**: Excelente para onboarding y debugging

**1.4 Logging Informativo**
```python
logger.info(f"✅ Token JWT válido recibido (primeros 20 chars): {token[:20]}...")
logger.warning(f"❌ Token JWT inválido: {e.message}")
```

**Positivo**:
- Uso de emojis para facilitar lectura en logs
- Solo muestra primeros 20 caracteres del token (seguridad)
- Logs diferenciados por nivel (info vs warning)

#### ⚠️ Áreas de Mejora

**1.5 Manejo de Errores Genéricos**
```python
# Líneas 135-142
except Exception as e:
    logger.error(f"Error inesperado al validar token: {str(e)}")
    raise HTTPException(
        status_code=500,
        detail={
            "error": "INTERNAL_ERROR",
            "message": "Error interno al validar token JWT"
        }
    )
```

**Preocupación**: El mensaje genérico oculta información potencialmente útil al cliente.

**Recomendación**:
- En entorno de desarrollo, incluir más detalles del error
- Considerar agregar request ID para correlacionar logs del servidor con respuestas del cliente

**1.6 Validación Parcial en Primera Llamada**
```python
# Línea 123
await validate_jwt(token, server_id=context.server_id)
```

**Observación**: La primera validación no recibe `resource_uri`, `tool_name` ni `tool_args`, por lo que las validaciones de expediente y permisos (pasos 7-8 en `auth.py`) no se ejecutan aquí.

**Impacto**:
- ✅ Correcto: Valida firma, expiración, audiencia, emisor (pasos 1-6)
- ⚠️ Pendiente: Validación de expediente y permisos se hace después en handlers individuales

**Recomendación**:
- Documentar explícitamente que esta es una "validación básica"
- Agregar comentario indicando que validaciones adicionales ocurren en handlers

---

### 2. Tests en `test_server_http.py`

#### ✅ Fortalezas

**2.1 Cobertura Completa de Casos de Error**

Tests implementados:
1. `test_sse_endpoint_sin_token` - Request sin token
2. `test_sse_endpoint_token_invalido` - Token con firma inválida
3. `test_sse_endpoint_token_expirado` - Token expirado
4. `test_sse_endpoint_token_sin_claim_obligatorio` - Token sin claim `iss`
5. `test_sse_endpoint_header_sin_bearer` - Header sin prefijo "Bearer"
6. `test_health_endpoint_no_requiere_token` - Endpoint público
7. `test_info_endpoint_no_requiere_token` - Endpoint público

**Positivo**: Cobertura exhaustiva de casos de rechazo

**2.2 Uso Correcto de TestClient**
```python
with TestClient(app, raise_server_exceptions=False) as client:
    response = client.post("/sse", ...)
```

**Positivo**: `raise_server_exceptions=False` permite capturar respuestas 401/403 sin que pytest las trate como errores

**2.3 Aserciones Claras**
```python
assert response.status_code == 401
assert data["error"] == "AUTH_INVALID_TOKEN"
assert "Se requiere token JWT" in data["message"]
```

**Positivo**: Tests verifican tanto código de estado como estructura de respuesta

#### ⚠️ Áreas de Mejora

**2.4 Test de Caso Exitoso Deshabilitado**
```python
# Líneas 104-116
def test_sse_endpoint_token_valido_permite_procesamiento():
    pytest.skip("Test deshabilitado: transporte SSE causa timeouts...")
```

**Preocupación**: No hay test automatizado que verifique que tokens válidos funcionan correctamente.

**Impacto en Confianza del Código**: ⚠️ Medio
- Los tests de error son suficientes para validar el fail-fast
- El comportamiento exitoso solo se puede validar manualmente con curl

**Recomendación**:
1. **Corto plazo**: Mantener test deshabilitado, documentar proceso de test manual
2. **Largo plazo**: Implementar test de integración con cliente MCP real que:
   - Use pytest-asyncio para manejar comunicación SSE
   - Verifique que una operación MCP se complete exitosamente

**2.5 Generación de Tokens en Tests**
```python
# Líneas 48-62
token_expirado = jwt.encode(
    {
        "iss": "agentix-bpmn",
        "sub": "Automático",
        "aud": ["agentix-mcp-expedientes"],
        "exp": int(time.time()) - 3600,  # Expirado
        ...
    },
    os.getenv("JWT_SECRET", "test-secret-key"),
    algorithm="HS256"
)
```

**Observación**: Los tests generan tokens manualmente en lugar de usar `generate_token.py`

**Impacto**: ⚠️ Bajo (pero duplicación de lógica)

**Recomendación**: Extraer generación de tokens a función helper reutilizable:
```python
def create_test_token(exp_offset=3600, **overrides):
    """Crea token de test con claims personalizables"""
    ...
```

---

### 3. Cambios en Datos de Prueba

#### Cambios en `EXP-2024-001.json`

```diff
- "fecha_inicio": "2024-01-15T08:30:00Z",
+ "fecha_inicio": "2024-01-15T08:30:00+00:00",

- "importe_solicitado": 5000.00,
+ "importe_solicitado": 5000.0,

+ {
+   "id": "HIST-075715",
+   "fecha": "2025-11-22T19:17:55.715218",
+   "usuario": "Automático",
+   "tipo": "ANOTACION",
+   "accion": "ANOTACION",
+   "detalles": "Documentación verificada correctamente"
+ }
```

#### Análisis

**3.1 Formato de Fecha**: Cambio de `Z` a `+00:00` es equivalente (ambos representan UTC)
- ✅ Consistencia mejorada con formato ISO 8601 explícito

**3.2 Formato Numérico**: `5000.00` → `5000.0`
- ℹ️ Cambio cosmético, sin impacto funcional

**3.3 Nueva Entrada en Historial**
- ✅ Indica que se ejecutó una prueba del sistema (añadir_anotacion)
- ⚠️ **Dato residual de testing**: Debería limpiarse antes de commit

**Recomendación**:
- Revertir la entrada HIST-075715 (dato temporal de testing)
- O documentar que es parte de datos de ejemplo para demostración

---

## Análisis de Seguridad

### ✅ Fortalezas de Seguridad

1. **Fail-Fast Authentication**: Tokens inválidos son rechazados antes de procesar requests
2. **No Leakage de Información Sensible**:
   - Solo primeros 20 caracteres del token en logs
   - Mensajes de error no revelan estructura interna
3. **Validación JWT Completa**:
   - Firma (HS256)
   - Expiración (exp)
   - Not Before (nbf)
   - Audiencia (aud)
   - Emisor (iss)
4. **Separación de Responsabilidades**:
   - Módulo `auth.py` centraliza lógica de autenticación
   - `server_http.py` solo orquesta validación

### ⚠️ Consideraciones de Seguridad

**1. Logging de Tokens Parciales**
```python
logger.info(f"✅ Token JWT válido recibido (primeros 20 chars): {token[:20]}...")
```

**Análisis**: Mostrar 20 caracteres del token podría ayudar en ataques de correlación si los logs son comprometidos.

**Riesgo**: Bajo (pero presente)

**Recomendación**:
- Loguear solo un hash del token: `hashlib.sha256(token.encode()).hexdigest()[:16]`
- O deshabilitar este log en producción

**2. JWT_SECRET en Variable de Entorno**
```python
os.getenv("JWT_SECRET", "test-secret-key")
```

**Análisis**:
- ✅ Uso correcto de variable de entorno
- ⚠️ Fallback a `"test-secret-key"` en tests podría ser peligroso si se usa en producción

**Recomendación**:
- En código de producción, NO usar fallback (fallar si JWT_SECRET no está configurado)
- En tests, usar fixture de pytest que configure explícitamente la variable

---

## Análisis de Rendimiento

### Impacto de la Validación Temprana

**Antes**:
1. Crear transporte SSE
2. Conectar cliente
3. Recibir request MCP
4. Validar JWT
5. Procesar request

**Después**:
1. **Validar JWT** ← Nueva posición
2. Crear transporte SSE
3. Conectar cliente
4. Recibir request MCP
5. Procesar request

### ✅ Beneficios de Rendimiento

1. **Reducción de Trabajo Inútil**: Requests inválidas se rechazan antes de crear conexiones SSE
2. **Menor Uso de Recursos**: No se consumen recursos del servidor para clientes no autorizados
3. **Mejor Experiencia de Cliente**: Errores de auth retornan inmediatamente (no timeout)

### Overhead Introducido

- **Validación JWT**: ~1-5ms (decodificación + verificación de firma)
- **Impacto**: Despreciable comparado con latencia de red y procesamiento MCP

---

## Resultados de Tests

### Tests Ejecutados

Según el output capturado, los tests están fallando:

```
tests/test_server_http.py::test_sse_endpoint_sin_token FAILED
tests/test_server_http.py::test_sse_endpoint_token_invalido FAILED
tests/test_server_http.py::test_sse_endpoint_token_expirado FAILED
tests/test_server_http.py::test_sse_endpoint_token_sin_claim_obligatorio FAILED
```

### 🔴 CRÍTICO: Tests Fallando

**Análisis**: Los tests están fallando, lo que indica que:
1. La implementación no está funcionando como se espera, O
2. Los tests tienen errores de configuración, O
3. Hay una dependencia no satisfecha (ej: JWT_SECRET no configurado en entorno de test)

**Impacto**: ⚠️ ALTO - No se puede validar que el código funcione correctamente

**Recomendación URGENTE**:
1. Ejecutar tests con `-vv` para ver detalles de los fallos
2. Verificar que JWT_SECRET esté configurado en el entorno de test
3. Revisar si `raise_server_exceptions=False` está funcionando correctamente
4. Agregar prints de debug en los tests para ver qué respuestas se reciben

---

## Consistencia con Arquitectura del Proyecto

### ✅ Alineación con Principios de aGEntiX

Según `/doc/CLAUDE.md`:

**1. Separación de Responsabilidades**
- ✅ Módulo `auth.py` independiente
- ✅ Server solo orquesta validación

**2. Propagación de Permisos** (doc/052-propagacion-permisos.md)
- ✅ Token JWT se valida en boundary (servidor HTTP)
- ✅ Permisos se propagan: Agente → MCP → API

**3. Auditoría** (doc/033-auditoria-agente.md)
- ✅ Logs de validación exitosa/fallida
- ⚠️ Falta logging estructurado (JSON) para sistemas de auditoría

**4. Enfoque Conservador** (doc/041-enfoque-conservador.md)
- ✅ Validación estricta de tokens
- ✅ Rechazo explícito de requests no autorizadas

---

## Recomendaciones Priorizadas

### 🔴 Críticas (Bloquean Merge)

1. **RESOLVER TESTS FALLANDO**: Investigar y corregir fallos en test suite
   - Sin tests pasando, no se puede validar que el código funcione
   - Ejecutar: `pytest tests/test_server_http.py -vv --tb=short`

2. **LIMPIAR DATOS DE PRUEBA**: Revertir entrada HIST-075715 en EXP-2024-001.json
   - Es dato residual de testing manual

### ⚠️ Importantes (Antes de Producción)

3. **AGREGAR TEST DE CASO EXITOSO**: Implementar test de integración que valide flujo completo
   - Considerar usar pytest-asyncio con cliente MCP real

4. **DOCUMENTAR VALIDACIÓN DE DOS ETAPAS**:
   - Agregar comentario en `server_http.py:123` explicando que esta es validación básica
   - Documentar que validaciones de expediente/permisos ocurren en handlers

5. **MEJORAR LOGGING DE SEGURIDAD**:
   - Reemplazar `token[:20]` por hash del token
   - Agregar request ID para correlación de logs

### ℹ️ Mejoras Futuras

6. **REFACTORIZAR GENERACIÓN DE TOKENS EN TESTS**: Extraer a función helper reutilizable

7. **AGREGAR LOGGING ESTRUCTURADO**: Usar JSON logs para auditoría

8. **REMOVER FALLBACK DE JWT_SECRET**: En código de producción, fallar si no está configurado

---

## Conclusión

### Calidad General del Código: ⚠️ **B+ (Bueno con Reservas)**

**Fortalezas**:
- ✅ Implementación correcta de validación fail-fast
- ✅ Manejo de errores estructurado y consistente
- ✅ Documentación excelente con ejemplos de uso
- ✅ Cobertura de tests exhaustiva para casos de error
- ✅ Alineación con arquitectura del proyecto

**Debilidades**:
- 🔴 Tests fallando (CRÍTICO)
- ⚠️ Datos de prueba con entradas residuales
- ⚠️ No hay test automatizado de caso exitoso
- ⚠️ Logging de seguridad podría mejorarse

### Recomendación de Merge

**NO APROBAR** hasta que:
1. ✅ Todos los tests pasen correctamente
2. ✅ Se limpien datos de prueba (HIST-075715)
3. ✅ Se documente validación de dos etapas

**Después de resolver críticos**: Re-review y aprobar para merge

---

## Checklist de Revisión

- [x] Código revisado línea por línea
- [x] Tests revisados y analizados
- [x] Seguridad evaluada
- [x] Rendimiento considerado
- [x] Consistencia con arquitectura verificada
- [x] Documentación revisada
- [x] Datos de prueba inspeccionados
- [x] Recomendaciones priorizadas
- [ ] **Tests ejecutados y pasando** ← PENDIENTE
- [ ] **Datos de prueba limpiados** ← PENDIENTE

---

**Firma**: Claude Code
**Fecha**: 2025-12-01
