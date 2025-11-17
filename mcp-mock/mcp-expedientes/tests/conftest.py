"""
Configuración de pytest y fixtures comunes.

Este módulo proporciona configuración global y fixtures
que pueden ser usadas en todos los tests.
"""

import os
import sys
import shutil
from pathlib import Path
import pytest

# Configurar path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Configurar JWT_SECRET para todos los tests
os.environ["JWT_SECRET"] = "test-secret-key"


@pytest.fixture(scope="session")
def jwt_secret():
    """Fixture que proporciona la clave secreta JWT"""
    return "test-secret-key"


@pytest.fixture(scope="session")
def test_expedientes():
    """Fixture que proporciona los IDs de expedientes de prueba"""
    return [
        "EXP-2024-001",  # Subvenciones en trámite
        "EXP-2024-002",  # Licencia pendiente documentación
        "EXP-2024-003"   # Certificado archivado
    ]


@pytest.fixture
def exp_id_subvenciones():
    """ID del expediente de subvenciones"""
    return "EXP-2024-001"


@pytest.fixture
def exp_id_licencia():
    """ID del expediente de licencia"""
    return "EXP-2024-002"


@pytest.fixture
def exp_id_certificado():
    """ID del expediente de certificado"""
    return "EXP-2024-003"


@pytest.fixture
def restore_expediente_data():
    """
    Restaura los datos de expedientes desde archivos .backup.

    Esta fixture debe usarse en tests que modifiquen datos (escritura),
    para garantizar que cada test empiece con datos limpios.

    Los archivos .backup contienen el estado original de los expedientes
    y siempre deben existir en data/expedientes/*.json.backup

    Uso:
        @pytest.mark.usefixtures("restore_expediente_data")
        async def test_modificar_datos():
            # Test que modifica datos
            pass
    """
    data_dir = Path(__file__).parent.parent / "data" / "expedientes"

    # Restaurar todos los expedientes desde backup
    for backup_file in data_dir.glob("*.json.backup"):
        test_file = backup_file.with_suffix("")  # Elimina .backup
        shutil.copy(backup_file, test_file)

    yield

    # Opcionalmente limpiar después del test
    # (por ahora no hacemos nada, dejamos el estado final para debug)
