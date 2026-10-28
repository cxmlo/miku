"""
tests/test_action_verification.py - Pruebas automatizadas de resultados verdaderos,
detección de operaciones sensibles y prevención de falsos éxitos.

Estas pruebas utilizan mocks y fakes en memoria:
- Cero llamadas a APIs externas de pago.
- Cero movimientos del ratón real del usuario.
- Cero filtración o uso de secretos reales.
"""

import pytest
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from action_result import ActionResult, ActionStatus, check_sensitive_action
import computer_use
import brain

# 1. Pruebas de ActionStatus y ActionResult
def test_action_result_states_and_serialization():
    confirmed = ActionResult(
        status=ActionStatus.CONFIRMED.value,
        action="click_visual",
        target="Botón Reproducir",
        evidence="Icono de pausa visible tras el clic.",
        data={"x": 500, "y": 300}
    )
    assert confirmed.is_confirmed()
    assert not confirmed.is_failed()
    assert not confirmed.is_unverified()
    assert not confirmed.requires_user()
    
    agent_str = confirmed.to_agent_string()
    assert "Estado: CONFIRMED" in agent_str
    assert "Objetivo: Botón Reproducir" in agent_str
    assert "Evidencia: Icono de pausa visible" in agent_str

    parsed = ActionResult.parse(agent_str)
    assert parsed.status == ActionStatus.CONFIRMED.value
    assert parsed.action == "click_visual"
    assert parsed.target == "Botón Reproducir"

def test_action_result_failed_state():
    failed = ActionResult(
        status=ActionStatus.FAILED.value,
        action="click_element",
        target="Campo Inexistente",
        error="El control no fue encontrado en la ventana."
    )
    assert failed.is_failed()
    assert not confirmed_bool(failed)
    agent_str = failed.to_agent_string()
    assert "Estado: FAILED" in agent_str
    assert "Error: El control no fue encontrado" in agent_str

def confirmed_bool(res):
    return res.is_confirmed()

# 2. Pruebas de Detección de Operaciones Sensibles (requires_user)
@pytest.mark.parametrize("sensitive_text", [
    "Ingresa la contraseña de tu cuenta de Google",
    "Escribe el password del administrador",
    "Introduce el código 2FA recibido por SMS",
    "Confirmar clave del banco o PIN de tarjeta",
    "Autorizar pago de 50 dólares en la pasarela",
    "Introducir token de seguridad o API key secreta",
    "Aceptar diálogo UAC de elevación"
])
def test_sensitive_action_detection(sensitive_text):
    reason = check_sensitive_action(intent=sensitive_text)
    assert reason is not None
    assert "sensible" in reason.lower() or "seguridad" in reason.lower()

def test_safe_action_not_flagged_sensitive():
    reason = check_sensitive_action(intent="Hacer clic en la barra de búsqueda de Spotify y reproducir jazz")
    assert reason is None

# 3. Pruebas de Computer Use con Mocks
def test_hacer_clic_visual_sensitive_returns_requires_user(monkeypatch):
    monkeypatch.setattr(computer_use.security_manager, "is_gui_automation_allowed", lambda: (True, ""))
    
    res = computer_use.hacer_clic_visual("Escribir mi contraseña maestra en el gestor de claves")
    assert isinstance(res, ActionResult)
    assert res.status == ActionStatus.REQUIRES_USER.value
    assert res.requires_user()
    assert res.requires_user_reason is not None

def test_hacer_clic_visual_unverified_does_not_save_spatial_memory(monkeypatch):
    monkeypatch.setattr(computer_use.security_manager, "is_gui_automation_allowed", lambda: (True, ""))
    
    # Mocking PyAutoGUI to prevent real mouse movements
    monkeypatch.setattr(computer_use.pyautogui, "size", lambda: (1920, 1080))
    monkeypatch.setattr(computer_use.pyautogui, "moveTo", lambda *args, **kwargs: None)
    monkeypatch.setattr(computer_use.pyautogui, "click", lambda *args, **kwargs: None)
    
    # Mock screenshot and model coordinates
    dummy_img = MagicMock()
    monkeypatch.setattr(computer_use, "_capturar_pantalla_limpia", lambda: dummy_img)
    monkeypatch.setattr(computer_use, "_pedir_coordenadas", lambda img, intent: {
        "box": (100, 200, 120, 250),
        "clicks": 1,
        "app": "TestApp",
        "target": "Buscador"
    })
    
    # Mock spatial memory save to track if it's called
    saved = []
    monkeypatch.setattr(computer_use.spatial_memory, "get_cached_coordinates", lambda intent: None)
    monkeypatch.setattr(computer_use.spatial_memory, "save_coordinates", lambda intent, coords: saved.append((intent, coords)))

    # When verificar_exito is False
    res = computer_use.hacer_clic_visual("Hacer clic en el buscador", verificar_exito=False)
    
    assert res.status == ActionStatus.EXECUTED_UNVERIFIED.value
    assert not res.is_confirmed()
    assert len(saved) == 0, "No debe guardarse en memoria espacial si la acción quedó sin verificar"
    assert "No se solicitó verificación" in res.evidence

