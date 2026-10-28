"""
spatial_memory.py - Memoria Espacial Inteligente V2 de Miku V2
Gestiona la persistencia de coordenadas de interfaz gráfica y selectores de UI Automation (UIA)
para evitar consultas repetitivas a modelos de visión multimodal de IA (ahorro de tokens y latencia cero).

Características V2:
- Esquema versionado (version: 2) con migración automática desde el formato v1 sin pérdida de datos.
- Búsqueda flexible de intenciones (normalización de texto sin obligatoriedad de '[ESTÁTICO]').
- Eliminación del borrado destructivo: Si una ventana cambia de título, NO borra la memoria.
- Validación por patrón de título y proceso de Windows.
- Soporte para selectores UIA (automation_id, class_name, process_name) y coordenadas relativas.
"""

import json
import os
import re
import time
import ctypes
from typing import Dict, List, Optional, Tuple, Any
from miku_paths import WORKSPACE_DIR

CACHE_FILE = os.path.join(WORKSPACE_DIR, "spatial_memory.json")


# =========================================================================
# UTILIDADES DE INSPECCIÓN DE VENTANAS ACTIVAS (WINDOWS)
# =========================================================================

def get_active_window_rect() -> Optional[List[int]]:
    """Retorna [left, top, right, bottom] de la ventana en primer plano."""
    try:
        from ctypes.wintypes import RECT
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            return None
        rect = RECT()
        if ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return [rect.left, rect.top, rect.right, rect.bottom]
    except Exception:
        pass
    return None


def get_active_window_title() -> str:
    """Retorna el título de la ventana en primer plano."""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            return ""
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value or ""
    except Exception:
        return ""


def get_active_process_name() -> str:
    """Retorna el nombre del proceso ejecutable de la ventana en primer plano si es posible."""
    try:
        import win32gui, win32process, win32api, win32con
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return ""
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid <= 0:
            return ""
        h_proc = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
        full_path = win32process.GetModuleFileNameEx(h_proc, 0)
        return os.path.basename(full_path).lower()
    except Exception:
        return ""


def extract_window_pattern(title: str, process_name: str = "") -> str:
    """Extrae un patrón simplificado o palabra clave para matching tolerante de ventana."""
    if not title:
        return process_name or ".*"
    
    # Si contiene separadores comunes como '-' o '•' (ej. 'Canción - Spotify' o 'Instagram • Mensajes - Opera')
    parts = re.split(r'[-•|—]', title)
    for p in reversed(parts):
        cleaned = p.strip().lower()
        if cleaned and len(cleaned) >= 3:
            return cleaned

    # Tomar la primera palabra representativa
    words = [w.lower() for w in re.findall(r'\w+', title) if len(w) >= 3]
    return words[-1] if words else title.lower()


# =========================================================================
# NORMALIZACIÓN DE INTENCIONES
# =========================================================================

def normalize_intent_key(intent: str) -> str:
    """
    Normaliza la intención eliminando prefijos ([ESTÁTICO], verbos de acción, artículos)
    para permitir búsquedas difusas y seguras sin importar si el LLM pone o no [ESTÁTICO].
    """
    if not intent:
        return ""
    texto = intent.replace("[ESTÁTICO]", "").replace("[ESTATICO]", "").strip().lower()
    
    # Remover verbos de acción al inicio
    verbos = [
        "hacer triple clic en", "haz triple clic en", "triple clic en",
        "hacer doble clic en", "haz doble clic en", "doble clic en",
        "hacer clic en", "haz clic en", "clic en", "click en",
        "pulsa en", "pulsa el", "pulsa", "presiona en", "presiona el", "presiona",
        "selecciona la", "selecciona el", "selecciona", "escribe en", "escribir en"
    ]
    for v in verbos:
        if texto.startswith(v):
            texto = texto[len(v):].strip()
            break

    # Remover sustantivos de interfaz comunes
    sustantivos = [
        "el botón de ", "el boton de ", "el botón ", "el boton ", "botón de ", "boton de ", "botón ", "boton ",
        "la pestaña de ", "la pestana de ", "la pestaña ", "la pestana ", "pestaña ", "pestana ",
        "el menú de ", "el menu de ", "el menú ", "el menu ", "menú ", "menu ",
        "el icono de ", "el ícono de ", "el icono ", "el ícono ", "icono de ", "ícono de ", "icono ", "ícono ",
        "el campo de ", "el campo ", "campo de ", "campo ", "la barra de ", "barra de "
    ]
    for s in sustantivos:
        if texto.startswith(s):
            texto = texto[len(s):].strip()
            break

    for art in ["el ", "la ", "los ", "las ", "un ", "una "]:
        if texto.startswith(art):
            texto = texto[len(art):].strip()
            break

    return texto.strip().strip("'\"")


