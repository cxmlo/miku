"""
security_manager.py - Gestor Centralizado de Seguridad y Modos de Ejecución de Miku V2
Inspirado en los niveles de permisos de Antigravity:
1. FULL ('full'): Acceso total a toda la PC (consola, archivos, scripts, automatización).
2. SANDBOX ('sandbox'): Entorno aislado dentro del workspace del proyecto.
3. RESTRICTED ('restricted'): Modo seguro de solo lectura y consultas (bloquea comandos, scripts y clics).
"""

import os
import json
import logging
import tempfile
from typing import Tuple, Optional, Dict, Any
from miku_paths import get_settings_config_path, WORKSPACE_DIR, get_miku_data_dir

logger = logging.getLogger("SecurityManager")

MODE_FULL = "full"
MODE_SANDBOX = "sandbox"
MODE_RESTRICTED = "restricted"

VALID_MODES = {
    MODE_FULL: {
        "id": MODE_FULL,
        "name": "Toda mi PC (Acceso Total)",
        "desc": "Miku tiene acceso completo a la consola del sistema, todos los discos, automatización de interfaz y scripts sin restricciones de sandbox.",
        "icon": "🌐"
    },
    MODE_SANDBOX: {
        "id": MODE_SANDBOX,
        "name": "Entorno Sandbox (Espacio de Trabajo)",
        "desc": "Miku trabaja confinada de forma segura dentro del proyecto. Comandos y scripts se ejecutan estrictamente dentro del workspace.",
        "icon": "📦"
    },
    MODE_RESTRICTED: {
        "id": MODE_RESTRICTED,
        "name": "Entorno Restringido (Solo Lectura)",
        "desc": "Modo de máxima protección. Bloquea ejecución de comandos de consola, scripts arbitrarios, borrado de archivos y clics desatendidos.",
        "icon": "🔒"
    }
}

DEFAULT_MODE = MODE_FULL

_cached_mode = None
_cached_mtime = 0

def _get_config_file() -> str:
    try:
        return get_settings_config_path()
    except Exception:
        return os.path.join(WORKSPACE_DIR, "settings_config.json")

def get_execution_mode() -> str:
    """Devuelve el modo de ejecución actual ('full', 'sandbox', 'restricted')."""
    global _cached_mode, _cached_mtime
    cfg_file = _get_config_file()
    
    if os.path.exists(cfg_file):
        try:
            mtime = os.path.getmtime(cfg_file)
            if _cached_mode and mtime == _cached_mtime:
                return _cached_mode
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                mode = data.get("execution_mode", DEFAULT_MODE).lower().strip()
                if mode in VALID_MODES:
                    _cached_mode = mode
                    _cached_mtime = mtime
                    return mode
        except Exception as e:
            logger.warning(f"Error leyendo modo de ejecución de {cfg_file}: {e}")
            
    _cached_mode = DEFAULT_MODE
    return DEFAULT_MODE

