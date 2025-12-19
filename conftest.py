"""
Configuración global de pytest para aGEntiX.

Este archivo configura el entorno de pytest antes de la colección de tests.
Agrega src/ al PYTHONPATH para permitir imports de los paquetes.
"""

import sys
from pathlib import Path

# Agregar src/ al PYTHONPATH para que pytest pueda importar los módulos
project_root = Path(__file__).parent
src_path = project_root / "src"

if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
