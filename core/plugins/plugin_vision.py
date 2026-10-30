"""
Plugin Vision (`core/plugins/plugin_vision.py`):
Lazy-loaded screen capture and Automatic Visual Bridge (`gemini-2.5-flash`) so text-only
models (such as `deepseek-chat` or `deepseek-reasoner`) never fail with HTTP 400 when
inspecting screenshots or performing visual clicks.
"""

import base64
import io
import os
from typing import Any, Dict, Optional

from action_result import ActionResult, ActionStatus
from core.engine.lazy_loader import lazy_import
from core.security.vault import get_secret

# Deferred heavy imports for <1.5s startup
_pyautogui = lazy_import("pyautogui")


def describe_screenshot_via_gemini_bridge(
    image_bytes: bytes,
    prompt_hint: str = "Describe detalladamente los elementos interactivos, textos, botones y errores visibles en esta pantalla.",
) -> Dict[str, Any]:
    """
    Uses `gemini-2.5-flash` as a fast, low-cost visual bridge to convert a screenshot into
    structured text + coordinates for text-only primary models (e.g., DeepSeek).
    """
    api_key = get_secret("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {
            "ok": False,
            "bridge_model": "gemini-2.5-flash",
            "description": "",
            "error": "GEMINI_API_KEY no configurada en el Vault para el puente visual.",
        }

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                prompt_hint,
            ],
        )
        text = getattr(response, "text", "") or ""
        return {
            "ok": True,
            "bridge_model": "gemini-2.5-flash",
            "description": text.strip(),
        }
    except Exception as exc:
        return {
            "ok": False,
            "bridge_model": "gemini-2.5-flash",
            "description": "",
            "error": str(exc),
        }


def analizar_pantalla_con_puente_visual(objetivo: str = "Describir elementos activos en pantalla") -> str:
    """
    Captures the current screen lazily and describes it using the Gemini 2.5 Flash bridge.
    """
    try:
        from PIL import ImageGrab

        img = ImageGrab.grab()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        raw_bytes = buf.getvalue()
    except Exception as exc:
        return ActionResult(
            status=ActionStatus.FAILED,
            action="analizar_pantalla_con_puente_visual",
            message="No fue posible capturar la pantalla en este entorno (sin servidor gráfico o permisos).",
            error=str(exc),
            data={"objective": objetivo, "b64_size": 0},
        ).to_tool_response()

    bridge = describe_screenshot_via_gemini_bridge(
        raw_bytes,
        prompt_hint=f"Objetivo del usuario: {objetivo}. Enumera textos, botones y coordenadas aproximadas.",
    )
    if bridge.get("ok"):
        return ActionResult(
            status=ActionStatus.CONFIRMED,
            action="analizar_pantalla_con_puente_visual",
            message=f"[Puente Visual {bridge['bridge_model']}]:\n{bridge['description']}",
            evidence=f"bytes={len(raw_bytes)} model={bridge['bridge_model']}",
            data=bridge,
        ).to_tool_response()

    return ActionResult(
        status=ActionStatus.FAILED,
        action="analizar_pantalla_con_puente_visual",
        message="La captura se realizó, pero el puente visual no pudo procesarla.",
        error=bridge.get("error", "Error desconocido"),
        data={"bytes": len(raw_bytes), **bridge},
    ).to_tool_response()


def register(reg: Any) -> None:
    reg.register_tool(
        name="analizar_pantalla_con_puente_visual",
        description=(
            "Captura la pantalla de forma diferida (lazy) y la analiza mediante el puente visual "
            "gemini-2.5-flash, permitiendo que modelos de solo texto (como DeepSeek) entiendan "
            "exactamente qué hay en el escritorio sin errores HTTP 400."
        ),
        parameters={
            "type": "object",
            "properties": {
                "objetivo": {
                    "type": "string",
                    "description": "Qué elemento, ventana o texto específico deseas inspeccionar en la pantalla.",
                }
            },
            "required": ["objetivo"],
        },
        handler=analizar_pantalla_con_puente_visual,
        plugin_tag="vision",
    )
