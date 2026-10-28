"""
test_model_catalog.py - Pruebas del Catálogo, Clasificación de Capacidades y Prueba de Conectividad
Fase 3 de Miku V2: Valida capacidades explícitas (text, vision, tools, structured_output, audio_stt, native_computer_use),
origen (catalog, verified, custom), pruebas de conectividad antes de guardar y gestión de modelos personalizados.
"""

import pytest
import os
import sys
import json
import tempfile
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models_provider
from models_provider import (
    FALLBACK_CATALOG,
    get_available_models,
    get_model_capabilities,
    check_model_connectivity,
    save_custom_model,
    get_custom_models
)


# =========================================================================
# 1. CAPACIDADES EXPLÍCITAS Y ORIGEN EN EL CATÁLOGO
# =========================================================================

def test_catalog_explicit_capabilities():
    """Verifica que los modelos del catálogo tengan capacidades explícitas asignadas."""
    # Google
    google_flash = next(m for m in FALLBACK_CATALOG["google"] if m["id"] == "gemini-1.5-flash")
    assert "text" in google_flash["capabilities"]
    assert "vision" in google_flash["capabilities"]
    assert "tools" in google_flash["capabilities"]
    assert "structured_output" in google_flash["capabilities"]
    assert google_flash["origin"] == "catalog"
    assert google_flash["context_window"] >= 1000000

    # Anthropic Claude 3.5 Sonnet
    claude = next(m for m in FALLBACK_CATALOG["anthropic"] if "sonnet" in m["id"])
    assert "native_computer_use" in claude["capabilities"]
    assert "vision" in claude["capabilities"]
    assert "tools" in claude["capabilities"]

    # STT
    whisper = next(m for m in FALLBACK_CATALOG["groq"] if "whisper" in m["id"])
    assert "audio_stt" in whisper["capabilities"]
    assert "stt" in whisper["capabilities"]
    assert "text" not in whisper["capabilities"]

    # DeepSeek
    ds_chat = next(m for m in FALLBACK_CATALOG["deepseek"] if m["id"] == "deepseek-chat")
    assert "text" in ds_chat["capabilities"]
    assert "tools" in ds_chat["capabilities"]
    assert "vision" not in ds_chat["capabilities"]


def test_get_available_models_includes_origin_and_context_window():
    """Verifica que get_available_models preserve los campos origin y context_window."""
    avail = get_available_models()
    chat_list = avail.get("chat", [])
    assert len(chat_list) > 0

    first = chat_list[0]
    assert "origin" in first
    assert first["origin"] in ("catalog", "verified", "custom")
    assert "context_window" in first
    assert "capabilities" in first


# =========================================================================
# 2. PRUEBA DE CONECTIVIDAD EN VIVO (TEST MODEL CONNECTIVITY)
# =========================================================================

def test_connectivity_test_success(monkeypatch):
    """Verifica que una prueba de conectividad exitosa retorne success=True y latencia."""
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="pong"))]
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_resp

    monkeypatch.setattr(models_provider, "create_provider_client", lambda prov, mod: (mock_client, mod, prov))

    res = check_model_connectivity(provider="google", model_id="gemini-1.5-flash")
    assert res["success"] is True
    assert res["latency_ms"] >= 0
    assert "Conexión exitosa" in res["message"]
    assert res["provider"] == "google"
    assert res["model"] == "gemini-1.5-flash"


def test_connectivity_test_auth_failure(monkeypatch):
    """Verifica que ante credencial inválida devuelva mensaje claro de autenticación sin romper."""
    class AuthError(Exception):
        status_code = 401

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = AuthError("Invalid API key")

    monkeypatch.setattr(models_provider, "create_provider_client", lambda prov, mod: (mock_client, mod, prov))

    res = check_model_connectivity(provider="openai", model_id="gpt-4o")
    assert res["success"] is False
    assert "Error de autenticación" in res["message"]


def test_connectivity_test_no_client(monkeypatch):
    """Verifica respuesta cuando no hay cliente o clave configurada para el proveedor."""
    monkeypatch.setattr(models_provider, "create_provider_client", lambda prov, mod: (None, "", "none"))

    res = check_model_connectivity(provider="nvidia", model_id="meta/llama-3.3-70b-instruct")
    assert res["success"] is False
    assert "No se pudo crear cliente" in res["message"]