# =========================================================================
# MIGRACIÓN Y CARGA DE CACHÉ
# =========================================================================

def _migrate_v1_to_v2(v1_data: Dict[str, Any]) -> Dict[str, Any]:
    """Migra el diccionario plano de versión 1 al esquema estructurado de versión 2."""
    v2_elements = {}
    now = int(time.time())

    for raw_intent, item in v1_data.items():
        if not isinstance(item, dict):
            continue
        coords = item.get("coords")
        if not coords or len(coords) != 4:
            continue

        w_title = item.get("window_title", "")
        w_rect = item.get("window_rect", [-8, -8, 1928, 1160])
        norm_key = normalize_intent_key(raw_intent)
        w_pattern = extract_window_pattern(w_title)

        v2_elements[raw_intent] = {
            "intent": raw_intent,
            "normalized_key": norm_key,
            "process_name": "",
            "window_title": w_title,
            "window_pattern": w_pattern,
            "coords": coords,
            "window_rect": w_rect,
            "automation_id": item.get("automation_id", ""),
            "class_name": item.get("class_name", ""),
            "control_type": item.get("control_type", ""),
            "hits": item.get("hits", 1),
            "created_at": item.get("created_at", now),
            "last_hit_at": item.get("last_hit_at", now)
        }

    return {
        "version": 2,
        "updated_at": now,
        "elements": v2_elements
    }


def _load_cache() -> Dict[str, Any]:
    """Carga la memoria espacial garantizando siempre el esquema versionado V2."""
    if not os.path.exists(CACHE_FILE):
        return {"version": 2, "updated_at": int(time.time()), "elements": {}}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Si es formato v1 antiguo, migrarlo inmediatamente
        if isinstance(data, dict) and "version" not in data:
            migrated = _migrate_v1_to_v2(data)
            _save_cache(migrated)
            return migrated
            
        if isinstance(data, dict) and "elements" in data:
            return data
            
        return {"version": 2, "updated_at": int(time.time()), "elements": {}}
    except Exception as e:
        print(f"[Memoria Espacial] Error cargando caché ({e}), usando estructura limpia.")
        return {"version": 2, "updated_at": int(time.time()), "elements": {}}


def _save_cache(cache: Dict[str, Any]):
    """Persiste la memoria espacial en disco de forma segura."""
    try:
        cache["version"] = 2
        cache["updated_at"] = int(time.time())
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[Memoria Espacial] Error guardando caché: {e}")


# =========================================================================
# CONSULTA Y PERSISTENCIA DE COORDENADAS
# =========================================================================

