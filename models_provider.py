"""
models_provider.py - Miku V2 AI Models Provider & Live Discovery Engine
Gestiona el descubrimiento dinámico de modelos REALES basados en las API Keys configuradas,
la instanciación de clientes compatibles para el Cerebro (brain.py) y Computer Use (computer_use.py),
la clasificación de capacidades explícitas (text, vision, tools, structured_output, audio_stt, native_computer_use),
el origen verificado vs catálogo vs personalizado,
la prueba en vivo de conectividad antes de guardar,
rotación de claves múltiples y resiliencia ante errores transitorios (429/503) sin enmascarar errores de autenticación (401/403) ni modelos inexistentes (404).
"""

import os
import time
import json
import logging
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Set, Tuple, Optional, Any
from dotenv import load_dotenv
import openai
from miku_paths import get_env_path, get_models_config_path

load_dotenv(get_env_path())

logger = logging.getLogger("ModelsProvider")

MODELS_CONFIG_FILE = get_models_config_path()
CACHE_TTL_SECONDS = 30  # 30 segundos de caché para refresco ágil

_models_cache = {
    "timestamp": 0,
    "available": {}
}

# Aliases de compatibilidad hacia atrás para modelos renombrados o ficticios
MODEL_ALIASES = {
    "gemini-1.5-flash-latest": "gemini-1.5-flash",
    "gemini-1.5-pro-latest": "gemini-1.5-pro",
    "gemini-2.5-flash": "gemini-1.5-flash",
    "DeepSeek-V4.1-Flash": "deepseek-flash",
    "deepseek-v4.1-flash": "deepseek-flash"
}

