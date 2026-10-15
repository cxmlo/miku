#!/usr/bin/env python3
"""
miku_hook.py — Disparador de eventos y hooks para la Isla Dinámica de Miku.
Permite a cualquier agente, script o herramienta CLI notificar a Miku en tiempo real.

Uso desde terminal:
    python scripts/miku_hook.py "Pensando..." --agent claude --event UserPromptSubmit
    python scripts/miku_hook.py "Escribiendo archivo" --agent cursor --event PreToolUse --tool write_file
    python scripts/miku_hook.py "¡Tarea completada!" --agent antigravity --event Stop
    python scripts/miku_hook.py "¿Permitir ejecutar comando?" --event PermissionRequest --tool "rm -rf build/"

Uso como módulo de Python:
    from scripts.miku_hook import notify_miku
    notify_miku("Descargando modelo...", agent="custom", event="PreToolUse")
"""

import sys
import argparse
import urllib.request
import json

DEFAULT_URL = "http://127.0.0.1:8000/api/hook"

def notify_miku(message: str, agent: str = "claude", event: str = "PreToolUse", tool: str = "", url: str = DEFAULT_URL) -> bool:
    payload = {
        "agent": agent,
        "hook_event_name": event,
        "event": event,
        "prompt": message,
        "message": message,
        "tool_name": tool or message,
        "tool": tool or message
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=2.0) as res:
            return res.status == 200
    except Exception as e:
        # Falla silenciosamente si Miku no está abierta
        return False

def main():
    parser = argparse.ArgumentParser(description="Envía eventos en vivo a la Isla Dinámica de Miku")
    parser.add_argument("message", nargs="?", default="", help="Mensaje o descripción de la acción")
    parser.add_argument("-a", "--agent", default="claude", help="Nombre del agente (claude, cursor, antigravity, vercel, etc.)")
    parser.add_argument("-e", "--event", default="PreToolUse", choices=["UserPromptSubmit", "PreToolUse", "PermissionRequest", "Stop", "StopFailure", "Notification"], help="Tipo de evento")
    parser.add_argument("-t", "--tool", default="", help="Herramienta o comando que se está ejecutando")
    parser.add_argument("--url", default=DEFAULT_URL, help="URL del gateway de Miku")

    args = parser.parse_args()
    msg = args.message or args.tool or "Acción en progreso"
    ok = notify_miku(message=msg, agent=args.agent, event=args.event, tool=args.tool, url=args.url)
    if ok:
        print(f"Hook enviado a Miku: [{args.agent}] -> {args.event}: {msg}")
    else:
        print("Miku Core no disponible (¿server.py está en ejecución?)")

if __name__ == "__main__":
    main()