def get_cached_coordinates(intent: str) -> Optional[List[int]]:
    """
    Busca si la intención del usuario tiene coordenadas guardadas y válidas en la ventana activa.
    0 llamadas a APIs de visión, 0 tokens gastados.
    NUNCA borra la memoria si el título de ventana es distinto (previene pérdida destructiva).
    """
    if not intent:
        return None

    cache = _load_cache()
    elements = cache.get("elements", {})
    if not elements:
        return None

    norm_query = normalize_intent_key(intent)
    current_title = get_active_window_title().strip()
    current_proc = get_active_process_name().strip().lower()
    
    # 1. Búsqueda exacta por clave original o normalizada
    matched_entry = None
    if intent in elements:
        matched_entry = elements[intent]
    else:
        # Buscar por intención normalizada
        for _, entry in elements.items():
            if entry.get("normalized_key") == norm_query:
                matched_entry = entry
                break
        
        # Búsqueda por contención si la normalización exacta falló (solo si hay alta similitud)
        if not matched_entry and len(norm_query) >= 6:
            for _, entry in elements.items():
                saved_norm = entry.get("normalized_key", "")
                if saved_norm and len(saved_norm) >= 6 and (norm_query in saved_norm or saved_norm in norm_query):
                    # Evitar falsos positivos donde una frase corta coincide con otra distinta
                    ratio = min(len(norm_query), len(saved_norm)) / max(len(norm_query), len(saved_norm))
                    if ratio >= 0.65:
                        matched_entry = entry
                        break

    if not matched_entry:
        return None

    # 2. Validación de ventana activa tolerante (SIN BORRADO DESTRUCTIVO)
    saved_title = matched_entry.get("window_title", "").strip()
    saved_pattern = matched_entry.get("window_pattern", "").strip().lower()
    saved_proc = matched_entry.get("process_name", "").strip().lower()

    # Si hay títulos para comparar, verificar si hay afinidad
    if current_title and (saved_title or saved_pattern):
        c_title_low = current_title.lower()
        is_browser = any(b in c_title_low or b in current_proc for b in ("opera", "chrome", "msedge", "edge", "brave", "firefox", "vivaldi"))
        if is_browser and saved_title:
            # En navegadores web, la página/sitio cambia las coordenadas de contenido; exigir coincidencia de título o sitio
            saved_site = re.split(r'[-•|—]', saved_title.lower())[0].strip()
            curr_site = re.split(r'[-•|—]', c_title_low)[0].strip()
            title_matches = (saved_title.lower() == c_title_low) or (len(saved_site) >= 4 and saved_site == curr_site)
        else:
            title_matches = (
                (saved_title and saved_title.lower() == c_title_low) or
                (saved_pattern and saved_pattern in c_title_low) or
                (saved_proc and current_proc and saved_proc == current_proc)
            )
        
        # Si la ventana no coincide con la guardada, simplemente es un MISS temporal
        # NUNCA borramos la entrada de la memoria
        if not title_matches:
            return None

    # 3. Hit seguro: Ajustar coordenadas si la ventana se movió o cambió de tamaño, actualizar contadores y devolver
    coords = matched_entry.get("coords")
    if coords and len(coords) == 4:
        adjusted_coords = list(coords)
        saved_rect = matched_entry.get("window_rect")
        current_rect = get_active_window_rect()
        if (
            saved_rect and current_rect
            and len(saved_rect) == 4 and len(current_rect) == 4
            and saved_rect != current_rect
        ):
            sw = saved_rect[2] - saved_rect[0]
            sh = saved_rect[3] - saved_rect[1]
            cw = current_rect[2] - current_rect[0]
            ch = current_rect[3] - current_rect[1]
            if sw > 100 and sh > 100 and cw > 100 and ch > 100:
                try:
                    screen_w = ctypes.windll.user32.GetSystemMetrics(0) or 1920
                    screen_h = ctypes.windll.user32.GetSystemMetrics(1) or 1080
                    ymin, xmin, ymax, xmax = coords
                    # Convertir de escala 0-1000 global a píxeles, luego a posición relativa en saved_rect y proyectar en current_rect
                    px_x1 = (xmin / 1000.0) * screen_w
                    px_x2 = (xmax / 1000.0) * screen_w
                    px_y1 = (ymin / 1000.0) * screen_h
                    px_y2 = (ymax / 1000.0) * screen_h
                    if (saved_rect[0] - 20 <= px_x1 <= saved_rect[2] + 20) and (saved_rect[1] - 20 <= px_y1 <= saved_rect[3] + 20):
                        rel_x1 = (px_x1 - saved_rect[0]) / sw
                        rel_x2 = (px_x2 - saved_rect[0]) / sw
                        rel_y1 = (px_y1 - saved_rect[1]) / sh
                        rel_y2 = (px_y2 - saved_rect[1]) / sh
                        new_x1 = int(max(0, min(1000, ((current_rect[0] + rel_x1 * cw) / screen_w) * 1000)))
                        new_x2 = int(max(0, min(1000, ((current_rect[0] + rel_x2 * cw) / screen_w) * 1000)))
                        new_y1 = int(max(0, min(1000, ((current_rect[1] + rel_y1 * ch) / screen_h) * 1000)))
                        new_y2 = int(max(0, min(1000, ((current_rect[1] + rel_y2 * ch) / screen_h) * 1000)))
                        adjusted_coords = [new_y1, new_x1, new_y2, new_x2]
                except Exception:
                    pass

        matched_entry["hits"] = matched_entry.get("hits", 0) + 1
        matched_entry["last_hit_at"] = int(time.time())
        _save_cache(cache)
        print(f"[Memoria Espacial] ¡Hit seguro! (hits={matched_entry['hits']}) Reutilizando coordenadas para: '{intent}' (0 tokens consumidos)")
        return adjusted_coords

    return None