def set_execution_mode(mode: str) -> bool:
    """Actualiza el modo de ejecución y lo persiste tanto en AppData como en el Workspace."""
    global _cached_mode, _cached_mtime
    mode_clean = mode.lower().strip()
    if mode_clean not in VALID_MODES:
        logger.warning(f"Modo de ejecución no reconocido: {mode}. Modos válidos: {list(VALID_MODES.keys())}")
        return False
        
    cfg_file = _get_config_file()
    cfg_data = {}
    if os.path.exists(cfg_file):
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                cfg_data = json.load(f)
        except Exception:
            cfg_data = {}
            
    cfg_data["execution_mode"] = mode_clean
    
    # 1. Guardar en archivo primario (AppData)
    try:
        os.makedirs(os.path.dirname(cfg_file), exist_ok=True)
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(cfg_data, f, indent=2, ensure_ascii=False)
        _cached_mode = mode_clean
        _cached_mtime = os.path.getmtime(cfg_file)
    except Exception as e:
        logger.error(f"Error escribiendo {cfg_file}: {e}")
        return False

    # 2. Sincronizar en workspace si existe
    ws_file = os.path.join(WORKSPACE_DIR, "settings_config.json")
    if os.path.abspath(ws_file) != os.path.abspath(cfg_file):
        try:
            with open(ws_file, "w", encoding="utf-8") as f:
                json.dump(cfg_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    logger.info(f"Modo de ejecución actualizado a: {mode_clean.upper()} ({VALID_MODES[mode_clean]['name']})")
    return True

def get_modes_info() -> Dict[str, Any]:
    """Devuelve la información de todos los modos disponibles y el actual."""
    current = get_execution_mode()
    return {
        "current_mode": current,
        "current_details": VALID_MODES[current],
        "available_modes": list(VALID_MODES.values())
    }

def is_path_allowed(path: str, write: bool = False, mode: Optional[str] = None) -> Tuple[bool, str]:
    """
    Comprueba si el acceso a la ruta está permitido según el modo de ejecución.
    Devuelve (permitido, mensaje_error).
    """
    current_mode = (mode or get_execution_mode()).lower()
    
    if not path:
        return True, ""
        
    try:
        norm_path = os.path.normcase(os.path.abspath(path))
    except Exception:
        norm_path = path.lower()

    # Protección absoluta de seguridad para archivos del núcleo de Windows
    rutas_criticas_so = [
        os.path.normcase("C:\\Windows"),
        os.path.normcase("C:\\Program Files"),
        os.path.normcase("C:\\ProgramData"),
    ]
    
    if write:
        for crit in rutas_criticas_so:
            if norm_path.startswith(crit) or "system32" in norm_path:
                return False, f"Protección de Sistema: Miku tiene prohibido modificar o borrar archivos en rutas críticas ({crit})."

    # MODO 1: FULL (Toda mi PC)
    if current_mode == MODE_FULL:
        return True, ""

    # MODO 2: RESTRICTED (Solo Lectura)
    if current_mode == MODE_RESTRICTED:
        if write:
            return False, "Modo Restringido Activo: La creación, modificación o eliminación de archivos está bloqueada en este modo. Cambia a 'Toda mi PC' o 'Sandbox' en Ajustes para continuar."
        return True, ""

    # MODO 3: SANDBOX (Espacio de Trabajo del Proyecto)
    if current_mode == MODE_SANDBOX:
        ws_norm = os.path.normcase(os.path.abspath(WORKSPACE_DIR))
        appdata_norm = os.path.normcase(os.path.abspath(get_miku_data_dir()))
        temp_norm = os.path.normcase(os.path.abspath(tempfile.gettempdir()))

        allowed_roots = [ws_norm, appdata_norm, temp_norm]
        
        # Opcionalmente permitir Desktop si está configurado
        desktop = os.path.normcase(os.path.abspath(os.path.join(os.path.expanduser("~"), "Desktop")))
        allowed_roots.append(desktop)

        is_sub = any(norm_path.startswith(root) for root in allowed_roots)
        if not is_sub:
            return False, f"Modo Sandbox Activo: Acceso bloqueado a '{path}'. En modo Sandbox Miku solo puede operar dentro de la carpeta del proyecto ({WORKSPACE_DIR})."

        return True, ""

    return True, ""

def is_command_allowed(command: str, mode: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Comprueba si un comando de consola (CMD/PowerShell) puede ejecutarse.
    Devuelve (permitido, razón, cwd_sugerido).
    """
    current_mode = (mode or get_execution_mode()).lower()
    cmd_lower = command.lower().strip()

    # MODO RESTRICTED: Totalmente bloqueado
    if current_mode == MODE_RESTRICTED:
        return (
            False,
            "Modo Restringido Activo: La ejecución de comandos en la consola de Windows está completamente bloqueada en este modo de seguridad. Cambia el modo a 'Toda mi PC' o 'Sandbox' en Ajustes.",
            None
        )

    # Filtrar comandos altamente destructivos en cualquier modo
    comandos_peligrosos = ["format ", "format.com", "del /f /s /q c:\\", "rmdir /s /q c:\\", "rd /s /q c:\\"]
    if any(p in cmd_lower for p in comandos_peligrosos):
        return (False, "Comando destructivo crítico bloqueado por el sistema de seguridad de Miku.", None)

    # MODO SANDBOX: Ejecutar siempre dentro del WORKSPACE_DIR y bloquear comandos que salgan de él
    if current_mode == MODE_SANDBOX:
        # Prevenir saltos de directorio explícitos al sistema raíz
        if "c:\\windows" in cmd_lower or "system32" in cmd_lower or "reg delete" in cmd_lower:
            return (False, "Modo Sandbox: Comando bloqueado por intentar interactuar con el sistema operativo fuera del workspace.", None)
        return (True, "Comando permitido en modo Sandbox.", WORKSPACE_DIR)

    # MODO FULL: Acceso total a la PC
    return (True, "Comando permitido en modo Toda mi PC.", None)

def is_code_execution_allowed(mode: Optional[str] = None) -> Tuple[bool, str]:
    """Comprueba si se permite ejecutar scripts Python generados por la IA."""
    current_mode = (mode or get_execution_mode()).lower()

    if current_mode == MODE_RESTRICTED:
        return (
            False,
            "Modo Restringido Activo: La ejecución de scripts Python generados está bloqueada en modo Restringido. Cambia a 'Toda mi PC' o 'Sandbox' en Ajustes."
        )

    return (True, "Ejecución de código permitida.")

def is_gui_automation_allowed(mode: Optional[str] = None) -> Tuple[bool, str]:
    """Comprueba si se permite hacer clics y escribir en ventanas activas."""
    current_mode = (mode or get_execution_mode()).lower()

    if current_mode == MODE_RESTRICTED:
        return (
            False,
            "Modo Restringido Activo: La interacción automática con el ratón o teclado está deshabilitada en modo Restringido."
        )

    return (True, "Automatización de interfaz permitida.")