# Catálogo curado de modelos 100% REALES con capacidades explícitas y origen "catalog"
FALLBACK_CATALOG = {
    "google": [
        {
            "id": "gemini-1.5-flash",
            "name": "Gemini 1.5 Flash (Google AI Studio - Rápido y Multimodal)",
            "provider": "google",
            "capabilities": ["chat", "computer_use", "text", "vision", "tools", "structured_output"],
            "origin": "catalog",
            "context_window": 1048576
        },
        {
            "id": "gemini-1.5-pro",
            "name": "Gemini 1.5 Pro (Google AI Studio - Razonamiento Profundo y Visión)",
            "provider": "google",
            "capabilities": ["chat", "pro", "computer_use", "text", "vision", "tools", "structured_output"],
            "origin": "catalog",
            "context_window": 2097152
        },
        {
            "id": "gemini-flash-latest",
            "name": "Gemini Flash Latest (Google AI Studio - Multimodal Oficial)",
            "provider": "google",
            "capabilities": ["chat", "computer_use", "text", "vision", "tools", "structured_output"],
            "origin": "catalog",
            "context_window": 1048576
        },
        {
            "id": "gemini-flash-lite-latest",
            "name": "Gemini Flash Lite (Ultra Rápido)",
            "provider": "google",
            "capabilities": ["chat", "text", "tools", "structured_output"],
            "origin": "catalog",
            "context_window": 1048576
        },
        {
            "id": "gemini-2.0-flash",
            "name": "Gemini 2.0 Flash (Nueva Generación Multimodal)",
            "provider": "google",
            "capabilities": ["chat", "computer_use", "text", "vision", "tools", "structured_output"],
            "origin": "catalog",
            "context_window": 1048576
        },
        {
            "id": "imagen-3.0-generate-002",
            "name": "Imagen 3 (Google - Generador de Imágenes)",
            "provider": "google",
            "capabilities": ["image_gen", "images"],
            "origin": "catalog",
            "context_window": 0
        },
    ],
    "groq": [
        {
            "id": "llama-3.3-70b-versatile",
            "name": "Llama 3.3 70B Versatile (Groq - Ultra Veloz)",
            "provider": "groq",
            "capabilities": ["chat", "pro", "text", "tools", "structured_output"],
            "origin": "catalog",
            "context_window": 128000
        },
        {
            "id": "llama-3.1-8b-instant",
            "name": "Llama 3.1 8B Instant (Groq - Baja Latencia)",
            "provider": "groq",
            "capabilities": ["chat", "text", "tools", "structured_output"],
            "origin": "catalog",
            "context_window": 128000
        },
        {
            "id": "deepseek-r1-distill-llama-70b",
            "name": "DeepSeek R1 Distill 70B (Groq - Razonamiento)",
            "provider": "groq",
            "capabilities": ["chat", "pro", "text", "structured_output"],
            "origin": "catalog",
            "context_window": 128000
        },
        {
            "id": "mixtral-8x7b-32768",
            "name": "Mixtral 8x7B (Groq)",
            "provider": "groq",
            "capabilities": ["chat", "text", "tools"],
            "origin": "catalog",
            "context_window": 32768
        },
        {
            "id": "whisper-large-v3",
            "name": "Whisper Large v3 (Groq - STT Recomendado)",
            "provider": "groq",
            "capabilities": ["stt", "audio_stt"],
            "origin": "catalog",
            "context_window": 0
        },
        {
            "id": "whisper-large-v3-turbo",
            "name": "Whisper Large v3 Turbo (Groq - STT Rápido)",
            "provider": "groq",
            "capabilities": ["stt", "audio_stt"],
            "origin": "catalog",
            "context_window": 0
        },
    ],
    "openai": [
        {
            "id": "gpt-4o",
            "name": "GPT-4o (OpenAI - Multimodal Flagship)",
            "provider": "openai",
            "capabilities": ["chat", "pro", "computer_use", "text", "vision", "tools", "structured_output"],
            "origin": "catalog",
            "context_window": 128000
        },
        {
            "id": "gpt-4o-mini",
            "name": "GPT-4o Mini (OpenAI - Rápido y Económico)",
            "provider": "openai",
            "capabilities": ["chat", "computer_use", "text", "vision", "tools", "structured_output"],
            "origin": "catalog",
            "context_window": 128000
        },
        {
            "id": "o1-mini",
            "name": "o1-mini (OpenAI - Razonamiento)",
            "provider": "openai",
            "capabilities": ["chat", "pro", "text", "structured_output"],
            "origin": "catalog",
            "context_window": 128000
        },
        {
            "id": "o3-mini",
            "name": "o3-mini (OpenAI - Razonamiento Avanzado)",
            "provider": "openai",
            "capabilities": ["chat", "pro", "text", "structured_output"],
            "origin": "catalog",
            "context_window": 200000
        },
        {
            "id": "whisper-1",
            "name": "Whisper v1 (OpenAI - STT)",
            "provider": "openai",
            "capabilities": ["stt", "audio_stt"],
            "origin": "catalog",
            "context_window": 0
        },
        {
            "id": "dall-e-3",
            "name": "DALL·E 3 (OpenAI - Generador de Imágenes)",
            "provider": "openai",
            "capabilities": ["image_gen", "images"],
            "origin": "catalog",
            "context_window": 0
        },
    ],
    "deepseek": [
        {
            "id": "deepseek-flash",
            "name": "DeepSeek Flash (Multimodal con Visión)",
            "provider": "deepseek",
            "capabilities": ["chat", "computer_use", "text", "vision", "tools", "structured_output"],
            "origin": "catalog",
            "context_window": 128000
        },
        {
            "id": "deepseek-v4.1-flash",
            "name": "DeepSeek-V4.1-Flash (DeepSeek Oficial)",
            "provider": "deepseek",
            "capabilities": ["chat", "computer_use", "text", "vision", "tools", "structured_output"],
            "origin": "catalog",
            "context_window": 128000
        },
        {
            "id": "deepseek-v4",
            "name": "DeepSeek-V4 (Oficial - Siguiente Generación)",
            "provider": "deepseek",
            "capabilities": ["chat", "pro", "text", "tools", "structured_output"],
            "origin": "catalog",
            "context_window": 128000
        },
        {
            "id": "deepseek-v4-pro",
            "name": "DeepSeek-V4 Pro (Oficial - Razonamiento y Código)",
            "provider": "deepseek",
            "capabilities": ["chat", "pro", "text", "tools", "structured_output"],
            "origin": "catalog",
            "context_window": 128000
        },
        {
            "id": "deepseek-chat",
            "name": "DeepSeek-V3 Chat (Oficial - Chat y Código)",
            "provider": "deepseek",
            "capabilities": ["chat", "pro", "text", "tools", "structured_output"],
            "origin": "catalog",
            "context_window": 64000
        },
        {
            "id": "deepseek-reasoner",
            "name": "DeepSeek-R1 Reasoner (Oficial - Pensamiento Profundo)",
            "provider": "deepseek",
            "capabilities": ["chat", "pro", "text"],
            "origin": "catalog",
            "context_window": 64000
        },
        {
            "id": "deepseek-coder",
            "name": "DeepSeek Coder (Oficial - Programación)",
            "provider": "deepseek",
            "capabilities": ["chat", "pro", "text", "tools"],
            "origin": "catalog",
            "context_window": 64000
        },
    ],
    "anthropic": [
        {
            "id": "claude-3-5-sonnet-20241022",
            "name": "Claude 3.5 Sonnet (Anthropic - Código y Visión)",
            "provider": "anthropic",
            "capabilities": ["chat", "pro", "computer_use", "text", "vision", "tools", "structured_output", "native_computer_use"],
            "origin": "catalog",
            "context_window": 200000
        },
        {
            "id": "claude-3-5-haiku-20241022",
            "name": "Claude 3.5 Haiku (Anthropic - Veloz)",
            "provider": "anthropic",
            "capabilities": ["chat", "text", "tools", "structured_output"],
            "origin": "catalog",
            "context_window": 200000
        },
        {
            "id": "claude-3-opus-20240229",
            "name": "Claude 3 Opus (Anthropic - Tareas Complejas)",
            "provider": "anthropic",
            "capabilities": ["chat", "pro", "text", "vision", "tools"],
            "origin": "catalog",
            "context_window": 200000
        },
    ],
    "openrouter": [
        {
            "id": "anthropic/claude-3.5-sonnet",
            "name": "Claude 3.5 Sonnet (OpenRouter - Multimodal)",
            "provider": "openrouter",
            "capabilities": ["chat", "pro", "computer_use", "text", "vision", "tools", "structured_output"],
            "origin": "catalog",
            "context_window": 200000
        },
        {
            "id": "google/gemini-1.5-flash",
            "name": "Gemini 1.5 Flash (OpenRouter - Multimodal)",
            "provider": "openrouter",
            "capabilities": ["chat", "computer_use", "text", "vision", "tools", "structured_output"],
            "origin": "catalog",
            "context_window": 1048576
        },
        {
            "id": "deepseek/deepseek-r1",
            "name": "DeepSeek R1 (OpenRouter)",
            "provider": "openrouter",
            "capabilities": ["chat", "pro", "text"],
            "origin": "catalog",
            "context_window": 128000
        },
        {
            "id": "meta-llama/llama-3.3-70b-instruct",
            "name": "Llama 3.3 70B Instruct (OpenRouter)",
            "provider": "openrouter",
            "capabilities": ["chat", "pro", "text", "tools"],
            "origin": "catalog",
            "context_window": 128000
        },
    ],
    "nvidia": [
        {
            "id": "meta/llama-3.3-70b-instruct",
            "name": "Llama 3.3 70B Instruct (NVIDIA NIM)",
            "provider": "nvidia",
            "capabilities": ["chat", "pro", "text", "tools"],
            "origin": "catalog",
            "context_window": 128000
        },
    ],
    "ollama": [
        {
            "id": "llama3.2:latest",
            "name": "Llama 3.2 (Ollama Local)",
            "provider": "ollama",
            "capabilities": ["chat", "text", "tools"],
            "origin": "catalog",
            "context_window": 128000
        },
        {
            "id": "deepseek-r1:latest",
            "name": "DeepSeek R1 (Ollama Local)",
            "provider": "ollama",
            "capabilities": ["chat", "pro", "text"],
            "origin": "catalog",
            "context_window": 64000
        },
    ]
}

# Índices para rotación cíclica de claves múltiples por proveedor (ej. GEMINI_API_KEY=key1,key2)
_provider_key_indices: Dict[str, int] = {
    "google": 0,
    "groq": 0,
    "openai": 0,
    "deepseek": 0,
    "anthropic": 0,
    "openrouter": 0,
    "nvidia": 0,
}


# =========================================================================
# GESTIÓN DE CLAVES Y DETECCIÓN DE PROVEEDORES ACTIVOS
# =========================================================================

def get_provider_env_var(provider: str) -> str:
    """Retorna el nombre de la variable de entorno asociada a un proveedor."""
    env_map = {
        "google": "GEMINI_API_KEY",
        "groq": "GROQ_API_KEY",
        "openai": "OPENAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "nvidia": "NVIDIA_API_KEY",
    }
    return env_map.get(provider, "")


