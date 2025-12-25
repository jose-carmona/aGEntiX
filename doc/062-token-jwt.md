# Token JWT de Ejecución

Token JWT firmado para autorizar ejecución de agentes sobre expedientes.

## Características

- **Tipo**: JWT firmado (HS256)
- **Generación**: Endpoint `/api/v1/auth/generate-jwt`
- **Validez**: 1-24 horas
- **Almacenamiento**: Solo memoria (NO localStorage)

## Endpoints protegidos

| Endpoint | Descripción |
|----------|-------------|
| `/api/v1/agent/execute` | Ejecutar agente |
| `/api/v1/agent/status/{id}` | Estado de ejecución |

## Claims principales

| Claim | Descripción |
|-------|-------------|
| `exp_id` | ID del expediente autorizado |
| `permisos` | `["consulta"]` o `["consulta", "gestion"]` |
| `aud` | MCP servers autorizados |

## Generación

Requiere Admin Token para generar:

```
POST /api/v1/auth/generate-jwt
Headers: Authorization: Bearer {admin_token}
Body: { exp_id, permisos, ... }
→ { token: "eyJ...", claims: {...} }
```

## Módulos

- Generación: `backoffice/auth/jwt_generator.py`
- Validación: `backoffice/auth/jwt_validator.py`

## Notas relacionadas

- [Sistema de Autenticación Dual](060-autenticacion-dual.md)
- [Token Administrativo](061-token-admin.md)
- [Propagación de permisos](052-propagacion-permisos.md)
