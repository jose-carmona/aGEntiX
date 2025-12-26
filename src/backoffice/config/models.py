# backoffice/config/models.py

from pydantic import BaseModel, HttpUrl
from typing import List, Literal
from pathlib import Path
import yaml


class MCPAuthConfig(BaseModel):
    """Configuración de autenticación para un MCP"""
    type: Literal["jwt", "api_key", "none"] = "jwt"
    audience: str


class MCPServerConfig(BaseModel):
    """Configuración de un servidor MCP"""
    id: str
    name: str
    description: str
    url: HttpUrl
    type: Literal["http", "stdio"] = "http"
    auth: MCPAuthConfig
    timeout: int = 30
    enabled: bool = True  # Permite habilitar/deshabilitar MCPs
    endpoint: str = "/rpc"  # Endpoint para JSON-RPC (configurable)


class MCPServersConfig(BaseModel):
    """Catálogo completo de servidores MCP"""
    mcp_servers: List[MCPServerConfig]

    @classmethod
    def load_from_file(cls, path: str) -> "MCPServersConfig":
        """Carga configuración desde archivo YAML"""
        config_path = Path(path)
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def get_enabled_servers(self) -> List[MCPServerConfig]:
        """Retorna solo los servidores MCP habilitados"""
        return [s for s in self.mcp_servers if s.enabled]
