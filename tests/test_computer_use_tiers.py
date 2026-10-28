"""
test_computer_use_tiers.py - Pruebas del subsistema Computer Use por niveles
Fase 4 de Miku V2: Comprueba Nivel 1 (UI Automation de Windows, 0 tokens), Nivel 2 (Memoria Espacial),
y Nivel 3 (Visión multimodal API como fallback), además de limpieza de intenciones y acciones sensibles.
"""

import pytest
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import computer_use
from computer_use import (
    limpiar_intencion,
    buscar_control_uia,
    hacer_clic_visual,
    interactuar_elemento
)
from action_result import ActionStatus


# =========================================================================
# 1. LIMPIEZA DE INTENCIONES PARA BÚSQUEDA ACCESIBLE
# =========================================================================

def test_limpiar_intencion():
    assert limpiar_intencion("haz clic en el botón Guardar") == "guardar"
    assert limpiar_intencion("hacer clic en la pestaña Configuración") == "configuración"
    assert limpiar_intencion("doble clic en el icono Chrome") == "chrome"
    assert limpiar_intencion("pulsa el botón Aceptar") == "aceptar"
    assert limpiar_intencion("selecciona la pestaña General") == "general"
    assert limpiar_intencion("Cerrar") == "cerrar"
    assert limpiar_intencion("") == ""


# =========================================================================
# 2. BÚSQUEDA DE CONTROLES POR UI AUTOMATION (NIVEL 1)
# =========================================================================

class MockRect:
    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
    def width(self):
        return self.right - self.left
    def height(self):
        return self.bottom - self.top


class MockControl:
    def __init__(self, name, c_type, automation_id="", width=100, height=40, left=50, top=50):
        self.Name = name
        self.ControlType = c_type
        self.ControlTypeName = getattr(c_type, "name", "Control")
        self.AutomationId = automation_id
        self.BoundingRectangle = MockRect(left, top, left + width, top + height) if width > 0 else None


def test_buscar_control_uia_exact_match(monkeypatch):
    """Verifica coincidencia exacta por nombre en controles de primer plano."""
    import uiautomation as auto

    btn_guardar = MockControl("Guardar", auto.ControlType.ButtonControl, automation_id="btnSave", left=100, top=200)
    mock_window = MockControl("Bloc de notas", auto.ControlType.WindowControl)

    def mock_walk(win, maxDepth=4):
        return [(btn_guardar, 1)]

    monkeypatch.setattr(auto, "GetForegroundControl", lambda: mock_window)
    monkeypatch.setattr(auto, "WalkControl", mock_walk)

    res = buscar_control_uia("haz clic en el botón Guardar")
    assert res is not None
    assert res["name"] == "Guardar"
    assert res["automation_id"] == "btnSave"
    assert res["center"] == (150, 220)  # 100 + 100//2, 200 + 40//2
    assert res["exact"] is True


def test_buscar_control_uia_partial_match(monkeypatch):
    """Verifica coincidencia parcial cuando el nombre contiene el término."""
    import uiautomation as auto

    tab_code = MockControl("Pestaña Código Fuente (Activa)", auto.ControlType.TabItemControl, left=10, top=10)
    mock_window = MockControl("IDE", auto.ControlType.WindowControl)

    monkeypatch.setattr(auto, "GetForegroundControl", lambda: mock_window)
    monkeypatch.setattr(auto, "WalkControl", lambda win, maxDepth=4: [(tab_code, 1)])

    res = buscar_control_uia("código fuente")
    assert res is not None
    assert "Código Fuente" in res["name"]
    assert res["exact"] is False


def test_buscar_control_uia_ignores_zero_size(monkeypatch):
    """Verifica que ignore controles invisibles con ancho o alto cero."""
    import uiautomation as auto

    hidden_btn = MockControl("Guardar", auto.ControlType.ButtonControl, width=0, height=0)
    mock_window = MockControl("App", auto.ControlType.WindowControl)

    monkeypatch.setattr(auto, "GetForegroundControl", lambda: mock_window)
    monkeypatch.setattr(auto, "WalkControl", lambda win, maxDepth=4: [(hidden_btn, 1)])

    res = buscar_control_uia("Guardar")
    assert res is None


# =========================================================================
# 3. EJECUCIÓN POR NIVELES (TIER 1 -> TIER 2 -> TIER 3)
# =========================================================================

