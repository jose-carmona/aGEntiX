#!/usr/bin/env python3
"""
DEPRECADO: Usar backoffice.auth.jwt_generator en su lugar.

Este módulo se mantiene por retrocompatibilidad pero redirige todas
las llamadas al generador centralizado en backoffice.auth.jwt_generator.

Para generar tokens JWT, usar:

    from backoffice.auth.jwt_generator import generate_jwt

    result = generate_jwt(
        expediente_id="EXP-2024-001",
        permisos=["consulta", "gestion"]
    )
    print(result.token)

El módulo centralizado:
- Usa la configuración de settings.py (JWT_SECRET, etc.)
- Garantiza consistencia con la validación (jwt_validator.py)
- Provee funciones adicionales como format_jwt_info()
"""

import warnings
import argparse
from typing import List, Optional

# Importar del módulo centralizado
import sys
sys.path.insert(0, str(__file__).replace('/mcp_mock/mcp_expedientes/generate_token.py', ''))

from backoffice.auth.jwt_generator import (
    generate_jwt,
    decode_jwt_unsafe,
    format_jwt_info,
    GeneratedJWT,
    JWTGeneratorConfig
)


def _emit_deprecation_warning():
    """Emite warning de deprecación."""
    warnings.warn(
        "generate_token.py está DEPRECADO. "
        "Usar backoffice.auth.jwt_generator.generate_jwt() en su lugar.",
        DeprecationWarning,
        stacklevel=3
    )


def generate_test_token(
    exp_id: str,
    exp_tipo: str = "SUBVENCIONES",
    tarea_id: str = "TAREA-TEST-001",
    tarea_nombre: str = "TAREA_TEST",
    permisos: List[str] = None,
    mcp_servers: List[str] = None,
    secret: Optional[str] = None,
    exp_hours: int = 1
) -> str:
    """
    DEPRECADO: Usar backoffice.auth.jwt_generator.generate_jwt()

    Genera un JWT de prueba válido para testing.
    Esta función es un wrapper de retrocompatibilidad.

    Args:
        exp_id: ID del expediente (ej: "EXP-2024-001")
        exp_tipo: Tipo de expediente (ej: "SUBVENCIONES")
        tarea_id: ID de la tarea BPMN
        tarea_nombre: Nombre de la tarea
        permisos: Lista de permisos (ej: ["consulta"] o ["consulta", "gestion"])
        mcp_servers: Lista de MCP servers autorizados (default: solo expedientes)
        secret: IGNORADO - usa JWT_SECRET de settings
        exp_hours: Horas hasta expiración (default: 1)

    Returns:
        Token JWT firmado
    """
    _emit_deprecation_warning()

    # El parámetro secret se ignora - siempre usa settings.JWT_SECRET
    if secret is not None:
        warnings.warn(
            "El parámetro 'secret' es ignorado. Se usa JWT_SECRET de settings.",
            DeprecationWarning,
            stacklevel=2
        )

    result = generate_jwt(
        expediente_id=exp_id,
        tarea_id=tarea_id,
        permisos=permisos,
        expediente_tipo=exp_tipo,
        tarea_nombre=tarea_nombre,
        audiences=mcp_servers,
        expiration_hours=exp_hours
    )

    return result.token


def decode_token(token: str, secret: Optional[str] = None) -> dict:
    """
    DEPRECADO: Usar backoffice.auth.jwt_generator.decode_jwt_unsafe()

    Decodifica un token JWT para inspección (sin validar expiración).

    Args:
        token: Token JWT a decodificar
        secret: IGNORADO - usa JWT_SECRET de settings

    Returns:
        Payload decodificado del token
    """
    _emit_deprecation_warning()

    if secret is not None:
        warnings.warn(
            "El parámetro 'secret' es ignorado. Se usa JWT_SECRET de settings.",
            DeprecationWarning,
            stacklevel=2
        )

    return decode_jwt_unsafe(token)


