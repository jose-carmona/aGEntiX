# backoffice/tests/test_jwt_validator.py
import pytest
import jwt
from datetime import datetime, timezone, timedelta
from backoffice.auth.jwt_validator import (
    validate_jwt,
    get_required_permissions_for_tools,
    JWTValidationError,
    JWTClaims
)


@pytest.fixture
def jwt_secret():
    """Secret para tests"""
    return "test-secret-key"


@pytest.fixture
def jwt_algorithm():
    """Algoritmo para tests"""
    return "HS256"


@pytest.fixture
def valid_claims():
    """Claims válidos para tests"""
    now = datetime.now(timezone.utc)
    return {
        "iss": "agentix-bpmn",
        "sub": "Automático",
        "aud": ["agentix-mcp-expedientes"],
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "jti": "test-jti-123",
        "exp_id": "EXP-2024-001",
        "permisos": ["consulta", "gestion"]
    }


def test_validate_jwt_success(jwt_secret, jwt_algorithm, valid_claims):
    """Test: JWT válido se valida correctamente"""
    # Crear token válido
    token = jwt.encode(valid_claims, jwt_secret, algorithm=jwt_algorithm)

    # Validar
    result = validate_jwt(
        token=token,
        secret=jwt_secret,
        algorithm=jwt_algorithm,
        expected_expediente_id="EXP-2024-001",
        required_permissions=["consulta"]
    )

    # Verificar
    assert isinstance(result, JWTClaims)
    assert result.iss == "agentix-bpmn"
    assert result.sub == "Automático"
    assert result.exp_id == "EXP-2024-001"
    assert "consulta" in result.permisos


def test_validate_jwt_expired(jwt_secret, jwt_algorithm, valid_claims):
    """Test: Token expirado es rechazado"""
    # Crear token expirado
    now = datetime.now(timezone.utc)
    expired_claims = valid_claims.copy()
    expired_claims["exp"] = int((now - timedelta(hours=1)).timestamp())

    token = jwt.encode(expired_claims, jwt_secret, algorithm=jwt_algorithm)

    # Verificar que lanza excepción
    with pytest.raises(JWTValidationError) as exc_info:
        validate_jwt(
            token=token,
            secret=jwt_secret,
            algorithm=jwt_algorithm,
            expected_expediente_id="EXP-2024-001"
        )

    assert exc_info.value.codigo == "AUTH_TOKEN_EXPIRED"
    assert "expirado" in exc_info.value.mensaje.lower()


def test_validate_jwt_invalid_signature(jwt_secret, jwt_algorithm, valid_claims):
    """Test: Firma inválida es rechazada"""
    # Crear token con secret correcto
    token = jwt.encode(valid_claims, jwt_secret, algorithm=jwt_algorithm)

    # Intentar validar con secret incorrecto
    with pytest.raises(JWTValidationError) as exc_info:
        validate_jwt(
            token=token,
            secret="wrong-secret",
            algorithm=jwt_algorithm,
            expected_expediente_id="EXP-2024-001"
        )

    assert exc_info.value.codigo == "AUTH_INVALID_TOKEN"


def test_validate_jwt_invalid_issuer(jwt_secret, jwt_algorithm, valid_claims):
    """Test: Emisor incorrecto es rechazado"""
    # Token con emisor incorrecto
    invalid_claims = valid_claims.copy()
    invalid_claims["iss"] = "unknown-issuer"

    token = jwt.encode(invalid_claims, jwt_secret, algorithm=jwt_algorithm)

    with pytest.raises(JWTValidationError) as exc_info:
        validate_jwt(
            token=token,
            secret=jwt_secret,
            algorithm=jwt_algorithm,
            expected_expediente_id="EXP-2024-001"
        )

    assert exc_info.value.codigo == "AUTH_PERMISSION_DENIED"
    assert "agentix-bpmn" in exc_info.value.mensaje
    assert "unknown-issuer" in exc_info.value.mensaje