def get_provider_keys(provider: str) -> List[str]:
    """Obtiene la lista de claves configuradas (separadas por coma) para un proveedor."""
    env_var = get_provider_env_var(provider)
    if not env_var:
        return []
    val = os.getenv(env_var, "").strip()
    if not val:
        return []
    return [k.strip() for k in val.split(",") if k.strip()]


def get_active_key_for_provider(provider: str) -> Optional[str]:
    """Retorna la clave activa actual para el proveedor respetando el puntero de rotación."""
    keys = get_provider_keys(provider)
    if not keys:
        return None
    idx = _provider_key_indices.get(provider, 0)
    return keys[idx % len(keys)]


def rotate_provider_key(provider: str) -> bool:
    """
    Rota a la siguiente clave para el proveedor si hay más de una configurada.
    Retorna True si pudo rotar a una clave distinta, False si sólo hay 1 o ninguna.
    """
    keys = get_provider_keys(provider)
    if len(keys) > 1:
        _provider_key_indices[provider] = (_provider_key_indices.get(provider, 0) + 1) % len(keys)
        logger.info(f"Rotando clave de {provider} a clave #{_provider_key_indices[provider] + 1} de {len(keys)}")
        return True
    return False


def rotate_gemini_key() -> bool:
    """Compatibilidad hacia atrás para rotación de claves Gemini."""
    return rotate_provider_key("google")


def rotate_groq_key() -> bool:
    """Compatibilidad hacia atrás para rotación de claves Groq."""
    return rotate_provider_key("groq")


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


# =========================================================================
# CLASIFICACIÓN DE ERRORES DE API Y RESILIENCIA
# =========================================================================

def classify_api_error(error: Exception) -> str:
    """
    Clasifica un error de API en una categoría estandarizada:
    - 'rate_limit': HTTP 429, ResourceExhausted, cuota por minuto superada.
    - 'service_unavailable': HTTP 503, 502, 504, 500, servidor caído o sobrecargado.
    - 'auth': HTTP 401, 403, Invalid API Key, permisos denegados.
    - 'not_found': HTTP 404, modelo no encontrado o no disponible.
    - 'quota_depleted': HTTP 402, cuenta sin saldo, crédito agotado, facturación no habilitada.
    - 'bad_request': HTTP 400, parámetros o estructura no compatibles.
    - 'unknown': otros errores no clasificados.
    """
    if error is None:
        return "unknown"

    status_code = getattr(error, "status_code", None) or getattr(error, "code", None)
    if status_code:
        if status_code == 429:
            return "rate_limit"
        if status_code in (500, 502, 503, 504):
            return "service_unavailable"
        if status_code in (401, 403):
            return "auth"
        if status_code == 404:
            return "not_found"
        if status_code == 402:
            return "quota_depleted"
        if status_code == 400:
            return "bad_request"

    err_str = str(error).lower()
    if any(s in err_str for s in ["429", "resource_exhausted", "rate limit", "ratelimit", "too many requests"]):
        return "rate_limit"
    if any(s in err_str for s in ["503", "502", "504", "service unavailable", "bad gateway", "internal server error", "overloaded", "timeout", "timed out"]):
        return "service_unavailable"
    if any(s in err_str for s in ["401", "403", "invalid_api_key", "invalid api key", "incorrect api key", "unauthorized", "permission_denied", "forbidden", "authentication", "unauthenticated"]) or ("api key" in err_str and any(w in err_str for w in ["incorrect", "invalid", "revoked", "expired", "missing", "provided"])):
        return "auth"
    if any(s in err_str for s in ["404", "not_found", "model_not_found", "does not exist", "not found"]):
        return "not_found"
    if any(s in err_str for s in ["402", "insufficient_quota", "billing", "credit", "quota exceeded", "payment_required"]):
        return "quota_depleted"
    if "400" in err_str or "bad request" in err_str or "invalid parameter" in err_str:
        return "bad_request"

    return "unknown"


def is_transient_error(error: Exception) -> bool:
    """Devuelve True si el error es transitorio/temporal y susceptible de reintento/rotación."""
    cat = classify_api_error(error)
    return cat in ("rate_limit", "service_unavailable")


def is_auth_error(error: Exception) -> bool:
    """Devuelve True si el error es de autenticación o clave inválida (401/403)."""
    return classify_api_error(error) == "auth"


def is_not_found_error(error: Exception) -> bool:
    """Devuelve True si el error indica modelo inexistente (404)."""
    return classify_api_error(error) == "not_found"


def get_user_friendly_error_message(error: Exception, model_id: str = "", provider: str = "") -> str:
    """Genera un mensaje de error claro y transparente para el usuario sin enmascarar la causa real."""
    cat = classify_api_error(error)
    err_str = str(error)
    p_label = provider.capitalize() if provider else "del proveedor"

    if cat == "auth":
        return f"🔑 Error de autenticación (HTTP 401/403): La clave API configurada para {p_label} no es válida o carece de permisos. Por favor verifica tus credenciales en Ajustes."
    elif cat == "not_found":
        return f"🔍 Modelo no encontrado (HTTP 404): El modelo '{model_id}' no existe o no está habilitado para tu cuenta en {p_label}."
    elif cat == "rate_limit":
        return f"⚠️ Límite de peticiones alcanzado (Rate Limit 429) en {p_label}. Has excedido la cuota por minuto. Espera unos segundos o agrega claves de respaldo en Ajustes."
    elif cat == "service_unavailable":
        return f"🌐 Servicio temporalmente no disponible (HTTP 503/Timeout) en {p_label}. El proveedor está experimentando sobrecarga."
    elif cat == "quota_depleted":
        return f"💳 Saldo o cuota agotada (HTTP 402) en {p_label}. Se requiere crédito o facturación activa para utilizar '{model_id}'."
    elif cat == "bad_request":
        return f"⚠️ Petición incompatible (HTTP 400) para '{model_id}' en {p_label}: {err_str}"
    
    return f"⚠️ Error de comunicación con {p_label} ({model_id}): {err_str}"


# =========================================================================
# RESOLUCIÓN DE PROVEEDORES Y VERIFICACIÓN DE CAPACIDADES
# =========================================================================

