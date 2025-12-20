"""
Configuración global de pytest para aGEntiX.

Este archivo configura el entorno de pytest antes de la colección de tests.
Agrega src/ al PYTHONPATH y configura environment variables para tests.
"""

import sys
import os
from pathlib import Path
import pytest

# ============================================================================
# PYTHONPATH Setup (ÚNICO LUGAR - NO DUPLICAR EN OTROS CONFTEST)
# ============================================================================
project_root = Path(__file__).parent
src_path = project_root / "src"

if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def pytest_configure(config):
    """
    Hook de pytest que se ejecuta ANTES de la colección de tests.

    Asegura que src/ esté en sys.path antes de que pytest intente
    importar cualquier módulo de test.
    """
    # Volver a verificar que src/ está en sys.path
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


# ============================================================================
# Test Constants - Centralización de valores hardcoded
# ============================================================================
@pytest.fixture(scope="session")
def test_constants():
    """
    Constantes compartidas entre todos los tests.

    Centraliza valores hardcoded para facilitar mantenimiento.
    Cambiar un valor aquí lo actualiza en todos los tests que lo usan.
    """
    return {
        "jwt_secret": "test-secret-key",
        "jwt_algorithm": "HS256",
        "issuer": "agentix-bpmn",
        "subject": "Automático",
        "audience": "agentix-mcp-expedientes",
        "default_exp_ids": ["EXP-2024-001", "EXP-2024-002", "EXP-2024-003"]
    }


# ============================================================================
# Environment Setup - Autouse + Cleanup
# ============================================================================
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(test_constants):
    """
    Configura variables de entorno para todos los tests.

    autouse=True: Se ejecuta automáticamente sin necesidad de declararlo.
    scope="session": Se ejecuta una sola vez al inicio de la sesión de tests.

    Garantiza cleanup incluso si tests fallan.
    """
    original_env = {}

    # Backup valores originales
    for key in ["JWT_SECRET", "JWT_ALGORITHM", "LOG_LEVEL"]:
        original_env[key] = os.environ.get(key)

    # Configurar valores de test
    os.environ["JWT_SECRET"] = test_constants["jwt_secret"]
    os.environ["JWT_ALGORITHM"] = test_constants["jwt_algorithm"]
    os.environ["LOG_LEVEL"] = "INFO"

    yield

    # Cleanup (SIEMPRE se ejecuta, incluso si hay excepciones)
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)


# ============================================================================
# Shared Fixtures - Disponibles para todos los tests
# ============================================================================
@pytest.fixture(scope="session")
def jwt_secret(test_constants):
    """JWT secret para validación en todos los tests"""
    return test_constants["jwt_secret"]


@pytest.fixture(scope="session")
def jwt_algorithm(test_constants):
    """JWT algorithm para todos los tests"""
    return test_constants["jwt_algorithm"]
