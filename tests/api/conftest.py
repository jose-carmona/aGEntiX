# tests/api/conftest.py

"""
Configuración de pytest para tests de API.
"""

import sys
import os
from pathlib import Path

# Cambiar al directorio raíz para acceso a .env
root_dir = Path(__file__).parent.parent.parent
os.chdir(str(root_dir))
