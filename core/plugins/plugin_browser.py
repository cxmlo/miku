"""
Plugin Browser (`core/plugins/plugin_browser.py`):
Lazy-loaded Playwright & fast HTTP web extraction plugin with real status verification.
"""

from typing import Any
from urllib.parse import urlparse
import urllib.request

try:
    import requests
except ImportError:
    requests = None  # type: ignore

from action_result import ActionResult, ActionStatus
from core.engine.lazy_loader import lazy_import

# Playwright is lazy-loaded so startup never pays its import cost
_playwright = lazy_import("playwright.sync_api")


def inspeccionar_url_rapido(url: str, timeout_segundos: float = 12.0) -> str:
    """
    Fetches and summarizes a web page cleanly with HTTP status verification.
    """
    clean_url = (url or "").strip()
    parsed = urlparse(clean_url)
    if not parsed.scheme:
        clean_url = "https://" + clean_url

    try:
        resp = requests.get(
            clean_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MikuCompanion/2.5"},
            timeout=max(2.0, min(float(timeout_segundos), 30.0)),
        )
        status_code = resp.status_code
        if status_code >= 400:
            return ActionResult(
                status=ActionStatus.FAILED,
                action="inspeccionar_url_rapido",
                message=f"La URL devolvió un error HTTP {status_code}.",
                error=f"HTTP {status_code} para {clean_url}",
                data={"url": clean_url, "status_code": status_code},
            ).to_tool_response()

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        title = (soup.title.string or "").strip() if soup.title else clean_url
        body_text = " ".join(soup.get_text(separator=" ").split())[:3500]
        return ActionResult(
            status=ActionStatus.CONFIRMED,
            action="inspeccionar_url_rapido",
            message=f"Título: {title}\nURL: {clean_url} (HTTP {status_code})\n\n{body_text}",
            evidence=f"http_status={status_code} len={len(body_text)}",
            data={"url": clean_url, "status_code": status_code, "title": title},
        ).to_tool_response()
    except Exception as exc:
        return ActionResult(
            status=ActionStatus.FAILED,
            action="inspeccionar_url_rapido",
            message=f"Error al conectar con {clean_url}.",
            error=str(exc),
            data={"url": clean_url},
        ).to_tool_response()


def register(reg: Any) -> None:
    reg.register_tool(
        name="inspeccionar_url_rapido",
        description=(
            "Inspecciona una URL web verificando su código HTTP real y extrayendo el título y texto limpio "
            "sin cargar recursos innecesarios."
        ),
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL completa a inspeccionar."},
                "timeout_segundos": {"type": "number", "description": "Tiempo límite en segundos (por defecto 12)."},
            },
            "required": ["url"],
        },
        handler=inspeccionar_url_rapido,
        plugin_tag="browser",
    )
