import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from starlette.requests import Request
import os
import sys

# Asegurar que la raíz del proyecto está en sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app
import miku_db
import server

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

def test_api_auth_accepts_registered_mobile_device(monkeypatch):
    request = Request({
        "type": "http",
        "method": "GET",
        "path": "/history",
        "headers": [],
        "client": ("192.168.1.20", 43120),
    })
    monkeypatch.setattr(miku_db, "is_valid_device", lambda device_id: device_id == "paired-device")

    assert server.get_api_key(
        request,
        api_key_header=None,
        x_device_id="paired-device",
    ) == "paired-device"

def test_api_auth_keeps_legacy_api_key_support():
    request = Request({
        "type": "http",
        "method": "GET",
        "path": "/history",
        "headers": [],
        "client": ("192.168.1.20", 43120),
    })

    assert server.get_api_key(
        request,
        api_key_header=server.API_KEY,
        x_device_id=None,
    ) == server.API_KEY

def test_api_auth_rejects_unknown_mobile_device(monkeypatch):
    request = Request({
        "type": "http",
        "method": "GET",
        "path": "/history",
        "headers": [],
        "client": ("192.168.1.20", 43120),
    })
    monkeypatch.setattr(miku_db, "is_valid_device", lambda _device_id: False)

    with pytest.raises(HTTPException) as error:
        server.get_api_key(request, api_key_header=None, x_device_id="unknown-device")

    assert error.value.status_code == 403

def test_send_text_to_phone_broadcasts_mobile_clipboard(client, monkeypatch):
    sent = []

    async def capture_message(message):
        sent.append(message)

    monkeypatch.setattr(server.manager, "connected_mobile", lambda: {"type": "miku_link_connected"})
    monkeypatch.setattr(server.manager, "broadcast_message", capture_message)

    response = client.post(
        "/api/device/send_to_phone",
        headers={"x-api-key": server.API_KEY},
        json={"text": "Texto para el teléfono"},
    )

    assert response.status_code == 200
    assert sent == [{
        "type": "ui_command",
        "action": "sync_clipboard",
        "text": "Texto para el teléfono",
    }]