def test_hacer_clic_visual_resolves_tier_1_zero_tokens(monkeypatch):
    """Nivel 1: Si UIA encuentra el control, se ejecuta inmediatamente sin llamar al modelo multimodal de visión."""
    import security_manager
    import pyautogui

    monkeypatch.setattr(security_manager, "is_gui_automation_allowed", lambda: (True, "OK"))
    monkeypatch.setattr(pyautogui, "moveTo", lambda *a, **k: None)
    monkeypatch.setattr(pyautogui, "click", lambda *a, **k: None)

    # Simular match UIA
    mock_uia_match = {
        "name": "Aceptar",
        "type": "ButtonControl",
        "automation_id": "btnOk",
        "center": (300, 400)
    }
    monkeypatch.setattr(computer_use, "buscar_control_uia", lambda intent: mock_uia_match)

    # Mock del modelo visual para asegurar que NUNCA sea llamado
    mock_pedir_coords = MagicMock()
    monkeypatch.setattr(computer_use, "_pedir_coordenadas", mock_pedir_coords)

    res = hacer_clic_visual("haz clic en el botón Aceptar", verificar_exito=False, usar_niveles=True)
    assert res.is_unverified() or res.is_confirmed()
    assert res.data.get("tier") == 1
    assert res.data.get("source") == "uia"
    assert res.data.get("x") == 300
    assert res.data.get("y") == 400

    # COMPROBACIÓN CRÍTICA: 0 llamadas a la API multimodal
    assert mock_pedir_coords.call_count == 0


def test_hacer_clic_visual_resolves_tier_2_spatial_memory(monkeypatch):
    """Nivel 2: Si UIA falla pero Memoria Espacial tiene las coordenadas, no se llama a visión API."""
    import security_manager
    import pyautogui
    import spatial_memory
    import models_provider

    monkeypatch.setattr(security_manager, "is_gui_automation_allowed", lambda: (True, "OK"))
    monkeypatch.setattr(pyautogui, "size", lambda: (1920, 1080))
    monkeypatch.setattr(pyautogui, "moveTo", lambda *a, **k: None)
    monkeypatch.setattr(pyautogui, "click", lambda *a, **k: None)

    # UIA no lo encuentra
    monkeypatch.setattr(computer_use, "buscar_control_uia", lambda intent: None)

    # Memoria espacial SÍ lo tiene
    monkeypatch.setattr(spatial_memory, "get_cached_coordinates", lambda intent: [100, 200, 140, 240])

    mock_client = MagicMock()
    monkeypatch.setattr(models_provider, "get_client_and_model", lambda **k: (mock_client, "gemini-1.5-flash", "google"))

    mock_pedir_coords = MagicMock()
    monkeypatch.setattr(computer_use, "_pedir_coordenadas", mock_pedir_coords)

    res = hacer_clic_visual("icono de la papelera", verificar_exito=False, usar_niveles=True)
    assert res.data.get("tier") == 2
    assert res.data.get("source") == "spatial_memory"

    # COMPROBACIÓN CRÍTICA: 0 llamadas a _pedir_coordenadas de visión multimodal
    assert mock_pedir_coords.call_count == 0


def test_hacer_clic_visual_falls_back_to_tier_3_vision(monkeypatch):
    """Nivel 3: Si Nivel 1 y Nivel 2 fallan, recurre a visión multimodal API."""
    import security_manager
    import pyautogui
    import spatial_memory
    import models_provider

    monkeypatch.setattr(security_manager, "is_gui_automation_allowed", lambda: (True, "OK"))
    monkeypatch.setattr(pyautogui, "size", lambda: (1920, 1080))
    monkeypatch.setattr(pyautogui, "moveTo", lambda *a, **k: None)
    monkeypatch.setattr(pyautogui, "click", lambda *a, **k: None)

    # UIA falla
    monkeypatch.setattr(computer_use, "buscar_control_uia", lambda intent: None)
    # Memoria falla
    monkeypatch.setattr(spatial_memory, "get_cached_coordinates", lambda intent: None)

    mock_client = MagicMock()
    monkeypatch.setattr(models_provider, "get_client_and_model", lambda **k: (mock_client, "gemini-1.5-flash", "google"))
    monkeypatch.setattr(computer_use, "_capturar_pantalla_limpia", lambda: MagicMock())

    # Mock de visión API que detecta coordenadas
    monkeypatch.setattr(
        computer_use,
        "_pedir_coordenadas",
        lambda img, intent: {"box": (300, 400, 340, 480), "clicks": 1, "app": "Google (gemini-1.5-flash)", "target": intent}
    )

    res = hacer_clic_visual("botón dibujar en canvas web", verificar_exito=False, usar_niveles=True)
    assert res.data.get("tier") == 3
    assert res.data.get("source") == "vision_api"


# =========================================================================
# 4. SEGURIDAD: ACCIONES SENSIBLES BLOQUEADAS EN CUALQUIER NIVEL
# =========================================================================

def test_hacer_clic_visual_blocks_sensitive_before_any_tier():
    """Comprueba que una acción sensible (contraseña, 2FA, PIN) sea detenida antes de intentar UIA o Visión."""
    res = hacer_clic_visual("Ingresar la contraseña de root")
    assert res.requires_user() is True
    assert "contraseña" in res.requires_user_reason.lower() or "credencial" in res.requires_user_reason.lower()