# =========================================================================
# 3. GESTIÓN DE MODELOS PERSONALIZADOS (CUSTOM MODELS)
# =========================================================================

def test_save_and_retrieve_custom_model(tmp_path, monkeypatch):
    """Verifica que se pueda registrar y recuperar un modelo personalizado."""
    fake_config_file = str(tmp_path / "models_config.json")
    with open(fake_config_file, "w", encoding="utf-8") as f:
        json.dump({"chat": "gemini-1.5-flash"}, f)

    monkeypatch.setattr(models_provider, "MODELS_CONFIG_FILE", fake_config_file)

    save_res = save_custom_model(
        provider="ollama",
        model_id="mistral-custom:latest",
        name="Mi Mistral Ajustado",
        capabilities=["chat", "text", "tools"],
        context_window=32768
    )
    assert save_res["success"] is True
    assert save_res["model"]["id"] == "mistral-custom:latest"
    assert save_res["model"]["origin"] == "custom"

    # Recuperar lista de custom
    customs = get_custom_models()
    assert len(customs) == 1
    assert customs[0]["id"] == "mistral-custom:latest"

    # Verificar que get_model_capabilities lo reconozca
    caps = get_model_capabilities("mistral-custom:latest", "ollama")
    assert "tools" in caps
    assert "chat" in caps


# =========================================================================
# 4. ENDPOINTS EN SERVER.PY (TESTCLIENT)
# =========================================================================

def test_server_models_test_endpoint(monkeypatch):
    """Verifica el endpoint POST /api/config/models/test a través de FastAPI TestClient."""
    from fastapi.testclient import TestClient
    import server

    # Mockear test_model_connectivity para no hacer llamadas externas
    monkeypatch.setattr(
        models_provider,
        "test_model_connectivity",
        lambda prov, mod: {"success": True, "latency_ms": 120, "model": mod, "provider": prov, "message": "OK"}
    )

    client = TestClient(server.app)
    resp = client.post("/api/config/models/test", json={"provider": "google", "model_id": "gemini-1.5-flash"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["latency_ms"] == 120


def test_server_custom_model_endpoint_blocks_on_failed_test(monkeypatch):
    """Verifica que POST /api/config/models/custom rechace el guardado si falla la prueba de conectividad con test_first=True."""
    from fastapi.testclient import TestClient
    import server

    # Simular fallo de conectividad
    monkeypatch.setattr(
        models_provider,
        "test_model_connectivity",
        lambda prov, mod: {"success": False, "latency_ms": 0, "model": mod, "provider": prov, "message": "Clave inválida"}
    )

    client = TestClient(server.app)
    resp = client.post("/api/config/models/custom", json={
        "provider": "openai",
        "model_id": "mi-modelo-no-existente",
        "test_first": True
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "error"
    assert "Prueba de conectividad fallida" in data["message"]


def test_deepseek_v4_catalog_presence():
    """Verifica que la familia DeepSeek V4 esté catalogada con sus capacidades correspondientes."""
    ds_models = {m["id"]: m for m in FALLBACK_CATALOG["deepseek"]}
    assert "deepseek-v4" in ds_models
    assert "deepseek-v4-pro" in ds_models
    assert "pro" in ds_models["deepseek-v4-pro"]["capabilities"]
    assert "tools" in ds_models["deepseek-v4"]["capabilities"]
    assert ds_models["deepseek-v4"]["context_window"] >= 128000


def test_models_selectable_flag_matches_key(monkeypatch):
    """Verifica que el flag selectable corresponda estrictamente con has_key."""
    models_provider._models_cache["timestamp"] = 0
    # Simular que solo google tiene clave
    monkeypatch.setattr(models_provider, "get_active_providers", lambda: {"google"})
    avail = get_available_models(force_refresh=True)

    for cat in ["chat", "computer_use", "pro", "stt"]:
        for m in avail.get(cat, []):
            if m["provider"] == "google":
                assert m["has_key"] is True
                assert m["selectable"] is True
            else:
                assert m["has_key"] is False
                assert m["selectable"] is False