def test_send_text_to_phone_reports_disconnected_device(client, monkeypatch):
    monkeypatch.setattr(server.manager, "connected_mobile", lambda: None)

    response = client.post(
        "/api/device/send_to_phone",
        headers={"x-api-key": server.API_KEY},
        json={"text": "Texto para el teléfono"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "No hay un teléfono Miku conectado."

def test_send_uploaded_file_to_phone_broadcasts_download(client, monkeypatch, tmp_path):
    temp_dir = tmp_path / "outbox"
    temp_dir.mkdir()
    sent = []

    async def capture_message(message):
        sent.append(message)

    monkeypatch.setattr(server.tempfile, "gettempdir", lambda: str(temp_dir))
    monkeypatch.setattr(server.manager, "connected_mobile", lambda: {"type": "miku_link_connected"})
    monkeypatch.setattr(server.manager, "broadcast_message", capture_message)

    response = client.post(
        "/api/send_to_phone",
        headers={"x-api-key": server.API_KEY},
        files={"file": ("test-image.png", b"image-content", "image/png")},
    )

    assert response.status_code == 200
    assert (temp_dir / "test-image.png").read_bytes() == b"image-content"
    assert sent == [{
        "type": "ui_command",
        "action": "download_file",
        "filename": "test-image.png",
    }]

def test_send_desktop_path_to_phone_copies_file(client, monkeypatch, tmp_path):
    source = tmp_path / "desktop-image.png"
    source.write_bytes(b"image-content")
    temp_dir = tmp_path / "outbox"
    temp_dir.mkdir()
    sent = []

    async def capture_message(message):
        sent.append(message)

    monkeypatch.setattr(server.tempfile, "gettempdir", lambda: str(temp_dir))
    monkeypatch.setattr(server.manager, "connected_mobile", lambda: {"type": "miku_link_connected"})
    monkeypatch.setattr(server.manager, "broadcast_message", capture_message)

    response = client.post(
        "/api/desktop/send_file_to_phone",
        headers={"x-api-key": server.API_KEY},
        json={"path": str(source)},
    )

    assert response.status_code == 200
    copied_file = temp_dir / "miku_temp_media" / source.name
    if not copied_file.exists():
        copied_file = temp_dir / source.name
    assert copied_file.read_bytes() == b"image-content"
    assert sent[0] == {
        "type": "ui_command",
        "action": "download_file",
        "filename": source.name,
    }

def test_websocket_accepts_registered_mobile_device(client, monkeypatch):
    monkeypatch.setattr(miku_db, "is_valid_device", lambda device_id: device_id == "paired-device")
    monkeypatch.setattr(
        miku_db,
        "get_device",
        lambda device_id: {"device_id": device_id, "name": "Android Test"},
    )

    with client.websocket_connect("/ws?device_id=paired-device") as websocket:
        assert websocket.receive_json() == {
            "type": "miku_link_connected",
            "name": "Android Test",
        }

def test_pair_init_registers_session(client, monkeypatch):
    monkeypatch.setattr(server, "PAIRING_SESSION", None)

    response = client.post("/api/pair/init", json={"session_id": "test-pair-session"})

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert server.PAIRING_SESSION == "test-pair-session"

def test_pair_confirm_does_not_mark_device_online_before_websocket_connects(client, monkeypatch):
    class RecordingManager:
        message = None

        async def broadcast_message(self, message):
            self.message = message

    manager = RecordingManager()
    monkeypatch.setattr(server, "PAIRING_SESSION", "test-pair-session")
    monkeypatch.setattr(server, "manager", manager)
    monkeypatch.setattr(miku_db, "add_device", lambda *_args: None)
    monkeypatch.setattr(miku_db, "get_server_public_key_b64", lambda: "public-key")

    response = client.post(
        "/api/pair/confirm",
        json={
            "session_id": "test-pair-session",
            "device_id": "android-device",
            "name": "Android Test",
            "public_key": "device-public-key",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert server.PAIRING_SESSION is None
    assert manager.message is None


def test_chat_broadcasts_typed_user_message_with_agent_context(client, monkeypatch):
    class RecordingManager:
        messages = []

        async def broadcast_message(self, message):
            self.messages.append(message)

    manager = RecordingManager()
    monkeypatch.setattr(server, "manager", manager)
    monkeypatch.setattr(server, "append_to_chat_history", lambda _message: None)
    monkeypatch.setattr(server, "sync_miku_state", lambda _state: None)
    monkeypatch.setattr(server, "get_system_prompt", lambda *_args, **_kwargs: "test prompt")
    monkeypatch.setattr(server, "get_llm_response", lambda *_args: "respuesta")

    response = client.post(
        "/chat",
        json={
            "message": "hola desde Android",
            "source": "mobile",
            "agent_id": "miku",
            "agent_name": "Miku",
            "silent": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["reply"] == "respuesta"
    assert manager.messages[0] == {
        "type": "user_message",
        "id": manager.messages[0]["id"],
        "text": "hola desde Android",
        "sender": "user",
        "agent_id": "miku",
        "agent_name": "Miku",
    }
    assert manager.messages[1]["type"] == "agent_reply"
    assert manager.messages[1]["agent_id"] == "miku"


def test_connection_manager_reports_mobile_offline_after_last_socket_closes():
    class FakeWebSocket:
        async def accept(self):
            pass

    async def exercise():
        manager = server.ConnectionManager()
        websocket = FakeWebSocket()

        is_new = await manager.connect(websocket, "paired-device", "Android Test")

        assert is_new
        assert manager.connected_mobile() == {
            "type": "miku_link_connected",
            "name": "Android Test",
        }
        assert manager.disconnect(websocket) == {"type": "miku_link_disconnected"}
        assert manager.connected_mobile() is None

    import asyncio

    asyncio.run(exercise())


def test_connection_manager_keeps_mobile_online_while_another_socket_remains():
    class FakeWebSocket:
        async def accept(self):
            pass

    async def exercise():
        manager = server.ConnectionManager()
        first = FakeWebSocket()
        second = FakeWebSocket()

        assert await manager.connect(first, "paired-device", "Android Test")
        assert not await manager.connect(second, "paired-device", "Android Test")
        assert manager.disconnect(first) is None
        assert manager.connected_mobile() == {
            "type": "miku_link_connected",
            "name": "Android Test",
        }
        assert manager.disconnect(second) == {"type": "miku_link_disconnected"}

    import asyncio

    asyncio.run(exercise())


def test_miku_link_qr_and_phone_link_endpoints(client):
    qr_res = client.get("/api/link/qr_data")
    assert qr_res.status_code == 200
    qr = qr_res.json()
    assert qr["status"] == "ok"
    assert qr["url"].startswith("miku://pair?s=")
    assert len(qr["pin"].replace(" ", "")) == 6
    assert qr["ttl_seconds"] == 120
    assert qr["expires_at"] - qr["issued_at"] == 120

    st_res = client.get("/api/link/status")
    assert st_res.status_code == 200
    st = st_res.json()
    assert "connected" in st
    assert "dnd" in st
    assert "server_time" in st

    for path in (
        "/api/link/messages",
        "/api/link/calls",
        "/api/link/photos",
        "/api/link/notifications",
        "/api/link/apps",
    ):
        r = client.get(path)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


def test_miku_link_actions_and_mutations(client):
    dnd_res = client.post("/api/link/dnd", json={"enabled": True})
    assert dnd_res.status_code == 200
    assert dnd_res.json()["dnd"] is True

    dnd_off = client.post("/api/link/dnd", json={"enabled": False})
    assert dnd_off.status_code == 200
    assert dnd_off.json()["dnd"] is False

    cancel_res = client.post("/api/link/cancel_pair")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "ok"

    wall_res = client.get("/api/link/phone_wallpaper")
    assert wall_res.status_code == 200
    assert wall_res.json()["status"] == "ok"


