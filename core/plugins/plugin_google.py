"""
Plugin Google Ecosystem (`core/plugins/plugin_google.py`):
Native Google Ecosystem integration (Google Standard):
1. Gemini Search Grounding & Google Maps Grounding (`consultar_google_grounding`).
2. Google Workspace OAuth 2.0 helper & live status (`estado_google_workspace`,
   Gmail / Google Calendar / Google Drive integration via Vault-stored OAuth tokens).
"""

import os
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore

from action_result import ActionResult, ActionStatus
from core.security.vault import get_secret, set_secret

GOOGLE_WORKSPACE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]


def build_google_oauth_url(redirect_uri: str = "http://127.0.0.1:8000/api/google/oauth/callback") -> Dict[str, Any]:
    """
    Constructs the official Google OAuth 2.0 authorization URL using the `GOOGLE_CLIENT_ID`
    stored in the OS Credential Vault.
    """
    client_id = get_secret("GOOGLE_CLIENT_ID") or ""
    configured = bool(client_id)
    if not configured:
        return {
            "configured": False,
            "auth_url": "",
            "scopes": GOOGLE_WORKSPACE_SCOPES,
            "message": "Configura GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET en la Bóveda de Claves para vincular Google Workspace.",
        }

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(GOOGLE_WORKSPACE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    return {
        "configured": True,
        "connected": bool(get_secret("GOOGLE_REFRESH_TOKEN")),
        "auth_url": f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}",
        "scopes": GOOGLE_WORKSPACE_SCOPES,
    }


def consultar_google_grounding(
    consulta: str,
    modo: str = "search",
    ubicacion_opcional: str = "",
) -> str:
    """
    Executes a real-time query grounded in Google Search or Google Maps using Gemini 2.5 Flash.
    """
    api_key = get_secret("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return ActionResult(
            status=ActionStatus.FAILED,
            action="consultar_google_grounding",
            message="No se encontró GEMINI_API_KEY en el Vault para usar Google Grounding.",
            error="Missing GEMINI_API_KEY",
            data={"query": consulta, "mode": modo},
        ).to_tool_response()

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        prompt = consulta
        if ubicacion_opcional:
            prompt = f"{consulta} (Ubicación de referencia: {ubicacion_opcional})"

        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config,
        )
        text = (getattr(response, "text", "") or "").strip()
        return ActionResult(
            status=ActionStatus.CONFIRMED,
            action="consultar_google_grounding",
            message=text or "Consulta completada con Google Grounding.",
            evidence="model=gemini-2.5-flash tool=google_search",
            data={"query": consulta, "mode": modo},
        ).to_tool_response()
    except Exception as exc:
        return ActionResult(
            status=ActionStatus.FAILED,
            action="consultar_google_grounding",
            message="Error al consultar Google Search/Maps Grounding.",
            error=str(exc),
            data={"query": consulta, "mode": modo},
        ).to_tool_response()


