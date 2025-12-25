# Token Administrativo

Token simple para acceso al dashboard de monitorización.

## Características

- **Tipo**: String (NO es JWT)
- **Origen**: Variable `API_ADMIN_TOKEN` en `.env`
- **Almacenamiento**: `localStorage` en frontend
- **Validez**: Permanente (hasta cambio manual)

## Endpoints protegidos

| Endpoint | Descripción |
|----------|-------------|
| `/api/v1/auth/generate-jwt` | Generar JWT |
| `/api/v1/agent/agents` | Listar agentes |
| `/api/v1/metrics/*` | Métricas |
| `/api/v1/logs/*` | Logs |

## Validación

```
POST /api/v1/auth/validate-admin-token
Body: { "token": "..." }
→ Compara con API_ADMIN_TOKEN de .env
```

## Notas relacionadas

- [Sistema de Autenticación Dual](060-autenticacion-dual.md)
- [Token JWT de Ejecución](062-token-jwt.md)