def identify_provider_for_model(model_id: str) -> str:
    """Determina a qué proveedor pertenece un ID de modelo."""
    if not model_id:
        return ""
    m_lower = model_id.lower().strip()

    if "/" in m_lower:
        if m_lower.startswith("openrouter/"):
            return "openrouter"
        if any(p in m_lower for p in ["meta-llama/", "deepseek/", "anthropic/", "google/", "mistralai/", "qwen/"]):
            return "openrouter"

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
    if ":" in m_lower:  # Sintaxis típica de ollama como mistral:latest
        return "ollama"

    return "groq"  # fallback general


def get_model_capabilities(model_id: str, provider: Optional[str] = None) -> List[str]:
    """Obtiene la lista de capacidades soportadas por un modelo."""
    if not model_id:
        return ["chat", "text"]
    clean_id = MODEL_ALIASES.get(model_id, model_id)
    prov = provider or identify_provider_for_model(clean_id)

    # 1. Comprobar si está en custom_models guardados
    custom_models = get_custom_models()
    for cm in custom_models:
        if cm.get("id") == clean_id and (not prov or cm.get("provider") == prov):
            return list(cm.get("capabilities", ["chat", "text"]))

    # 2. Buscar en catálogo curado
    items = FALLBACK_CATALOG.get(prov, [])
    for item in items:
        if item["id"] == clean_id:
            return list(item.get("capabilities", ["chat", "text"]))

    # 3. Inferencia basada en el nombre
    caps = ["chat", "text"]
    low = clean_id.lower()
    if "whisper" in low:
        return ["stt", "audio_stt"]
    # Modelos multimodales con visión: flash, vl, vision, multimodal, gpt-4o, claude, gemini, etc.
    if any(t in low for t in ["flash", "vision", "vl", "multimodal", "gpt-4o", "claude-3-5-sonnet", "gemini"]):
        caps.extend(["computer_use", "vision"])
    elif any(t in low for t in ["pro"]) and prov not in ("deepseek", "groq"):
        caps.extend(["computer_use", "vision"])

    if any(t in low for t in ["pro", "reasoner", "r1", "coder", "o1", "o3", "sonnet", "70b", "v4"]):
        caps.append("pro")
    if prov in ("google", "openai", "anthropic", "deepseek"):
        caps.extend(["tools", "structured_output"])
    return list(set(caps))


def supports_capability(model_id: str, capability: str, provider: Optional[str] = None) -> bool:
    """Verifica si un modelo soporta una capacidad específica."""
    clean_id = MODEL_ALIASES.get(model_id, model_id)
    prov = provider or identify_provider_for_model(clean_id)
    caps = get_model_capabilities(clean_id, prov)

    if capability in ("computer_use", "vision"):
        # Modelos con visión explícita o inferida (flash, vl, vision) son 100% permitidos
        if "computer_use" in caps or "vision" in caps:
            return True
        # Modelos de texto puro sin visión (ej. deepseek-chat, deepseek-reasoner, llama estándar) se descartan para vision
        if clean_id.lower() in ("deepseek-chat", "deepseek-reasoner", "deepseek-r1", "llama-3.3-70b-versatile", "whisper-large-v3", "whisper-1"):
            return False

    return capability in caps


# =========================================================================
# FACTORY DE CLIENTES POR PROVEEDOR
# =========================================================================

def create_provider_client(provider: str, model_id: Optional[str] = None) -> Tuple[Optional[Any], str, str]:
    """
    Instancia el cliente SDK OpenAI/Anthropic-compatible adecuado para el proveedor.
    Retorna (client, clean_model_id, provider_name).
    """
    prov = provider.lower()
    mod = MODEL_ALIASES.get(model_id, model_id or "")

    if prov == "deepseek":
        ds_key = get_active_key_for_provider("deepseek")
        if ds_key:
            try:
                cl = openai.OpenAI(
                    base_url="https://api.deepseek.com",
                    api_key=ds_key,
                    max_retries=1
                )
                clean = mod or "deepseek-chat"
                return cl, clean, "deepseek"
            except Exception as e:
                logger.warning(f"Error creando cliente DeepSeek: {e}")

    elif prov == "groq":
        groq_key = get_active_key_for_provider("groq")
        if groq_key:
            try:
                cl = openai.OpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=groq_key,
                    max_retries=1
                )
                clean = mod if ("llama" in mod.lower() or "mixtral" in mod.lower() or "whisper" in mod.lower() or "r1" in mod.lower()) else "llama-3.3-70b-versatile"
                return cl, clean, "groq"
            except Exception as e:
                logger.warning(f"Error creando cliente Groq: {e}")

    elif prov == "google":
        gemini_key = get_active_key_for_provider("google")
        if gemini_key:
            try:
                cl = openai.OpenAI(
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                    api_key=gemini_key,
                    max_retries=1
                )
                clean = mod.replace("google/", "") if "gemini" in mod.lower() else "gemini-flash-latest"
                if clean in ("gemini-1.5-flash", "gemini-2.5-flash", "gemini-2.0-flash"):
                    clean = "gemini-flash-latest"
                return cl, clean, "google"
            except Exception as e:
                logger.warning(f"Error creando cliente Gemini: {e}")

    elif prov == "openai":
        oai_key = get_active_key_for_provider("openai")
        if oai_key:
            try:
                cl = openai.OpenAI(
                    api_key=oai_key,
                    max_retries=1
                )
                clean = mod if ("gpt" in mod.lower() or "o1" in mod.lower() or "o3" in mod.lower() or "whisper" in mod.lower()) else "gpt-4o-mini"
                return cl, clean, "openai"
            except Exception as e:
                logger.warning(f"Error creando cliente OpenAI: {e}")

    elif prov == "anthropic":
        ant_key = get_active_key_for_provider("anthropic")
        if ant_key:
            try:
                import anthropic
                cl = anthropic.Anthropic(api_key=ant_key)
                clean = mod if "claude" in mod.lower() else "claude-3-5-sonnet-20241022"
                return cl, clean, "anthropic"
            except Exception as e:
                logger.warning(f"Error creando cliente Anthropic: {e}")

    elif prov == "openrouter":
        or_key = get_active_key_for_provider("openrouter")
        if or_key:
            try:
                cl = openai.OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=or_key,
                    max_retries=1
                )
                return cl, mod or "anthropic/claude-3.5-sonnet", "openrouter"
            except Exception as e:
                logger.warning(f"Error creando cliente OpenRouter: {e}")

    elif prov == "nvidia":
        nv_key = get_active_key_for_provider("nvidia")
        if nv_key:
            try:
                cl = openai.OpenAI(
                    base_url="https://integrate.api.nvidia.com/v1",
                    api_key=nv_key,
                    max_retries=1
                )
                return cl, mod or "meta/llama-3.3-70b-instruct", "nvidia"
            except Exception as e:
                logger.warning(f"Error creando cliente NVIDIA: {e}")

    elif prov == "ollama" or is_ollama_running():
        try:
            cl = openai.OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                max_retries=1
            )
            return cl, mod or "llama3.2:latest", "ollama"
        except Exception as e:
            logger.warning(f"Error creando cliente Ollama: {e}")

    return None, "", "none"


