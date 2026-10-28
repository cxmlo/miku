"""
test_spatial_memory_v2.py - Pruebas de la Memoria Espacial Inteligente V2
Fase 5 de Miku V2: Valida esquema versionado V2, migración automática sin pérdida de datos,
eliminación del borrado destructivo ante cambios de título de ventana y ahorro seguro de tokens.
"""

import pytest
import os
import sys
import json
import tempfile
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import spatial_memory
from spatial_memory import (
    _load_cache,
    _save_cache,
    _migrate_v1_to_v2,
    get_cached_coordinates,
    save_coordinates,
    normalize_intent_key,
    extract_window_pattern,
    get_memory_stats
)


# =========================================================================
# 1. NORMALIZACIÓN Y PATRONES DE VENTANA
# =========================================================================

def test_normalize_intent_key():
    assert normalize_intent_key("[ESTÁTICO] hacer clic en el botón Guardar") == "guardar"
    assert normalize_intent_key("haz clic en la barra de búsqueda de Spotify") == "búsqueda de spotify"
    assert normalize_intent_key("clic en el botón de compartir") == "compartir"
    assert normalize_intent_key("Descargas") == "descargas"


def test_extract_window_pattern():
    assert extract_window_pattern("Spotify Premium", "spotify.exe") == "spotify premium"
    assert extract_window_pattern("Anuel AA - Mejor Que Yo - Spotify", "spotify.exe") == "spotify"
    assert extract_window_pattern("Instagram • Mensajes - Opera", "opera.exe") == "opera"
    assert extract_window_pattern("Descargas - Explorador de archivos", "explorer.exe") == "explorador de archivos"


# =========================================================================
# 2. MIGRACIÓN AUTOMÁTICA DE V1 A V2
# =========================================================================

def test_auto_migration_from_v1_to_v2(tmp_path, monkeypatch):
    """Verifica que un archivo v1 plano sea migrado automáticamente a version 2 sin perder datos."""
    v1_data = {
        "[ESTÁTICO] botón Guardar": {
            "coords": [100, 200, 140, 240],
            "window_rect": [-8, -8, 1928, 1160],
            "window_title": "Documento - Bloc de notas"
        },
        "[ESTÁTICO] buscar en Spotify": {
            "coords": [50, 60, 80, 90],
            "window_rect": [10, 10, 800, 600],
            "window_title": "Spotify Premium"
        }
    }
    fake_file = str(tmp_path / "spatial_memory.json")
    with open(fake_file, "w", encoding="utf-8") as f:
        json.dump(v1_data, f)

    monkeypatch.setattr(spatial_memory, "CACHE_FILE", fake_file)

    loaded = _load_cache()
    assert loaded["version"] == 2
    assert "elements" in loaded
    assert len(loaded["elements"]) == 2
    assert "[ESTÁTICO] botón Guardar" in loaded["elements"]
    assert loaded["elements"]["[ESTÁTICO] botón Guardar"]["coords"] == [100, 200, 140, 240]

    # Verificar que se escribió la versión 2 al archivo
    with open(fake_file, "r", encoding="utf-8") as f:
        on_disk = json.load(f)
    assert on_disk["version"] == 2


# =========================================================================
# 3. ELIMINACIÓN DEL BORRADO DESTRUCTIVO
# =========================================================================