def test_validate_jwt_invalid_subject(jwt_secret, jwt_algorithm, valid_claims):
    """Test: Subject incorrecto es rechazado"""
    # Token con subject incorrecto
    invalid_claims = valid_claims.copy()
    invalid_claims["sub"] = "Manual"

    token = jwt.encode(invalid_claims, jwt_secret, algorithm=jwt_algorithm)

    with pytest.raises(JWTValidationError) as exc_info:
        validate_jwt(
            token=token,
            secret=jwt_secret,
            algorithm=jwt_algorithm,
            expected_expediente_id="EXP-2024-001"
        )

    assert exc_info.value.codigo == "AUTH_PERMISSION_DENIED"
    assert "Automático" in exc_info.value.mensaje


def test_validate_jwt_missing_audience(jwt_secret, jwt_algorithm, valid_claims):
    """Test: Audiencia incorrecta es rechazada"""
    # Token sin la audiencia correcta
    invalid_claims = valid_claims.copy()
    invalid_claims["aud"] = ["wrong-audience"]

    token = jwt.encode(invalid_claims, jwt_secret, algorithm=jwt_algorithm)

    with pytest.raises(JWTValidationError) as exc_info:
        validate_jwt(
            token=token,
            secret=jwt_secret,
            algorithm=jwt_algorithm,
            expected_expediente_id="EXP-2024-001"
        )

    assert exc_info.value.codigo == "AUTH_PERMISSION_DENIED"
    assert "agentix-mcp-expedientes" in exc_info.value.mensaje


def test_validate_jwt_audience_as_string(jwt_secret, jwt_algorithm, valid_claims):
    """Test: Audiencia como string (no lista) funciona correctamente"""
    # Token con audiencia como string
    claims_with_string_aud = valid_claims.copy()
    claims_with_string_aud["aud"] = "agentix-mcp-expedientes"

    token = jwt.encode(claims_with_string_aud, jwt_secret, algorithm=jwt_algorithm)

    # Debe validar correctamente
    result = validate_jwt(
        token=token,
        secret=jwt_secret,
        algorithm=jwt_algorithm,
        expected_expediente_id="EXP-2024-001"
    )

    assert result.exp_id == "EXP-2024-001"


def test_validate_jwt_wrong_expediente(jwt_secret, jwt_algorithm, valid_claims):
    """Test: Expediente no autorizado es rechazado"""
    token = jwt.encode(valid_claims, jwt_secret, algorithm=jwt_algorithm)

    # Intentar validar para expediente diferente
    with pytest.raises(JWTValidationError) as exc_info:
        validate_jwt(
            token=token,
            secret=jwt_secret,
            algorithm=jwt_algorithm,
            expected_expediente_id="EXP-2024-999"
        )

    assert exc_info.value.codigo == "AUTH_EXPEDIENTE_MISMATCH"
    assert "EXP-2024-001" in exc_info.value.mensaje
    assert "EXP-2024-999" in exc_info.value.mensaje


def test_validate_jwt_insufficient_permissions(jwt_secret, jwt_algorithm, valid_claims):
    """Test: Permisos insuficientes son rechazados"""
    # Token con solo permiso de consulta
    limited_claims = valid_claims.copy()
    limited_claims["permisos"] = ["consulta"]

    token = jwt.encode(limited_claims, jwt_secret, algorithm=jwt_algorithm)

    # Intentar validar requiriendo más permisos
    with pytest.raises(JWTValidationError) as exc_info:
        validate_jwt(
            token=token,
            secret=jwt_secret,
            algorithm=jwt_algorithm,
            expected_expediente_id="EXP-2024-001",
            required_permissions=["consulta", "gestion"]
        )

    assert exc_info.value.codigo == "AUTH_INSUFFICIENT_PERMISSIONS"
    assert "gestion" in exc_info.value.mensaje


def test_validate_jwt_not_yet_valid(jwt_secret, jwt_algorithm, valid_claims):
    """Test: Token con nbf en el futuro es rechazado"""
    # Token que no es válido aún
    now = datetime.now(timezone.utc)
    future_claims = valid_claims.copy()
    future_claims["nbf"] = int((now + timedelta(hours=1)).timestamp())

    token = jwt.encode(future_claims, jwt_secret, algorithm=jwt_algorithm)

    with pytest.raises(JWTValidationError) as exc_info:
        validate_jwt(
            token=token,
            secret=jwt_secret,
            algorithm=jwt_algorithm,
            expected_expediente_id="EXP-2024-001"
        )

    assert exc_info.value.codigo == "AUTH_TOKEN_NOT_YET_VALID"