def format_token_info(token: str, secret: Optional[str] = None) -> str:
    """
    DEPRECADO: Usar backoffice.auth.jwt_generator.format_jwt_info()

    Formatea la información de un token para visualización.

    Args:
        token: Token JWT
        secret: IGNORADO - usa JWT_SECRET de settings

    Returns:
        String formateado con la información del token
    """
    _emit_deprecation_warning()

    if secret is not None:
        warnings.warn(
            "El parámetro 'secret' es ignorado. Se usa JWT_SECRET de settings.",
            DeprecationWarning,
            stacklevel=2
        )

    return format_jwt_info(token)


def main():
    """
    DEPRECADO: Este CLI se mantiene por retrocompatibilidad.

    Uso recomendado:
        python -c "from backoffice.auth.jwt_generator import generate_jwt, format_jwt_info; ..."
    """
    parser = argparse.ArgumentParser(
        description=(
            "DEPRECADO: Usar backoffice.auth.jwt_generator\n\n"
            "Este script se mantiene por retrocompatibilidad."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
DEPRECADO - Usar el módulo centralizado:

  python -c "
  import sys; sys.path.insert(0, 'src')
  from backoffice.auth.jwt_generator import generate_jwt, format_jwt_info
  result = generate_jwt(expediente_id='EXP-2024-001')
  print(format_jwt_info(result.token))
  "
        """
    )

    parser.add_argument(
        "--exp-id",
        type=str,
        help="ID del expediente (ej: EXP-2024-001)"
    )

    parser.add_argument(
        "--exp-tipo",
        type=str,
        default="SUBVENCIONES",
        help="Tipo de expediente (default: SUBVENCIONES)"
    )

    parser.add_argument(
        "--tarea-id",
        type=str,
        default="TAREA-TEST-001",
        help="ID de la tarea BPMN (default: TAREA-TEST-001)"
    )

    parser.add_argument(
        "--tarea-nombre",
        type=str,
        default="TAREA_TEST",
        help="Nombre de la tarea BPMN (default: TAREA_TEST)"
    )

    parser.add_argument(
        "--permisos",
        nargs="+",
        default=["consulta"],
        choices=["consulta", "gestion"],
        help="Permisos a incluir (default: consulta)"
    )

    parser.add_argument(
        "--mcp-servers",
        nargs="+",
        default=["agentix-mcp-expedientes"],
        help="Lista de MCP servers autorizados (default: agentix-mcp-expedientes)"
    )

    parser.add_argument(
        "--secret",
        type=str,
        default=None,
        help="IGNORADO - siempre usa JWT_SECRET de settings"
    )

    parser.add_argument(
        "--exp-hours",
        type=int,
        default=1,
        help="Horas hasta expiración (default: 1)"
    )

    parser.add_argument(
        "--formato",
        choices=["info", "raw"],
        default="info",
        help="Formato de salida: 'info' (detallado) o 'raw' (solo token)"
    )

    parser.add_argument(
        "--decode",
        type=str,
        metavar="TOKEN",
        help="Decodificar y mostrar información de un token existente"
    )

    args = parser.parse_args()

    # Mostrar warning de deprecación
    print("=" * 60)
    print("ADVERTENCIA: Este script está DEPRECADO")
    print("Usar: backoffice.auth.jwt_generator")
    print("=" * 60)
    print()

    # Modo decodificación
    if args.decode:
        try:
            print(format_jwt_info(args.decode))
        except Exception as e:
            print(f"Error al decodificar token: {e}")
            return 1
        return 0

    # Validar que exp_id esté presente
    if not args.exp_id:
        parser.error("--exp-id es requerido (o usa --decode para decodificar un token)")

    # Generar token usando el módulo centralizado
    result = generate_jwt(
        expediente_id=args.exp_id,
        tarea_id=args.tarea_id,
        permisos=args.permisos,
        expediente_tipo=args.exp_tipo,
        tarea_nombre=args.tarea_nombre,
        audiences=args.mcp_servers,
        expiration_hours=args.exp_hours
    )

    # Mostrar según formato
    if args.formato == "raw":
        print(result.token)
    else:
        print(format_jwt_info(result.token))

    return 0


if __name__ == "__main__":
    exit(main())
