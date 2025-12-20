# tests/api/conftest.py

"""
Configuración de pytest para tests de API.

NOTA: sys.path ya está configurado en conftest.py global.
No duplicar configuración aquí para evitar problemas de imports.

Si se necesitan fixtures específicas de API, definirlas aquí.
"""

# ELIMINADO: os.chdir() - antipatrón que modifica estado global
# ELIMINADO: sys.path manipulation - ya está en conftest.py global
