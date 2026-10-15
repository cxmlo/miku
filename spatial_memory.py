import json
import os
import ctypes
from ctypes.wintypes import RECT

CACHE_FILE = "spatial_memory.json"

def get_active_window_rect():
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            return None
        rect = RECT()
        if ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return [rect.left, rect.top, rect.right, rect.bottom]
    except Exception as e:
        print(f"[Caché Espacial] Error obteniendo ventana activa: {e}")
    return None

def get_active_window_title():
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value
    except:
        return ""

def _load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[Caché Espacial] Error guardando caché: {e}")

def get_cached_coordinates(intent: str):
    if not intent.startswith("[ESTÁTICO]"):
        return None
        
    cache = _load_cache()
    if intent not in cache:
        return None
        
    cached_data = cache[intent]
    
    # Verificación estricta de ventana activa
    current_title = get_active_window_title()
    saved_title = cached_data.get("window_title", "")
    
    # Solo validamos si ambos títulos son válidos (para compatibilidad con caché antiguo)
    if saved_title and current_title and saved_title != current_title:
        print(f"[Caché Espacial] Ventana diferente. Activa: '{current_title}' | Esperada: '{saved_title}'. Invalidando caché para: {intent}")
        del cache[intent]
        _save_cache(cache)
        return None
    
    print(f"[Caché Espacial] ¡Hit seguro! Reutilizando coordenadas para: {intent}")
    return cached_data.get("coords")

def save_coordinates(intent: str, coords_box):
    if not intent.startswith("[ESTÁTICO]"):
        return
        
    current_rect = get_active_window_rect()
    if current_rect is None:
        return
        
    cache = _load_cache()
    # Guardamos también el título de la ventana
    window_title = get_active_window_title()
    
    cache[intent] = {
        "coords": coords_box,
        "window_rect": current_rect,
        "window_title": window_title
    }
    _save_cache(cache)
    print(f"[Caché Espacial] Coordenadas y ventana '{window_title}' guardadas para: {intent}")
    print(f"[Caché Espacial] Coordenadas guardadas para: {intent}")