def save_coordinates(
    intent: str,
    coords_box: List[int],
    automation_id: str = "",
    class_name: str = "",
    control_type: str = ""
):
    """
    Guarda las coordenadas y selectores de una acción CONFIRMADA en la memoria espacial.
    """
    if not intent or not coords_box or len(coords_box) != 4:
        return

    current_rect = get_active_window_rect()
    current_title = get_active_window_title().strip()
    current_proc = get_active_process_name().strip().lower()
    window_pattern = extract_window_pattern(current_title, current_proc)

    cache = _load_cache()
    elements = cache.get("elements", {})

    # Usar la clave original o prefijada
    entry_key = intent
    norm_key = normalize_intent_key(intent)
    now = int(time.time())

    existing = elements.get(entry_key, {})
    hits = existing.get("hits", 0) + 1

    elements[entry_key] = {
        "intent": intent,
        "normalized_key": norm_key,
        "process_name": current_proc,
        "window_title": current_title,
        "window_pattern": window_pattern,
        "coords": coords_box,
        "window_rect": current_rect or [-8, -8, 1928, 1160],
        "automation_id": automation_id or existing.get("automation_id", ""),
        "class_name": class_name or existing.get("class_name", ""),
        "control_type": control_type or existing.get("control_type", ""),
        "hits": hits,
        "created_at": existing.get("created_at", now),
        "last_hit_at": now
    }

    cache["elements"] = elements
    _save_cache(cache)
    print(f"[Memoria Espacial V2] Entrada guardada para '{intent}' (patrón ventana: '{window_pattern}')")


def invalidate_cache_entry(intent: str) -> bool:
    """Elimina explícitamente una entrada de memoria espacial si se determina que ya no es válida."""
    cache = _load_cache()
    elements = cache.get("elements", {})
    if intent in elements:
        del elements[intent]
        _save_cache(cache)
        return True
    
    norm = normalize_intent_key(intent)
    for k, v in list(elements.items()):
        if v.get("normalized_key") == norm:
            del elements[k]
            _save_cache(cache)
            return True
            
    return False


def get_memory_stats() -> Dict[str, Any]:
    """Retorna métricas del uso de la memoria espacial."""
    cache = _load_cache()
    elements = cache.get("elements", {})
    total = len(elements)
    total_hits = sum(e.get("hits", 1) for e in elements.values())
    return {
        "version": cache.get("version", 2),
        "total_elements": total,
        "total_hits": total_hits,
        "saved_tokens_approx": total_hits * 1200  # Aprox 1200 tokens por consulta multimodal ahorrada
    }