def test_validate_jwt_missing_required_claim(jwt_secret, jwt_algorithm, valid_claims):
    """Test: Claims faltantes son rechazados"""
    # Token sin claim exp_id
    incomplete_claims = valid_claims.copy()
    del incomplete_claims["exp_id"]

    token = jwt.encode(incomplete_claims, jwt_secret, algorithm=jwt_algorithm)

    with pytest.raises(JWTValidationError) as exc_info:
        validate_jwt(
            token=token,
            secret=jwt_secret,
            algorithm=jwt_algorithm,
            expected_expediente_id="EXP-2024-001"
        )

    assert exc_info.value.codigo == "AUTH_INVALID_TOKEN"
    assert "incompleto" in exc_info.value.mensaje.lower()


def test_validate_jwt_malformed_token(jwt_secret, jwt_algorithm):
    """Test: Token mal formado es rechazado"""
    malformed_token = "esto.no.es.un.jwt.valido"

    with pytest.raises(JWTValidationError) as exc_info:
        validate_jwt(
            token=malformed_token,
            secret=jwt_secret,
            algorithm=jwt_algorithm,
            expected_expediente_id="EXP-2024-001"
        )

    assert exc_info.value.codigo == "AUTH_INVALID_TOKEN"


def test_get_required_permissions_readonly():
    """Test: Herramientas de solo lectura requieren solo 'consulta'"""
    tools = ["consultar_expediente", "listar_documentos", "leer_documento"]

    perms = get_required_permissions_for_tools(tools)

    assert perms == ["consulta"]


def test_get_required_permissions_write():
    """Test: Herramientas de escritura requieren 'consulta' y 'gestion'"""
    tools = ["actualizar_datos", "añadir_anotacion"]

    perms = get_required_permissions_for_tools(tools)

    assert "consulta" in perms
    assert "gestion" in perms


def test_get_required_permissions_mixed():
    """Test: Mix de herramientas requiere ambos permisos"""
    tools = ["consultar_expediente", "actualizar_datos"]

    perms = get_required_permissions_for_tools(tools)

    assert "consulta" in perms
    assert "gestion" in perms


def test_get_required_permissions_unknown_tool():
    """Test: Herramienta desconocida no requiere permisos"""
    tools = ["unknown_tool"]

    perms = get_required_permissions_for_tools(tools)

    assert perms == []


def test_get_required_permissions_empty():
    """Test: Sin herramientas no requiere permisos"""
    tools = []

    perms = get_required_permissions_for_tools(tools)

    assert perms == []


def test_validate_jwt_multiple_audiences(jwt_secret, jwt_algorithm, valid_claims):
    """Test: Token con múltiples audiencias funciona si incluye la requerida"""
    # Token con múltiples audiencias
    multi_aud_claims = valid_claims.copy()
    multi_aud_claims["aud"] = [
        "agentix-mcp-expedientes",
        "agentix-mcp-contabilidad",
        "agentix-other-service"
    ]

    token = jwt.encode(multi_aud_claims, jwt_secret, algorithm=jwt_algorithm)

    # Debe validar correctamente
    result = validate_jwt(
        token=token,
        secret=jwt_secret,
        algorithm=jwt_algorithm,
        expected_expediente_id="EXP-2024-001"
    )

    assert result.exp_id == "EXP-2024-001"


def test_validate_jwt_no_required_permissions(jwt_secret, jwt_algorithm, valid_claims):
    """Test: Sin required_permissions no valida permisos"""
    # Token con permisos vacíos
    no_perms_claims = valid_claims.copy()
    no_perms_claims["permisos"] = []

    token = jwt.encode(no_perms_claims, jwt_secret, algorithm=jwt_algorithm)

    # Sin required_permissions debe pasar
    result = validate_jwt(
        token=token,
        secret=jwt_secret,
        algorithm=jwt_algorithm,
        expected_expediente_id="EXP-2024-001",
        required_permissions=None
    )

    assert result.exp_id == "EXP-2024-001"
    assert result.permisos == []
