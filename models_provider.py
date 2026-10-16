"""
models_provider.py - Miku V2 AI Models Provider & Live Discovery Engine
Gestiona el descubrimiento dinámico de modelos REALES basados en las API Keys configuradas
y la instanciación de clientes compatibles para el Cerebro (brain.py).
"""

import os
import time
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Set, Tuple, Optional, Any
from dotenv import load_dotenv
import openai
from miku_paths import get_env_path, get_models_config_path

load_dotenv(get_env_path())

logger = logging.getLogger("ModelsProvider")

MODELS_CONFIG_FILE = get_models_config_path()
CACHE_TTL_SECONDS = 300  # 5 minutos de caché para no saturar las APIs

_models_cache = {
    "timestamp": 0,
    "available": {}
}

# Catálogo curado de modelos 100% REALES como respaldo ante caída de red o APIs sin endpoint de lista
FALLBACK_CATALOG = {
    "google": [
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash (Google AI Studio - Recomendado)", "provider": "google", "capabilities": ["chat", "computer_use"]},
        {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro (Google AI Studio - Razonamiento)", "provider": "google", "capabilities": ["chat", "computer_use"]},
        {"id": "gemini-flash-latest", "name": "Gemini Flash Latest (Google AI Studio)", "provider": "google", "capabilities": ["chat", "computer_use"]},
        {"id": "gemini-flash-lite-latest", "name": "Gemini Flash Lite (Ultra Rápido)", "provider": "google", "capabilities": ["chat"]},
        {"id": "gemini-2.5-flash-lite", "name": "Gemini 2.5 Flash Lite", "provider": "google", "capabilities": ["chat"]},
        {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash (Estable)", "provider": "google", "capabilities": ["chat", "computer_use"]},
        {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro (Estable)", "provider": "google", "capabilities": ["chat", "computer_use"]},
    ],
    "groq": [
        {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B Versatile (Groq - Ultra Veloz)", "provider": "groq", "capabilities": ["chat"]},
        {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B Instant (Groq - Baja Latencia)", "provider": "groq", "capabilities": ["chat"]},
        {"id": "deepseek-r1-distill-llama-70b", "name": "DeepSeek R1 Distill 70B (Groq - Razonamiento)", "provider": "groq", "capabilities": ["chat"]},
        {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B (Groq)", "provider": "groq", "capabilities": ["chat"]},
        {"id": "whisper-large-v3", "name": "Whisper Large v3 (Groq - STT Recomendado)", "provider": "groq", "capabilities": ["stt"]},
        {"id": "whisper-large-v3-turbo", "name": "Whisper Large v3 Turbo (Groq - STT Rápido)", "provider": "groq", "capabilities": ["stt"]},
    ],
    "openai": [
        {"id": "gpt-4o", "name": "GPT-4o (OpenAI - Multimodal Flagship)", "provider": "openai", "capabilities": ["chat", "computer_use"]},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini (OpenAI - Rápido y Económico)", "provider": "openai", "capabilities": ["chat", "computer_use"]},
        {"id": "o1-mini", "name": "o1-mini (OpenAI - Razonamiento)", "provider": "openai", "capabilities": ["chat"]},
        {"id": "o3-mini", "name": "o3-mini (OpenAI - Razonamiento Avanzado)", "provider": "openai", "capabilities": ["chat"]},
        {"id": "whisper-1", "name": "Whisper v1 (OpenAI - STT)", "provider": "openai", "capabilities": ["stt"]},
    ],
    "deepseek": [
        {"id": "deepseek-chat", "name": "DeepSeek-V3 Chat (DeepSeek Oficial - Excelente Calidad/Precio)", "provider": "deepseek", "capabilities": ["chat"]},
        {"id": "deepseek-reasoner", "name": "DeepSeek-R1 Reasoner (DeepSeek Oficial - Pensamiento Profundo)", "provider": "deepseek", "capabilities": ["chat"]},
    ],
    "anthropic": [
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet (Anthropic - Código y Visión)", "provider": "anthropic", "capabilities": ["chat", "computer_use"]},
        {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku (Anthropic - Veloz)", "provider": "anthropic", "capabilities": ["chat"]},
        {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus (Anthropic - Tareas Complejas)", "provider": "anthropic", "capabilities": ["chat"]},
    ],
    "openrouter": [
        {"id": "deepseek/deepseek-r1", "name": "DeepSeek R1 (OpenRouter)", "provider": "openrouter", "capabilities": ["chat"]},
        {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet (OpenRouter)", "provider": "openrouter", "capabilities": ["chat", "computer_use"]},
        {"id": "meta-llama/llama-3.3-70b-instruct", "name": "Llama 3.3 70B Instruct (OpenRouter)", "provider": "openrouter", "capabilities": ["chat"]},
        {"id": "google/gemini-2.5-flash", "name": "Gemini 2.5 Flash (OpenRouter)", "provider": "openrouter", "capabilities": ["chat", "computer_use"]},
    ],
    "ollama": [
        {"id": "llama3.2:latest", "name": "Llama 3.2 (Ollama Local)", "provider": "ollama", "capabilities": ["chat"]},
        {"id": "deepseek-r1:latest", "name": "DeepSeek R1 (Ollama Local)", "provider": "ollama", "capabilities": ["chat"]},
    ]
}


def get_active_providers() -> Set[str]:
    """Detecta qué proveedores tienen credenciales activas en .env o entorno."""
    env_path = get_env_path()
    env_keys = {}
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#") and "=" in stripped:
                        k, v = stripped.split("=", 1)
                        env_keys[k.strip()] = v.strip().strip('"').strip("'")
        except Exception as e:
            logger.warning(f"Error leyendo .env en get_active_providers: {e}")

    active = set()
    if env_keys.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or env_keys.get("GOOGLE_CLOUD_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT"):
        active.add("google")
    if env_keys.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY"):
        active.add("groq")
    if env_keys.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"):
        active.add("openai")
    if env_keys.get("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API_KEY"):
        active.add("deepseek")
    if env_keys.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
        active.add("anthropic")
    if env_keys.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY"):
        active.add("openrouter")
    if env_keys.get("NVIDIA_API_KEY") or os.getenv("NVIDIA_API_KEY"):
        active.add("nvidia")
        
    # Verificar si Ollama local está corriendo
    if is_ollama_running():
        active.add("ollama")

    return active


def is_ollama_running() -> bool:
    """Verifica de forma ultra-rápida (500ms timeout) si Ollama está corriendo en localhost:11434."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", headers={"User-Agent": "Miku-V2"})
        with urllib.request.urlopen(req, timeout=0.6) as response:
            return response.status == 200
    except Exception:
        return False


def _fetch_live_google_models(key: str) -> List[Dict]:
    """Descubre modelos reales de Google AI Studio vía API oficial."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Miku-V2"})
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        models = []
        for m in data.get("models", []):
            methods = m.get("supportedGenerationMethods", [])
            if "generateContent" not in methods:
                continue
            raw_id = m.get("name", "").replace("models/", "")
            if not raw_id:
                continue
            # Omitir modelos experimentales viejos o embedding
            if "embedding" in raw_id or "aqa" in raw_id:
                continue
            
            display_name = m.get("displayName") or raw_id
            caps = ["chat"]
            if any(term in raw_id for term in ["flash", "pro", "gemini-2"]):
                caps.append("computer_use")
            
            models.append({
                "id": raw_id,
                "name": f"{display_name} ({raw_id})",
                "provider": "google",
                "capabilities": caps
            })
        return models


def _fetch_live_groq_models(key: str) -> List[Dict]:
    """Descubre modelos reales de Groq vía endpoint oficial."""
    url = "https://api.groq.com/openai/v1/models"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {key}",
        "User-Agent": "Mozilla/5.0 Miku-V2"
    })
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        models = []
        for m in data.get("data", []):
            m_id = m.get("id", "")
            if not m_id:
                continue
            # Separar STT (Whisper) de Chat
            if "whisper" in m_id:
                models.append({
                    "id": m_id,
                    "name": f"{m_id.capitalize()} (Groq STT)",
                    "provider": "groq",
                    "capabilities": ["stt"]
                })
            elif "guard" not in m_id and "orpheus" not in m_id:
                models.append({
                    "id": m_id,
                    "name": f"{m_id} (Groq)",
                    "provider": "groq",
                    "capabilities": ["chat"]
                })
        return models


def _fetch_live_openai_models(key: str) -> List[Dict]:
    """Descubre modelos reales de OpenAI."""
    url = "https://api.openai.com/v1/models"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {key}",
        "User-Agent": "Mozilla/5.0 Miku-V2"
    })
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        models = []
        for m in data.get("data", []):
            m_id = m.get("id", "")
            if "whisper" in m_id:
                models.append({
                    "id": m_id,
                    "name": f"{m_id} (OpenAI Audio)",
                    "provider": "openai",
                    "capabilities": ["stt"]
                })
            elif any(prefix in m_id for prefix in ["gpt-4o", "gpt-4-turbo", "o1", "o3"]):
                caps = ["chat"]
                if "gpt-4o" in m_id:
                    caps.append("computer_use")
                models.append({
                    "id": m_id,
                    "name": f"{m_id} (OpenAI)",
                    "provider": "openai",
                    "capabilities": caps
                })
        return models


def _fetch_live_ollama_models() -> List[Dict]:
    """Descubre modelos instalados en la instancia local de Ollama."""
    url = "http://localhost:11434/api/tags"
    req = urllib.request.Request(url, headers={"User-Agent": "Miku-V2"})
    with urllib.request.urlopen(req, timeout=1.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        models = []
        for m in data.get("models", []):
            m_name = m.get("name", "")
            if m_name:
                models.append({
                    "id": m_name,
                    "name": f"{m_name} (Ollama Local)",
                    "provider": "ollama",
                    "capabilities": ["chat"]
                })
        return models


def discover_provider_models(provider: str) -> List[Dict]:
    """Consulta la API en vivo del proveedor con fallback al catálogo curado."""
    env_key = ""
    if provider == "google":
        env_key = os.getenv("GEMINI_API_KEY", "")
        if env_key:
            first_key = env_key.split(",")[0].strip()
            try:
                live = _fetch_live_google_models(first_key)
                if live:
                    return live
            except Exception as e:
                logger.warning(f"No se pudo consultar lista en vivo de Google ({e}), usando catálogo curado.")
    elif provider == "groq":
        env_key = os.getenv("GROQ_API_KEY", "")
        if env_key:
            first_key = env_key.split(",")[0].strip()
            try:
                live = _fetch_live_groq_models(first_key)
                if live:
                    return live
            except Exception as e:
                logger.warning(f"No se pudo consultar lista en vivo de Groq ({e}), usando catálogo curado.")
    elif provider == "openai":
        env_key = os.getenv("OPENAI_API_KEY", "")
        if env_key:
            try:
                live = _fetch_live_openai_models(env_key)
                if live:
                    return live
            except Exception as e:
                logger.warning(f"No se pudo consultar lista en vivo de OpenAI ({e}), usando catálogo curado.")
    elif provider == "ollama":
        try:
            live = _fetch_live_ollama_models()
            if live:
                return live
        except Exception:
            pass

    # Fallback garantizado: modelos 100% reales pre-verificados
    return FALLBACK_CATALOG.get(provider, [])


def get_available_models(force_refresh: bool = False) -> Dict[str, List[Dict]]:
    """Devuelve los modelos disponibles categorizados (chat, computer_use, stt) filtrados por API keys activas."""
    global _models_cache
    now = time.time()
    if not force_refresh and (now - _models_cache["timestamp"] < CACHE_TTL_SECONDS) and _models_cache["available"]:
        return _models_cache["available"]

    active_providers = get_active_providers()
    all_provider_models = []
    for prov in active_providers:
        prov_models = discover_provider_models(prov)
        all_provider_models.extend(prov_models)

    chat_models = []
    computer_use_models = []
    stt_models = []

    seen_ids = set()
    for m in all_provider_models:
        mid = m["id"]
        caps = m.get("capabilities", ["chat"])
        
        # Entrada limpia para el frontend
        entry = {
            "id": mid,
            "name": m["name"],
            "provider": m["provider"]
        }
        
        if "chat" in caps and (mid, "chat") not in seen_ids:
            seen_ids.add((mid, "chat"))
            chat_models.append(entry)
            
        if "computer_use" in caps and (mid, "computer_use") not in seen_ids:
            seen_ids.add((mid, "computer_use"))
            computer_use_models.append(entry)
            
        if "stt" in caps and (mid, "stt") not in seen_ids:
            seen_ids.add((mid, "stt"))
            stt_models.append(entry)

    # Ordenar priorizando modelos recomendados
    def _sort_key(item):
        name = item["name"].lower()
        if "recomendado" in name or "flash" in name or "3.3 70b" in name:
            return 0
        return 1

    chat_models.sort(key=_sort_key)
    computer_use_models.sort(key=_sort_key)
    stt_models.sort(key=_sort_key)

    result = {
        "chat": chat_models,
        "computer_use": computer_use_models,
        "stt": stt_models
    }

    _models_cache["timestamp"] = now
    _models_cache["available"] = result
    return result


def get_configured_models() -> Dict[str, str]:
    """Carga la configuración guardada de modelos desde models_config.json."""
    default_config = {
        "chat": "gemini-2.5-flash",
        "computer_use": "gemini-2.5-flash",
        "stt": "whisper-large-v3"
    }
    if os.path.exists(MODELS_CONFIG_FILE):
        try:
            with open(MODELS_CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                default_config.update(saved)
        except Exception as e:
            logger.error(f"Error cargando models_config.json: {e}")
    return default_config


def identify_provider_for_model(model_id: str) -> str:
    """Determina a qué proveedor pertenece un ID de modelo."""
    if not model_id:
        return ""
    m_lower = model_id.lower()
    if m_lower.startswith("gemini") or "google" in m_lower or "gemma" in m_lower:
        return "google"
    if "deepseek" in m_lower and not ("distill" in m_lower or "groq" in m_lower):
        return "deepseek"
    if m_lower.startswith("llama") or "mixtral" in m_lower or "groq" in m_lower or "whisper-large" in m_lower:
        return "groq"
    if m_lower.startswith("gpt-") or m_lower.startswith("o1") or m_lower.startswith("o3") or m_lower == "whisper-1":
        return "openai"
    if m_lower.startswith("claude"):
        return "anthropic"
    if "/" in m_lower and any(p in m_lower for p in ["meta-llama", "deepseek", "anthropic", "google"]):
        return "openrouter"
    if ":" in m_lower:  # Sintaxis típica de ollama como mistral:latest
        return "ollama"
    return "groq"  # fallback general


def get_client_and_model(preferred_model: Optional[str] = None, category: str = "chat") -> Tuple[Optional[Any], str, str]:
    """
    Crea e inicializa el cliente OpenAI-compatible adecuado según el modelo configurado.
    Devuelve (client, model_id, provider_name).
    Si el proveedor configurado no está disponible, rota a otro proveedor activo.
    """
    config = get_configured_models()
    model_to_use = preferred_model or config.get(category, "")
    provider = identify_provider_for_model(model_to_use)
    active_providers = get_active_providers()

    # Si el proveedor del modelo configurado no está activo, seleccionar el primer proveedor activo
    if provider not in active_providers and active_providers:
        available = get_available_models().get(category, [])
        if available:
            model_to_use = available[0]["id"]
            provider = available[0]["provider"]

    # 1. Google Gemini AI Studio
    if provider == "google":
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if gemini_key:
            keys = [k.strip() for k in gemini_key.split(",") if k.strip()]
            selected_key = keys[0] if keys else ""
            if selected_key:
                try:
                    cl = openai.OpenAI(
                        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                        api_key=selected_key,
                        max_retries=2
                    )
                    # Asegurar nombre real sin prefijo
                    clean_model = model_to_use.replace("google/", "")
                    if clean_model not in ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-flash-latest", "gemini-flash-lite-latest", "gemini-1.5-flash", "gemini-1.5-pro"]:
                        clean_model = "gemini-2.5-flash"
                    return cl, clean_model, "google"
                except Exception as e:
                    logger.warning(f"Error creando cliente Gemini: {e}")

    # 2. Groq
    if provider == "groq" or "groq" in active_providers:
        groq_key = os.getenv("GROQ_API_KEY", "")
        if groq_key:
            keys = [k.strip() for k in groq_key.split(",") if k.strip()]
            selected_key = keys[0] if keys else ""
            if selected_key:
                try:
                    cl = openai.OpenAI(
                        base_url="https://api.groq.com/openai/v1",
                        api_key=selected_key,
                        max_retries=2
                    )
                    clean_model = model_to_use if provider == "groq" else "llama-3.3-70b-versatile"
                    return cl, clean_model, "groq"
                except Exception as e:
                    logger.warning(f"Error creando cliente Groq: {e}")

    # 3. DeepSeek
    if provider == "deepseek":
        ds_key = os.getenv("DEEPSEEK_API_KEY", "")
        if ds_key:
            try:
                cl = openai.OpenAI(
                    base_url="https://api.deepseek.com",
                    api_key=ds_key,
                    max_retries=2
                )
                clean_model = model_to_use if model_to_use in ["deepseek-chat", "deepseek-reasoner"] else "deepseek-chat"
                return cl, clean_model, "deepseek"
            except Exception as e:
                logger.warning(f"Error creando cliente DeepSeek: {e}")

    # 4. OpenAI
    if provider == "openai":
        oai_key = os.getenv("OPENAI_API_KEY", "")
        if oai_key:
            try:
                cl = openai.OpenAI(
                    api_key=oai_key,
                    max_retries=2
                )
                clean_model = model_to_use or "gpt-4o-mini"
                return cl, clean_model, "openai"
            except Exception as e:
                logger.warning(f"Error creando cliente OpenAI: {e}")

    # 5. Ollama Local
    if provider == "ollama" or is_ollama_running():
        try:
            cl = openai.OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                max_retries=1
            )
            return cl, model_to_use or "llama3.2:latest", "ollama"
        except Exception as e:
            logger.warning(f"Error creando cliente Ollama: {e}")

    # Fallback absoluto de emergencia
    return None, "", "none"
