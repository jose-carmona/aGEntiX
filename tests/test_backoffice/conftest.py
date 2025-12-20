# tests/test_backoffice/conftest.py

"""
Configuración de pytest para tests de backoffice.

NOTA: pytest-asyncio ya proporciona event_loop con function scope automáticamente.
No es necesario definir fixtures personalizadas de event_loop aquí.

El event_loop session-scoped fue eliminado porque:
- pytest-asyncio recomienda function-scoped event loops
- session-scoped puede causar state leakage entre tests async
- Puede generar deprecation warnings en versiones nuevas de pytest-asyncio
"""
