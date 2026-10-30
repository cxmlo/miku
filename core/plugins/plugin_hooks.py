"""
Plugin Hooks (`core/plugins/plugin_hooks.py`):
Universal IDE & CLI Webhook Listener (`/api/hooks/event`) for Miku Companion.
Allows external developer tools (Claude Code, Cursor, VS Code tasks, Git hooks, CI scripts)
to push live state transitions, approval requests, or completion alerts directly to Miku's
Dynamic Island (`thinking`, `working`, `talking`, `error`, `idle`).
"""

import time
import uuid
from typing import Any, Dict, List

from action_result import ActionResult, ActionStatus
from .plugin_ui import _emit_to_island, solicitar_aprobacion_comando

_RECENT_HOOK_EVENTS: List[Dict[str, Any]] = []

HOOK_EVENT_STATE_MAP: Dict[str, str] = {
    "session_start": "thinking",
    "tool_start": "working",
    "tool_running": "working",
    "searching": "searching",
    "waiting_approval": "thinking",
    "permission_prompt": "thinking",
    "task_complete": "talking",
    "stop": "idle",
    "idle": "idle",
    "error": "error",
    "task_failed": "error",
}


def process_hook_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes an incoming IDE/CLI hook event (`POST /api/hooks/event`) and synchronizes
    Miku's Dynamic Island state + ThoughtStream or ApprovalCard.
    """
    event_type = str(payload.get("event") or payload.get("type") or "tool_running").strip().lower()
    source = str(payload.get("source") or "cli_hook").strip()
    title = str(payload.get("title") or payload.get("message") or f"[{source}] {event_type}").strip()
    command = str(payload.get("command") or "").strip()
    diff_preview = str(payload.get("diff") or "").strip()
    miku_state = str(payload.get("miku_state") or HOOK_EVENT_STATE_MAP.get(event_type, "working")).strip()

    event_record = {
        "id": f"hook_{uuid.uuid4().hex[:8]}",
        "event": event_type,
        "source": source,
        "title": title,
        "command": command,
        "miku_state": miku_state,
        "timestamp": int(time.time() * 1000),
    }
    _RECENT_HOOK_EVENTS.append(event_record)
    if len(_RECENT_HOOK_EVENTS) > 50:
        del _RECENT_HOOK_EVENTS[:-50]

    # Update 2D Canvas Miku state and ThoughtStream
    _emit_to_island({"type": "miku_state", "state": miku_state})
    _emit_to_island(
        {
            "type": "thought_stream",
            "step": f"[{source}] {title}",
            "state": miku_state,
            "diff": diff_preview,
            "file": str(payload.get("file") or ""),
            "ts": event_record["timestamp"],
        }
    )

    if event_type in ("waiting_approval", "permission_prompt") and command:
        solicitar_aprobacion_comando(
            comando=command,
            titulo=title or f"Aprobación requerida por {source}",
            riesgo=str(payload.get("risk") or "medio"),
            diff_preview=diff_preview,
        )
    elif event_type in ("error", "task_failed"):
        _emit_to_island(
            {
                "type": "scene",
                "name": "error_card",
                "data": {
                    "id": event_record["id"],
                    "title": title,
                    "stderr": str(payload.get("stderr") or payload.get("detail") or "Fallo reportado por hook externo"),
                    "exit_code": int(payload.get("exit_code") or 1),
                    "retry_cmd": command,
                },
            }
        )

    return {"status": "ok", "hook": event_record}


def get_recent_hook_events() -> List[Dict[str, Any]]:
    return list(reversed(_RECENT_HOOK_EVENTS))


def emitir_evento_hook_ide(
    evento: str,
    origen: str = "cursor",
    mensaje: str = "",
    comando: str = "",
) -> str:
    res = process_hook_event(
        {
            "event": evento,
            "source": origen,
            "title": mensaje or f"Evento {evento} desde {origen}",
            "command": comando,
        }
    )
    return ActionResult(
        status=ActionStatus.CONFIRMED,
        action="emitir_evento_hook_ide",
        message=f"Hook '{evento}' procesado desde '{origen}' -> estado Miku: {res['hook']['miku_state']}",
        evidence=f"hook_id={res['hook']['id']}",
        data=res["hook"],
    ).to_tool_response()


def register(reg: Any) -> None:
    reg.register_tool(
        name="emitir_evento_hook_ide",
        description=(
            "Emite un evento al bus universal de Hooks de IDE/CLI (compatible con Claude Code, Cursor y Git hooks) "
            "para sincronizar el estado de Miku en la Isla Dinámica."
        ),
        parameters={
            "type": "object",
            "properties": {
                "evento": {
                    "type": "string",
                    "enum": [
                        "session_start",
                        "tool_start",
                        "searching",
                        "waiting_approval",
                        "task_complete",
                        "error",
                        "idle",
                    ],
                    "description": "Tipo de ciclo de vida del hook.",
                },
                "origen": {"type": "string", "description": "Herramienta emisora (ej. 'claude-code', 'cursor', 'git')."},
                "mensaje": {"type": "string", "description": "Descripción breve de la actividad."},
                "comando": {"type": "string", "description": "Comando opcional si requiere aprobación."},
            },
            "required": ["evento"],
        },
        handler=emitir_evento_hook_ide,
        plugin_tag="hooks",
    )
