#!/usr/bin/env python3
"""
Simulador de invocación BPMN para testing del MCP Mock.

Este script simula el comportamiento del motor BPMN al invocar un agente:
1. Lee un expediente
2. Genera un JWT válido para la tarea
3. Configura el entorno para el MCP server
4. Muestra información de simulación

Uso:
    python simulate_bpmn.py --exp-id EXP-2024-001 --tarea-id TAREA-VALIDAR-DOC-001
    python simulate_bpmn.py --exp-id EXP-2024-001 --permisos consulta gestion
    python simulate_bpmn.py --help
"""

import json
import argparse
import sys
from pathlib import Path
from typing import List
from generate_token import generate_test_token
from resources import load_expediente


class BPMNSimulator:
    """Simulador del motor BPMN"""

    def __init__(self, data_dir: Path = None):
        """
        Inicializa el simulador.

        Args:
            data_dir: Directorio de datos (default: ./data)
        """
        if data_dir is None:
            data_dir = Path(__file__).parent / "data"
        self.data_dir = data_dir

    def simulate_task(
        self,
        exp_id: str,
        tarea_id: str = None,
        permisos: List[str] = None,
        task_prompt: str = None,
        mcp_servers: List[str] = None
    ):
        """
        Simula la ejecución de una tarea BPMN.

        Args:
            exp_id: ID del expediente
            tarea_id: ID de la tarea a ejecutar (opcional, se toma del expediente)
            permisos: Lista de permisos para el agente (default: ["consulta", "gestion"])
            task_prompt: Prompt específico de la tarea (opcional)
            mcp_servers: Lista de MCP servers autorizados (default: solo expedientes)
        """
        if permisos is None:
            permisos = ["consulta", "gestion"]

        if mcp_servers is None:
            mcp_servers = ["agentix-mcp-expedientes"]

        print(f"\n{'=' * 70}")
        print(f"SIMULACIÓN BPMN - Inicio de Tarea")
        print(f"{'=' * 70}\n")

        # 1. Cargar expediente
        print(f"[BPMN] Cargando expediente {exp_id}...")
        try:
            expediente = load_expediente(exp_id)
            print(f"[BPMN] ✓ Expediente cargado: {expediente.tipo} - {expediente.estado}")
        except Exception as e:
            print(f"[BPMN] ✗ Error al cargar expediente: {str(e)}")
            return

        # 2. Obtener información de la tarea
        tarea = expediente.metadatos.tarea_actual

        # Si no se especifica tarea_id, usar la tarea actual
        if tarea_id is None:
            tarea_id = tarea.id

        print(f"\n[BPMN] Información de la tarea:")
        print(f"  ID:              {tarea.id}")
        print(f"  Nombre:          {tarea.nombre}")
        print(f"  Tipo:            {tarea.tipo}")
        print(f"  Estado:          {tarea.estado}")
        print(f"  Responsable:     {tarea.responsable}")
        print(f"  Fecha inicio:    {tarea.fecha_inicio}")
        print(f"  Fecha límite:    {tarea.fecha_limite}")

        # 3. Generar token JWT
        print(f"\n[BPMN] Generando token JWT...")
        token = generate_test_token(
            exp_id=expediente.id,
            exp_tipo=expediente.tipo,
            tarea_id=tarea_id,
            tarea_nombre=tarea.nombre,
            permisos=permisos,
            mcp_servers=mcp_servers
        )
        print(f"[BPMN] ✓ Token generado con permisos: {', '.join(permisos)}")
        if len(mcp_servers) > 1:
            print(f"[BPMN] ✓ Autorizado para múltiples MCP servers: {', '.join(mcp_servers)}")

        # 4. Mostrar información para el agente
        print(f"\n{'=' * 70}")
        print(f"CONFIGURACIÓN PARA EL AGENTE")
        print(f"{'=' * 70}\n")

        print(f"Variables de entorno:")
        print(f"  export MCP_JWT_TOKEN='{token[:50]}...'")
        print(f"  export JWT_SECRET='test-secret-key'")

        print(f"\nConfiguración Claude Desktop:")
        print(json.dumps({
            "mcpServers": {
                "gex-expedientes": {
                    "command": "python",
                    "args": [str(Path(__file__).parent / "server_stdio.py")],
                    "env": {
                        "MCP_JWT_TOKEN": token,
                        "JWT_SECRET": "test-secret-key"
                    }
                }
            }
        }, indent=2))

        # 5. Mostrar prompt de la tarea
        if task_prompt:
            print(f"\n{'=' * 70}")
            print(f"PROMPT DE LA TAREA")
            print(f"{'=' * 70}\n")
            print(task_prompt)

        # 6. Mostrar contexto del expediente
        print(f"\n{'=' * 70}")
        print(f"CONTEXTO DEL EXPEDIENTE")
        print(f"{'=' * 70}\n")

        print(f"Datos del solicitante:")
        if hasattr(expediente.datos, "get"):
            solicitante = expediente.datos.get("solicitante", {})
        else:
            solicitante = expediente.datos.get("solicitante", {}) if isinstance(expediente.datos, dict) else {}

        if solicitante:
            print(f"  Nombre: {solicitante.get('nombre', 'N/A')}")
            print(f"  NIF:    {solicitante.get('nif', 'N/A')}")
            print(f"  Email:  {solicitante.get('email', 'N/A')}")

        print(f"\nDocumentos ({len(expediente.documentos)}):")
        for doc in expediente.documentos:
            estado = "✓ Validado" if doc.validado else "⧗ Pendiente" if doc.validado is None else "✗ Rechazado"
            print(f"  - {doc.id}: {doc.nombre} ({doc.tipo}) - {estado}")

        print(f"\nHistorial reciente ({len(expediente.historial)} entradas):")
        for entry in expediente.historial[-3:]:  # Últimas 3 entradas
            print(f"  - [{entry.fecha}] {entry.usuario} ({entry.tipo}): {entry.accion}")

        # 7. Mostrar posibles siguientes tareas
        if expediente.metadatos.siguiente_tarea.candidatos:
            print(f"\n{'=' * 70}")
            print(f"POSIBLES SIGUIENTES TAREAS")
            print(f"{'=' * 70}\n")

            for candidato in expediente.metadatos.siguiente_tarea.candidatos:
                print(f"  - {candidato.nombre} (ID: {candidato.id})")
                print(f"    Condición: {candidato.condicion}")

        print(f"\n{'=' * 70}")
        print(f"FIN DE LA SIMULACIÓN")
        print(f"{'=' * 70}\n")


