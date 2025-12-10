# tests/api/test_health_endpoints.py

"""
Tests para endpoints de health y utilidades.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_root_endpoint_returns_api_info():
    """Test: Endpoint raíz retorna información de la API"""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "aGEntiX API"
    assert data["version"] == "1.0.0"
    assert "docs" in data
    assert "endpoints" in data


def test_health_endpoint_returns_healthy():
    """Test: Health check retorna healthy"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "dependencies" in data


def test_metrics_endpoint_is_accessible():
    """Test: Endpoint de métricas Prometheus es accesible"""
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]

    # Verificar que contiene métricas básicas de FastAPI
    content = response.text
    assert "http_requests_total" in content or "python_info" in content


def test_openapi_docs_accessible():
    """Test: Documentación OpenAPI es accesible"""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert data["info"]["title"] == "aGEntiX API"
    assert "paths" in data
