"""
Plugin MCP (`core/plugins/plugin_mcp.py`):
1-Click MCP Catalog & On-Demand Auto-Installer for Miku Companion.
Provides curated official MCP servers (Filesystem, GitHub, Brave Search, PostgreSQL,
Playwright, Memory, Sequential Thinking, Fetch) and installs/configures them into
`.agent/mcp_config.json` without blocking stdin.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from action_result import ActionResult, ActionStatus

MCP_CONFIG_PATH = Path(".agent/mcp_config.json")

OFFICIAL_MCP_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "filesystem",
        "name": "Filesystem MCP",
        "category": "Sistema",
        "description": "Lectura, escritura y búsqueda rápida de archivos locales con permisos acotados.",
        "command": "npx",
        "args": ["--yes", "@modelcontextprotocol/server-filesystem", "."],
        "env_keys": [],
    },
    {
        "id": "github",
        "name": "GitHub Official MCP",
        "category": "DevOps",
        "description": "Gestión de repositorios, Pull Requests, Issues, ramas y código en GitHub.",
        "command": "npx",
        "args": ["--yes", "@modelcontextprotocol/server-github"],
        "env_keys": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
    },
    {
        "id": "playwright",
        "name": "Playwright Browser MCP",
        "category": "Web & QA",
        "description": "Automatización web real, capturas DOM y pruebas E2E en Chromium headless.",
        "command": "npx",
        "args": ["--yes", "@playwright/mcp@latest", "--headless"],
        "env_keys": [],
    },
    {
        "id": "memory",
        "name": "Knowledge Graph Memory MCP",
        "category": "Memoria",
        "description": "Grafo de conocimiento persistente de entidades y relaciones del usuario.",
        "command": "npx",
        "args": ["--yes", "@modelcontextprotocol/server-memory"],
        "env_keys": [],
    },
    {
        "id": "sequential-thinking",
        "name": "Sequential Thinking MCP",
        "category": "Razonamiento",
        "description": "Descomposición estructurada y reflexiva de problemas complejos paso a paso.",
        "command": "npx",
        "args": ["--yes", "@modelcontextprotocol/server-sequential-thinking"],
        "env_keys": [],
    },
    {
        "id": "postgres",
        "name": "PostgreSQL Inspector MCP",
        "category": "Base de Datos",
        "description": "Inspección de esquemas SQL y consultas seguras sobre bases PostgreSQL.",
        "command": "npx",
        "args": ["--yes", "@modelcontextprotocol/server-postgres"],
        "env_keys": ["POSTGRES_CONNECTION_STRING"],
    },
]

ALLOWED_MCP_BINARIES = {"npx", "uvx", "node", "python", "python3"}
FORBIDDEN_SHELL_TOKENS = {"cmd.exe", "powershell", "pwsh", "bash", "sh", "/c", "-c", ";", "&&", "||", "|", "`", "$("}


def validate_mcp_manifest(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Validate an external MCP server manifest against RCE and shell injection."""
    if not isinstance(manifest, dict):
        return {"ok": False, "error": "El manifiesto MCP debe ser un diccionario JSON."}

    name = str(manifest.get("name", manifest.get("id", ""))).strip()
    command = str(manifest.get("command", "")).strip()
    args = manifest.get("args", [])

    if not name or not command:
        return {"ok": False, "error": "El manifiesto MCP requiere 'name' y 'command'."}

    if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
        return {"ok": False, "error": "'args' debe ser una lista de cadenas de texto."}

    base_cmd = os.path.basename(command).lower()
    if base_cmd.endswith(".exe"):
        base_cmd = base_cmd[:-4]

    if base_cmd not in ALLOWED_MCP_BINARIES:
        return {
            "ok": False,
            "error": f"Ejecutable no permitido '{command}'. Solo se autorizan binarios verificados: {sorted(ALLOWED_MCP_BINARIES)}",
        }

    for arg in args:
        arg_lower = arg.strip().lower()
        for token in FORBIDDEN_SHELL_TOKENS:
            if arg_lower == token or (token in {"&&", "||", ";", "`", "$("} and token in arg_lower):
                return {
                    "ok": False,
                    "error": f"Argumento bloqueado por sandboxing de seguridad: '{arg}' contiene patrón de shell no permitido.",
                }

    requires_permission_prompt = False
    permission_reasons = []
    for arg in args:
        if ".." in arg or arg.startswith("/") or (len(arg) > 2 and arg[1] == ":"):
            requires_permission_prompt = True
            permission_reasons.append(f"Acceso a ruta fuera del directorio de trabajo ({arg})")
        if "--allow-all" in arg or "--privileged" in arg or "--network=host" in arg:
            requires_permission_prompt = True
            permission_reasons.append(f"Permiso amplio de sistema/red ({arg})")

    return {
        "ok": True,
        "name": name,
        "command": base_cmd,
        "args": list(args),
        "requires_permission_prompt": requires_permission_prompt,
        "permission_reasons": permission_reasons,
    }


