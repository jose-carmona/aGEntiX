"""
Configuración de pytest y fixtures comunes.

Este módulo proporciona configuración global y fixtures
que pueden ser usadas en todos los tests.
"""

import os
import sys
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
