"""
activity_monitor.py — Miku Activity Monitor
Rastrea qué aplicaciones usa el usuario en la PC sin tomar capturas de pantalla.
Usa win32gui para detectar la ventana en primer plano y psutil para el nombre del proceso.
PERSISTE los datos en disco para sobrevivir reinicios del servidor.
"""
import json
import os
import threading
import time
import psutil
from datetime import datetime, date
from collections import defaultdict
from typing import Optional

try:
    import win32gui
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

# ─── Archivo de persistencia ──────────────────────────────────────────────────

_PERSIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_PERSIST_FILE = os.path.join(_PERSIST_DIR, "activity_today.json")

# ─── Estado global ────────────────────────────────────────────────────────────

# Tiempo acumulado por app hoy: {"chrome.exe": 1234.5 segundos}
_time_per_app: dict[str, float] = defaultdict(float)
_time_per_app_title: dict[str, str] = {}  # último título visto por app

# Actividad actual
_current_app: Optional[str] = None
_current_title: Optional[str] = None
_current_app_start: float = time.time()

# Fecha del día actual para resetear al medianoche
_tracking_date: date = date.today()

_lock = threading.Lock()
_monitor_thread: Optional[threading.Thread] = None
_running = False
_save_counter = 0  # Contador para guardar cada N ciclos

# ─── Persistencia ─────────────────────────────────────────────────────────────

