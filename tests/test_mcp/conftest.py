"""
Configuración de pytest y fixtures comunes.

Este módulo proporciona configuración global y fixtures
que pueden ser usadas en todos los tests.
"""

import sys
import shutil
from pathlib import Path
import pytest

# NOTA: src/ ya está en sys.path (conftest global)
# PERO necesitamos agregar directorio local para imports de fixtures/
sys.path.insert(0, str(Path(__file__).parent))

# os.environ["JWT_SECRET"] configurado por fixture autouse en conftest global


# ELIMINADO: jwt_secret fixture - ahora está en conftest.py global


@pytest.fixture(scope="session")
def test_expedientes(test_constants):
    """Fixture que proporciona los IDs de expedientes de prueba"""
    return test_constants["default_exp_ids"]


@pytest.fixture
def exp_id_subvenciones(test_constants):
    """ID del expediente de subvenciones"""
    return test_constants["default_exp_ids"][0]


@pytest.fixture
def exp_id_licencia(test_constants):
    """ID del expediente de licencia"""
    return test_constants["default_exp_ids"][1]


@pytest.fixture
def exp_id_certificado(test_constants):
    """ID del expediente de certificado"""
    return test_constants["default_exp_ids"][2]


@pytest.fixture
def restore_expediente_data():
    """
    Restaura los datos de expedientes desde archivos .backup.

    Esta fixture debe usarse en tests que modifiquen datos (escritura),
    para garantizar que cada test empiece con datos limpios.

    Los archivos .backup contienen el estado original de los expedientes
    y siempre deben existir en data/expedientes/*.json.backup

    IMPORTANTE: Esta fixture es idempotente - restaura el estado limpio
    tanto ANTES como DESPUÉS de cada test.

    Uso:
        @pytest.mark.usefixtures("restore_expediente_data")
        async def test_modificar_datos():
            # Test que modifica datos
            pass
    """
    root_dir = Path(__file__).parent.parent.parent
    data_dir = root_dir / "src" / "mcp_mock" / "mcp_expedientes" / "data" / "expedientes"

    def _restore_from_backup():
        """Restaura todos los expedientes desde sus backups"""
        for backup_file in data_dir.glob("*.json.backup"):
            test_file = backup_file.with_suffix("")  # Elimina .backup
            shutil.copy(backup_file, test_file)

    # Setup: Restaurar estado limpio ANTES del test
    _restore_from_backup()

    yield

    # Teardown: Restaurar estado limpio DESPUÉS del test (idempotencia)
    _restore_from_backup()