def test_hacer_clic_visual_verification_failure_stops_without_blind_click(monkeypatch):
    monkeypatch.setattr(computer_use.security_manager, "is_gui_automation_allowed", lambda: (True, ""))
    monkeypatch.setattr(computer_use.pyautogui, "size", lambda: (1920, 1080))
    monkeypatch.setattr(computer_use.pyautogui, "moveTo", lambda *args, **kwargs: None)
    
    clicks_count = 0
    def mock_click(*args, **kwargs):
        nonlocal clicks_count
        clicks_count += 1
    monkeypatch.setattr(computer_use.pyautogui, "click", mock_click)
    
    dummy_img = MagicMock()
    monkeypatch.setattr(computer_use, "_capturar_pantalla_limpia", lambda: dummy_img)
    monkeypatch.setattr(computer_use, "_capturar_pantalla_base64", lambda: "fake_b64")
    monkeypatch.setattr(computer_use, "_pedir_coordenadas", lambda img, intent: {
        "box": (100, 200, 120, 250),
        "clicks": 1,
        "app": "TestApp",
        "target": "Canción"
    })
    
    # Verification returns failure
    monkeypatch.setattr(computer_use, "_verificar_accion", lambda *args, **kwargs: (False, "La pantalla no cambió de estado", (150, 250, 160, 260)))
    monkeypatch.setattr(computer_use.spatial_memory, "get_cached_coordinates", lambda intent: None)

    saved = []
    monkeypatch.setattr(computer_use.spatial_memory, "save_coordinates", lambda intent, coords: saved.append((intent, coords)))

    res = computer_use.hacer_clic_visual("Reproducir tema", verificar_exito=True)
    
    assert res.status == ActionStatus.FAILED.value
    assert res.is_failed()
    assert clicks_count == 1, "No debe emitir un segundo clic ciego si la verificación determinó fallo"
    assert len(saved) == 0, "No debe guardarse en memoria espacial si la verificación falló"

def test_hacer_clic_visual_confirmed_saves_spatial_memory(monkeypatch):
    monkeypatch.setattr(computer_use.security_manager, "is_gui_automation_allowed", lambda: (True, ""))
    monkeypatch.setattr(computer_use.pyautogui, "size", lambda: (1920, 1080))
    monkeypatch.setattr(computer_use.pyautogui, "moveTo", lambda *args, **kwargs: None)
    monkeypatch.setattr(computer_use.pyautogui, "click", lambda *args, **kwargs: None)
    
    dummy_img = MagicMock()
    monkeypatch.setattr(computer_use, "_capturar_pantalla_limpia", lambda: dummy_img)
    monkeypatch.setattr(computer_use, "_capturar_pantalla_base64", lambda: "fake_b64")
    monkeypatch.setattr(computer_use, "_pedir_coordenadas", lambda img, intent: {
        "box": (100, 200, 120, 250),
        "clicks": 1,
        "app": "TestApp",
        "target": "Canción"
    })
    
    monkeypatch.setattr(computer_use, "_verificar_accion", lambda *args, **kwargs: (True, "Barra de progreso visible y reproduciendo", None))
    monkeypatch.setattr(computer_use.spatial_memory, "get_cached_coordinates", lambda intent: None)

    saved = []
    monkeypatch.setattr(computer_use.spatial_memory, "save_coordinates", lambda intent, coords: saved.append((intent, coords)))

    res = computer_use.hacer_clic_visual("Reproducir tema", verificar_exito=True)
    
    assert res.status == ActionStatus.CONFIRMED.value
    assert res.is_confirmed()
    assert len(saved) == 1
    assert "confirmado por inspección visual" in res.evidence