def load_mcp_config() -> Dict[str, Any]:
    if not MCP_CONFIG_PATH.exists():
        return {"mcpServers": {}}
    try:
        data = json.loads(MCP_CONFIG_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"mcpServers": {}}
        data.setdefault("mcpServers", {})
        return data
    except Exception:
        return {"mcpServers": {}}


def save_mcp_config(cfg: Dict[str, Any]) -> None:
    MCP_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    MCP_CONFIG_PATH.write_text(
        json.dumps(cfg, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def get_mcp_catalog_with_status() -> List[Dict[str, Any]]:
    cfg = load_mcp_config()
    installed = cfg.get("mcpServers", {})
    out = []
    for item in OFFICIAL_MCP_CATALOG:
        srv_id = item["id"]
        is_installed = srv_id in installed
        enabled = bool(installed.get(srv_id, {}).get("enabled", True)) if is_installed else False
        out.append({**item, "installed": is_installed, "enabled": enabled})
    return out


def install_mcp_from_catalog(server_id: str) -> Dict[str, Any]:
    clean_id = (server_id or "").strip().lower()
    entry = next((item for item in OFFICIAL_MCP_CATALOG if item["id"] == clean_id), None)
    if not entry:
        return {"ok": False, "error": f"Servidor MCP '{clean_id}' no existe en el catálogo oficial."}

    cfg = load_mcp_config()
    cfg.setdefault("mcpServers", {})[clean_id] = {
        "command": entry["command"],
        "args": list(entry["args"]),
        "enabled": True,
        "description": entry["description"],
    }
    save_mcp_config(cfg)
    return {"ok": True, "server_id": clean_id, "config": cfg["mcpServers"][clean_id]}


def instalar_servidor_mcp_catalogo(servidor_id: str) -> str:
    res = install_mcp_from_catalog(servidor_id)
    if res.get("ok"):
        return ActionResult(
            status=ActionStatus.CONFIRMED,
            action="instalar_servidor_mcp_catalogo",
            message=f"Servidor MCP '{servidor_id}' instalado y habilitado en `.agent/mcp_config.json` con flags `--yes` no interactivos.",
            evidence=f"mcpServers.{servidor_id}",
            data=res,
        ).to_tool_response()
    return ActionResult(
        status=ActionStatus.FAILED,
        action="instalar_servidor_mcp_catalogo",
        message=f"No se pudo instalar el servidor MCP '{servidor_id}'.",
        error=res.get("error", "ID desconocido"),
        data=res,
    ).to_tool_response()


def register(reg: Any) -> None:
    reg.register_tool(
        name="instalar_servidor_mcp_catalogo",
        description=(
            "Instala y activa en 1 clic un servidor MCP del catálogo oficial (filesystem, github, "
            "playwright, memory, sequential-thinking, postgres) garantizando ejecución no interactiva (--yes)."
        ),
        parameters={
            "type": "object",
            "properties": {
                "servidor_id": {
                    "type": "string",
                    "enum": ["filesystem", "github", "playwright", "memory", "sequential-thinking", "postgres"],
                    "description": "Identificador del servidor MCP oficial a instalar.",
                }
            },
            "required": ["servidor_id"],
        },
        handler=instalar_servidor_mcp_catalogo,
        plugin_tag="mcp",
    )
