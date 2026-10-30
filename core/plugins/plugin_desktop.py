"""
Plugin Desktop (`core/plugins/plugin_desktop.py`):
Non-blocking subprocess execution (`stdin=subprocess.DEVNULL`, `CREATE_NO_WINDOW`),
automatic injection of non-interactive flags (`--yes`, `-y`), and real exit-code verification
using `ActionResult` (never masking failures).
"""

import os
import platform
import re
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

from action_result import ActionResult, ActionStatus

INTERACTIVE_CLI_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bnpx\s+(?!--yes\b|-y\b)", re.IGNORECASE), "npx --yes "),
    (re.compile(r"\bnpm\s+init\b(?!\s+-y|\s+--yes)", re.IGNORECASE), "npm init -y"),
    (re.compile(r"\bapt-get\s+install\b(?!\s+-y|\s+--yes)", re.IGNORECASE), "apt-get install -y"),
    (re.compile(r"\bwinget\s+install\b(?!.*--accept-package-agreements)", re.IGNORECASE),
     "winget install --accept-package-agreements --accept-source-agreements"),
]


def sanitize_non_interactive_command(command: str) -> str:
    """
    Ensures CLI commands run non-interactively so they never hang waiting for stdin `[y/N]`.
    """
    sanitized = (command or "").strip()
    for pattern, replacement in INTERACTIVE_CLI_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def run_non_blocking_command(
    comando: str,
    cwd: Optional[str] = None,
    timeout_segundos: float = 25.0,
) -> Dict[str, Any]:
    """
    Executes a shell command with `stdin=subprocess.DEVNULL`, `CI=true`, and `CREATE_NO_WINDOW`
    on Windows, returning real exit_code, stdout, stderr, and duration_ms.
    """
    final_cmd = sanitize_non_interactive_command(comando)
    env = os.environ.copy()
    env["CI"] = "true"
    env["DEBIAN_FRONTEND"] = "noninteractive"
    env["NPM_CONFIG_YES"] = "true"
    env["PYTHONIOENCODING"] = "utf-8"

    creationflags = 0
    if platform.system().lower() == "windows":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            final_cmd,
            shell=True,
            cwd=cwd or None,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max(1.0, min(float(timeout_segundos), 120.0)),
            creationflags=creationflags,
        )
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return {
            "ok": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": (proc.stdout or "").strip(),
            "stderr": (proc.stderr or "").strip(),
            "command": final_cmd,
            "duration_ms": elapsed_ms,
        }
    except subprocess.TimeoutExpired as exc:
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return {
            "ok": False,
            "exit_code": -1,
            "stdout": (exc.stdout or "") if isinstance(exc.stdout, str) else "",
            "stderr": f"TimeoutExpired after {timeout_segundos}s",
            "command": final_cmd,
            "duration_ms": elapsed_ms,
        }
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return {
            "ok": False,
            "exit_code": -2,
            "stdout": "",
            "stderr": str(exc),
            "command": final_cmd,
            "duration_ms": elapsed_ms,
        }


def ejecutar_comando_no_bloqueante(
    comando: str,
    directorio: str = "",
    timeout_segundos: float = 25.0,
) -> str:
    """
    Tool handler for non-blocking shell execution with verified exit code reporting.
    """
    res = run_non_blocking_command(
        comando=comando,
        cwd=directorio.strip() or None,
        timeout_segundos=timeout_segundos,
    )
    if res["ok"]:
        output_preview = res["stdout"][:2000] if res["stdout"] else "(Sin salida en stdout, código 0)"
        return ActionResult(
            status=ActionStatus.CONFIRMED,
            action="ejecutar_comando_no_bloqueante",
            message=f"Comando ejecutado con éxito (exit_code=0 en {res['duration_ms']}ms).\n{output_preview}",
            evidence=f"exit_code=0 cmd={res['command']}",
            data=res,
        ).to_tool_response()

    from .plugin_ui import mostrar_error_interactivo

    err_detail = res["stderr"] or res["stdout"] or f"Fallo con código de salida {res['exit_code']}"
    mostrar_error_interactivo(
        titulo=f"Error ejecutando comando (exit {res['exit_code']})",
        detalle_error=err_detail[:600],
        codigo_salida=res["exit_code"],
        comando_reintento=res["command"],
    )
    return ActionResult(
        status=ActionStatus.FAILED,
        action="ejecutar_comando_no_bloqueante",
        message=f"El comando falló con código de salida {res['exit_code']}.",
        error=err_detail[:1000],
        evidence=f"exit_code={res['exit_code']} cmd={res['command']}",
        data=res,
    ).to_tool_response()


def register(reg: Any) -> None:
    reg.register_tool(
        name="ejecutar_comando_no_bloqueante",
        description=(
            "Ejecuta un comando de terminal en modo no interactivo garantizado (stdin cerrado, flags --yes "
            "automáticos y verificación estricta de código de salida 0). Si falla, muestra ErrorCard en la Isla."
        ),
        parameters={
            "type": "object",
            "properties": {
                "comando": {"type": "string", "description": "Comando de consola a ejecutar."},
                "directorio": {"type": "string", "description": "Directorio de trabajo opcional."},
                "timeout_segundos": {
                    "type": "number",
                    "description": "Tiempo máximo de espera en segundos (por defecto 25).",
                },
            },
            "required": ["comando"],
        },
        handler=ejecutar_comando_no_bloqueante,
        plugin_tag="desktop",
    )
