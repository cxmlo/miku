import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import music_controller

def test_music_controller_info_structure():
    """Verifica que el controlador multimedia devuelva una estructura válida sin lanzar excepciones"""
    info = music_controller.get_current_playback_info()
    assert isinstance(info, dict)
    assert "title" in info
    assert "artist" in info
    assert "playing" in info
    assert "position_sec" in info
    assert "duration_sec" in info
    assert "thumbnail_b64" in info
    assert isinstance(info["playing"], bool)
    assert isinstance(info["position_sec"], (int, float))
    assert isinstance(info["duration_sec"], (int, float))

def test_music_controller_fallback_safety():
    """Verifica que si no hay música activa, los campos devuelvan valores seguros y legibles"""
    info = music_controller.get_current_playback_info()
    if not info["playing"]:
        assert info["position_sec"] >= 0
        assert info["duration_sec"] >= 0
