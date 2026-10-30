"""
Plugin UI (`core/plugins/plugin_ui.py`):
Miku interactive Dynamic Island cards while keeping 2D Canvas Miku (`#mk`) intact:
- `solicitar_aprobacion_comando` (ApprovalCard with [Y] Permitir, [N] Denegar, [A] Siempre)
- `preguntar_opciones_usuario` (QuestionCard with interactive clickable options so Miku never says she lacks an option tool)
- `mostrar_error_interactivo` (ErrorCard with real exit_code/stderr and Miku native `error` state)
- `emitir_pensamiento_vivo` (ThoughtStream single-line step + optional syntax diff preview)
"""

import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from action_result import ActionResult, ActionStatus

# Shared in-memory state for interactive UI cards resolved via WebSocket / REST `/api/ui/choice`
_PENDING_DECISIONS: Dict[str, Dict[str, Any]] = {}
_ALWAYS_ALLOWED_COMMANDS: set[str] = set()
_UI_LOCK = threading.RLock()
_BROADCAST_CALLBACK: Optional[Callable[[Dict[str, Any]], None]] = None


def set_ui_broadcaster(callback: Callable[[Dict[str, Any]], None]) -> None:
    """Registers a callback that broadcasts JSON payloads to the Dynamic Island WebSocket."""
    global _BROADCAST_CALLBACK
    _BROADCAST_CALLBACK = callback


def _emit_to_island(payload: Dict[str, Any]) -> bool:
    if _BROADCAST_CALLBACK is not None:
        try:
            _BROADCAST_CALLBACK(payload)
            return True
        except Exception:
            pass
    return False


