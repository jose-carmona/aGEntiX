# tests/api/conftest.py

"""
Configuración de pytest para tests de API.
"""

import sys
import os
from pathlib import Path

# Añadir directorio raíz al PYTHONPATH
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# También cambiar al directorio raíz para imports relativos
os.chdir(str(root_dir))
