# Sistema de Autenticación Dual

aGEntiX usa **dos tokens diferentes** con propósitos distintos:

| Token | Propósito | Tipo |
|-------|-----------|------|
| **Admin Token** | Acceso al dashboard | String fijo |
| **JWT Token** | Ejecución de agentes | JWT firmado |

## Principio de separación

- **Ver el sistema** ≠ **Actuar sobre expedientes**
- El admin token da acceso al panel de control
- El JWT autoriza operaciones específicas sobre un expediente concreto

## Flujo

```
Login (Admin Token) → Dashboard → Generar JWT → Ejecutar Agente (JWT)
```

## Notas relacionadas

- [Token Administrativo](061-token-admin.md)
- [Token JWT de Ejecución](062-token-jwt.md)
- [Propagación de permisos](052-propagacion-permisos.md)
