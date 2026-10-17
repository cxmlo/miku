import pytest
from fastapi.testclient import TestClient
import os
import sys

# Asegurar que la raíz del proyecto está en sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app

@pytest.fixture
def client():
    return TestClient(app)

def test_mouse_endpoint(client):
    """Verifica que el endpoint /mouse responda con coordenadas numéricas x, y"""
    response = client.get("/mouse")
    assert response.status_code == 200
    data = response.json()
    assert "x" in data and "y" in data
    assert isinstance(data["x"], (int, float))
    assert isinstance(data["y"], (int, float))

def test_models_config_endpoint(client):
    """Verifica que /api/config/models retorne la estructura con categorías chat, pro, computer_use y stt"""
    response = client.get("/api/config/models")
    assert response.status_code == 200
    data = response.json()
    assert "current" in data
    assert "available" in data
    avail = data["available"]
    assert "chat" in avail
    assert "pro" in avail
    assert "computer_use" in avail
    assert "stt" in avail

def test_api_keys_endpoint(client):
    """Verifica que /api/config/keys enmascare las claves configuradas"""
    response = client.get("/api/config/keys")
    assert response.status_code == 200
    data = response.json()
    assert "keys" in data
    assert isinstance(data["keys"], dict)

def test_audio_devices_endpoint(client):
    """Verifica que /api/audio/devices devuelva la lista de dispositivos de audio"""
    response = client.get("/api/audio/devices")
    assert response.status_code == 200
    data = response.json()
    assert "devices" in data
    assert isinstance(data["devices"], list)

def test_detectable_apps_endpoint(client):
    """Verifica que /api/apps/detectable devuelva el catálogo de juegos y aplicaciones para alertas"""
    response = client.get("/api/apps/detectable")
    assert response.status_code == 200
    data = response.json()
    assert "apps" in data
    assert len(data["apps"]) > 0
