"""
test_provider_resilience.py - Pruebas de resiliencia de proveedores, verificación de capacidades y errores transitorios
Fase 2 de Miku V2: Comprueba clasificación de errores (429/503 vs 401/403/404), rotación finita de claves,
verificación estricta de visión para computer_use y prevención de fallbacks silenciosos ante credenciales inválidas.
"""

import pytest
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models_provider
from models_provider import (
    identify_provider_for_model,
    supports_capability,
    get_model_capabilities,
    classify_api_error,
    is_transient_error,
    is_auth_error,
    is_not_found_error,
    get_user_friendly_error_message,
    rotate_provider_key,
    get_active_key_for_provider,
    get_provider_keys,
    execute_completion_with_resilience,
    get_client_and_model,
    MODEL_ALIASES
)


# =========================================================================
# 1. IDENTIFICACIÓN Y NORMALIZACIÓN DE MODELOS
# =========================================================================

def test_identify_provider_clean():
    assert identify_provider_for_model("gemini-1.5-flash") == "google"
    assert identify_provider_for_model("gemini-2.0-flash") == "google"
    assert identify_provider_for_model("llama-3.3-70b-versatile") == "groq"
    assert identify_provider_for_model("deepseek-chat") == "deepseek"
    assert identify_provider_for_model("deepseek-reasoner") == "deepseek"
    assert identify_provider_for_model("gpt-4o") == "openai"
    assert identify_provider_for_model("gpt-4o-mini") == "openai"
    assert identify_provider_for_model("claude-3-5-sonnet-20241022") == "anthropic"
    assert identify_provider_for_model("anthropic/claude-3.5-sonnet") == "openrouter"
    assert identify_provider_for_model("deepseek/deepseek-r1") == "openrouter"
    assert identify_provider_for_model("mistral:latest") == "ollama"


def test_model_aliases():
    assert MODEL_ALIASES.get("gemini-1.5-flash-latest") == "gemini-1.5-flash"
    assert MODEL_ALIASES.get("gemini-1.5-pro-latest") == "gemini-1.5-pro"
    assert identify_provider_for_model("deepseek-v4") == "deepseek"
    assert identify_provider_for_model("deepseek-v4-pro") == "deepseek"


# =========================================================================
# 2. CAPACIDADES ESTRICTAS (VISIÓN MULTIMODAL VS TEXTO/CÓDIGO)
# =========================================================================

def test_computer_use_vision_capabilities():
    # Modelos multimodales que SÍ soportan visión para computer_use
    assert supports_capability("gemini-1.5-flash", "computer_use") is True
    assert supports_capability("gemini-1.5-pro", "computer_use") is True
    assert supports_capability("gemini-2.0-flash", "computer_use") is True
    assert supports_capability("gpt-4o", "computer_use") is True
    assert supports_capability("gpt-4o-mini", "computer_use") is True
    assert supports_capability("claude-3-5-sonnet-20241022", "computer_use") is True
    assert supports_capability("anthropic/claude-3.5-sonnet", "computer_use") is True
    assert supports_capability("deepseek-flash", "computer_use") is True

    # Modelos que NO soportan visión para computer_use (texto puro sin visión)
    assert supports_capability("deepseek-chat", "computer_use") is False
    assert supports_capability("deepseek-reasoner", "computer_use") is False
    assert supports_capability("llama-3.3-70b-versatile", "computer_use") is False
    assert supports_capability("deepseek-r1-distill-llama-70b", "computer_use") is False


def test_stt_and_pro_capabilities():
    assert supports_capability("whisper-large-v3", "stt") is True
    assert supports_capability("whisper-1", "stt") is True
    assert supports_capability("whisper-large-v3", "chat") is False

    assert supports_capability("deepseek-chat", "pro") is True
    assert supports_capability("deepseek-reasoner", "pro") is True
    assert supports_capability("llama-3.3-70b-versatile", "pro") is True


# =========================================================================
# 3. CLASIFICACIÓN DE ERRORES DE API
# =========================================================================