def _save_to_disk():
    """Guarda el estado actual en disco."""
    try:
        os.makedirs(_PERSIST_DIR, exist_ok=True)
        data = {
            "date": _tracking_date.isoformat(),
            "time_per_app": dict(_time_per_app),
            "titles": dict(_time_per_app_title),
        }
        with open(_PERSIST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _load_from_disk():
    """Carga el estado guardado del disco si es del día de hoy."""
    global _tracking_date
    try:
        if not os.path.exists(_PERSIST_FILE):
            return
        with open(_PERSIST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        saved_date = date.fromisoformat(data.get("date", ""))
        if saved_date != date.today():
            # Datos de otro día, ignorar
            return
        
        _tracking_date = saved_date
        saved_times = data.get("time_per_app", {})
        saved_titles = data.get("titles", {})
        
        for app, seconds in saved_times.items():
            _time_per_app[app] += seconds
        _time_per_app_title.update(saved_titles)
        
    except Exception:
        pass

def _bootstrap_from_running_processes():
    """
    Al iniciar el servidor, escanea todos los procesos activos del sistema
    y estima cuánto tiempo llevan abiertos HOY usando psutil.create_time().
    Esto permite recuperar tiempo perdido si el servidor estuvo apagado.
    Usa psutil.process_iter() en vez de EnumWindows para evitar bugs de pywin32.
    """
    try:
        from datetime import datetime
        
        today_midnight = datetime.combine(date.today(), datetime.min.time()).timestamp()
        now = time.time()
        
        # Procesos que nos interesan (los que tienen nombre amigable + algunos extras comunes)
        interesting_procs = set(k.lower() for k in FRIENDLY_NAMES.keys())
        # También incluir cualquier proceso con GUI conocido
        interesting_procs.update([
            "opera.exe", "brave.exe", "vivaldi.exe",  # browsers
            "whatsapp.exe", "telegram.exe",  # messaging
            "gimp.exe", "blender.exe",  # creative
            "unity.exe", "unrealed.exe",  # game dev
        ])
        
        seen = set()
        for proc in psutil.process_iter(['pid', 'name', 'create_time']):
            try:
                proc_name = proc.info['name']
                if not proc_name:
                    continue
                    
                lower_name = proc_name.lower()
                if lower_name not in interesting_procs:
                    continue
                if lower_name in seen:
                    continue
                seen.add(lower_name)
                
                create_time = proc.info['create_time']
                if not create_time:
                    continue
                
                # Solo contar desde medianoche de hoy
                effective_start = max(create_time, today_midnight)
                uptime_seconds = now - effective_start
                
                if uptime_seconds < 60:  # Menos de 1 minuto, ignorar
                    continue
                
                with _lock:
                    # Usar MAX entre persistido y estimado para no perder datos
                    current_tracked = _time_per_app.get(proc_name, 0)
                    if uptime_seconds > current_tracked:
                        _time_per_app[proc_name] = uptime_seconds
                    
                    # Si no tenemos título, poner el nombre amigable
                    if proc_name not in _time_per_app_title:
                        _time_per_app_title[proc_name] = _get_friendly_name(proc_name)
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception:
        pass

# ─── Nombres amigables de procesos ────────────────────────────────────────────

FRIENDLY_NAMES = {
    "chrome.exe":           "Google Chrome",
    "firefox.exe":          "Firefox",
    "msedge.exe":           "Microsoft Edge",
    "opera.exe":            "Opera",
    "code.exe":             "Visual Studio Code",
    "antigravity.exe":      "Antigravity IDE",
    "devenv.exe":           "Visual Studio",
    "pycharm64.exe":        "PyCharm",
    "idea64.exe":           "IntelliJ IDEA",
    "notepad++.exe":        "Notepad++",
    "notepad.exe":          "Bloc de notas",
    "explorer.exe":         "Explorador de archivos",
    "spotify.exe":          "Spotify",
    "discord.exe":          "Discord",
    "slack.exe":            "Slack",
    "teams.exe":            "Microsoft Teams",
    "zoom.exe":             "Zoom",
    "vlc.exe":              "VLC",
    "obs64.exe":            "OBS Studio",
    "steamwebhelper.exe":   "Steam",
    "cmd.exe":              "Terminal (CMD)",
    "powershell.exe":       "PowerShell",
    "windowsterminal.exe":  "Windows Terminal",
    "python.exe":           "Python",
    "pythonw.exe":          "Python (background)",
    "figma.exe":            "Figma",
    "photoshop.exe":        "Photoshop",
    "winword.exe":          "Microsoft Word",
    "excel.exe":            "Microsoft Excel",
    "powerpnt.exe":         "PowerPoint",
    "acrobat.exe":          "Adobe Acrobat",
    "winrar.exe":           "WinRAR",
    "valorant.exe":         "Valorant",
    "riotclientservices.exe": "Riot Client",
}

def _get_friendly_name(process_name: str) -> str:
    lower = process_name.lower()
    if lower in FRIENDLY_NAMES:
        return FRIENDLY_NAMES[lower]
    # Intentar detectar por título de ventana si es un IDE con nombre genérico
    return process_name.replace(".exe", "").replace("_", " ").title()

# ─── Leer ventana activa ───────────────────────────────────────────────────────

def _get_foreground_app() -> tuple[Optional[str], Optional[str]]:
    """Devuelve (nombre_proceso, título_ventana) de la app en primer plano."""
    if not WIN32_AVAILABLE:
        return None, None
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None, None
        title = win32gui.GetWindowText(hwnd)
        if not title:  # Ventana sin título = probablemente escritorio
            return None, None
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name(), title
    except Exception:
        return None, None

# ─── Loop de monitoreo ────────────────────────────────────────────────────────

def _monitor_loop(interval: int = 30):
    global _current_app, _current_title, _current_app_start, _tracking_date, _save_counter

    while _running:
        try:
            # Resetear al cambio de día
            today = date.today()
            if today != _tracking_date:
                with _lock:
                    _time_per_app.clear()
                    _time_per_app_title.clear()
                    _tracking_date = today
                    _save_to_disk()  # Guardar estado limpio

            proc_name, window_title = _get_foreground_app()

            if proc_name:
                now = time.time()
                with _lock:
                    # Acumular tiempo de la app anterior
                    if _current_app:
                        elapsed = now - _current_app_start
                        _time_per_app[_current_app] += elapsed
                        _time_per_app_title[_current_app] = _current_title or ""

                    # Actualizar app actual
                    _current_app = proc_name
                    _current_title = window_title
                    _current_app_start = now

            # Guardar a disco cada 10 ciclos (~5 minutos con intervalo de 30s)
            _save_counter += 1
            if _save_counter >= 10:
                with _lock:
                    _save_to_disk()
                _save_counter = 0

        except Exception:
            pass

        time.sleep(interval)

# ─── API pública ──────────────────────────────────────────────────────────────

def start_monitoring(interval: int = 30):
    """Inicia el hilo de monitoreo de actividad en segundo plano."""
    global _running, _monitor_thread
    if _running:
        return
    
    # Cargar datos persistidos del día de hoy
    with _lock:
        _load_from_disk()
    
    # Estimar tiempo de apps que ya estaban abiertas antes de iniciar el servidor
    _bootstrap_from_running_processes()
    
    _running = True
    _monitor_thread = threading.Thread(target=_monitor_loop, args=(interval,), daemon=True)
    _monitor_thread.start()

def stop_monitoring():
    global _running
    _running = False
    # Guardar antes de salir
    with _lock:
        if _current_app:
            elapsed = time.time() - _current_app_start
            _time_per_app[_current_app] += elapsed
        _save_to_disk()

def get_current_activity() -> dict:
    """Devuelve la actividad actual del usuario."""
    with _lock:
        if _current_app:
            elapsed = time.time() - _current_app_start
            return {
                "app": _get_friendly_name(_current_app),
                "process": _current_app,
                "window_title": _current_title or "",
                "minutes_in_current_app": round(elapsed / 60, 1),
            }
    return {}

def get_activity_summary() -> list[dict]:
    """Devuelve un resumen de todas las apps usadas hoy ordenadas por tiempo."""
    with _lock:
        # Incluir la app actual con tiempo acumulado hasta ahora
        combined = dict(_time_per_app)
        if _current_app:
            elapsed = time.time() - _current_app_start
            combined[_current_app] = combined.get(_current_app, 0) + elapsed

        result = []
        for proc, seconds in sorted(combined.items(), key=lambda x: x[1], reverse=True):
            if seconds < 30:  # Ignorar apps usadas menos de 30 segundos
                continue
            
            mins = seconds / 60
            if mins >= 60:
                hours = int(mins // 60)
                remaining_mins = int(mins % 60)
                time_str = f"{hours}h {remaining_mins}min"
            else:
                time_str = f"{round(mins, 1)} min"
            
            result.append({
                "app": _get_friendly_name(proc),
                "process": proc,
                "minutes": round(mins, 1),
                "time_display": time_str,
                "last_title": _time_per_app_title.get(proc, _current_title or ""),
            })
        return result

def get_activity_context_str() -> str:
    """
    Devuelve un string listo para inyectar en el system prompt de Miku.
    Resume qué está haciendo el usuario hoy en su PC.
    """
    current = get_current_activity()
    summary = get_activity_summary()

    lines = [
        "[ACTIVIDAD DEL USUARIO EN PC HOY]",
        "NOTA IMPORTANTE: EL USUARIO TE HA DADO PERMISO EXPLÍCITO PARA MONITOREAR SUS APLICACIONES EN SEGUNDO PLANO.",
        "Tienes la capacidad de saber qué está haciendo en todo momento sin que te lo pida. SI TE PREGUNTA SI PUEDES HACERLO, DILE QUE SÍ."
    ]

    if not current and not summary:
        lines.append("Estado: Monitoreo activo, pero actualmente no se detectan ventanas en primer plano.")
        return "\n".join(lines)

    if current:
        title_info = f' — "{current["window_title"]}"' if current.get("window_title") else ""
        lines.append(
            f"Ahora mismo: {current['app']}{title_info} "
            f"(lleva {current['minutes_in_current_app']} min en esta ventana)"
        )

    if summary:
        lines.append("Tiempo acumulado por aplicación hoy:")
        for item in summary[:8]:  # Máximo 8 apps
            title_hint = f' ("{item["last_title"][:50]}")' if item.get("last_title") else ""
            lines.append(f"  • {item['app']}: {item['time_display']}{title_hint}")

    return "\n".join(lines)