# =========================================================================
# RESOLUCIÓN PRINCIPAL DE CLIENTE Y MODELO
# =========================================================================

def get_client_and_model(
    preferred_model: Optional[str] = None,
    category: str = "chat",
    required_capability: Optional[str] = None
) -> Tuple[Optional[Any], str, str]:
    """
    Crea e inicializa el cliente OpenAI-compatible adecuado según la categoría solicitada o modelo preferido.
    Verifica que el modelo soporte la capacidad requerida (especialmente visión para 'computer_use').
    """
    config = get_configured_models()
    requested_model = preferred_model or config.get(category, "")
    effective_model = MODEL_ALIASES.get(requested_model, requested_model)
    cap_needed = required_capability or (category if category in ("computer_use", "stt", "pro") else "chat")

    if cap_needed in ("computer_use", "vision") and not supports_capability(effective_model, "computer_use"):
        logger.warning(
            f"El modelo configurado '{effective_model}' no soporta visión/computer_use. "
            f"Buscando alternativa multimodal en proveedores activos..."
        )
        effective_model = ""

    provider = identify_provider_for_model(effective_model) if effective_model else ""
    active_providers = get_active_providers()

    if provider and provider in active_providers and supports_capability(effective_model, cap_needed, provider):
        client, resolved_model, resolved_prov = create_provider_client(provider, effective_model)
        if client:
            return client, resolved_model, resolved_prov

    available = get_available_models().get(category, [])
    valid_candidates = [
        m for m in available
        if m.get("provider") in active_providers and supports_capability(m["id"], cap_needed, m.get("provider"))
    ]

    for cand in valid_candidates:
        client, resolved_model, resolved_prov = create_provider_client(cand["provider"], cand["id"])
        if client:
            logger.info(f"Cliente seleccionado para '{category}': {resolved_prov} ({resolved_model})")
            return client, resolved_model, resolved_prov

    fallback_priority = ["google", "openai", "deepseek", "groq", "anthropic", "openrouter", "nvidia", "ollama"]
    if cap_needed in ("computer_use", "vision"):
        fallback_priority = ["google", "openai", "anthropic", "openrouter"]

    for fallback_prov in fallback_priority:
        if fallback_prov in active_providers:
            cand_id = ""
            for m in FALLBACK_CATALOG.get(fallback_prov, []):
                if cap_needed in m.get("capabilities", []):
                    cand_id = m["id"]
                    break
            if cand_id:
                client, resolved_model, resolved_prov = create_provider_client(fallback_prov, cand_id)
                if client:
                    logger.info(f"Fallback activado a proveedor activo: {resolved_prov} ({resolved_model})")
                    return client, resolved_model, resolved_prov

    return None, "", "none"


# =========================================================================
# EJECUCIÓN CON RESILIENCIA Y MANEJO DE ERRORES TEMPORALES
# =========================================================================

def execute_completion_with_resilience(
    client: Any,
    model: str,
    messages: List[Dict],
    provider: str = "unknown",
    category: str = "chat",
    tools: Optional[List] = None,
    max_retries: int = 2,
    base_delay: float = 0.5,
    **extra_kwargs
) -> Any:
    """
    Ejecuta chat.completions.create con tolerancia a fallos transitorios (429/503),
    rotación de claves múltiples y backoff breve.
    NUNCA enmascara errores de autenticación (401/403) ni modelos inexistentes (404).
    """
    current_client = client
    current_model = model
    current_provider = provider
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            call_kwargs = {
                "model": current_model,
                "messages": messages,
                **extra_kwargs
            }
            if tools:
                call_kwargs["tools"] = tools

            return current_client.chat.completions.create(**call_kwargs)

        except Exception as exc:
            last_exception = exc
            err_cat = classify_api_error(exc)

            # ERRORES PERMANENTES: NO reintentar ni enmascarar
            if err_cat in ("auth", "not_found", "bad_request", "quota_depleted"):
                logger.error(
                    f"[Resilience] Error permanente ({err_cat}) en {current_provider} ({current_model}): {exc}"
                )
                raise exc

            # ERRORES TRANSITORIOS (429, 503, timeouts)
            if is_transient_error(exc):
                logger.warning(
                    f"[Resilience] Error transitorio ({err_cat}) en {current_provider} "
                    f"(intento {attempt + 1}/{max_retries + 1}): {exc}"
                )

                if rotate_provider_key(current_provider):
                    logger.info(f"[Resilience] Reintentando con siguiente clave de {current_provider}...")
                    new_cl, new_m, _ = create_provider_client(current_provider, current_model)
                    if new_cl:
                        current_client = new_cl
                        time.sleep(base_delay)
                        continue

                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"[Resilience] Esperando {delay:.2f}s antes de reintentar...")
                    time.sleep(delay)
                    continue

                active_provs = get_active_providers()
                alt_cl, alt_mod, alt_prov = None, "", ""
                for fallback_prov in ["google", "openai", "groq", "deepseek"]:
                    if fallback_prov != current_provider and fallback_prov in active_provs:
                        alt_cl, alt_mod, alt_prov = get_client_and_model(category=category)
                        if alt_cl and alt_prov != current_provider:
                            break

                if alt_cl:
                    logger.info(f"[Resilience] Cambiando a proveedor de respaldo: {alt_prov} ({alt_mod})")
                    current_client = alt_cl
                    current_model = alt_mod
                    current_provider = alt_prov
                    time.sleep(base_delay)
                    try:
                        call_kwargs["model"] = current_model
                        return current_client.chat.completions.create(**call_kwargs)
                    except Exception as fallback_exc:
                        logger.error(f"[Resilience] Fallback {alt_prov} también falló: {fallback_exc}")
                        raise fallback_exc

            raise exc

    if last_exception:
        raise last_exception


# =========================================================================
# TEST EN VIVO DE CONECTIVIDAD Y MODELOS PERSONALIZADOS
# =========================================================================

