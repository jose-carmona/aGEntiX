#!/usr/bin/env python3
"""
Ejemplo de uso del sistema de back-office de agentes IA.

IMPORTANTE: Antes de ejecutar este script:
1. Iniciar el servidor MCP Expedientes:
   cd mcp-mock/mcp-expedientes
   python -m mcp_expedientes.server_http

2. Generar un token JWT válido:
   python -m mcp_expedientes.generate_token EXP-2024-001
"""

import asyncio
from backoffice.executor_factory import create_default_executor
from backoffice.models import AgentConfig
from backoffice.config import settings


async def ejemplo_validador_documental():
    """Ejemplo: Validar documentación de un expediente"""
    print("=" * 60)
    print("EJEMPLO: ValidadorDocumental")
    print("=" * 60)

    # 1. Crear executor
    executor = create_default_executor(
        mcp_config_path=settings.MCP_CONFIG_PATH,
        jwt_secret=settings.JWT_SECRET
    )

    # 2. Configurar agente
    agent_config = AgentConfig(
        nombre="ValidadorDocumental",
        system_prompt="Eres un validador de documentación",
        modelo="claude-3-5-sonnet-20241022",
        prompt_tarea="Valida que todos los documentos estén presentes",
        herramientas=["consultar_expediente", "actualizar_datos", "añadir_anotacion"]
    )

    # 3. Token JWT (IMPORTANTE: Generar uno válido con generate_token.py)
    # Para este ejemplo, asumimos que tienes un token válido
    print("\n⚠️  IMPORTANTE: Necesitas un token JWT válido")
    print("   Genera uno con: cd mcp-mock/mcp-expedientes && python -m mcp_expedientes.generate_token EXP-2024-001")
    print("\nPega tu token JWT aquí (o presiona Enter para usar token de ejemplo):")

    token = input().strip()
    if not token:
        print("⚠️  Usando token de ejemplo (probablemente expirado)")
        # Este token es solo un ejemplo y probablemente esté expirado
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ejemplo.firma"

    # 4. Ejecutar agente
    print(f"\n🚀 Ejecutando ValidadorDocumental para expediente EXP-2024-001...")

    resultado = await executor.execute(
        token=token,
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-VALIDAR-DOC-001",
        agent_config=agent_config
    )

    # 5. Mostrar resultado
    print("\n" + "=" * 60)
    print("RESULTADO")
    print("=" * 60)

    if resultado.success:
        print(f"✅ Agente ejecutado exitosamente!")
        print(f"\n📋 Run ID: {resultado.agent_run_id}")
        print(f"\n💬 Mensaje: {resultado.resultado.get('mensaje', 'N/A')}")
        print(f"\n🔧 Herramientas usadas: {', '.join(resultado.herramientas_usadas)}")

        print(f"\n📝 Log de auditoría ({len(resultado.log_auditoria)} entradas):")
        for i, log in enumerate(resultado.log_auditoria, 1):
            print(f"   {i}. {log}")

        if resultado.resultado.get('datos_actualizados'):
            print(f"\n💾 Datos actualizados:")
            for campo, valor in resultado.resultado['datos_actualizados'].items():
                print(f"   - {campo}: {valor}")

    else:
        print(f"❌ Error al ejecutar agente")
        print(f"\n🚫 Código: {resultado.error.codigo}")
        print(f"📄 Mensaje: {resultado.error.mensaje}")
        if resultado.error.detalle:
            print(f"🔍 Detalle: {resultado.error.detalle}")

        if resultado.log_auditoria:
            print(f"\n📝 Log de auditoría hasta el error:")
            for i, log in enumerate(resultado.log_auditoria, 1):
                print(f"   {i}. {log}")


async def ejemplo_analizador_subvencion():
    """Ejemplo: Analizar solicitud de subvención"""
    print("\n\n" + "=" * 60)
    print("EJEMPLO: AnalizadorSubvencion")
    print("=" * 60)

    executor = create_default_executor(
        mcp_config_path=settings.MCP_CONFIG_PATH,
        jwt_secret=settings.JWT_SECRET
    )

    agent_config = AgentConfig(
        nombre="AnalizadorSubvencion",
        system_prompt="Eres un analizador de subvenciones",
        modelo="claude-3-5-sonnet-20241022",
        prompt_tarea="Analiza si el solicitante cumple los requisitos",
        herramientas=["consultar_expediente", "actualizar_datos", "añadir_anotacion"]
    )

    print("\n🔍 Analizando solicitud de subvención...")
    print("   (Mock: siempre aprueba si documentación válida)")

    # Para este ejemplo, asumir token válido del usuario
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ejemplo.firma"

    resultado = await executor.execute(
        token=token,
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-ANALIZAR-001",
        agent_config=agent_config
    )

    if resultado.success:
        print(f"\n✅ Análisis completado")
        print(f"   Resultado: {resultado.resultado.get('mensaje', 'N/A')}")
    else:
        print(f"\n❌ Error: {resultado.error.codigo}")


async def ejemplo_generador_informe():
    """Ejemplo: Generar informe del expediente"""
    print("\n\n" + "=" * 60)
    print("EJEMPLO: GeneradorInforme")
    print("=" * 60)

    executor = create_default_executor(
        mcp_config_path=settings.MCP_CONFIG_PATH,
        jwt_secret=settings.JWT_SECRET
    )

    agent_config = AgentConfig(
        nombre="GeneradorInforme",
        system_prompt="Eres un generador de informes",
        modelo="claude-3-5-sonnet-20241022",
        prompt_tarea="Genera un informe resumiendo el estado del expediente",
        herramientas=["consultar_expediente", "actualizar_datos", "añadir_anotacion"]
    )

    print("\n📄 Generando informe...")

    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ejemplo.firma"

    resultado = await executor.execute(
        token=token,
        expediente_id="EXP-2024-001",
        tarea_id="TAREA-INFORME-001",
        agent_config=agent_config
    )

    if resultado.success:
        print(f"\n✅ Informe generado")
        informe = resultado.resultado.get('informe', {})
        if informe:
            print(f"\n📊 Resumen del informe:")
            resumen = informe.get('resumen', {})
            for key, value in resumen.items():
                print(f"   - {key}: {value}")


async def main():
    """Función principal que ejecuta todos los ejemplos"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     aGEntiX - Sistema de Agentes IA (Paso 1: Mock)          ║
║                                                              ║
║  Demostración del back-office con arquitectura multi-MCP    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    print("🎯 Este script demuestra los tres agentes mock disponibles:\n")
    print("   1. ValidadorDocumental - Valida documentación completa")
    print("   2. AnalizadorSubvencion - Analiza requisitos")
    print("   3. GeneradorInforme - Genera informes resumidos")

    print("\n⚙️  Configuración actual:")
    print(f"   - MCP Config: {settings.MCP_CONFIG_PATH}")
    print(f"   - Log Dir: {settings.LOG_DIR}")
    print(f"   - JWT Algorithm: {settings.JWT_ALGORITHM}")

    try:
        # Ejecutar ejemplo principal
        await ejemplo_validador_documental()

        # Comentar estas líneas si no tienes un token válido
        # await ejemplo_analizador_subvencion()
        # await ejemplo_generador_informe()

    except Exception as e:
        print(f"\n❌ Error inesperado: {type(e).__name__}")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("FIN DE LA DEMOSTRACIÓN")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