def resolve_ui_decision(card_id: str, decision: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Called by `/api/ui/choice` or WebSocket handler when the user clicks an option
    or presses [Y]/[N]/[A] on the Dynamic Island.
    """
    with _UI_LOCK:
        entry = _PENDING_DECISIONS.get(card_id)
        if not entry:
            # Create resolved record even if arrived asynchronously
            _PENDING_DECISIONS[card_id] = {
                "id": card_id,
                "status": "resolved",
                "decision": decision,
                "extra": extra or {},
                "resolved_at": time.time(),
            }
            return _PENDING_DECISIONS[card_id]

        entry["status"] = "resolved"
        entry["decision"] = decision
        entry["extra"] = extra or {}
        entry["resolved_at"] = time.time()
        cmd_sig = entry.get("command_signature")
        if decision in ("always", "A", "allow_always") and cmd_sig:
            _ALWAYS_ALLOWED_COMMANDS.add(cmd_sig)
        evt = entry.get("event")
        if isinstance(evt, threading.Event):
            evt.set()
        return {
            "id": card_id,
            "status": "resolved",
            "decision": decision,
            "extra": entry["extra"],
        }


def get_pending_decisions() -> List[Dict[str, Any]]:
    with _UI_LOCK:
        out = []
        for k, v in _PENDING_DECISIONS.items():
            if v.get("status") == "pending":
                out.append({key: val for key, val in v.items() if key != "event"})
        return out


def solicitar_aprobacion_comando(
    comando: str,
    titulo: str = "¿Ejecutar comando del sistema?",
    riesgo: str = "medio",
    diff_preview: str = "",
    timeout_segundos: float = 0.0,
) -> str:
    """
    Displays the Miku ApprovalCard in the Dynamic Island with Miku in `thinking` state
    and shortcuts [Y] Permitir, [N] Denegar, [A] Siempre.
    """
    cmd_sig = (comando or "").strip()
    if cmd_sig in _ALWAYS_ALLOWED_COMMANDS:
        return ActionResult(
            status=ActionStatus.CONFIRMED,
            action="solicitar_aprobacion_comando",
            message=f"Comando pre-autorizado por regla 'Siempre' ([A]): `{cmd_sig}`",
            evidence="Regla en _ALWAYS_ALLOWED_COMMANDS",
            data={"decision": "always", "command": cmd_sig},
        ).to_tool_response()

    card_id = f"approve_{uuid.uuid4().hex[:8]}"
    evt = threading.Event()
    record = {
        "id": card_id,
        "type": "approve",
        "title": titulo,
        "command": cmd_sig,
        "command_signature": cmd_sig,
        "risk": riesgo,
        "diff": diff_preview,
        "status": "pending",
        "decision": None,
        "created_at": time.time(),
        "event": evt,
    }
    with _UI_LOCK:
        _PENDING_DECISIONS[card_id] = record

    _emit_to_island(
        {
            "type": "scene",
            "name": "approve",
            "data": {
                "id": card_id,
                "title": titulo,
                "cmd": cmd_sig,
                "risk": riesgo,
                "diff": diff_preview,
                "shortcuts": [
                    {"key": "Y", "label": "Permitir", "value": "allow"},
                    {"key": "N", "label": "Denegar", "value": "deny"},
                    {"key": "A", "label": "Siempre", "value": "always"},
                ],
            },
        }
    )

    if timeout_segundos and timeout_segundos > 0:
        evt.wait(timeout=min(float(timeout_segundos), 60.0))
        with _UI_LOCK:
            decision = _PENDING_DECISIONS.get(card_id, {}).get("decision")
        if decision:
            return ActionResult(
                status=ActionStatus.CONFIRMED,
                action="solicitar_aprobacion_comando",
                message=f"Decisión del usuario recibida: {decision}",
                evidence=f"card_id={card_id} decision={decision}",
                data={"card_id": card_id, "decision": decision, "command": cmd_sig},
            ).to_tool_response()

    return ActionResult(
        status=ActionStatus.EXECUTED_UNVERIFIED,
        action="solicitar_aprobacion_comando",
        message=(
            f"Tarjeta de aprobación `{card_id}` mostrada en la Isla Dinámica para `{cmd_sig}`. "
            "Esperando confirmación del usuario ([Y] Permitir / [N] Denegar / [A] Siempre)."
        ),
        evidence=f"scene=approve id={card_id}",
        data={"card_id": card_id, "command": cmd_sig, "status": "pending"},
    ).to_tool_response()


def preguntar_opciones_usuario(
    pregunta: str,
    opciones: List[str],
    contexto: str = "",
) -> str:
    """
    Displays a native multi-choice QuestionCard in the Dynamic Island so the user can click
    one of the options directly (or press 1..9). Prevents Miku from ever saying she lacks a
    multi-option question tool.
    """
    clean_options = [str(opt).strip() for opt in (opciones or []) if str(opt).strip()]
    if not clean_options:
        clean_options = ["Sí, continuar", "No, cancelar"]

    card_id = f"question_{uuid.uuid4().hex[:8]}"
    evt = threading.Event()
    with _UI_LOCK:
        _PENDING_DECISIONS[card_id] = {
            "id": card_id,
            "type": "question",
            "question": pregunta,
            "context": contexto,
            "options": clean_options,
            "status": "pending",
            "decision": None,
            "created_at": time.time(),
            "event": evt,
        }

    _emit_to_island(
        {
            "type": "scene",
            "name": "question",
            "data": {
                "id": card_id,
                "title": pregunta,
                "sub": contexto,
                "options": clean_options,
            },
        }
    )

    return ActionResult(
        status=ActionStatus.CONFIRMED,
        action="preguntar_opciones_usuario",
        message=(
            f"Tarjeta interactiva de opciones (`{card_id}`) desplegada en la Isla Dinámica: "
            f"'{pregunta}' con opciones: {', '.join(clean_options)}"
        ),
        evidence=f"scene=question id={card_id}",
        data={"card_id": card_id, "question": pregunta, "options": clean_options},
    ).to_tool_response()


def mostrar_error_interactivo(
    titulo: str,
    detalle_error: str,
    codigo_salida: int = 1,
    comando_reintento: str = "",
) -> str:
    """
    Displays an interactive ErrorCard on the Dynamic Island with Miku in native `error` state
    on the 2D Canvas (`#mk`), showing the real exit code and stderr with [Reintentar] / [Ver detalles].
    """
    card_id = f"err_{uuid.uuid4().hex[:8]}"
    _emit_to_island(
        {
            "type": "scene",
            "name": "error_card",
            "data": {
                "id": card_id,
                "title": titulo,
                "stderr": detalle_error,
                "exit_code": codigo_salida,
                "retry_cmd": comando_reintento,
            },
        }
    )
    return ActionResult(
        status=ActionStatus.CONFIRMED,
        action="mostrar_error_interactivo",
        message=f"ErrorCard `{card_id}` mostrada en la Isla Dinámica (exit_code={codigo_salida}): {titulo}",
        evidence=f"scene=error_card id={card_id}",
        data={"card_id": card_id, "exit_code": codigo_salida, "stderr": detalle_error},
    ).to_tool_response()


def emitir_pensamiento_vivo(
    paso: str,
    estado_miku: str = "working",
    diff_codigo: str = "",
    archivo: str = "",
) -> str:
    """
    Pushes a live ThoughtStream single-line update and optional syntax diff preview (`-` red / `+` green)
    to the Dynamic Island while updating Miku's 2D Canvas state (`thinking`, `searching`, `working`).
    """
    _emit_to_island(
        {
            "type": "thought_stream",
            "step": paso,
            "state": estado_miku,
            "diff": diff_codigo,
            "file": archivo,
            "ts": int(time.time() * 1000),
        }
    )
    return ActionResult(
        status=ActionStatus.CONFIRMED,
        action="emitir_pensamiento_vivo",
        message=f"ThoughtStream actualizado: {paso}",
        evidence=f"state={estado_miku} file={archivo or 'none'}",
        data={"step": paso, "state": estado_miku, "file": archivo, "has_diff": bool(diff_codigo)},
    ).to_tool_response()


def register(reg: Any) -> None:
    reg.register_tool(
        name="solicitar_aprobacion_comando",
        description=(
            "Muestra una tarjeta interactiva ApprovalCard en la Isla Dinámica con atajos "
            "[Y] Permitir, [N] Denegar y [A] Siempre antes de ejecutar un comando delicado o destructivo."
        ),
        parameters={
            "type": "object",
            "properties": {
                "comando": {"type": "string", "description": "El comando o acción exacta a autorizar."},
                "titulo": {"type": "string", "description": "Título breve de la solicitud."},
                "riesgo": {
                    "type": "string",
                    "enum": ["bajo", "medio", "alto"],
                    "description": "Nivel de riesgo estimado.",
                },
                "diff_preview": {
                    "type": "string",
                    "description": "Vista previa opcional en formato diff (-/+ líneas) si modifica un archivo.",
                },
            },
            "required": ["comando"],
        },
        handler=solicitar_aprobacion_comando,
        plugin_tag="ui",
    )

    reg.register_tool(
        name="preguntar_opciones_usuario",
        description=(
            "Muestra una tarjeta interactiva QuestionCard en la Isla Dinámica con botones de opción múltiple "
            "para que el usuario elija con un clic o teclado. Úsala SIEMPRE que necesites ofrecer opciones o "
            "confirmar preferencias del usuario."
        ),
        parameters={
            "type": "object",
            "properties": {
                "pregunta": {"type": "string", "description": "Pregunta clara y concisa para el usuario."},
                "opciones": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de 2 a 5 opciones seleccionables.",
                },
                "contexto": {"type": "string", "description": "Subtítulo o contexto adicional opcional."},
            },
            "required": ["pregunta", "opciones"],
        },
        handler=preguntar_opciones_usuario,
        plugin_tag="ui",
    )

    reg.register_tool(
        name="mostrar_error_interactivo",
        description=(
            "Muestra una tarjeta ErrorCard en la Isla Dinámica con Miku en estado 'error', código de salida real, "
            "detalle técnico (stderr) y botón de reintento."
        ),
        parameters={
            "type": "object",
            "properties": {
                "titulo": {"type": "string", "description": "Resumen corto del fallo."},
                "detalle_error": {"type": "string", "description": "Mensaje de error real o stderr."},
                "codigo_salida": {"type": "integer", "description": "Código de salida del proceso (ej. 1)."},
                "comando_reintento": {"type": "string", "description": "Comando opcional para reintentar."},
            },
            "required": ["titulo", "detalle_error"],
        },
        handler=mostrar_error_interactivo,
        plugin_tag="ui",
    )

    reg.register_tool(
        name="emitir_pensamiento_vivo",
        description=(
            "Actualiza el ThoughtStream en vivo de la Isla Dinámica con el paso actual del agente y "
            "opcionalmente muestra un bloque diff coloreado (- rojo / + verde) de cambios de código."
        ),
        parameters={
            "type": "object",
            "properties": {
                "paso": {"type": "string", "description": "Descripción de una línea de lo que estás haciendo."},
                "estado_miku": {
                    "type": "string",
                    "enum": ["thinking", "searching", "working", "talking", "idle", "error"],
                    "description": "Estado visual de Miku en el Canvas 2D.",
                },
                "diff_codigo": {
                    "type": "string",
                    "description": "Opcional. Líneas diff unificadas (-/+ ) para previsualizar en la isla.",
                },
                "archivo": {"type": "string", "description": "Opcional. Nombre del archivo afectado."},
            },
            "required": ["paso"],
        },
        handler=emitir_pensamiento_vivo,
        plugin_tag="ui",
    )
