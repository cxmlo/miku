import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import security_manager
from fastapi.testclient import TestClient
from server import app

@pytest.fixture
def client():
    return TestClient(app)

def test_execution_modes_info_endpoint(client):
    """Verifica que el endpoint /api/config/execution_mode devuelva los modos full, sandbox y restricted"""
    resp = client.get("/api/config/execution_mode")
    assert resp.status_code == 200
    data = resp.json()
    assert "current_mode" in data
    assert "available_modes" in data
    mode_ids = [m["id"] for m in data["available_modes"]]
    assert "full" in mode_ids
    assert "sandbox" in mode_ids
    assert "restricted" in mode_ids

def test_execution_mode_update_endpoint(client):
    """Verifica que el endpoint POST /api/config/execution_mode actualice el modo"""
    original = security_manager.get_execution_mode()
    try:
        resp = client.post("/api/config/execution_mode", json={"mode": "sandbox"})
        assert resp.status_code == 200
        assert resp.json()["current_mode"] == "sandbox"
        assert security_manager.get_execution_mode() == "sandbox"
    finally:
        security_manager.set_execution_mode(original)

def test_sandbox_path_restrictions():
    """Verifica que el modo sandbox bloquee modificaciones en carpetas del sistema"""
    # Ruta dentro del workspace permitida
    allowed, _ = security_manager.is_path_allowed("local_file.txt", write=True, mode="sandbox")
    assert allowed is True

    # Ruta crítica del sistema bloqueada
    blocked, reason = security_manager.is_path_allowed("C:\\Windows\\System32\\cmd.exe", write=True, mode="sandbox")
    assert blocked is False
    assert "Sandbox" in reason or "Protección" in reason

def test_restricted_mode_blocks_destructive_actions():
    """Verifica que el modo restringido bloquee comandos de consola y ejecución de scripts"""
    cmd_allowed, reason_cmd, _ = security_manager.is_command_allowed("dir", mode="restricted")
    assert cmd_allowed is False
    assert "Restringido" in reason_cmd

    code_allowed, reason_code = security_manager.is_code_execution_allowed(mode="restricted")
    assert code_allowed is False
    assert "Restringido" in reason_code

    write_allowed, reason_write = security_manager.is_path_allowed("archivo.txt", write=True, mode="restricted")
    assert write_allowed is False
    assert "Restringido" in reason_write

def test_full_mode_allows_execution():
    """Verifica que el modo full permita comandos normales"""
    cmd_allowed, _, _ = security_manager.is_command_allowed("echo Hola", mode="full")
    assert cmd_allowed is True
    code_allowed, _ = security_manager.is_code_execution_allowed(mode="full")
    assert code_allowed is True