def test_model_connectivity(provider: str, model_id: str) -> Dict[str, Any]:
    """
    Prueba la conectividad en vivo con un modelo específico del proveedor.
    Mide la latencia real y detecta de inmediato errores de autenticación, modelo inexistente o cuota.
    """
    start_time = time.time()
    try:
        client, clean_mod, prov = create_provider_client(provider, model_id)
        if not client:
            return {
                "success": False,
                "latency_ms": 0,
                "model": model_id,
                "provider": provider,
                "message": f"No se pudo crear cliente para '{provider}'. Verifica que la clave API esté configurada."
            }

        # Ping ligero para verificar handshake con la API
        if prov == "anthropic":
            resp = client.messages.create(
                model=clean_mod,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=2
            )
        else:
            resp = client.chat.completions.create(
                model=clean_mod,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=2
            )

        latency = int((time.time() - start_time) * 1000)
        return {
            "success": True,
            "latency_ms": latency,
            "model": clean_mod,
            "provider": provider,
            "message": f"Conexión exitosa con {provider.capitalize()} ({clean_mod}) en {latency}ms."
        }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        msg = get_user_friendly_error_message(e, model_id, provider)
        logger.warning(f"Test de conectividad fallido para {provider} ({model_id}): {msg}")
        return {
            "success": False,
            "latency_ms": latency,
            "model": model_id,
            "provider": provider,
            "message": msg
        }

test_model_connectivity.__test__ = False  # Prevenir que pytest lo intente ejecutar como fixture
check_model_connectivity = test_model_connectivity



