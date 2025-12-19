#!/usr/bin/env python3
"""
Generador de tokens JWT para testing del MCP Mock de Expedientes.

Este script permite generar tokens JWT válidos para probar el servidor MCP.
Puede usarse tanto como librería Python como desde la línea de comandos.

Uso como librería:
    from generate_token import generate_test_token

    token = generate_test_token(
        exp_id="EXP-2024-001",
        exp_tipo="SUBVENCIONES",
        tarea_id="TAREA-001",
        tarea_nombre="VALIDAR_DOCUMENTACION",
        permisos=["consulta", "gestion"]
    )

Uso desde CLI:
    python generate_token.py --exp-id EXP-2024-001 --permisos consulta gestion
    python generate_token.py --exp-id EXP-2024-001 --formato raw
    python generate_token.py --help
"""

import jwt
import uuid
import argparse
from datetime import datetime, timedelta
from typing import List


def generate_test_token(
    exp_id: str,
    exp_tipo: str = "SUBVENCIONES",
    tarea_id: str = "TAREA-TEST-001",
    tarea_nombre: str = "TAREA_TEST",
    permisos: List[str] = None,
    mcp_servers: List[str] = None,
    secret: str = "test-secret-key",
    exp_hours: int = 1
) -> str:
    """
    Genera un JWT de prueba válido para testing.

    Args:
        exp_id: ID del expediente (ej: "EXP-2024-001")
        exp_tipo: Tipo de expediente (ej: "SUBVENCIONES")
        tarea_id: ID de la tarea BPMN
        tarea_nombre: Nombre de la tarea
        permisos: Lista de permisos (ej: ["consulta"] o ["consulta", "gestion"])
        mcp_servers: Lista de MCP servers autorizados (default: solo expedientes)
        secret: Clave secreta para firma (default: test-secret-key)
        exp_hours: Horas hasta expiración (default: 1)

    Returns:
        Token JWT firmado
    """
    if permisos is None:
        permisos = ["consulta"]

    if mcp_servers is None:
        mcp_servers = ["agentix-mcp-expedientes"]

    now = datetime.utcnow()
    payload = {
        "sub": "Automático",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=exp_hours)).timestamp()),
        "nbf": int(now.timestamp()),
        "iss": "agentix-bpmn",
        "aud": mcp_servers if len(mcp_servers) > 1 else mcp_servers[0],
        "jti": str(uuid.uuid4()),
        "exp_id": exp_id,
        "exp_tipo": exp_tipo,
        "tarea_id": tarea_id,
        "tarea_nombre": tarea_nombre,
        "permisos": permisos
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, secret: str = "test-secret-key") -> dict:
    """
    Decodifica un token JWT para inspección (sin validar expiración).

    Args:
        token: Token JWT a decodificar
        secret: Clave secreta

    Returns:
        Payload decodificado del token
    """
    return jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        options={"verify_exp": False}
    )


def format_token_info(token: str, secret: str = "test-secret-key") -> str:
    """
    Formatea la información de un token para visualización.

    Args:
        token: Token JWT
        secret: Clave secreta

    Returns:
        String formateado con la información del token
    """
    payload = decode_token(token, secret)

    lines = [
        "=" * 60,
        "TOKEN JWT GENERADO",
        "=" * 60,
        "",
        "Claims:",
        f"  Subject (sub):        {payload.get('sub')}",
        f"  Emisor (iss):         {payload.get('iss')}",
        f"  Audiencia (aud):      {payload.get('aud')}",
        f"  Token ID (jti):       {payload.get('jti')}",
        "",
        "Claims de Expediente:",
        f"  Expediente ID:        {payload.get('exp_id')}",
        f"  Tipo:                 {payload.get('exp_tipo')}",
        "",
        "Claims de Tarea BPMN:",
        f"  Tarea ID:             {payload.get('tarea_id')}",
        f"  Tarea Nombre:         {payload.get('tarea_nombre')}",
        "",
        "Permisos:",
        f"  {', '.join(payload.get('permisos', []))}",
        "",
        "Timestamps:",
        f"  Emitido (iat):        {datetime.fromtimestamp(payload.get('iat')).isoformat()}",
        f"  Válido desde (nbf):   {datetime.fromtimestamp(payload.get('nbf')).isoformat()}",
        f"  Expira (exp):         {datetime.fromtimestamp(payload.get('exp')).isoformat()}",
        "",
        "Token completo:",
        f"  {token}",
        "",
        "=" * 60
    ]

    return "\n".join(lines)


def main():
    """Punto de entrada para uso desde línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Genera tokens JWT para testing del MCP Mock de Expedientes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:

  # Token básico con solo lectura
  python generate_token.py --exp-id EXP-2024-001

  # Token con permisos de lectura y escritura
  python generate_token.py --exp-id EXP-2024-001 --permisos consulta gestion

  # Token para múltiples MCP servers
  python generate_token.py --exp-id EXP-2024-001 \\
    --mcp-servers agentix-mcp-expedientes agentix-mcp-normativa

  # Token con expiración personalizada (24 horas)
  python generate_token.py --exp-id EXP-2024-001 --exp-hours 24

  # Solo el token (sin formato, útil para scripts)
  python generate_token.py --exp-id EXP-2024-001 --formato raw

  # Decodificar un token existente
  python generate_token.py --decode "eyJhbGc..."
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
        default="test-secret-key",
        help="Clave secreta para firma (default: test-secret-key)"
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

    # Modo decodificación
    if args.decode:
        try:
            print(format_token_info(args.decode, args.secret))
        except Exception as e:
            print(f"Error al decodificar token: {e}")
            return 1
        return 0

    # Validar que exp_id esté presente
    if not args.exp_id:
        parser.error("--exp-id es requerido (o usa --decode para decodificar un token)")

    # Generar token
    token = generate_test_token(
        exp_id=args.exp_id,
        exp_tipo=args.exp_tipo,
        tarea_id=args.tarea_id,
        tarea_nombre=args.tarea_nombre,
        permisos=args.permisos,
        mcp_servers=args.mcp_servers,
        secret=args.secret,
        exp_hours=args.exp_hours
    )

    # Mostrar según formato
    if args.formato == "raw":
        print(token)
    else:
        print(format_token_info(token, args.secret))

    return 0


if __name__ == "__main__":
    exit(main())
