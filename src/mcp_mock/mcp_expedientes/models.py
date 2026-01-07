"""
Re-exportación del módulo models compartido.

Este archivo mantiene compatibilidad con imports existentes.
La implementación real está en src/mcp_mock/models.py
"""

# Re-exportar todo desde el módulo compartido
from ..models import (
    Solicitante,
    Documento,
    EntradaHistorial,
    FlujoBPMN,
    TareaActual,
    TareaCompletada,
    CandidatoSiguienteTarea,
    SiguienteTarea,
    Metadatos,
    Expediente,
    JWTClaims,
)

__all__ = [
    "Solicitante",
    "Documento",
    "EntradaHistorial",
    "FlujoBPMN",
    "TareaActual",
    "TareaCompletada",
    "CandidatoSiguienteTarea",
    "SiguienteTarea",
    "Metadatos",
    "Expediente",
    "JWTClaims",
]