# 4. Pruebas de Orquestación en brain.py
def test_brain_never_reports_success_on_failed_tool(monkeypatch):
    """Verifica que si una herramienta falla en el ciclo, brain nunca devuelva 'He completado las acciones'"""
    
    # Mocking client to return a tool call
    fake_tool_call = MagicMock()
    fake_tool_call.id = "call_123"
    fake_tool_call.function.name = "hacer_clic_visual"
    fake_tool_call.function.arguments = '{"intencion": "abrir ventana"}'
    
    import models_provider

    fake_message = MagicMock()
    fake_message.tool_calls = [fake_tool_call]
    fake_message.content = None
    
    fake_choice = MagicMock()
    fake_choice.message = fake_message
    fake_choice.finish_reason = "tool_calls"
    
    fake_response = MagicMock()
    fake_response.choices = [fake_choice]
    
    # Router response
    router_msg = MagicMock()
    router_msg.content = "COMPUTE"
    router_choice = MagicMock()
    router_choice.message = router_msg
    router_resp = MagicMock()
    router_resp.choices = [router_choice]

    mock_client = MagicMock()
    def mock_create(**kwargs):
        msgs = kwargs.get("messages", [])
        if msgs and isinstance(msgs[0], dict) and "Eres el instinto de Miku" in str(msgs[0].get("content", "")):
            return router_resp
        return fake_response

    mock_client.chat.completions.create.side_effect = mock_create
    
    monkeypatch.setattr(models_provider, "get_client_and_model", lambda **kw: (mock_client, "fake-model", "test-prov"))
    
    # Tool execution returns a FAILED ActionResult
    failed_result = ActionResult(
        status=ActionStatus.FAILED.value,
        action="click_visual",
        error="Ventana no encontrada en pantalla."
    )
    monkeypatch.setitem(brain.available_functions, "hacer_clic_visual", lambda **kw: failed_result)

    reply = brain.get_llm_response("Abre la ventana")
    
    assert "completado las acciones solicitadas" not in reply.lower()
    assert "fallo" in reply.lower() or "falló" in reply.lower() or "error" in reply.lower()

def test_brain_reports_unverified_truthfully(monkeypatch):
    """Verifica que si una acción no fue verificada, brain no afirme éxito confirmado."""
    import models_provider

    fake_tool_call = MagicMock()
    fake_tool_call.id = "call_unverified"
    fake_tool_call.function.name = "hacer_clic_visual"
    fake_tool_call.function.arguments = '{"intencion": "clic en enlace"}'
    
    fake_message = MagicMock()
    fake_message.tool_calls = [fake_tool_call]
    fake_message.content = None
    
    fake_choice = MagicMock()
    fake_choice.message = fake_message
    fake_choice.finish_reason = "tool_calls"
    
    fake_response = MagicMock()
    fake_response.choices = [fake_choice]
    
    router_msg = MagicMock()
    router_msg.content = "COMPUTE"
    router_choice = MagicMock()
    router_choice.message = router_msg
    router_resp = MagicMock()
    router_resp.choices = [router_choice]

    mock_client = MagicMock()
    def mock_create(**kwargs):
        msgs = kwargs.get("messages", [])
        if msgs and isinstance(msgs[0], dict) and "Eres el instinto de Miku" in str(msgs[0].get("content", "")):
            return router_resp
        return fake_response

    mock_client.chat.completions.create.side_effect = mock_create
    
    monkeypatch.setattr(models_provider, "get_client_and_model", lambda **kw: (mock_client, "fake-model", "test-prov"))
    
    unverified_result = ActionResult(
        status=ActionStatus.EXECUTED_UNVERIFIED.value,
        action="click_visual",
        evidence="Clic emitido en (400, 200). Sin verificación de pantalla."
    )
    monkeypatch.setitem(brain.available_functions, "hacer_clic_visual", lambda **kw: unverified_result)

    reply = brain.get_llm_response("Haz clic en el enlace")
    
    assert "completado las acciones solicitadas" not in reply.lower()
    assert "sin confirmación" in reply.lower() or "sin verificar" in reply.lower() or "no se ha verificado" in reply.lower()

def test_brain_halts_immediately_on_requires_user(monkeypatch):
    """Verifica que brain se detenga de inmediato ante un requires_user sin continuar el bucle."""
    import models_provider

    fake_tool_call = MagicMock()
    fake_tool_call.id = "call_pwd"
    fake_tool_call.function.name = "hacer_clic_visual"
    fake_tool_call.function.arguments = '{"intencion": "introducir contraseña"}'
    
    fake_message = MagicMock()
    fake_message.tool_calls = [fake_tool_call]
    fake_message.content = None
    
    fake_choice = MagicMock()
    fake_choice.message = fake_message
    fake_choice.finish_reason = "tool_calls"
    
    fake_response = MagicMock()
    fake_response.choices = [fake_choice]
    
    router_msg = MagicMock()
    router_msg.content = "COMPUTE"
    router_choice = MagicMock()
    router_choice.message = router_msg
    router_resp = MagicMock()
    router_resp.choices = [router_choice]

    mock_client = MagicMock()
    def mock_create(**kwargs):
        msgs = kwargs.get("messages", [])
        if msgs and isinstance(msgs[0], dict) and "Eres el instinto de Miku" in str(msgs[0].get("content", "")):
            return router_resp
        return fake_response

    mock_client.chat.completions.create.side_effect = mock_create
    
    monkeypatch.setattr(models_provider, "get_client_and_model", lambda **kw: (mock_client, "fake-model", "test-prov"))
    
    req_user_res = ActionResult(
        status=ActionStatus.REQUIRES_USER.value,
        action="click_visual",
        requires_user_reason="Paso sensible de autenticación."
    )
    monkeypatch.setitem(brain.available_functions, "hacer_clic_visual", lambda **kw: req_user_res)

    reply = brain.get_llm_response("Ingresa mi clave")
    assert "⚠️ Acción detenida" in reply
    assert "intervención directa" in reply or "sensible" in reply