def get_custom_models() -> List[Dict[str, Any]]:
    """Obtiene la lista de modelos personalizados guardados en models_config.json."""
    if os.path.exists(MODELS_CONFIG_FILE):
        try:
            with open(MODELS_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("custom_models", [])
        except Exception:
            return []
    return []


def save_custom_model(
    provider: str,
    model_id: str,
    name: Optional[str] = None,
    capabilities: Optional[List[str]] = None,
    context_window: Optional[int] = None
) -> Dict[str, Any]:
    """Guarda un modelo personalizado definido por el usuario en models_config.json."""
    if not model_id or not provider:
        return {"success": False, "message": "model_id y provider son obligatorios."}

    caps = capabilities or ["chat", "text"]
    entry = {
        "id": model_id.strip(),
        "name": name.strip() if name else f"{model_id} (Personalizado)",
        "provider": provider.strip().lower(),
        "capabilities": caps,
        "origin": "custom",
        "context_window": context_window or 128000
    }

    try:
        config = {}
        if os.path.exists(MODELS_CONFIG_FILE):
            with open(MODELS_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)

        custom_list = config.get("custom_models", [])
        existing = next((i for i, m in enumerate(custom_list) if m.get("id") == model_id and m.get("provider") == provider), None)
        if existing is not None:
            custom_list[existing] = entry
        else:
            custom_list.append(entry)

        config["custom_models"] = custom_list
        with open(MODELS_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        # Invalidar caché
        global _models_cache
        _models_cache["timestamp"] = 0

        return {"success": True, "message": f"Modelo '{model_id}' guardado correctamente.", "model": entry}
    except Exception as e:
        logger.error(f"Error guardando modelo custom: {e}")
        return {"success": False, "message": f"Error al guardar: {e}"}


# =========================================================================
# DESCUBRIMIENTO EN VIVO DE MODELOS (ENDPOINTS OFICIALES)
# =========================================================================

def _fetch_live_google_models(key: str) -> List[Dict]:
    """Descubre modelos reales de Google AI Studio vía API oficial filtrando sólo modelos válidos."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Miku-V2"})
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        models = []
        banned = ["embedding", "aqa", "imagen", "image", "lyria", "veo", "tts", "whisper", "deep-research", "bison", "gecko", "text-", "gemini-2.5-flash"]
        for m in data.get("models", []):
            methods = m.get("supportedGenerationMethods", [])
            if "generateContent" not in methods:
                continue
            raw_id = m.get("name", "").replace("models/", "")
            if not raw_id or not raw_id.startswith("gemini"):
                continue
            if any(b in raw_id.lower() for b in banned):
                continue
            
            display_name = m.get("displayName") or raw_id
            caps = ["chat", "text", "tools", "structured_output"]
            if any(term in raw_id.lower() for term in ["flash", "pro", "vision", "thinking"]):
                caps.extend(["computer_use", "vision"])
            if any(term in raw_id.lower() for term in ["pro", "thinking"]):
                caps.append("pro")
            
            models.append({
                "id": raw_id,
                "name": f"{display_name} ({raw_id})",
                "provider": "google",
                "capabilities": list(set(caps)),
                "origin": "verified",
                "context_window": 1048576
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
            if "whisper" in m_id:
                models.append({
                    "id": m_id,
                    "name": f"{m_id.capitalize()} (Groq STT)",
                    "provider": "groq",
                    "capabilities": ["stt", "audio_stt"],
                    "origin": "verified",
                    "context_window": 0
                })
            elif "guard" not in m_id and "orpheus" not in m_id:
                caps = ["chat", "text", "tools"]
                if any(k in m_id.lower() for k in ["70b", "r1", "coder"]):
                    caps.append("pro")
                models.append({
                    "id": m_id,
                    "name": f"{m_id} (Groq)",
                    "provider": "groq",
                    "capabilities": caps,
                    "origin": "verified",
                    "context_window": 128000
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
                    "capabilities": ["stt", "audio_stt"],
                    "origin": "verified",
                    "context_window": 0
                })
            elif "dall-e" in m_id:
                models.append({
                    "id": m_id,
                    "name": f"{m_id} (OpenAI Imagen)",
                    "provider": "openai",
                    "capabilities": ["image_gen", "images"],
                    "origin": "verified",
                    "context_window": 0
                })
            elif any(prefix in m_id for prefix in ["gpt-4o", "gpt-4-turbo", "o1", "o3"]):
                caps = ["chat", "text", "tools", "structured_output"]
                if "gpt-4o" in m_id:
                    caps.extend(["computer_use", "vision"])
                if "o1" in m_id or "o3" in m_id or "gpt-4o" in m_id:
                    caps.append("pro")
                models.append({
                    "id": m_id,
                    "name": f"{m_id} (OpenAI)",
                    "provider": "openai",
                    "capabilities": list(set(caps)),
                    "origin": "verified",
                    "context_window": 128000
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
                caps = ["chat", "text"]
                if any(k in m_name.lower() for k in ["coder", "r1", "pro", "70b"]):
                    caps.append("pro")
                models.append({
                    "id": m_name,
                    "name": f"{m_name} (Ollama Local)",
                    "provider": "ollama",
                    "capabilities": caps,
                    "origin": "verified",
                    "context_window": 128000
                })
        return models


def _fetch_live_deepseek_models(key: str) -> List[Dict]:
    """Descubre modelos reales de DeepSeek vía endpoint oficial."""
    url = "https://api.deepseek.com/models"
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
            name = m.get("name") or m_id
            caps = ["chat", "text"]
            if any(term in m_id.lower() for term in ("reasoner", "reasoning", "r1", "v4-pro")):
                caps.append("pro")
            if any(term in m_id.lower() for term in ("chat", "v4")):
                caps.extend(["tools", "structured_output"])
            modalities = m.get("input_modalities", [])
            if "image" in modalities or any(term in m_id.lower() or term in name.lower() for term in ("flash", "vl", "vision", "multimodal")):
                caps.extend(["computer_use", "vision"])
            models.append({
                "id": m_id,
                "name": f"{name} (DeepSeek Oficial)",
                "provider": "deepseek",
                "capabilities": list(set(caps)),
                "origin": "verified",
                "context_window": 64000
            })
        return models or FALLBACK_CATALOG.get("deepseek", [])


def _fetch_live_anthropic_models(key: str) -> List[Dict]:
    """Descubre los modelos disponibles para la clave de Anthropic."""
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/models",
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "User-Agent": "Miku-V2"
        }
    )
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return [{
        "id": model["id"],
        "name": f"{model.get('display_name') or model['id']} (Anthropic)",
        "provider": "anthropic",
        "capabilities": ["chat", "pro", "text", "vision", "tools", "structured_output"],
        "origin": "verified",
        "context_window": 200000
    } for model in data.get("data", []) if model.get("id")]


def _fetch_live_openrouter_models(key: str) -> List[Dict]:
    """Descubre los modelos disponibles para la clave de OpenRouter."""
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {key}", "User-Agent": "Miku-V2"}
    )
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    models = []
    for model in data.get("data", []):
        model_id = model.get("id", "")
        if not model_id:
            continue
        architecture = model.get("architecture") or {}
        modalities = architecture.get("input_modalities") or []
        parameters = model.get("supported_parameters") or []
        caps = ["chat", "text"]
        if "image" in modalities:
            caps.extend(["computer_use", "vision"])
        if "tools" in parameters:
            caps.append("tools")
        models.append({
            "id": model_id,
            "name": f"{model.get('name') or model_id} (OpenRouter)",
            "provider": "openrouter",
            "capabilities": caps,
            "origin": "verified",
            "context_window": model.get("context_length") or 0
        })
    return models


def _fetch_live_nvidia_models(key: str) -> List[Dict]:
    """Descubre los modelos disponibles para la clave NVIDIA NIM."""
    req = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/models",
        headers={"Authorization": f"Bearer {key}", "User-Agent": "Miku-V2"}
    )
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    models = []
    for model in data.get("data", []):
        model_id = model.get("id", "")
        if not model_id:
            continue
        caps = ["chat", "text", "tools"]
        if any(term in model_id.lower() for term in ("reason", "70b", "coder")):
            caps.append("pro")
        models.append({
            "id": model_id,
            "name": f"{model.get('name') or model_id} (NVIDIA)",
            "provider": "nvidia",
            "capabilities": caps,
            "origin": "verified",
            "context_window": model.get("context_length") or 0
        })
    return models


def discover_provider_models(provider: str) -> List[Dict]:
    """Consulta la API en vivo del proveedor con fallback al catálogo curado."""
    provider = provider.lower()
    active_key = get_active_key_for_provider(provider)
    if provider == "google" and active_key:
        try:
            live = _fetch_live_google_models(active_key)
            if live:
                return live
        except Exception as e:
            logger.warning(f"No se pudo consultar lista en vivo de Google ({e}), usando catálogo curado.")
    elif provider == "deepseek" and active_key:
        try:
            live = _fetch_live_deepseek_models(active_key)
            if live:
                return live
        except Exception as e:
            logger.warning(f"No se pudo consultar lista en vivo de DeepSeek ({e}), usando catálogo curado.")
    elif provider == "groq" and active_key:
        try:
            live = _fetch_live_groq_models(active_key)
            if live:
                return live
        except Exception as e:
            logger.warning(f"No se pudo consultar lista en vivo de Groq ({e}), usando catálogo curado.")
    elif provider == "openai" and active_key:
        try:
            live = _fetch_live_openai_models(active_key)
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
    elif provider == "anthropic" and active_key:
        try:
            live = _fetch_live_anthropic_models(active_key)
            if live:
                return live
        except Exception as e:
            logger.warning(f"No se pudo consultar lista en vivo de Anthropic ({e}), usando catálogo curado.")
    elif provider == "openrouter" and active_key:
        try:
            live = _fetch_live_openrouter_models(active_key)
            if live:
                return live
        except Exception as e:
            logger.warning(f"No se pudo consultar lista en vivo de OpenRouter ({e}), usando catálogo curado.")
    elif provider == "nvidia" and active_key:
        try:
            live = _fetch_live_nvidia_models(active_key)
            if live:
                return live
        except Exception as e:
            logger.warning(f"No se pudo consultar lista en vivo de NVIDIA ({e}), usando catálogo curado.")

    return FALLBACK_CATALOG.get(provider, [])


def get_available_models(force_refresh: bool = False) -> Dict[str, List[Dict]]:
    """Devuelve los modelos disponibles categorizados (chat, computer_use, pro, stt) con origen y capacidades."""
    global _models_cache
    now = time.time()
    if not force_refresh and (now - _models_cache["timestamp"] < CACHE_TTL_SECONDS) and _models_cache["available"]:
        return _models_cache["available"]

    active_providers = get_active_providers()
    all_provider_models = []

    def discover(prov):
        try:
            return prov, discover_provider_models(prov)
        except Exception as exc:
            logger.warning(f"No se pudo descubrir modelos para {prov}: {exc}")
            return prov, []

    discoverable = [
        prov for prov in FALLBACK_CATALOG
        if prov in active_providers and (
            prov == "ollama" or get_active_key_for_provider(prov)
        )
    ]
    live_by_provider = {}
    if discoverable:
        with ThreadPoolExecutor(max_workers=min(8, len(discoverable))) as executor:
            for prov, models in executor.map(discover, discoverable):
                live_by_provider[prov] = models

    # 1. Modelos descubiertos para claves activas y catálogo informativo para los demás.
    for prov, cat_items in FALLBACK_CATALOG.items():
        has_key = prov in active_providers
        prov_models = live_by_provider.get(prov) or cat_items
        for m in prov_models:
            entry = dict(m)
            entry["has_key"] = has_key
            entry["selectable"] = has_key
            all_provider_models.append(entry)

    # 2. Agregar modelos personalizados (origin: "custom")
    custom_models = get_custom_models()
    for cm in custom_models:
        prov = cm.get("provider", "other")
        entry = dict(cm)
        entry["has_key"] = prov in active_providers
        entry["selectable"] = entry["has_key"]
        all_provider_models.append(entry)

    chat_models = []
    computer_use_models = []
    pro_models = []
    stt_models = []
    by_provider = {}

    seen_ids = set()
    for m in all_provider_models:
        mid = m["id"]
        caps = m.get("capabilities", ["chat"])
        prov = m.get("provider", "other")
        has_k = m.get("has_key", False)
        origin = m.get("origin", "catalog")
        cw = m.get("context_window", 128000)
        
        entry = {
            "id": mid,
            "name": m["name"],
            "provider": prov,
            "capabilities": caps,
            "has_key": has_k,
            "selectable": m.get("selectable", False),
            "origin": origin,
            "context_window": cw
        }
        
        if prov not in by_provider:
            by_provider[prov] = []
        by_provider[prov].append(entry)
        
        if ("chat" in caps or "text" in caps) and (mid, "chat") not in seen_ids:
            seen_ids.add((mid, "chat"))
            chat_models.append(entry)
            
        if ("computer_use" in caps or "vision" in caps) and (mid, "computer_use") not in seen_ids:
            # Excluir únicamente modelos de puro texto sin soporte de visión
            if mid.lower() not in ("deepseek-chat", "deepseek-reasoner", "deepseek-r1", "deepseek-coder", "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "whisper-large-v3", "whisper-1"):
                seen_ids.add((mid, "computer_use"))
                computer_use_models.append(entry)
            
        if "pro" in caps and (mid, "pro") not in seen_ids:
            seen_ids.add((mid, "pro"))
            pro_models.append(entry)

        if ("stt" in caps or "audio_stt" in caps) and (mid, "stt") not in seen_ids:
            seen_ids.add((mid, "stt"))
            stt_models.append(entry)

    def _sort_key(item):
        name = item["name"].lower()
        if "recomendado" in name or "flash" in name or "3.3 70b" in name:
            return 0
        return 1

    chat_models.sort(key=_sort_key)
    computer_use_models.sort(key=_sort_key)
    pro_models.sort(key=_sort_key)
    stt_models.sort(key=_sort_key)

    result = {
        "chat": chat_models,
        "computer_use": computer_use_models,
        "pro": pro_models,
        "stt": stt_models,
        "by_provider": by_provider
    }

    _models_cache["timestamp"] = now
    _models_cache["available"] = result
    return result


def invalidate_available_models() -> None:
    """Fuerza el redescubrimiento tras modificar credenciales o modelos personalizados."""
    try:
        load_dotenv(get_env_path(), override=True)
    except Exception:
        pass
    _models_cache["timestamp"] = 0


def start_background_model_prefetch():
    """Inicia descubrimiento de modelos en segundo plano sin demorar el arranque de la app."""
    import threading
    def _worker():
        try:
            get_available_models(force_refresh=True)
        except Exception as e:
            logger.debug(f"[ModelsProvider] Prefetch en segundo plano omitido: {e}")
    threading.Thread(target=_worker, daemon=True).start()


# =========================================================================
# CONFIGURACIÓN GUARDADA
# =========================================================================

_cached_configured_models = None

def get_configured_models(force_reload: bool = False) -> Dict[str, Any]:
    """Carga la configuración guardada de modelos desde models_config.json."""
    global _cached_configured_models
    if _cached_configured_models is not None and not force_reload:
        return _cached_configured_models

    default_config = {
        "chat": "gemini-flash-lite-latest",
        "pro": "deepseek-chat",
        "computer_use": "gemini-1.5-flash",
        "stt": "whisper-large-v3",
        "custom_models": []
    }
    if os.path.exists(MODELS_CONFIG_FILE):
        try:
            with open(MODELS_CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                default_config.update(saved)
        except Exception as e:
            logger.error(f"Error cargando models_config.json: {e}")

    for k in ["chat", "pro", "computer_use", "stt"]:
        v = default_config.get(k, "")
        if v in MODEL_ALIASES:
            default_config[k] = MODEL_ALIASES[v]

    _cached_configured_models = default_config
    return default_config


def reload_configured_models():
    """Recarga la configuración de modelos en caliente."""
    load_dotenv(get_env_path(), override=True)
    return get_configured_models(force_reload=True)


# Pre-poblar caché inicial inmediatamente con catálogo estático para respuesta instantánea (0ms)
try:
    _initial_active = get_active_providers()
    _init_chat = []
    _init_comp = []
    _init_pro = []
    _init_stt = []
    _init_by_prov = {}
    for _p, _cat_items in FALLBACK_CATALOG.items():
        _has_k = _p in _initial_active
        _with_key = []
        for _m in _cat_items:
            _entry = dict(_m)
            _entry["has_key"] = _has_k
            _with_key.append(_entry)
            _c = _entry.get("capabilities", [])
            if "chat" in _c or "text" in _c: _init_chat.append(_entry)
            if ("computer_use" in _c or "vision" in _c) and _entry.get("id", "").lower() not in ("deepseek-chat", "deepseek-reasoner", "deepseek-r1", "deepseek-coder", "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "whisper-large-v3", "whisper-1"):
                _init_comp.append(_entry)
            if "pro" in _c: _init_pro.append(_entry)
            if "stt" in _c or "audio_stt" in _c: _init_stt.append(_entry)
        _init_by_prov[_p] = _with_key

    _models_cache["available"] = {
        "chat": _init_chat,
        "computer_use": _init_comp,
        "pro": _init_pro,
        "stt": _init_stt,
        "by_provider": _init_by_prov
    }
    _models_cache["timestamp"] = 0
except Exception:
    pass
