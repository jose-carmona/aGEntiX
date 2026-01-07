"""
MCP Mock Servers - Servidores MCP de prueba para aGEntiX.

Este paquete contiene servidores MCP mock para desarrollo y testing:

- **mcp_expedientes**: Gestión de expedientes (consulta, documentos, historial)
- **mcp_documentacion**: Documentación de tipos de expediente (normativa, instrucciones, plantillas)

El servidor HTTP unificado (puerto 8000) expone todas las tools y resources
de ambos módulos con autenticación JWT compartida.

Módulos compartidos:
- auth.py: Validación JWT y permisos
- models.py: Modelos de datos Pydantic
- data/: Datos mock compartidos

Uso:
    cd src/mcp_mock/mcp_expedientes
    python -m uvicorn server_http:app --reload --port 8000
"""