def test_cache_miss_does_not_delete_entry(tmp_path, monkeypatch):
    """
    CRÍTICO: Si la ventana activa no coincide, get_cached_coordinates debe retornar None,
    pero NUNCA borrar la entrada de la memoria espacial.
    """
    fake_file = str(tmp_path / "spatial_memory.json")
    monkeypatch.setattr(spatial_memory, "CACHE_FILE", fake_file)

    # Simular ventana y proceso para guardar
    monkeypatch.setattr(spatial_memory, "get_active_window_title", lambda: "Documento - Bloc de notas")
    monkeypatch.setattr(spatial_memory, "get_active_process_name", lambda: "notepad.exe")
    monkeypatch.setattr(spatial_memory, "get_active_window_rect", lambda: [0, 0, 1000, 800])

    save_coordinates("[ESTÁTICO] botón Guardar", [100, 200, 140, 240])

    # Ahora el usuario cambia a una ventana completamente diferente (ej. Discord)
    monkeypatch.setattr(spatial_memory, "get_active_window_title", lambda: "Discord - Canal General")
    monkeypatch.setattr(spatial_memory, "get_active_process_name", lambda: "discord.exe")

    # Debe ser un miss temporal
    hit_coords = get_cached_coordinates("[ESTÁTICO] botón Guardar")
    assert hit_coords is None

    # Comprobación de que la entrada NO fue destruida
    cache = _load_cache()
    assert "[ESTÁTICO] botón Guardar" in cache["elements"]


def test_tolerant_window_matching(tmp_path, monkeypatch):
    """Verifica que cambios ligeros en el título de la ventana (ej. cambio de canción o página) mantengan el hit."""
    fake_file = str(tmp_path / "spatial_memory.json")
    monkeypatch.setattr(spatial_memory, "CACHE_FILE", fake_file)

    # Guardado con Spotify Premium
    monkeypatch.setattr(spatial_memory, "get_active_window_title", lambda: "Spotify Premium")
    monkeypatch.setattr(spatial_memory, "get_active_process_name", lambda: "spotify.exe")
    monkeypatch.setattr(spatial_memory, "get_active_window_rect", lambda: [0, 0, 1200, 900])

    save_coordinates("[ESTÁTICO] barra de búsqueda", [50, 60, 80, 90])

    # Ahora la ventana cambió su título porque está sonando una canción pero sigue siendo Spotify
    monkeypatch.setattr(spatial_memory, "get_active_window_title", lambda: "Duki - She Don't Give a FO - Spotify")

    hit_coords = get_cached_coordinates("[ESTÁTICO] barra de búsqueda")
    assert hit_coords == [50, 60, 80, 90]


# =========================================================================
# 4. BÚSQUEDA FLEXIBLE SIN EXIGIR '[ESTÁTICO]'
# =========================================================================

def test_query_without_estatico_prefix(tmp_path, monkeypatch):
    """Permite que el LLM pregunte por 'haz clic en la barra de búsqueda' y encuentre la entrada guardada."""
    fake_file = str(tmp_path / "spatial_memory.json")
    monkeypatch.setattr(spatial_memory, "CACHE_FILE", fake_file)

    monkeypatch.setattr(spatial_memory, "get_active_window_title", lambda: "Spotify")
    monkeypatch.setattr(spatial_memory, "get_active_process_name", lambda: "spotify.exe")
    monkeypatch.setattr(spatial_memory, "get_active_window_rect", lambda: [0, 0, 1200, 900])

    save_coordinates("[ESTÁTICO] barra de búsqueda en Spotify", [50, 60, 80, 90])

    # Consulta sin '[ESTÁTICO]'
    coords = get_cached_coordinates("haz clic en la barra de búsqueda en Spotify")
    assert coords == [50, 60, 80, 90]


# =========================================================================
# 5. MÉTRICAS DE AHORRO DE TOKENS
# =========================================================================

def test_memory_stats(tmp_path, monkeypatch):
    fake_file = str(tmp_path / "spatial_memory.json")
    monkeypatch.setattr(spatial_memory, "CACHE_FILE", fake_file)

    monkeypatch.setattr(spatial_memory, "get_active_window_title", lambda: "Test")
    monkeypatch.setattr(spatial_memory, "get_active_process_name", lambda: "test.exe")
    monkeypatch.setattr(spatial_memory, "get_active_window_rect", lambda: [0, 0, 100, 100])

    save_coordinates("[ESTÁTICO] test_btn", [10, 20, 30, 40])
    get_cached_coordinates("[ESTÁTICO] test_btn")

    stats = get_memory_stats()
    assert stats["version"] == 2
    assert stats["total_elements"] == 1
    assert stats["total_hits"] >= 2
    assert stats["saved_tokens_approx"] > 0