def test_brain_records_tool_and_assistant_history_on_requires_user(monkeypatch):
    """Verifica que requires_user selle el historial con rol tool y assistant para no romper OpenAI/Google con HTTP 400."""
    import models_provider

    fake_tool_call = MagicMock()
    fake_tool_call.id = "call_auth_123"
    fake_tool_call.function.name = "hacer_clic_visual"
    fake_tool_call.function.arguments = '{"intencion": "clic en login"}'

    fake_message = MagicMock()
    fake_message.tool_calls = [fake_tool_call]
    fake_message.content = None

    fake_choice = MagicMock()
    fake_choice.message = fake_message
    fake_choice.finish_reason = "tool_calls"

    fake_response = MagicMock()
    fake_response.choices = [fake_choice]

    router_msg = MagicMock()
    router_msg.content = "COMPUTE"
    router_choice = MagicMock()
    router_choice.message = router_msg
    router_resp = MagicMock()
    router_resp.choices = [router_choice]

    mock_client = MagicMock()
    def mock_create(**kwargs):
        msgs = kwargs.get("messages", [])
        if msgs and isinstance(msgs[0], dict) and "Eres el instinto de Miku" in str(msgs[0].get("content", "")):
            return router_resp
        return fake_response

    mock_client.chat.completions.create.side_effect = mock_create
    monkeypatch.setattr(models_provider, "get_client_and_model", lambda **kw: (mock_client, "fake-model", "test-prov"))

    req_user_res = ActionResult(
        status=ActionStatus.REQUIRES_USER.value,
        action="click_visual",
        requires_user_reason="Paso sensible de autenticación."
    )
    monkeypatch.setitem(brain.available_functions, "hacer_clic_visual", lambda **kw: req_user_res)

    brain.conversation_history.clear()
    reply = brain.get_llm_response("Inicia sesión")

    assert "⚠️ Acción detenida" in reply
    # El historial debe tener: [system, user, assistant_with_tool_calls, tool_response, assistant_stop_msg]
    tool_msgs = [m for m in brain.conversation_history if isinstance(m, dict) and m.get("role") == "tool"]
    assert len(tool_msgs) >= 1
    assert tool_msgs[0].get("tool_call_id") == "call_auth_123"
    assert tool_msgs[0].get("name") == "hacer_clic_visual"
    
    last_msg = brain.conversation_history[-1]
    assert isinstance(last_msg, dict) and last_msg.get("role") == "assistant"
    assert "⚠️ Acción detenida" in last_msg.get("content", "")


def test_escribir_texto_con_en_campo_calls_hacer_clic_visual(monkeypatch):
    import tools_os
    import computer_use

    clicked_targets = []
    def mock_clic(intencion, **kw):
        clicked_targets.append(intencion)
        return ActionResult(
            status=ActionStatus.EXECUTED_UNVERIFIED.value,
            action="click_visual",
            target=intencion,
            evidence=f"Clic emitido en {intencion}"
        )

    monkeypatch.setattr(computer_use, "hacer_clic_visual", mock_clic)
    
    # Mock pyautogui y pyperclip
    copied_texts = []
    hotkeys_pressed = []
    presses = []
    monkeypatch.setattr("pyperclip.copy", lambda txt: copied_texts.append(txt))
    monkeypatch.setattr("pyautogui.hotkey", lambda *args: hotkeys_pressed.append(args))
    monkeypatch.setattr("pyautogui.press", lambda key: presses.append(key))

    res = tools_os.escribir_texto(
        texto="canción anime @2026",
        presionar_enter=True,
        limpiar_antes=True,
        en_campo="barra de búsqueda de youtube"
    )

    assert len(clicked_targets) == 1
    assert clicked_targets[0] == "barra de búsqueda de youtube"
    assert "canción anime @2026" in copied_texts
    assert ('ctrl', 'v') in hotkeys_pressed
    assert 'enter' in presses
    assert res.is_confirmed() or res.is_executed_unverified()
    assert "barra de búsqueda de youtube" in res.evidence