def test_classify_api_error_status_codes():
    class DummyHttpError(Exception):
        def __init__(self, code, msg):
            super().__init__(msg)
            self.status_code = code

    # Rate limit 429
    e_429 = DummyHttpError(429, "Too Many Requests")
    assert classify_api_error(e_429) == "rate_limit"
    assert is_transient_error(e_429) is True
    assert is_auth_error(e_429) is False

    # Server error 503
    e_503 = DummyHttpError(503, "Service Unavailable")
    assert classify_api_error(e_503) == "service_unavailable"
    assert is_transient_error(e_503) is True

    # Auth error 401 y 403
    e_401 = DummyHttpError(401, "Invalid API Key")
    assert classify_api_error(e_401) == "auth"
    assert is_transient_error(e_401) is False
    assert is_auth_error(e_401) is True

    e_403 = DummyHttpError(403, "Permission Denied")
    assert classify_api_error(e_403) == "auth"
    assert is_auth_error(e_403) is True

    # Not found 404
    e_404 = DummyHttpError(404, "The model does not exist")
    assert classify_api_error(e_404) == "not_found"
    assert is_not_found_error(e_404) is True
    assert is_transient_error(e_404) is False


def test_classify_api_error_text_strings():
    assert is_transient_error(Exception("Error: RESOURCE_EXHAUSTED quota exceeded")) is True
    assert is_transient_error(Exception("Connection timed out after 30000ms")) is True
    assert is_auth_error(Exception("Incorrect API key provided: sk-...")) is True
    assert is_auth_error(Exception("User not authorized or permission_denied")) is True
    assert is_not_found_error(Exception("model_not_found: deepseek-nonexistent")) is True


def test_user_friendly_error_messages():
    auth_msg = get_user_friendly_error_message(Exception("401 unauthorized"), "gpt-4o", "openai")
    assert "Error de autenticación" in auth_msg
    assert "Ajustes" in auth_msg

    not_found_msg = get_user_friendly_error_message(Exception("404 not found"), "fake-model", "google")
    assert "Modelo no encontrado" in not_found_msg
    assert "fake-model" in not_found_msg

    rate_msg = get_user_friendly_error_message(Exception("429 rate limit"), "gemini-1.5-flash", "google")
    assert "Límite de peticiones" in rate_msg


# =========================================================================
# 4. GESTIÓN Y ROTACIÓN DE CLAVES MÚLTIPLES
# =========================================================================

def test_rotate_provider_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "key_alpha,key_beta,key_gamma")
    models_provider._provider_key_indices["google"] = 0

    assert get_provider_keys("google") == ["key_alpha", "key_beta", "key_gamma"]
    assert get_active_key_for_provider("google") == "key_alpha"

    # Rotación 1 -> key_beta
    assert rotate_provider_key("google") is True
    assert get_active_key_for_provider("google") == "key_beta"

    # Rotación 2 -> key_gamma
    assert rotate_provider_key("google") is True
    assert get_active_key_for_provider("google") == "key_gamma"

    # Rotación 3 -> key_alpha (cíclica)
    assert rotate_provider_key("google") is True
    assert get_active_key_for_provider("google") == "key_alpha"


def test_rotate_provider_key_single_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-solo-una-clave")
    models_provider._provider_key_indices["openai"] = 0

    # Solo hay 1 clave, rotate debe retornar False sin romper
    assert rotate_provider_key("openai") is False
    assert get_active_key_for_provider("openai") == "sk-solo-una-clave"


# =========================================================================
# 5. RESILIENCIA: NO ENMASCARAR ERRORES 401/403/404
# =========================================================================

def test_resilience_raises_auth_error_immediately():
    """Verifica que un error de autenticación (401/403) NO se oculte con reintentos ni fallbacks a ciegas."""
    class AuthError(Exception):
        status_code = 401

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = AuthError("API key invalid")

    with pytest.raises(AuthError):
        execute_completion_with_resilience(
            client=mock_client,
            model="gpt-4o",
            messages=[{"role": "user", "content": "hola"}],
            provider="openai",
            max_retries=2
        )

    # Solo debe haberse llamado 1 vez, sin reintentos inútiles
    assert mock_client.chat.completions.create.call_count == 1


