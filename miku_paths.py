"""
miku_paths.py - Gestor Centralizado de Rutas de Datos y Persistencia de Miku
Garantiza que en modo empaquetado (.exe de producción) o en desarrollo,
las API keys (.env), historiales de chat y configuraciones se guarden de forma segura
en %APPDATA%/Miku para que nunca se pierdan al actualizar o reinstalar la app.
"""

import os
import sys
import shutil
import logging

logger = logging.getLogger("MikuPaths")

if getattr(sys, "frozen", False):
    WORKSPACE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_miku_data_dir() -> str:
    """
    Devuelve la ruta del directorio base de datos persistentes del usuario.
    En Windows estándar: %APPDATA%/Miku (ej. C:/Users/<User>/AppData/Roaming/Miku).
    Si se define MIKU_DATA_DIR, se respeta dicha variable.
    """
    if "MIKU_DATA_DIR" in os.environ and os.environ["MIKU_DATA_DIR"]:
        base_dir = os.environ["MIKU_DATA_DIR"]
    else:
        appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
        base_dir = os.path.join(appdata, "Miku")

    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def _ensure_migrated(src_rel: str, dst_abs: str, is_dir: bool = False):
    """Copia un archivo o carpeta base del workspace hacia APPDATA si aún no existe."""
    src_abs = os.path.join(WORKSPACE_DIR, src_rel)
    if not os.path.exists(src_abs):
        return

    try:
        if is_dir:
            os.makedirs(dst_abs, exist_ok=True)
            for fname in os.listdir(src_abs):
                s_file = os.path.join(src_abs, fname)
                d_file = os.path.join(dst_abs, fname)
                if not os.path.exists(d_file) and os.path.isfile(s_file):
                    shutil.copy2(s_file, d_file)
                    logger.info(f"[MikuPaths] Migrado archivo de chat {fname} -> {dst_abs}")
        else:
            if not os.path.exists(dst_abs):
                parent = os.path.dirname(dst_abs)
                if parent:
                    os.makedirs(parent, exist_ok=True)
                shutil.copy2(src_abs, dst_abs)
                logger.info(f"[MikuPaths] Migrado {src_rel} -> {dst_abs}")
    except Exception as e:
        logger.warning(f"[MikuPaths] No se pudo migrar {src_rel}: {e}")


def get_env_path() -> str:
    """Devuelve la ruta absoluta al archivo .env (priorizando %APPDATA%/Miku/.env)."""
    data_dir = get_miku_data_dir()
    env_target = os.path.join(data_dir, ".env")
    _ensure_migrated(".env", env_target, is_dir=False)
    # Si aún no existe pero hay .env.example en workspace, usarlo de plantilla
    if not os.path.exists(env_target):
        _ensure_migrated(".env.example", env_target, is_dir=False)
    return env_target


def get_chat_history_dir() -> str:
    """Devuelve la ruta al directorio de historiales de chat diarios."""
    data_dir = get_miku_data_dir()
    chat_dir = os.path.join(data_dir, "chat_history")
    os.makedirs(chat_dir, exist_ok=True)
    # Migrar chats previos si no se habían migrado
    _ensure_migrated("chat_history", chat_dir, is_dir=True)
    return chat_dir


def get_daily_chat_history_file() -> str:
    """Devuelve el archivo JSON de historial de chat de hoy."""
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(get_chat_history_dir(), f"history_{today}.json")


def get_models_config_path() -> str:
    """Devuelve la ruta al archivo models_config.json."""
    data_dir = get_miku_data_dir()
    p = os.path.join(data_dir, "models_config.json")
    _ensure_migrated("models_config.json", p, is_dir=False)
    return p


def get_agents_config_path() -> str:
    """Devuelve la ruta al archivo agents_config.json."""
    data_dir = get_miku_data_dir()
    p = os.path.join(data_dir, "agents_config.json")
    _ensure_migrated("agents_config.json", p, is_dir=False)
    return p


def get_mcp_config_path() -> str:
    """Devuelve la ruta al archivo mcp_config.json."""
    data_dir = get_miku_data_dir()
    p = os.path.join(data_dir, "mcp_config.json")
    _ensure_migrated("mcp_config.json", p, is_dir=False)
    return p


def get_alerts_config_path() -> str:
    """Devuelve la ruta al archivo alerts_config.json."""
    data_dir = get_miku_data_dir()
    data_sub = os.path.join(data_dir, "data")
    os.makedirs(data_sub, exist_ok=True)
    p = os.path.join(data_sub, "alerts_config.json")
    _ensure_migrated(os.path.join("data", "alerts_config.json"), p, is_dir=False)
    return p


def get_settings_config_path() -> str:
    """Devuelve la ruta al archivo settings_config.json."""
    data_dir = get_miku_data_dir()
    p = os.path.join(data_dir, "settings_config.json")
    _ensure_migrated("settings_config.json", p, is_dir=False)
    return p


def sync_env_to_workspace(env_lines: list):
    """
    Si el archivo .env existe en el workspace (modo desarrollo),
    mantiene una copia sincronizada para comodidad del desarrollador en el editor.
    """
    ws_env = os.path.join(WORKSPACE_DIR, ".env")
    try:
        if os.path.exists(ws_env) and os.path.abspath(ws_env) != os.path.abspath(get_env_path()):
            with open(ws_env, "w", encoding="utf-8") as f:
                f.writelines(env_lines)
    except Exception as e:
        logger.debug(f"[MikuPaths] Sync a workspace .env omitido: {e}")


def ensure_all_server_folders() -> dict:
    """
    Garantiza la creación y migración automática de todas las carpetas y archivos
    esenciales del servidor en %APPDATA%/Miku al arrancar Miku Desktop.
    """
    data_dir = get_miku_data_dir()
    chat_dir = get_chat_history_dir()
    data_sub = os.path.join(data_dir, "data")
    os.makedirs(data_sub, exist_ok=True)
    sandbox_dir = os.path.join(data_dir, "workspace")
    os.makedirs(sandbox_dir, exist_ok=True)
    
    env_path = get_env_path()
    models_path = get_models_config_path()
    agents_path = get_agents_config_path()
    settings_path = get_settings_config_path()
    alerts_path = get_alerts_config_path()
    mcp_path = get_mcp_config_path()

    return {
        "data_dir": data_dir,
        "chat_dir": chat_dir,
        "sandbox_dir": sandbox_dir,
        "env_path": env_path,
        "models_path": models_path,
        "agents_path": agents_path,
        "settings_path": settings_path,
        "alerts_path": alerts_path,
        "mcp_path": mcp_path
    }