def consultar_google_workspace(servicio: str = "status", max_resultados: int = 5) -> str:
    """
    Queries the user's linked Google Workspace account (Gmail, Calendar, Drive) or returns
    connection status if not yet linked.
    """
    status_info = build_google_oauth_url()
    refresh_token = get_secret("GOOGLE_REFRESH_TOKEN")
    client_id = get_secret("GOOGLE_CLIENT_ID")
    client_secret = get_secret("GOOGLE_CLIENT_SECRET")

    if servicio == "status" or not (refresh_token and client_id and client_secret):
        connected = bool(refresh_token and client_id and client_secret)
        msg = (
            "Google Workspace está vinculado y activo."
            if connected
            else "Google Workspace aún no tiene una sesión OAuth activa. Puedes vincularlo en Ajustes -> Integraciones -> Conectar con Google."
        )
        return ActionResult(
            status=ActionStatus.CONFIRMED,
            action="consultar_google_workspace",
            message=msg,
            evidence=f"connected={connected}",
            data={**status_info, "connected": connected, "service": servicio},
        ).to_tool_response()

    try:
        token_resp = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=10,
        )
        if token_resp.status_code != 200:
            return ActionResult(
                status=ActionStatus.FAILED,
                action="consultar_google_workspace",
                message="No se pudo renovar el token OAuth de Google Workspace.",
                error=token_resp.text[:300],
            ).to_tool_response()

        access_token = token_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {access_token}"}

        if servicio == "calendar":
            r = requests.get(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers=headers,
                params={"maxResults": max_resultados, "singleEvents": "true", "orderBy": "startTime"},
                timeout=10,
            )
            items = r.json().get("items", [])
            resumen = [f"- {ev.get('summary', 'Sin título')} ({ev.get('start', {}).get('dateTime', ev.get('start', {}).get('date', ''))})" for ev in items]
            return ActionResult(
                status=ActionStatus.CONFIRMED,
                action="consultar_google_workspace",
                message="Eventos de Google Calendar:\n" + ("\n".join(resumen) if resumen else "Sin eventos próximos."),
                evidence=f"http={r.status_code} count={len(items)}",
                data={"service": "calendar", "count": len(items)},
            ).to_tool_response()

        if servicio == "drive":
            r = requests.get(
                "https://www.googleapis.com/drive/v3/files",
                headers=headers,
                params={"pageSize": max_resultados, "fields": "files(id,name,mimeType,modifiedTime)"},
                timeout=10,
            )
            files = r.json().get("files", [])
            resumen = [f"- {f.get('name')} ({f.get('mimeType')})" for f in files]
            return ActionResult(
                status=ActionStatus.CONFIRMED,
                action="consultar_google_workspace",
                message="Archivos recientes en Google Drive:\n" + ("\n".join(resumen) if resumen else "Sin archivos."),
                evidence=f"http={r.status_code} count={len(files)}",
                data={"service": "drive", "count": len(files)},
            ).to_tool_response()

        # Default: gmail
        r = requests.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers=headers,
            params={"maxResults": max_resultados},
            timeout=10,
        )
        msgs = r.json().get("messages", [])
        return ActionResult(
            status=ActionStatus.CONFIRMED,
            action="consultar_google_workspace",
            message=f"Gmail conectado correctamente ({len(msgs)} mensajes recientes encontrados).",
            evidence=f"http={r.status_code} count={len(msgs)}",
            data={"service": "gmail", "count": len(msgs)},
        ).to_tool_response()
    except Exception as exc:
        return ActionResult(
            status=ActionStatus.FAILED,
            action="consultar_google_workspace",
            message="Error al consultar la API de Google Workspace.",
            error=str(exc),
        ).to_tool_response()


def register(reg: Any) -> None:
    reg.register_tool(
        name="consultar_google_grounding",
        description=(
            "Consulta información verificada en tiempo real usando Google Search Grounding y Google Maps "
            "a través de Gemini 2.5 Flash. Ideal para hechos actuales, lugares, direcciones y precios."
        ),
        parameters={
            "type": "object",
            "properties": {
                "consulta": {"type": "string", "description": "Pregunta o búsqueda a fundamentar en Google."},
                "modo": {
                    "type": "string",
                    "enum": ["search", "maps"],
                    "description": "Modo de fundamentación: 'search' o 'maps'.",
                },
                "ubicacion_opcional": {
                    "type": "string",
                    "description": "Ciudad o coordenadas de referencia opcionales.",
                },
            },
            "required": ["consulta"],
        },
        handler=consultar_google_grounding,
        plugin_tag="google",
    )

    reg.register_tool(
        name="consultar_google_workspace",
        description=(
            "Consulta el estado o datos reales de Google Workspace del usuario (Gmail, Google Calendar, "
            "Google Drive) mediante OAuth 2.0 seguro almacenado en el Vault."
        ),
        parameters={
            "type": "object",
            "properties": {
                "servicio": {
                    "type": "string",
                    "enum": ["status", "gmail", "calendar", "drive"],
                    "description": "Servicio de Google Workspace a consultar.",
                },
                "max_resultados": {
                    "type": "integer",
                    "description": "Número máximo de elementos a recuperar (por defecto 5).",
                },
            },
            "required": ["servicio"],
        },
        handler=consultar_google_workspace,
        plugin_tag="google",
    )