def main():
    """Punto de entrada para uso desde línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Simula la invocación BPMN de un agente para testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:

  # Simulación básica con tarea actual del expediente
  python simulate_bpmn.py --exp-id EXP-2024-001

  # Simulación con permisos específicos
  python simulate_bpmn.py --exp-id EXP-2024-001 --permisos consulta

  # Simulación con tarea específica
  python simulate_bpmn.py --exp-id EXP-2024-001 --tarea-id TAREA-CUSTOM-001

  # Simulación con múltiples MCP servers
  python simulate_bpmn.py --exp-id EXP-2024-001 \\
    --mcp-servers agentix-mcp-expedientes agentix-mcp-normativa

  # Simulación con prompt personalizado
  python simulate_bpmn.py --exp-id EXP-2024-001 --prompt "Valida los documentos"
        """
    )

    parser.add_argument(
        "--exp-id",
        type=str,
        required=True,
        help="ID del expediente a procesar (ej: EXP-2024-001)"
    )

    parser.add_argument(
        "--tarea-id",
        type=str,
        help="ID de la tarea BPMN (opcional, se toma del expediente)"
    )

    parser.add_argument(
        "--permisos",
        nargs="+",
        default=["consulta", "gestion"],
        choices=["consulta", "gestion"],
        help="Permisos a otorgar al agente (default: consulta gestion)"
    )

    parser.add_argument(
        "--mcp-servers",
        nargs="+",
        default=["agentix-mcp-expedientes"],
        help="Lista de MCP servers autorizados (default: agentix-mcp-expedientes)"
    )

    parser.add_argument(
        "--prompt",
        type=str,
        help="Prompt específico para la tarea"
    )

    args = parser.parse_args()

    # Crear simulador y ejecutar
    simulator = BPMNSimulator()

    try:
        simulator.simulate_task(
            exp_id=args.exp_id,
            tarea_id=args.tarea_id,
            permisos=args.permisos,
            task_prompt=args.prompt,
            mcp_servers=args.mcp_servers
        )
    except Exception as e:
        print(f"\n[ERROR] Error en simulación: {str(e)}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