def test_resilience_raises_not_found_error_immediately():
    """Verifica que un error 404 (modelo inexistente) NO se reintente inútilmente."""
    class NotFoundError(Exception):
        status_code = 404

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = NotFoundError("Model not found")

    with pytest.raises(NotFoundError):
        execute_completion_with_resilience(
            client=mock_client,
            model="modelo-inexistente",
            messages=[{"role": "user", "content": "hola"}],
            provider="google",
            max_retries=2
        )

    assert mock_client.chat.completions.create.call_count == 1


# =========================================================================
# 6. RESILIENCIA: ROTACIÓN Y REINTENTO ANTE ERRORES TRANSITORIOS (429/503)
# =========================================================================

def test_resilience_retries_and_succeeds_on_transient_error(monkeypatch):
    """Verifica que ante un error 429 transitorio, rote clave y reintente con éxito."""
    monkeypatch.setenv("GEMINI_API_KEY", "key1,key2")
    models_provider._provider_key_indices["google"] = 0

    class RateLimitError(Exception):
        status_code = 429

    mock_success_resp = MagicMock()
    mock_success_resp.choices = [MagicMock(message=MagicMock(content="Respuesta recuperada"))]

    mock_client_1 = MagicMock()
    mock_client_1.chat.completions.create.side_effect = RateLimitError("Rate limit exceeded")

    mock_client_2 = MagicMock()
    mock_client_2.chat.completions.create.return_value = mock_success_resp

    # Simular que al rotar se crea mock_client_2
    call_idx = [0]
    def mock_create_client(prov, mod):
        call_idx[0] += 1
        return mock_client_2, mod, prov

    monkeypatch.setattr(models_provider, "create_provider_client", mock_create_client)

    result = execute_completion_with_resilience(
        client=mock_client_1,
        model="gemini-1.5-flash",
        messages=[{"role": "user", "content": "hola"}],
        provider="google",
        max_retries=2,
        base_delay=0.01  # Delay mínimo para no demorar el test
    )

    assert result == mock_success_resp
    assert mock_client_2.chat.completions.create.call_count == 1


# =========================================================================
# 7. RESOLUCIÓN DE CLIENTE PARA COMPUTER_USE (SELECCIÓN MULTIMODAL OBLIGATORIA)
# =========================================================================

def test_get_client_and_model_redirects_non_vision_model(monkeypatch):
    """
    Si models_config.json o el usuario pide 'deepseek-chat' (sin visión) para computer_use,
    debe redirigir a un modelo multimodal real de Google u OpenAI activo, nunca a un modelo sin visión.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test_deepseek_key")

    mock_cl = MagicMock()
    monkeypatch.setattr(models_provider, "create_provider_client", lambda prov, mod: (mock_cl, mod, prov))

    client, mod, prov = get_client_and_model(
        preferred_model="deepseek-chat",
        category="computer_use",
        required_capability="computer_use"
    )

    assert client is not None
    # No puede ser deepseek-chat porque no soporta visión
    assert prov != "deepseek"
    assert supports_capability(mod, "computer_use") is True


def test_deepseek_flash_accepted_for_computer_use(monkeypatch):
    """
    Si el usuario selecciona 'deepseek-flash', debe ser aceptado directamente
    para computer_use ya que es multimodal y soporta imágenes.
    """
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test_deepseek_key")

    mock_cl = MagicMock()
    monkeypatch.setattr(models_provider, "create_provider_client", lambda prov, mod: (mock_cl, mod, prov))

    client, mod, prov = get_client_and_model(
        preferred_model="deepseek-flash",
        category="computer_use",
        required_capability="computer_use"
    )

    assert client is not None
    assert prov == "deepseek"
    assert mod == "deepseek-flash"
    assert supports_capability(mod, "computer_use") is True

